"""Module to handle endpoint responses"""

import logging
import unicodedata
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Path, status
from fastapi_cache.decorator import cache

from orcid_service_server.handler import SessionHandler
from orcid_service_server.models import ExpandedResult, HealthCheck, OrcidId
from orcid_service_server.session import get_session

router = APIRouter()

# "allen institute" rather than "allen", which also matches unrelated
# organizations such as the law firm Allen and Overy.
ALLEN_INSTITUTION = "allen institute"
ALLEN_DOMAIN = "alleninstitute.org"
# Verified email domains take one request per candidate, so they are only
# worth spending on a short list of namesakes.
MAX_DOMAIN_CHECKS = 10
# Successful lookups are cached. A 404 raises, so misses are never cached
# and are re-checked on the next request, which is what lets someone who
# has just added an affiliation to their ORCID record verify it at once.
# Send "Cache-Control: no-cache" to force a refresh of a cached hit.
CACHE_SECONDS = 86400


def fold_name(name: str) -> str:
    """Lowercase a name and drop accents, so Jerome matches Jérôme."""
    decomposed = unicodedata.normalize("NFKD", name)
    unaccented = "".join(
        char for char in decomposed if not unicodedata.combining(char)
    )
    return " ".join(unaccented.lower().split())


def name_matches(result: ExpandedResult, folded_name: str) -> bool:
    """
    Check that a result belongs to the person searched for. The default
    ORCID field indexes whole records, so a hit can come from a work title
    rather than from the record owner's own name.
    """
    given = result.given_names or ""
    family = result.family_names or ""
    known_names = [f"{given} {family}", result.credit_name or ""]
    known_names.extend(result.other_name)
    return any(fold_name(known) == folded_name for known in known_names)


def is_allen_record(result: ExpandedResult) -> bool:
    """
    Check a search result for an Allen institution name or a full Allen
    email address. The address is only in the payload when the person made
    it public, which is rare; verified email domains cover the rest.
    """
    return any(
        ALLEN_INSTITUTION in institution.lower()
        for institution in result.institution_name
    ) or any(
        email.lower().endswith(f"@{ALLEN_DOMAIN}") for email in result.email
    )


async def match_by_email_domain(
    handler: SessionHandler, results: List[ExpandedResult]
) -> List[str]:
    """
    Return the iDs whose record summary lists a verified Allen email
    domain. That endpoint is undocumented, so a failed lookup counts as no
    signal rather than an error.
    """
    matches = []
    for result in results:
        try:
            domains = await handler.get_email_domains(result.orcid_id)
        except Exception as error:
            logging.warning(
                f"ORCID summary failed for {result.orcid_id}: {error}"
            )
            continue
        if ALLEN_DOMAIN in domains:
            matches.append(result.orcid_id)
    return matches


async def resolve_orcid_id(name: str) -> Optional[str]:
    """
    Resolve a name to an ORCID iD, or None when the match is not
    definitive.
    """
    folded_name = fold_name(name)
    async with get_session() as session:
        handler = SessionHandler(session=session)
        results = [
            result
            for result in await handler.search_by_name(name)
            if name_matches(result, folded_name)
        ]

        # A name match alone would resolve an unregistered AIND person to
        # a stranger who shares their name, so an Allen signal is required
        # too. Institutions and public emails come back with the search.
        matches = [
            result.orcid_id for result in results if is_allen_record(result)
        ]
        if len(matches) == 1:
            return matches[0]

        # Nobody stood out, so check verified email domains as well.
        if 0 < len(results) <= MAX_DOMAIN_CHECKS:
            matches = await match_by_email_domain(handler, results)
            if len(matches) == 1:
                return matches[0]

    if results:
        logging.warning(
            f"Ambiguous ORCID search for {name}: {len(results)} name"
            f" matches, none uniquely tied to Allen"
        )
    return None


@router.get(
    "/healthcheck",
    tags=["healthcheck"],
    summary="Perform a Health Check",
    response_description="Return HTTP Status Code 200 (OK)",
    status_code=status.HTTP_200_OK,
    response_model=HealthCheck,
)
async def get_health() -> HealthCheck:
    """
    ## Endpoint to perform a healthcheck on.

    Returns:
        HealthCheck: Returns a JSON response with the health status
    """
    return HealthCheck()


@router.get("/orcid/{name}", response_model=OrcidId)
@cache(expire=CACHE_SECONDS)
async def get_orcid(
    name: str = Path(
        ...,
        examples=["Jerome Lecoq", "Saskia de Vries"],
        description="A researcher's given and family name.",
    ),
):
    """
    ## ORCID
    Return an Allen Institute researcher's ORCID iD, or 404 when the
    match is not definitive.

    We require the full name to match the name on the record, ignoring
    case and accents, plus one of the following must be true:

    - The record lists an Allen institution or a public Allen email
      address, found in the expanded-search endpoint results, or
    - The record summary lists a verified Allen email domain, found in a
      follow-up request to the summary endpoint.

    Calls to the summary endpoint require a request each, so they are
    capped at MAX_DOMAIN_CHECKS, which defaults to 10. Users with common
    names may exceed that limit. However, setting the affiliation to an
    Allen institution or a public Allen email address will guarantee a
    match without needing to check the summary endpoint, which is preferred.
    """
    # Quotes and backslashes would break the quoted Solr query.
    name_parts = name.replace('"', "").replace("\\", "").split()
    if len(name_parts) < 2:
        raise HTTPException(
            status_code=400,
            detail="Name must have given name(s) and a family name",
        )
    orcid_id = await resolve_orcid_id(name=" ".join(name_parts))
    if orcid_id is None:
        raise HTTPException(status_code=404, detail="Not found")
    return OrcidId(orcid=orcid_id)

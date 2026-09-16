"""Module to handle endpoint responses"""

import logging
import unicodedata
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Path, status
from fastapi_cache.decorator import cache

from orcid_service_server.handler import ALLEN_DOMAIN, SessionHandler
from orcid_service_server.models import ExpandedResult, HealthCheck, OrcidId
from orcid_service_server.session import get_session

router = APIRouter()

# Verified email domains are the one Allen signal ORCID does not index,
# so they take a request per candidate and are only worth spending on a
# short list of namesakes.
MAX_DOMAIN_CHECKS = 10
CACHE_SECONDS = 86400


def name_tokens(name: str) -> List[str]:
    """
    Reduce a name to sorted, lowercased, unaccented tokens. Sorting makes
    the comparison order-insensitive, so a record whose given and family
    names were entered the wrong way round still matches.
    """
    # NFKD splits an accented character into its base letter plus a
    # separate combining mark, so "é" becomes "e" + U+0301.
    decomposed = unicodedata.normalize("NFKD", name)
    # Dropping every combining mark then leaves the bare letters behind,
    # turning "Jérôme" into "Jerome". Letters that are not a base plus an
    # accent, such as "ø" and "ł", have nothing to strip and survive as
    # they are. ORCID does not fold those either, so this matches it.
    unaccented = "".join(
        char for char in decomposed if not unicodedata.combining(char)
    )
    # Sorting is what makes the comparison order-insensitive.
    return sorted(unaccented.lower().split())


def name_matches(result: ExpandedResult, wanted: List[str]) -> bool:
    """
    Check that a result belongs to the person searched for. The default
    ORCID field indexes whole records, so a hit can come from a work title
    rather than from the record owner's own name.
    """
    given = result.given_names or ""
    family = result.family_names or ""
    known_names = [f"{given} {family}", result.credit_name or ""]
    known_names.extend(result.other_name)
    return any(name_tokens(known) == wanted for known in known_names)


async def match_by_email_domain(
    handler: SessionHandler, results: List[ExpandedResult]
) -> List[str]:
    """
    Return the iDs whose record summary lists a verified Allen email
    domain. Only reached when someone has recorded no affiliation and no
    public Allen email, since otherwise the first search resolves them.

    This uses the summary endpoint rather than the standard public API.
    ORCID does not document that endpoint; it is what their own website
    calls to draw a record page, and we found it by looking at what that
    page fetches. Nothing stops them changing or removing it, so
    failures are caught and treated as no answer. If it goes away we
    lose only the people who could not be resolved the normal way.
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
    wanted = name_tokens(name)
    async with get_session() as session:
        handler = SessionHandler(session=session)

        # Ask ORCID for people with this name who it already knows are at
        # Allen. Doing it in the query rather than by filtering afterwards
        # stays exact for names with hundreds of holders, where a
        # name-only search would only return the first page of results.
        matches = [
            result.orcid_id
            for result in await handler.search_by_name(name, allen_only=True)
            if name_matches(result, wanted)
        ]
        if len(matches) == 1:
            return matches[0]

        # Nobody, or too many. Plenty of people record no affiliation and
        # keep their address private, and ORCID does not index the
        # verified email domain that would identify them, so fall back to
        # the name alone and read the domain off each candidate.
        results = [
            result
            for result in await handler.search_by_name(name)
            if name_matches(result, wanted)
        ]
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
    case, accents, and the order of the name parts, plus one of the
    following must be true:

    - ORCID lists an Allen institution or a public Allen email address on
      the record. We ask for this in the search itself rather than
      filtering afterwards, so the answer stays exact even for a name
      shared by hundreds of people.
    - The record summary lists a verified Allen email domain. ORCID does
      not index that, so finding it takes a second search on the name
      alone followed by one request per candidate.

    Those per-candidate requests are capped at MAX_DOMAIN_CHECKS, which
    defaults to 10, so someone with a common name and no affiliation may
    never reach that check. Setting the affiliation to an Allen
    institution or a public Allen email address will guarantee a match on
    the first search, which is preferred.
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

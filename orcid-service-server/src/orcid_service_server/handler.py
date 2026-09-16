"""Module to retrieve data from ORCID using a session object"""

import logging
from typing import List

from httpx import AsyncClient

from orcid_service_server.configs import settings
from orcid_service_server.models import (
    ExpandedResult,
    ExpandedSearch,
    RecordSummary,
)

# ORCID indexes affiliations and public emails, so it can filter to Allen
# people server-side. The phrase "Allen Institute" also excludes unrelated
# organizations such as the law firm Allen and Overy.
ALLEN_DOMAIN = "alleninstitute.org"
ALLEN_CLAUSE = (
    '(affiliation-org-name:"Allen Institute"' f" OR email:*@{ALLEN_DOMAIN})"
)


class SessionHandler:
    """Handle session object to get data"""

    def __init__(self, session: AsyncClient):
        """Class constructor"""
        self.session = session

    async def search_by_name(
        self, name: str, allen_only: bool = False
    ) -> List[ExpandedResult]:
        """
        Search the ORCID registry for a name.

        Every token is required, in any order, on the default Solr field.
        That field folds accents, and requiring tokens rather than an
        ordered phrase means we never guess which of them make up the
        family name, and still match records where the given and family
        names were entered the wrong way round. Each token is quoted so
        that a hyphen is read as part of the name rather than as Solr's
        NOT operator.

        Parameters
        ----------
        name : str
        allen_only : bool
          Also require an Allen institution or a public Allen email.
          ORCID applies this itself, so the result is exact even for a
          name with hundreds of holders, where asking for the name alone
          would return only the first page. Default is False.

        Returns
        -------
        List[ExpandedResult]

        """
        logging.debug(f"Searching ORCID for {name}")
        query = " AND ".join(f'"{token}"' for token in name.split())
        if allen_only:
            query = f"{query} AND {ALLEN_CLAUSE}"
        response = await self.session.get(
            "/v3.0/expanded-search/",
            params={"q": query, "rows": 50},
        )
        response.raise_for_status()
        search = ExpandedSearch(**response.json())
        return search.expanded_result or []

    async def get_email_domains(self, orcid_id: str) -> List[str]:
        """
        Get the verified email domains on a record.

        ORCID verifies the domain of an email even when the address itself
        is private, so this identifies people who recorded no affiliation.
        It is absent from the public API and from the search index, and is
        only served by the record summary the ORCID website itself calls.

        Parameters
        ----------
        orcid_id : str

        Returns
        -------
        List[str]

        """
        summary_host = settings.summary_host.unicode_string().rstrip("/")
        response = await self.session.get(
            f"{summary_host}/{orcid_id}/summary.json"
        )
        response.raise_for_status()
        summary = RecordSummary(**response.json())
        return [
            domain.value.lower()
            for domain in summary.email_domains
            if domain.value
        ]

"""Test routes"""

import pytest
from httpx import URL
from pytest_httpx import HTTPXMock
from starlette.testclient import TestClient

SEARCH_URL = "http://example.com/pub/v3.0/expanded-search/"
SUMMARY_URL = "http://example.com/{orcid_id}/summary.json"
ALLEN_CLAUSE = (
    '(affiliation-org-name:"Allen Institute" OR email:*@alleninstitute.org)'
)


def solr_query(name: str, allen_only: bool = False) -> str:
    """Build the query the service sends: every token, quoted, ANDed."""
    query = " AND ".join(f'"{token}"' for token in name.split())
    return f"{query} AND {ALLEN_CLAUSE}" if allen_only else query


def add_search(
    httpx_mock: HTTPXMock,
    name: str,
    *results: dict,
    allen_only: bool = False,
) -> None:
    """Queue an expanded-search response for one stage of the lookup."""
    httpx_mock.add_response(
        url=URL(
            SEARCH_URL,
            params={"q": solr_query(name, allen_only), "rows": 50},
        ),
        json={
            "expanded-result": list(results) or None,
            "num-found": len(results),
        },
    )


def add_summary(httpx_mock: HTTPXMock, orcid_id: str, *domains: str) -> None:
    """Queue a record summary response for an orcid id."""
    httpx_mock.add_response(
        url=SUMMARY_URL.format(orcid_id=orcid_id),
        json={"emailDomains": [{"value": d} for d in domains]},
    )


def person(orcid_id: str, given: str, family: str, **extra: object) -> dict:
    """Build a search result. Names and iDs are placeholders; the
    0000-0000-* iD range is unassigned by ORCID."""
    return {
        "orcid-id": orcid_id,
        "given-names": given,
        "family-names": family,
        **extra,
    }


class TestHealthcheckRoute:
    """Test healthcheck responses."""

    def test_get_health(self, client: TestClient):
        """Tests a good response"""
        response = client.get("/healthcheck")
        assert 200 == response.status_code
        assert "OK" == response.json()["status"]


class TestOrcidRoute:
    """Test orcid responses."""

    def test_get_orcid(self, client: TestClient, httpx_mock: HTTPXMock):
        """Tests a match found by the Allen constrained search"""
        add_search(
            httpx_mock,
            "Researcher One",
            person("0000-0000-0000-0011", "Researcher", "One"),
            allen_only=True,
        )

        response = client.get("/orcid/Researcher One")

        assert 200 == response.status_code
        assert {"orcid": "0000-0000-0000-0011"} == response.json()
        # One request only: ORCID did the Allen filtering itself.
        assert 1 == len(httpx_mock.get_requests())

    def test_allen_filter_is_applied_in_the_query(
        self, client: TestClient, httpx_mock: HTTPXMock
    ):
        """Tests the query asks ORCID for Allen people specifically"""
        add_search(
            httpx_mock,
            "Researcher One",
            person("0000-0000-0000-0011", "Researcher", "One"),
            allen_only=True,
        )

        client.get("/orcid/Researcher One")

        sent = httpx_mock.get_requests()[0].url.params["q"]
        # "Allen Institute" as a phrase, so the law firm Allen and Overy
        # is excluded by ORCID rather than filtered out afterwards.
        assert '"Researcher" AND "One" AND ' in sent
        assert 'affiliation-org-name:"Allen Institute"' in sent
        assert "email:*@alleninstitute.org" in sent

    def test_get_orcid_ignores_contaminating_hit(
        self, client: TestClient, httpx_mock: HTTPXMock
    ):
        """Tests a record matched on something other than its own name"""
        # The default ORCID field indexes whole records, so a search can
        # return someone whose work merely cites the person searched for.
        add_search(
            httpx_mock,
            "Researcher One",
            person("0000-0000-0000-0011", "Researcher", "One"),
            person("0000-0000-0000-9999", "Other", "Person"),
            allen_only=True,
        )

        response = client.get("/orcid/Researcher One")

        assert 200 == response.status_code
        assert {"orcid": "0000-0000-0000-0011"} == response.json()

    def test_get_orcid_accented_record(
        self, client: TestClient, httpx_mock: HTTPXMock
    ):
        """Tests an unaccented name matches an accented record"""
        # Models the real Jerome/Jérôme Lecoq case: the default ORCID
        # field folds accents, the fielded name indexes do not.
        add_search(
            httpx_mock,
            "Accented Researcher",
            person("0000-0000-0000-0012", "Áccented", "Researcher"),
            allen_only=True,
        )

        response = client.get("/orcid/Accented Researcher")

        assert 200 == response.status_code
        assert {"orcid": "0000-0000-0000-0012"} == response.json()

    def test_get_orcid_reversed_name_fields(
        self, client: TestClient, httpx_mock: HTTPXMock
    ):
        """Tests a record whose given and family names are swapped"""
        # Models the real Karel Svoboda record, filed as
        # given-names="svoboda", family-names="karel". Requiring tokens in
        # any order, and comparing sorted tokens, is what catches it.
        add_search(
            httpx_mock,
            "Researcher Four",
            person("0000-0000-0000-0019", "Four", "Researcher"),
            allen_only=True,
        )

        response = client.get("/orcid/Researcher Four")

        assert 200 == response.status_code
        assert {"orcid": "0000-0000-0000-0019"} == response.json()

    def test_get_orcid_verified_email_domain(
        self, client: TestClient, httpx_mock: HTTPXMock
    ):
        """Tests a record with no affiliation resolved by email domain"""
        # Models the real Saskia de Vries case: a multi-token surname, no
        # affiliation and a private address, so ORCID cannot filter for
        # her, plus two same-named stub records. Only the verified email
        # domain separates them.
        namesakes = [
            person(orcid_id, "Multi", "Token Surname")
            for orcid_id in [
                "0000-0000-0000-0014",
                "0000-0000-0000-0015",
                "0000-0000-0000-0013",
            ]
        ]
        add_search(httpx_mock, "Multi Token Surname", allen_only=True)
        add_search(httpx_mock, "Multi Token Surname", *namesakes)
        add_summary(httpx_mock, "0000-0000-0000-0014")
        add_summary(httpx_mock, "0000-0000-0000-0015")
        add_summary(httpx_mock, "0000-0000-0000-0013", "alleninstitute.org")

        response = client.get("/orcid/Multi Token Surname")

        assert 200 == response.status_code
        assert {"orcid": "0000-0000-0000-0013"} == response.json()

    def test_get_orcid_summary_lookup_failure(
        self, client: TestClient, httpx_mock: HTTPXMock
    ):
        """Tests a failed summary lookup counts as no signal"""
        add_search(httpx_mock, "Multi Token Surname", allen_only=True)
        add_search(
            httpx_mock,
            "Multi Token Surname",
            person("0000-0000-0000-0001", "Multi", "Token Surname"),
            person("0000-0000-0000-0002", "Multi", "Token Surname"),
        )
        for orcid_id in ["0000-0000-0000-0001", "0000-0000-0000-0002"]:
            httpx_mock.add_response(
                url=SUMMARY_URL.format(orcid_id=orcid_id), status_code=500
            )

        response = client.get("/orcid/Multi Token Surname")

        assert 404 == response.status_code
        assert {"detail": "Not found"} == response.json()

    def test_get_orcid_lone_match_without_allen_signal(
        self, client: TestClient, httpx_mock: HTTPXMock
    ):
        """Tests a lone name match with nothing tying it to Allen"""
        # An entirely empty ORCID record. Unique on name, but nothing says
        # it belongs to the AIND person being looked up.
        add_search(httpx_mock, "Researcher Five", allen_only=True)
        add_search(
            httpx_mock,
            "Researcher Five",
            person("0000-0000-0000-0018", "Researcher", "Five"),
        )
        add_summary(httpx_mock, "0000-0000-0000-0018")

        response = client.get("/orcid/Researcher Five")

        assert 404 == response.status_code
        assert {"detail": "Not found"} == response.json()

    def test_get_orcid_too_many_candidates(
        self, client: TestClient, httpx_mock: HTTPXMock
    ):
        """Tests no summary lookups when the candidate list is long"""
        from orcid_service_server.route import MAX_DOMAIN_CHECKS

        add_search(httpx_mock, "Common Name", allen_only=True)
        add_search(
            httpx_mock,
            "Common Name",
            *[
                person(f"0000-0000-0000-{index:04d}", "Common", "Name")
                for index in range(MAX_DOMAIN_CHECKS + 1)
            ],
        )

        response = client.get("/orcid/Common Name")

        assert 404 == response.status_code
        # The two searches only, no per-candidate summary lookups.
        assert 2 == len(httpx_mock.get_requests())

    def test_get_orcid_not_found(
        self, client: TestClient, httpx_mock: HTTPXMock
    ):
        """Tests a search with no results at either stage"""
        add_search(httpx_mock, "Unknown Researcher", allen_only=True)
        add_search(httpx_mock, "Unknown Researcher")

        response = client.get("/orcid/Unknown Researcher")

        assert 404 == response.status_code
        assert {"detail": "Not found"} == response.json()

    def test_get_orcid_invalid_name(self, client: TestClient):
        """Tests a name without a family name is rejected"""
        response = client.get("/orcid/OneToken")

        assert 400 == response.status_code


if __name__ == "__main__":
    pytest.main([__file__])

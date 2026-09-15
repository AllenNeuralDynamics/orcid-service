"""Test routes"""

import pytest
from httpx import URL
from pytest_httpx import HTTPXMock
from starlette.testclient import TestClient

SEARCH_URL = "http://example.com/pub/v3.0/expanded-search/"
SUMMARY_URL = "http://example.com/{orcid_id}/summary.json"


def add_search(httpx_mock: HTTPXMock, name: str, *results: dict) -> None:
    """Queue an expanded-search response for a name."""
    httpx_mock.add_response(
        url=URL(SEARCH_URL, params={"q": f'"{name}"', "rows": 50}),
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
        """Tests one Allen record among the name matches is returned"""
        # Names and iDs throughout these tests are placeholders; the
        # 0000-0000-* iD range is unassigned by ORCID. The second result
        # models a record matched on a work title rather than on its
        # owner's name, which is what the name check filters out.
        add_search(
            httpx_mock,
            "Researcher One",
            {
                "orcid-id": "0000-0000-0000-0011",
                "given-names": "Researcher",
                "family-names": "One",
                "institution-name": ["Allen Institute for Neural Dynamics"],
            },
            # Matched on a work title, not on the record owner's name.
            {
                "orcid-id": "0000-0000-0000-9999",
                "given-names": "Other",
                "family-names": "Person",
            },
        )

        response = client.get("/orcid/Researcher One")

        assert 200 == response.status_code
        assert {"orcid": "0000-0000-0000-0011"} == response.json()

    def test_get_orcid_accented_record(
        self, client: TestClient, httpx_mock: HTTPXMock
    ):
        """Tests an unaccented name matches an accented record"""
        # Models the real Jerome/Jérôme Lecoq case: fielded ORCID search
        # does not fold accents, so an ASCII query would otherwise miss.
        add_search(
            httpx_mock,
            "Accented Researcher",
            {
                "orcid-id": "0000-0000-0000-0012",
                "given-names": "Áccented",
                "family-names": "Researcher",
                "institution-name": ["Allen Institute"],
            },
        )

        response = client.get("/orcid/Accented Researcher")

        assert 200 == response.status_code
        assert {"orcid": "0000-0000-0000-0012"} == response.json()

    def test_get_orcid_ignores_unrelated_allen(
        self, client: TestClient, httpx_mock: HTTPXMock
    ):
        """Tests the law firm Allen and Overy is not an Allen institution"""
        # Allen and Overy is a real firm with ORCID-registered staff,
        # which is why the institution check is not just "allen".
        add_search(
            httpx_mock,
            "Researcher Two",
            {
                "orcid-id": "0000-0000-0000-0001",
                "given-names": "Researcher",
                "family-names": "Two",
                "institution-name": ["Allen and Overy"],
            },
            {
                "orcid-id": "0000-0000-0000-0016",
                "given-names": "Researcher",
                "family-names": "Two",
                "institution-name": ["Allen Institute for Brain Science"],
            },
        )

        response = client.get("/orcid/Researcher Two")

        assert 200 == response.status_code
        assert {"orcid": "0000-0000-0000-0016"} == response.json()

    def test_get_orcid_allen_email(
        self, client: TestClient, httpx_mock: HTTPXMock
    ):
        """Tests a public Allen email address resolves a tie"""
        # Only a handful of records expose a public Allen address, so
        # this signal is high precision and low recall.
        add_search(
            httpx_mock,
            "Researcher Three",
            {
                "orcid-id": "0000-0000-0000-0001",
                "given-names": "Researcher",
                "family-names": "Three",
                "email": ["someone@example.edu"],
            },
            {
                "orcid-id": "0000-0000-0000-0017",
                "credit-name": "Researcher Three",
                "email": ["researcher.three@AllenInstitute.org"],
            },
        )

        response = client.get("/orcid/Researcher Three")

        assert 200 == response.status_code
        assert {"orcid": "0000-0000-0000-0017"} == response.json()

    def test_get_orcid_verified_email_domain(
        self, client: TestClient, httpx_mock: HTTPXMock
    ):
        """Tests a record with no affiliation resolved by email domain"""
        # Models the real Saskia de Vries case: a multi-token surname,
        # no affiliation on the record, and two same-named stub records.
        # Only the verified email domain separates them.
        namesakes = [
            {
                "orcid-id": orcid_id,
                "given-names": "Multi",
                "family-names": "Token Surname",
            }
            for orcid_id in [
                "0000-0000-0000-0014",
                "0000-0000-0000-0015",
                "0000-0000-0000-0013",
            ]
        ]
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
        add_search(
            httpx_mock,
            "Multi Token Surname",
            {
                "orcid-id": "0000-0000-0000-0001",
                "given-names": "Multi",
                "family-names": "Token Surname",
            },
            {
                "orcid-id": "0000-0000-0000-0002",
                "given-names": "Multi",
                "family-names": "Token Surname",
            },
        )
        httpx_mock.add_response(
            url=SUMMARY_URL.format(orcid_id="0000-0000-0000-0001"),
            status_code=500,
        )
        httpx_mock.add_response(
            url=SUMMARY_URL.format(orcid_id="0000-0000-0000-0002"),
            status_code=500,
        )

        response = client.get("/orcid/Multi Token Surname")

        assert 404 == response.status_code
        assert {"detail": "Not found"} == response.json()

    def test_get_orcid_lone_match_without_allen_signal(
        self, client: TestClient, httpx_mock: HTTPXMock
    ):
        """Tests a lone name match with nothing tying it to Allen"""
        # An entirely empty ORCID record. Unique on name, but nothing
        # says it belongs to the AIND person being looked up.
        add_search(
            httpx_mock,
            "Researcher Five",
            {
                "orcid-id": "0000-0000-0000-0018",
                "given-names": "Researcher",
                "family-names": "Five",
            },
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

        add_search(
            httpx_mock,
            "Common Name",
            *[
                {
                    "orcid-id": f"0000-0000-0000-{index:04d}",
                    "given-names": "Common",
                    "family-names": "Name",
                }
                for index in range(MAX_DOMAIN_CHECKS + 1)
            ],
        )

        response = client.get("/orcid/Common Name")

        assert 404 == response.status_code
        # Only the search was called, no summary lookups.
        assert 1 == len(httpx_mock.get_requests())

    def test_get_orcid_not_found(
        self, client: TestClient, httpx_mock: HTTPXMock
    ):
        """Tests a search with no results"""
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

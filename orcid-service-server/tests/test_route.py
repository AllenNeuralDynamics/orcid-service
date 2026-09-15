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
        add_search(
            httpx_mock,
            "Daniel Birman",
            {
                "orcid-id": "0000-0003-3748-6289",
                "given-names": "Daniel",
                "family-names": "Birman",
                "institution-name": ["Allen Institute for Neural Dynamics"],
            },
            # Matched on a work title, not on the record owner's name.
            {
                "orcid-id": "0000-0000-0000-9999",
                "given-names": "Someone",
                "family-names": "Else",
            },
        )

        response = client.get("/orcid/Daniel Birman")

        assert 200 == response.status_code
        assert {"orcid": "0000-0003-3748-6289"} == response.json()

    def test_get_orcid_accented_record(
        self, client: TestClient, httpx_mock: HTTPXMock
    ):
        """Tests an unaccented name matches an accented record"""
        add_search(
            httpx_mock,
            "Jerome Lecoq",
            {
                "orcid-id": "0000-0002-0131-0938",
                "given-names": "Jérôme",
                "family-names": "Lecoq",
                "institution-name": ["Allen Institute"],
            },
        )

        response = client.get("/orcid/Jerome Lecoq")

        assert 200 == response.status_code
        assert {"orcid": "0000-0002-0131-0938"} == response.json()

    def test_get_orcid_ignores_unrelated_allen(
        self, client: TestClient, httpx_mock: HTTPXMock
    ):
        """Tests the law firm Allen and Overy is not an Allen institution"""
        add_search(
            httpx_mock,
            "David Feng",
            {
                "orcid-id": "0000-0000-0000-0001",
                "given-names": "David",
                "family-names": "Feng",
                "institution-name": ["Allen and Overy"],
            },
            {
                "orcid-id": "0000-0002-4920-8123",
                "given-names": "David",
                "family-names": "Feng",
                "institution-name": ["Allen Institute for Brain Science"],
            },
        )

        response = client.get("/orcid/David Feng")

        assert 200 == response.status_code
        assert {"orcid": "0000-0002-4920-8123"} == response.json()

    def test_get_orcid_allen_email(
        self, client: TestClient, httpx_mock: HTTPXMock
    ):
        """Tests a public Allen email address resolves a tie"""
        add_search(
            httpx_mock,
            "Galen Lynch",
            {
                "orcid-id": "0000-0000-0000-0001",
                "given-names": "Galen",
                "family-names": "Lynch",
                "email": ["someone@example.edu"],
            },
            {
                "orcid-id": "0000-0003-4307-0247",
                "credit-name": "Galen Lynch",
                "email": ["Galen.Lynch@AllenInstitute.org"],
            },
        )

        response = client.get("/orcid/Galen Lynch")

        assert 200 == response.status_code
        assert {"orcid": "0000-0003-4307-0247"} == response.json()

    def test_get_orcid_verified_email_domain(
        self, client: TestClient, httpx_mock: HTTPXMock
    ):
        """Tests a record with no affiliation resolved by email domain"""
        namesakes = [
            {
                "orcid-id": orcid_id,
                "given-names": "Saskia",
                "family-names": "de Vries",
            }
            for orcid_id in [
                "0009-0001-8211-0777",
                "0009-0009-1997-9515",
                "0000-0002-3704-3499",
            ]
        ]
        add_search(httpx_mock, "Saskia de Vries", *namesakes)
        add_summary(httpx_mock, "0009-0001-8211-0777")
        add_summary(httpx_mock, "0009-0009-1997-9515")
        add_summary(httpx_mock, "0000-0002-3704-3499", "alleninstitute.org")

        response = client.get("/orcid/Saskia de Vries")

        assert 200 == response.status_code
        assert {"orcid": "0000-0002-3704-3499"} == response.json()

    def test_get_orcid_summary_lookup_failure(
        self, client: TestClient, httpx_mock: HTTPXMock
    ):
        """Tests a failed summary lookup counts as no signal"""
        add_search(
            httpx_mock,
            "Saskia de Vries",
            {
                "orcid-id": "0000-0000-0000-0001",
                "given-names": "Saskia",
                "family-names": "de Vries",
            },
            {
                "orcid-id": "0000-0000-0000-0002",
                "given-names": "Saskia",
                "family-names": "de Vries",
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

        response = client.get("/orcid/Saskia de Vries")

        assert 404 == response.status_code
        assert {"detail": "Not found"} == response.json()

    def test_get_orcid_lone_match_without_allen_signal(
        self, client: TestClient, httpx_mock: HTTPXMock
    ):
        """Tests a lone name match with nothing tying it to Allen"""
        add_search(
            httpx_mock,
            "Peter Groblewski",
            {
                "orcid-id": "0000-0002-8415-1118",
                "given-names": "Peter",
                "family-names": "Groblewski",
            },
        )
        add_summary(httpx_mock, "0000-0002-8415-1118")

        response = client.get("/orcid/Peter Groblewski")

        assert 404 == response.status_code
        assert {"detail": "Not found"} == response.json()

    def test_get_orcid_too_many_candidates(
        self, client: TestClient, httpx_mock: HTTPXMock
    ):
        """Tests no summary lookups when the candidate list is long"""
        from orcid_service_server.route import MAX_DOMAIN_CHECKS

        add_search(
            httpx_mock,
            "John Smith",
            *[
                {
                    "orcid-id": f"0000-0000-0000-{index:04d}",
                    "given-names": "John",
                    "family-names": "Smith",
                }
                for index in range(MAX_DOMAIN_CHECKS + 1)
            ],
        )

        response = client.get("/orcid/John Smith")

        assert 404 == response.status_code
        # Only the search was called, no summary lookups.
        assert 1 == len(httpx_mock.get_requests())

    def test_get_orcid_not_found(
        self, client: TestClient, httpx_mock: HTTPXMock
    ):
        """Tests a search with no results"""
        add_search(httpx_mock, "Nobody Here")

        response = client.get("/orcid/Nobody Here")

        assert 404 == response.status_code
        assert {"detail": "Not found"} == response.json()

    def test_get_orcid_invalid_name(self, client: TestClient):
        """Tests a name without a family name is rejected"""
        response = client.get("/orcid/Birman")

        assert 400 == response.status_code


if __name__ == "__main__":
    pytest.main([__file__])

"""Tests handler module"""

import pytest
from httpx import URL, AsyncClient
from pytest_httpx import HTTPXMock

from orcid_service_server.handler import SessionHandler

SEARCH_URL = "http://example.com/pub/v3.0/expanded-search/"


@pytest.mark.asyncio
class TestSessionHandler:
    """Tests requests to ORCID"""

    async def test_search_by_name(self, httpx_mock: HTTPXMock):
        """Tests a search returns parsed results"""
        httpx_mock.add_response(
            url=URL(SEARCH_URL, params={"q": '"Researcher One"', "rows": 50}),
            json={
                "expanded-result": [
                    {
                        "orcid-id": "0000-0000-0000-0011",
                        "given-names": "Researcher",
                        "family-names": "One",
                    }
                ],
                "num-found": 1,
            },
        )
        async with AsyncClient(base_url="http://example.com/pub") as session:
            results = await SessionHandler(session=session).search_by_name(
                "Researcher One"
            )
        assert 1 == len(results)
        assert "0000-0000-0000-0011" == results[0].orcid_id

    async def test_search_by_name_no_results(self, httpx_mock: HTTPXMock):
        """Tests ORCID sending null rather than an empty list"""
        httpx_mock.add_response(
            url=URL(
                SEARCH_URL, params={"q": '"Unknown Researcher"', "rows": 50}
            ),
            json={"expanded-result": None, "num-found": 0},
        )
        async with AsyncClient(base_url="http://example.com/pub") as session:
            results = await SessionHandler(session=session).search_by_name(
                "Unknown Researcher"
            )
        assert [] == results

    async def test_get_email_domains(self, httpx_mock: HTTPXMock):
        """Tests verified email domains are lowercased"""
        httpx_mock.add_response(
            url="http://example.com/0000-0000-0000-0013/summary.json",
            json={"emailDomains": [{"value": "AllenInstitute.org"}]},
        )
        async with AsyncClient(base_url="http://example.com/pub") as session:
            domains = await SessionHandler(session=session).get_email_domains(
                "0000-0000-0000-0013"
            )
        assert ["alleninstitute.org"] == domains

    async def test_get_email_domains_empty(self, httpx_mock: HTTPXMock):
        """Tests a record with no verified domains"""
        httpx_mock.add_response(
            url="http://example.com/0000-0000-0000-0014/summary.json",
            json={"emailDomains": []},
        )
        async with AsyncClient(base_url="http://example.com/pub") as session:
            domains = await SessionHandler(session=session).get_email_domains(
                "0000-0000-0000-0014"
            )
        assert [] == domains


if __name__ == "__main__":
    pytest.main([__file__])

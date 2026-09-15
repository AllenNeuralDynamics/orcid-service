"""Tests session module"""

import pytest
from pydantic import SecretStr

from orcid_service_server.configs import settings
from orcid_service_server.session import get_session


@pytest.mark.asyncio
class TestGetSession:
    """Tests the ORCID session factory"""

    async def test_session_without_token(self):
        """Tests an anonymous session sends no Authorization header"""
        async with get_session() as session:
            assert "http://example.com/pub/" == str(session.base_url)
            assert "application/json" == session.headers.get("accept")
            assert session.headers.get("authorization") is None

    async def test_session_with_token(self, monkeypatch):
        """Tests a configured token is sent as a bearer header"""
        monkeypatch.setattr(
            "orcid_service_server.session.settings",
            settings.model_copy(
                update={"access_token": SecretStr("a-token")}, deep=True
            ),
        )
        async with get_session() as session:
            assert "Bearer a-token" == session.headers.get("authorization")


if __name__ == "__main__":
    pytest.main([__file__])

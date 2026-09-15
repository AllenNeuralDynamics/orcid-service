"""Tests session module"""

import pytest

from orcid_service_server.session import get_session


@pytest.mark.asyncio
class TestGetSession:
    """Tests the ORCID session factory"""

    async def test_session(self):
        """Tests the session targets the configured host"""
        async with get_session() as session:
            assert "http://example.com/pub/" == str(session.base_url)
            assert "application/json" == session.headers.get("accept")
            assert session.headers.get("authorization") is None


if __name__ == "__main__":
    pytest.main([__file__])

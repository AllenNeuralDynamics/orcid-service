"""Module to handle requests session"""

from httpx import AsyncClient

from orcid_service_server.configs import settings


def get_session() -> AsyncClient:
    """
    Build a session for the ORCID public API. The caller is responsible for
    closing it, which is why this is not a FastAPI dependency: the routes
    wrap their lookups in a cache decorator that dependencies cannot reach.
    """
    return AsyncClient(
        base_url=settings.api_host.unicode_string(),
        headers={"Accept": "application/json"},
        timeout=30.0,
    )

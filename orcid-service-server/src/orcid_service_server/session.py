"""Module to handle requests session"""

from httpx import AsyncClient

from orcid_service_server.configs import settings


def get_session() -> AsyncClient:
    """
    Build a session for the ORCID public API. The caller is responsible for
    closing it, which is why this is not a FastAPI dependency: the routes
    wrap their lookups in a cache decorator that dependencies cannot reach.
    """
    headers = {"Accept": "application/json"}
    if settings.access_token is not None:
        token = settings.access_token.get_secret_value()
        headers["Authorization"] = f"Bearer {token}"
    return AsyncClient(
        base_url=settings.api_host.unicode_string(),
        headers=headers,
        timeout=30.0,
    )

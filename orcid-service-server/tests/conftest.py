"""Set up fixtures to be used across all test modules."""

from typing import Any, Generator
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from pydantic import RedisDsn

from orcid_service_server.configs import settings

# Patched before main is imported so the cache decorator is a no-op and
# each test sees the responses it queued rather than a cached result.
patch(
    "fastapi_cache.decorator.cache", lambda *args, **kwargs: lambda f: f
).start()


@pytest.fixture
def client() -> Generator[TestClient, Any, None]:
    """Creating a client for testing purposes."""

    # Import moved to be able to mock cache
    from orcid_service_server.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="function")
def client_with_redis() -> Generator[TestClient, Any, None]:
    """Creating a client when settings have a redis_url. Only used in one test
    to verify the lifespan method in main is called correctly."""

    # Import moved to be able to mock cache
    from orcid_service_server.main import app

    settings_with_redis = settings.model_copy(
        update={"redis_url": RedisDsn("redis://example.com:1234")}, deep=True
    )
    with (
        patch(
            "orcid_service_server.main.settings",
            return_value=settings_with_redis,
        ),
        patch("orcid_service_server.main.from_url", return_value=None),
        patch("orcid_service_server.main.RedisBackend", return_value=None),
    ):
        with TestClient(app) as c:
            yield c

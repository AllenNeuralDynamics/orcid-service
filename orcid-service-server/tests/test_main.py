"""Module to test main app"""

import pytest
from starlette.testclient import TestClient


class TestMain:
    """Tests app endpoints"""

    def test_get_healthcheck(self, client: TestClient):
        """Tests healthcheck"""
        response = client.get("/healthcheck")
        assert 200 == response.status_code

    def test_app_with_redis(self, client_with_redis: TestClient):
        """Tests client is instantiated correctly when redis_url set."""
        response = client_with_redis.get("/healthcheck")
        assert 200 == response.status_code

    def test_app_with_in_memory_cache(self, client: TestClient):
        """Tests client is instantiated correctly when redis_url None."""
        response = client.get("/healthcheck")
        assert 200 == response.status_code

    def test_operation_ids_are_clean(self, client: TestClient):
        """Tests the generated client gets readable method names"""
        spec = client.get("/openapi.json").json()
        operation_ids = {
            path: list(ops.values())[0]["operationId"]
            for path, ops in spec["paths"].items()
        }
        assert "get_health" == operation_ids["/healthcheck"]
        assert "get_orcid" == operation_ids["/orcid/{name}"]


if __name__ == "__main__":
    pytest.main([__file__])

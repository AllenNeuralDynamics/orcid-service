# orcid-service-server

[![License](https://img.shields.io/badge/license-MIT-brightgreen)](LICENSE)
![Code Style](https://img.shields.io/badge/code%20style-black-black)
[![semantic-release: angular](https://img.shields.io/badge/semantic--release-angular-e10079?logo=semantic-release)](https://github.com/semantic-release/semantic-release)
![Interrogate](https://img.shields.io/badge/interrogate-100.0%25-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-99%25-brightgreen)
![Python](https://img.shields.io/badge/python->=3.10-blue?logo=python)
![support](https://img.shields.io/badge/support-supported-brightgreen)

REST service that resolves researcher names to ORCID iDs.

## Configuration

All settings are read from the environment with an `ORCID_` prefix, and all of them have defaults, so the service runs with no configuration.

| Setting | Default | Purpose |
| --- | --- | --- |
| `ORCID_API_HOST` | `https://pub.orcid.org` | The ORCID public API |
| `ORCID_SUMMARY_HOST` | `https://orcid.org` | Record summaries, which carry verified email domains |
| `ORCID_ACCESS_TOKEN` | unset | Optional `/read-public` token. Raises the rate limit; anonymous access works without it |
| `ORCID_REDIS_URL` | unset | Cache backend. Falls back to an in-process cache when unset |

Lookups are cached for 24 hours, since ORCID iDs are permanent.

## Development

```bash
uv venv && uv pip install -e ".[dev]"
uv run uvicorn orcid_service_server.main:app --port 8000
uv run coverage run -m pytest && uv run coverage report
uv run flake8 . && uv run interrogate -v .
```

The interactive docs at `/docs` are the quickest way to try a name by hand.

## Modules

| Module | Purpose |
| --- | --- |
| `configs.py` | Settings |
| `models.py` | Pydantic models for ORCID payloads and this service's responses |
| `session.py` | Builds the HTTP client, attaching the bearer token when one is configured |
| `handler.py` | One method per outbound ORCID request |
| `route.py` | Endpoints and the matching rule |
| `main.py` | App, cache lifespan, CORS |

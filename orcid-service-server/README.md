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
| `ORCID_REDIS_URL` | unset | Cache backend. Falls back to an in-process cache when unset |

## Caching

Successful lookups are cached for 24 hours, keyed on the name, in Redis when `ORCID_REDIS_URL` is set and in-process otherwise.

**Lookups that return 404 are not cached.** A miss raises, and exceptions are never cached, so a name that does not resolve is re-checked on every request. As a result, someone who has just added an affiliation to their ORCID record can verify it immediately rather than waiting for the cache to reset.

To force a refresh of a cached *successful* lookup, send `Cache-Control: no-cache`:

```bash
curl -H "Cache-Control: no-cache" "http://localhost:8000/orcid/Jerome%20Lecoq"
```

So request volume splits in two:

- **Names that resolve** result in at most one ORCID search per name per day, however many data assets name that person.
- **Names that do not resolve** result in a lookup every single time, because nothing is cached. We do not know how many AIND people have no usable affiliation on their ORCID record, so this side is unmeasured.

For upload-time use that is comfortable. ORCID allows 12 requests/second and 25,000 reads/day per IP for anonymous clients, and normal upload traffic will not approach it.

**Bulk callers need to deduplicate.** A migration that regenerates metadata for 10,000 assets with three investigators each would make 30,000 lookups and exceed the cap, even though the same finite set of people is involved. Resolve each distinct name once per run and reuse the result.

When the quota is exhausted ORCID returns 429, which surfaces here as a 500 with the status in the logs. 


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
| `session.py` | Builds the HTTP client |
| `handler.py` | One method per outbound ORCID request |
| `route.py` | Endpoints and the matching rule |
| `main.py` | App, cache lifespan, CORS |

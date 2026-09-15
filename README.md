# orcid-service

![support](https://img.shields.io/badge/support-supported-brightgreen)

Resolves researcher names to [ORCID](https://orcid.org) iDs using the public ORCID registry.

Names come in, an ORCID iD comes back when the match is unambiguous, and a 404 when it is not. Intended to be called by other AIND services (primarily [aind-metadata-service](https://github.com/AllenNeuralDynamics/aind-metadata-service)) so that `registry_identifier` can be populated on `Person` objects in metadata, but it is usable on its own.

No credentials are required. ORCID's public API serves anonymous requests, at a lower rate limit than a registered token.

## Repository layout

| Path | Written by | Purpose |
| --- | --- | --- |
| `orcid-service-server/` | hand | The FastAPI service |
| `orcid-service-client/` | CI | Synchronous Python client, generated from the OpenAPI spec |
| `orcid-service-async-client/` | CI | Async Python client, generated from the OpenAPI spec |
| `openapirc.json`, `openapirc_async.json` | hand | Client generator config |
| `scripts/generate_openapi.py` | hand | Dumps the OpenAPI spec from the running app |

The two client directories are build artifacts kept in git. Do not edit them. They are regenerated from the service's routes and models on every push to `main`, which means the client API is only as good as the Pydantic models in the service.

## Running it locally

```bash
cd orcid-service-server
uv venv && uv pip install -e ".[dev]"
uv run uvicorn orcid_service_server.main:app --port 8000
```

Then open http://localhost:8000/docs for the interactive API docs, or http://localhost:8000/healthcheck.

Every setting has a default pointing at the public ORCID hosts, so no configuration is needed to run or test.

## Tests

```bash
cd orcid-service-server
uv run coverage run -m pytest && uv run coverage report
uv run flake8 . && uv run interrogate -v .
```

Coverage and docstring coverage are both enforced at 100%.

## Releases

On a push to `main`, CI increments the tag, publishes the server as a Docker image to `ghcr.io/allenneuraldynamics/orcid-service-server`, and regenerates both clients. The clients are installed from GitHub rather than PyPI:

```bash
uv add "orcid-service-async-client @ git+https://github.com/AllenNeuralDynamics/orcid-service.git@v0.1.0#subdirectory=orcid-service-async-client"
```

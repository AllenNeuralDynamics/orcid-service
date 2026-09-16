"""Starts and runs a FastAPI Server"""

import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.backends.redis import RedisBackend
from redis.asyncio import from_url

from orcid_service_server import __version__ as service_version
from orcid_service_server.configs import settings
from orcid_service_server.route import router

# The log level can be set by adding an environment variable before launch.
log_level = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(level=log_level)

description = """
## orcid-service

Service to resolve researcher names to ORCID iDs using the public ORCID
registry.

"""


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Init cache and add to lifespan of app"""
    if settings.redis_url is not None:
        redis = from_url(settings.redis_url.unicode_string())
        FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
    else:
        FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")
    yield


# noinspection PyTypeChecker
app = FastAPI(
    title="orcid-service",
    description=description,
    summary="Resolves researcher names to ORCID iDs.",
    version=service_version,
    lifespan=lifespan,
)

# noinspection PyTypeChecker
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(router)

"""Starts and runs a FastAPI Server"""

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute

from aind_service_template_server import __version__ as service_version
from aind_service_template_server.route import router

# The log level can be set by adding an environment variable before launch.
log_level = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(level=log_level)

description = """
## aind-service-template

Service to pull data from example backend.

"""

# noinspection PyTypeChecker
app = FastAPI(
    title="aind-service-template",
    description=description,
    summary="Serves data from example backend.",
    version=service_version,
)

# noinspection PyTypeChecker
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)
app.include_router(router)

# Clean up the methods names that is generated in the client code
for route in app.routes:
    if isinstance(route, APIRoute):
        route.operation_id = route.name

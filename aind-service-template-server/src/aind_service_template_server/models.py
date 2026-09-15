"""Models and schema definitions for backend data structures"""

from typing import Literal

from pydantic import BaseModel, Field

from aind_service_template_server import __version__


class HealthCheck(BaseModel):
    """Response model to validate and return when performing a health check."""

    status: Literal["OK"] = "OK"
    service_version: str = __version__


class Content(BaseModel):
    """Response model for querying example content"""

    info: str = Field(..., description="Example Info")
    arg: str = Field(..., description="Argument passed into request")

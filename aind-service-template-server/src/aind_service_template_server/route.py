"""Module to handle endpoint responses"""

from fastapi import APIRouter, Depends, HTTPException, Path, status
from requests_toolbelt.sessions import BaseUrlSession

from aind_service_template_server.handler import SessionHandler
from aind_service_template_server.models import Content, HealthCheck
from aind_service_template_server.session import get_session

router = APIRouter()


@router.get(
    "/healthcheck",
    tags=["healthcheck"],
    summary="Perform a Health Check",
    response_description="Return HTTP Status Code 200 (OK)",
    status_code=status.HTTP_200_OK,
    response_model=HealthCheck,
)
async def get_health() -> HealthCheck:
    """
    ## Endpoint to perform a healthcheck on.

    Returns:
        HealthCheck: Returns a JSON response with the health status
    """
    return HealthCheck()


@router.get(
    "/{example_arg}",
    response_model=Content,
)
async def get_content(
    example_arg: str = Path(..., examples=["raw", "length"]),
    session: BaseUrlSession = Depends(get_session),
):
    """
    ## Example content
    Return either the raw content or the number of characters.
    """
    content = SessionHandler(session=session).get_info(example_arg=example_arg)
    # Adding this for illustrative purposes.
    if len(content.info) == 0:
        raise HTTPException(status_code=404, detail="Not found")
    else:
        return content

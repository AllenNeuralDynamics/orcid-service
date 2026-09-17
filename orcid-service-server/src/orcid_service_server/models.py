"""Models and schema definitions for backend data structures"""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from orcid_service_server import __version__


class HealthCheck(BaseModel):
    """Response model to validate and return when performing a health check."""

    status: Literal["OK"] = "OK"
    service_version: str = __version__


class ExpandedResult(BaseModel):
    """One record in an ORCID expanded-search response"""

    orcid_id: Optional[str] = Field(default=None, alias="orcid-id")
    given_names: Optional[str] = Field(default=None, alias="given-names")
    family_names: Optional[str] = Field(default=None, alias="family-names")
    credit_name: Optional[str] = Field(default=None, alias="credit-name")
    other_name: List[str] = Field(default=[], alias="other-name")
    email: List[str] = Field(default=[])
    institution_name: List[str] = Field(default=[], alias="institution-name")


class ExpandedSearch(BaseModel):
    """An ORCID expanded-search response"""

    # ORCID sends null rather than an empty list when nothing matches.
    expanded_result: Optional[List[ExpandedResult]] = Field(
        default=None, alias="expanded-result"
    )
    num_found: int = Field(default=0, alias="num-found")


class RecordSummary(BaseModel):
    """The part of an ORCID record summary this service reads"""

    email_domains: List[dict] = Field(default=[], alias="emailDomains")


class OrcidId(BaseModel):
    """Response model for a resolved ORCID iD"""

    orcid: str = Field(..., description="The resolved ORCID iD")

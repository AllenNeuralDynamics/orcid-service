"""Module for settings to connect to ORCID"""

from typing import Optional

from aind_settings_utils.aws import ParameterStoreAppBaseSettings
from pydantic import Field, HttpUrl, RedisDsn, SecretStr
from pydantic_settings import SettingsConfigDict


class Settings(ParameterStoreAppBaseSettings):
    """Settings needed to connect to ORCID"""

    model_config = SettingsConfigDict(
        env_prefix="ORCID_", case_sensitive=False
    )
    api_host: HttpUrl = Field(
        default=HttpUrl("https://pub.orcid.org"),
        title="API Host",
        description="Host address of the ORCID public API.",
    )
    summary_host: HttpUrl = Field(
        default=HttpUrl("https://orcid.org"),
        title="Summary Host",
        description=(
            "Host address for ORCID record summaries. Verified email "
            "domains are served here rather than from the public API."
        ),
    )
    access_token: Optional[SecretStr] = Field(
        default=None,
        title="Access Token",
        description=(
            "Optional ORCID /read-public token. The public API works "
            "without one, at a lower rate limit."
        ),
    )
    redis_url: Optional[RedisDsn] = Field(default=None)


settings = Settings()

"""Module for settings to connect to backend"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    ### Settings needed to connect to a database or website.
    We will just connect to an example website.
    """

    model_config = SettingsConfigDict(env_prefix="MYENV_")
    host: str = Field(
        ...,
        title="Host",
        description="Host address of example.com",
    )

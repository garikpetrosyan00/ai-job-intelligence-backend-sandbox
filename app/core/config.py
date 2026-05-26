"""Application settings.

The project uses a settings layer from Day 1 so environment-dependent values
do not get hardcoded inside routes or services.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Job Intelligence Backend"
    environment: str = "local"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Cache settings so they are created once per process."""
    return Settings()


settings = get_settings()

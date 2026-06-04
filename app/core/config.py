from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(
        default="AI Job Intelligence Backend",
        validation_alias="APP_NAME",
    )
    environment: str = Field(
        default="local",
        validation_alias="APP_ENVIRONMENT",
    )
    debug: bool = Field(
        default=False,
        validation_alias="APP_DEBUG",
    )
    database_url: str = Field(
        validation_alias="DATABASE_URL",
    )
    jwt_secret_key: str = Field(
        validation_alias="JWT_SECRET_KEY",
    )
    jwt_algorithm: str = Field(
        default="HS256",
        validation_alias="JWT_ALGORITHM",
    )
    jwt_access_token_expire_minutes: int = Field(
        default=30,
        validation_alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def app_environment(self) -> str:
        return self.environment


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

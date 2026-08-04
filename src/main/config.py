"""Centralized application settings loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"


class AppSettings(BaseSettings):
    """Validated application settings for the runtime composition root."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    env: Literal["development", "production", "testing"] = Field(alias="ENV")

    rabbitmq_host: str = Field(alias="RABBITMQ_HOST", min_length=1)
    rabbitmq_port: int = Field(alias="RABBITMQ_PORT", ge=1, le=65535)
    rabbitmq_username: str = Field(alias="RABBITMQ_USERNAME", min_length=1)
    rabbitmq_password: SecretStr = Field(alias="RABBITMQ_PASSWORD")

    database_host: str = Field(alias="DATABASE_HOST", min_length=1)
    database_port: int = Field(alias="DATABASE_PORT", ge=1, le=65535)
    database_username: str = Field(alias="DATABASE_USERNAME", min_length=1)
    database_password: SecretStr = Field(alias="DATABASE_PASSWORD")
    database_name: str = Field(alias="DATABASE_NAME", min_length=1)


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """Return the cached, fully validated application settings."""

    return AppSettings()
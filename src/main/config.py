"""Centralized application settings loaded from environment variables using Pydantic."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import sys
from typing import Literal
from urllib.parse import quote_plus

from pydantic import Field, SecretStr, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


# ------------------------------------------------------------------
# Global Constants (used across the program)
# ------------------------------------------------------------------
APP_NAME = "PyRuleBuilder"

DEFAULT_TIMEOUT_SECONDS = 30


# ------------------------------------------------------------------
# Path Setup
# ------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / ".env"


class AppSettings(BaseSettings):
    """Validated environment settings."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # 1. ENV - dev | production
    env: Literal["dev", "production"] = Field(alias="ENV")

    # 2. PORT - Server port (Valid port range: 1024-65535 or 1-65535)
    port: int = Field(default=8000, alias="PORT", ge=1, le=65535)

    # RabbitMQ Configuration
    rabbitmq_host: str = Field(alias="RABBITMQ_HOST", min_length=1)
    rabbitmq_port: int = Field(alias="RABBITMQ_PORT", ge=1, le=65535)
    rabbitmq_username: str = Field(alias="RABBITMQ_USERNAME", min_length=1)
    rabbitmq_password: SecretStr = Field(alias="RABBITMQ_PASSWORD")

    # Database Configuration Components
    database_host: str = Field(alias="DATABASE_HOST", min_length=1)
    database_port: int = Field(alias="DATABASE_PORT", ge=1, le=65535)
    database_username: str = Field(alias="DATABASE_USERNAME", min_length=1)
    database_password: SecretStr = Field(alias="DATABASE_PASSWORD")
    database_name: str = Field(alias="DATABASE_NAME", min_length=1)

    # ------------------------------------------------------------------
    # Dynamic Derivative Properties (Computed Configurations)
    # ------------------------------------------------------------------

    @property
    def rabbitmq_uri(self) -> str:
        """Build the validated RabbitMQ connection URI."""
        username = quote_plus(self.rabbitmq_username)
        password = quote_plus(self.rabbitmq_password.get_secret_value())
        return f"amqp://{username}:{password}@{self.rabbitmq_host}:{self.rabbitmq_port}/"

    @property
    def database_uri(self) -> str:
        """
        Builds the Database URI dynamically.
        Adjusts the database name based on the ENV (dev vs production).
        """
        username = quote_plus(self.database_username)
        password = quote_plus(self.database_password.get_secret_value())
        host = self.database_host
        port = self.database_port

        # 3.b Select Database based on ENV
        db_name = self.database_name
        if self.env == "dev" and not db_name.endswith("_dev"):
            db_name = f"{db_name}_dev"
        elif self.env == "production" and not db_name.endswith("_prod"):
            db_name = f"{db_name}_prod"

        return f"postgresql://{username}:{password}@{host}:{port}/{db_name}"


@lru_cache(maxsize=1)
def load_settings() -> AppSettings:
    """
    Validates environment variables on load.
    If validation fails, halts the server immediately (fail-fast).
    """
    try:
        return AppSettings()
    except ValidationError as e:
        print(" CRITICAL: Environment configuration error! Server halting.", file=sys.stderr)
        print(e, file=sys.stderr)
        sys.exit(1)


# Exported config object & constants ready for import across the program
config = load_settings()
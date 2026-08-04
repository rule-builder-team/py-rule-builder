"""Tests for centralized configuration management."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pydantic import ValidationError

from src.main.config import AppSettings


VALID_ENV = {
    "ENV": "development",
    "RABBITMQ_HOST": "localhost",
    "RABBITMQ_PORT": "5672",
    "RABBITMQ_USERNAME": "guest",
    "RABBITMQ_PASSWORD": "guest",
    "DATABASE_HOST": "localhost",
    "DATABASE_PORT": "5432",
    "DATABASE_USERNAME": "postgres",
    "DATABASE_PASSWORD": "postgres",
    "DATABASE_NAME": "py_rule_builder",
}


class AppSettingsTests(unittest.TestCase):
    def test_settings_fail_fast_when_required_values_are_missing(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValidationError):
                AppSettings()

    def test_settings_fail_when_port_is_out_of_range(self) -> None:
        invalid_env = dict(VALID_ENV)
        invalid_env["RABBITMQ_PORT"] = "70000"

        with patch.dict(os.environ, invalid_env, clear=True):
            with self.assertRaises(ValidationError):
                AppSettings()

    def test_settings_load_from_env_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            env_file = Path(temp_dir) / ".env"
            env_file.write_text(
                "\n".join(f"{key}={value}" for key, value in VALID_ENV.items()),
                encoding="utf-8",
            )

            with patch.dict(os.environ, {}, clear=True):
                settings = AppSettings(_env_file=env_file)

        self.assertEqual(settings.env, "development")
        self.assertEqual(settings.rabbitmq_host, "localhost")
        self.assertEqual(settings.database_name, "py_rule_builder")

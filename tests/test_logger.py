"""Smoke tests for structured logging initialization."""

from __future__ import annotations

import importlib
import os
import sys
import unittest
from unittest.mock import patch


VALID_ENV = {
    "ENV": "dev",
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


class LoggerTests(unittest.TestCase):
    def test_logger_initializes_successfully(self) -> None:
        with patch.dict(os.environ, VALID_ENV, clear=True):
            sys.modules.pop("src.main.config", None)
            sys.modules.pop("src.main.logger", None)
            logger_module = importlib.import_module("src.main.logger")

        self.assertIsNotNone(logger_module.logger)

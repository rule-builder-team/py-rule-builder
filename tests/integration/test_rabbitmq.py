"""Integration test for the RabbitMQ connection adapter."""

from __future__ import annotations

import importlib
import os
import sys
import unittest
from unittest.mock import patch


DEV_ENV = {
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


class RabbitMQIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_connection_opens_and_closes(self) -> None:
        with patch.dict(os.environ, DEV_ENV, clear=True):
            sys.modules.pop("src.main.config", None)
            sys.modules.pop("src.main.logger", None)
            sys.modules.pop("src.adapters.queue.rabbitmq", None)
            rabbitmq_module = importlib.import_module("src.adapters.queue.rabbitmq")

        connection_manager = rabbitmq_module.RabbitMQConnection()

        connection = await connection_manager.connect()
        self.assertFalse(connection.is_closed)

        await connection_manager.close()
        self.assertTrue(connection.is_closed)

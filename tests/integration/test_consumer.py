"""Integration test for the firewall rule RabbitMQ consumer."""

from __future__ import annotations

import asyncio
import importlib
import contextlib
import json
import os
import sys
import unittest
from unittest.mock import patch

from aio_pika import Message, connect_robust


DEV_ENV = {
    "ENV": "dev",
    "RABBITMQ_HOST": "127.0.0.1",
    "RABBITMQ_PORT": "5672",
    "RABBITMQ_USERNAME": "guest",
    "RABBITMQ_PASSWORD": "guest",
    "DATABASE_HOST": "localhost",
    "DATABASE_PORT": "5432",
    "DATABASE_USERNAME": "postgres",
    "DATABASE_PASSWORD": "postgres",
    "DATABASE_NAME": "py_rule_builder",
}


class FirewallRuleConsumerIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_consumer_receives_validates_and_acks_message(self) -> None:
        with patch.dict(os.environ, DEV_ENV, clear=True):
            sys.modules.pop("src.main.config", None)
            sys.modules.pop("src.main.logger", None)
            sys.modules.pop("src.adapters.queue.rabbitmq", None)
            sys.modules.pop("src.adapters.inbound.queue.consumer", None)
            config_module = importlib.import_module("src.main.config")
            consumer_module = importlib.import_module("src.adapters.inbound.queue.consumer")

        consumer = consumer_module.FirewallRuleConsumer(
            connection=consumer_module.rabbitmq_connection,
            queue_name="firewall.rules.test",
        )

        consumer_task = asyncio.create_task(consumer.start())
        await consumer.ready_event.wait()

        publisher_connection = await connect_robust(config_module.settings.rabbitmq_uri)
        try:
            channel = await publisher_connection.channel()
            queue = await channel.declare_queue("firewall.rules.test", durable=True)
            await channel.default_exchange.publish(
                Message(
                    body=json.dumps(
                        {
                            "ruleId": "rule-123",
                            "type": "firewall",
                            "mode": "allow",
                            "values": ["10.0.0.1", "10.0.0.2"],
                        }
                    ).encode("utf-8"),
                    content_type="application/json",
                    message_id="message-123",
                ),
                routing_key=queue.name,
            )

            await asyncio.wait_for(self._wait_for_message(consumer), timeout=10)
        finally:
            await consumer.stop()
            consumer_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await consumer_task
            await publisher_connection.close()

        self.assertIsNotNone(consumer.last_message)
        self.assertEqual(consumer.last_message.rule_id, "rule-123")
        self.assertEqual(consumer.last_message.mode, "allow")

    async def _wait_for_message(self, consumer: object) -> None:
        while getattr(consumer, "last_message") is None:
            await asyncio.sleep(0.05)

"""Async RabbitMQ consumer for firewall rule messages."""

from __future__ import annotations

import asyncio
from typing import Literal

from aio_pika import IncomingMessage, RobustQueue
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from src.adapters.queue.rabbitmq import RabbitMQConnection, rabbitmq_connection
from src.main.config import settings
from src.main.logger import logger


class FirewallRuleMessage(BaseModel):
    """Strict schema for incoming firewall rule payloads."""

    model_config = ConfigDict(extra="forbid", strict=True)

    rule_id: str = Field(alias="ruleId", min_length=1)
    rule_type: str = Field(alias="type", min_length=1)
    mode: Literal["allow", "deny"]
    values: list[str] = Field(min_length=1)


class FirewallRuleConsumer:
    """Consume and validate firewall rule messages from RabbitMQ."""

    def __init__(
        self,
        connection: RabbitMQConnection | None = None,
        queue_name: str = "firewall.rules",
    ) -> None:
        self._connection = connection or rabbitmq_connection
        self._queue_name = queue_name
        self._ready_event = asyncio.Event()
        self._stopped_event = asyncio.Event()
        self._last_message: FirewallRuleMessage | None = None
        self._consumer_tag: str | None = None
        self._queue: RobustQueue | None = None
        self._is_closed = False

    @property
    def ready_event(self) -> asyncio.Event:
        """Signal that the consumer is attached to the queue."""

        return self._ready_event

    @property
    def last_message(self) -> FirewallRuleMessage | None:
        """Return the last validated payload handled by the consumer."""

        return self._last_message

    async def start(self) -> None:
        """Start consuming firewall rule messages until stopped or cancelled."""

        logger.info(
            "firewall_consumer_starting",
            env=settings.env,
            queue=self._queue_name,
        )

        connection = await self._connection.connect()
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)
        self._queue = await channel.declare_queue(self._queue_name, durable=True)
        self._consumer_tag = await self._queue.consume(self._handle_message, no_ack=False)
        self._ready_event.set()

        await self._stopped_event.wait()
        await self._close_resources()

    async def stop(self) -> None:
        """Stop the consumer and close the shared RabbitMQ connection."""

        self._stopped_event.set()
        await self._close_resources()

    async def _close_resources(self) -> None:
        """Close queue and connection resources once."""

        if self._is_closed:
            return

        self._is_closed = True

        if self._queue is not None and self._consumer_tag is not None:
            await self._queue.cancel(self._consumer_tag)
            self._consumer_tag = None

        await self._connection.close()

    async def _handle_message(self, message: IncomingMessage) -> None:
        message_id = message.message_id or "unknown"
        logger.info(
            "firewall_consumer_message_received",
            env=settings.env,
            queue=self._queue_name,
            message_id=message_id,
        )

        try:
            payload = FirewallRuleMessage.model_validate_json(message.body)
        except ValidationError as exc:
            logger.error(
                "firewall_consumer_validation_failed",
                env=settings.env,
                queue=self._queue_name,
                message_id=message_id,
                error=str(exc),
            )
            await message.reject(requeue=False)
            return

        self._last_message = payload
        await message.ack()

        logger.info(
            "firewall_consumer_message_acked",
            env=settings.env,
            queue=self._queue_name,
            message_id=message_id,
            rule_id=payload.rule_id,
        )


firewall_rule_consumer = FirewallRuleConsumer()

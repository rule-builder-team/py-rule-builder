"""Async RabbitMQ consumer for firewall rule messages."""

from __future__ import annotations
import asyncio
from typing import Literal, Union
from aio_pika import IncomingMessage, RobustQueue
from pydantic import BaseModel, ConfigDict, Field, ValidationError, TypeAdapter

from src.adapters.queue.rabbitmq import RabbitMQConnection, rabbitmq_connection
from src.application.use_cases.firewall_service import FirewallService
from src.main.logger import logger


# ==========================================
# 1. מודלים של הודעות מ-RabbitMQ
# ==========================================

class AddRuleMessage(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    action: Literal["add"]
    rule_id: str = Field(alias="ruleId", min_length=1)
    rule_type: str = Field(alias="type", min_length=1)
    mode: Literal["blacklist", "whitelist"]
    values: list[str] = Field(min_length=1)


class DeleteRuleMessage(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    action: Literal["delete"]
    ids: list[int] = Field(min_length=1)


class UpdateStatusMessage(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    action: Literal["update_status"]
    ids: list[int] = Field(min_length=1)
    active: bool


# איחוד כלל סוגי ההודעות ואדפטר שיודע לפענח אותן לפי ה-action
FirewallMessage = Union[AddRuleMessage, DeleteRuleMessage, UpdateStatusMessage]
MessageAdapter = TypeAdapter(FirewallMessage)


# ==========================================
# 2. ה-Consumer
# ==========================================

class FirewallRuleConsumer:
    def __init__(
            self,
            firewall_service: FirewallService,
            connection: RabbitMQConnection | None = None,
            queue_name: str = "firewall.rules",
    ) -> None:
        self._firewall_service = firewall_service
        self._connection = connection or rabbitmq_connection
        self._queue_name = queue_name
        self._ready_event = asyncio.Event()
        self._stopped_event = asyncio.Event()
        self._queue: RobustQueue | None = None
        self._consumer_tag: str | None = None

    @property
    def ready_event(self) -> asyncio.Event:
        return self._ready_event

    async def start(self) -> None:
        connection = await self._connection.connect()
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)

        self._queue = await channel.declare_queue(self._queue_name, durable=True)

        self._consumer_tag = await self._queue.consume(self._handle_message)
        self._ready_event.set()

        await self._stopped_event.wait()

    async def stop(self) -> None:
        self._stopped_event.set()
        if self._queue and self._consumer_tag:
            await self._queue.cancel(self._consumer_tag)
        await self._connection.close()

    async def _handle_message(self, message: IncomingMessage) -> None:
        # אנו משתמשים ב-requeue=False, כך שאם יש שגיאה ההודעה נמחקת או הולכת ל-DLQ
        async with message.process(requeue=False):
            logger.info("message_received_from_queue", queue=self._queue_name)

            try:
                # 1. ולידציה אוטומטית - Pydantic מזהה את ה-action ומאמת את השדות
                payload = MessageAdapter.validate_json(message.body)

                # 2. ניתוב (Routing) לפי סוג הפעולה
                if payload.action == "add":
                    result = await self._firewall_service.add_rules(payload)
                elif payload.action == "delete":
                    result = await self._firewall_service.delete_rules(payload)
                elif payload.action == "update_status":
                    result = await self._firewall_service.update_rules_status(payload)
                else:
                    logger.warning("unknown_action_received", action=getattr(payload, "action", "unknown"))
                    return

                # 3. בדיקת תוצאת הלוגיקה העסקית (שגיאות DB וכו')
                if result.is_err:
                    error = result.unwrap_err()
                    logger.error(
                        "business_logic_error",
                        error_code=error.code,
                        message=error.message,
                        action=payload.action
                    )
                else:
                    logger.info("message_processed_successfully", action=payload.action)

            except ValidationError as e:
                # ה-JSON שהגיע מ-Node.js שגוי ולא עומד בחוקים של Pydantic
                logger.error("invalid_message_format", error=str(e), body=message.body.decode('utf-8'))

            except Exception as e:
                # שגיאות בלתי צפויות במהלך העיבוד
                logger.exception("unexpected_error_processing_message", error=str(e))

# משתנה לאתחול גלובלי או הזרקת תלויות בהמשך
# יש להעביר את ה-firewall_service המתאים כאן בעת האתחול
# firewall_rule_consumer = FirewallRuleConsumer(firewall_service=...)
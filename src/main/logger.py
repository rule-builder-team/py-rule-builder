"""Structured logging configuration for the application composition root."""

from __future__ import annotations

import logging

import structlog
from structlog.contextvars import merge_contextvars

from src.main.config import settings


def _configure_structlog() -> None:
    """Configure structlog once at import time based on the application environment."""

    renderer = (
        structlog.processors.JSONRenderer()
        if settings.env == "production"
        else structlog.dev.ConsoleRenderer(colors=True)
    )

    structlog.configure(
        processors=[
            merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.TimeStamper(fmt="iso"),
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
    )


_configure_structlog()
logger = structlog.get_logger()

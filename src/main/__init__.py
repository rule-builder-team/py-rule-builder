"""Composition root for application startup and infrastructure wiring."""

from .config import AppSettings, get_settings

__all__ = ["AppSettings", "get_settings"]

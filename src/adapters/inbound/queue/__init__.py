"""Inbound queue adapters."""

from .consumer import FirewallRuleConsumer, FirewallRuleMessage, firewall_rule_consumer

__all__ = ["FirewallRuleConsumer", "FirewallRuleMessage", "firewall_rule_consumer"]

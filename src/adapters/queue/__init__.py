"""RabbitMQ adapter package."""

from .rabbitmq import RabbitMQConnection, rabbitmq_connection

__all__ = ["RabbitMQConnection", "rabbitmq_connection"]
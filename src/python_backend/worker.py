import json
import os
import sys
from datetime import datetime

import pika
import psycopg2


def get_database_uri() -> str:
    env = os.getenv("ENV", "dev")
    dev_uri = os.getenv("DATABASE_URI_DEV")
    prod_uri = os.getenv("DATABASE_URI_PROD")
    if env == "production":
        return prod_uri or dev_uri or ""
    return dev_uri or prod_uri or ""


def handle_message(channel, method, properties, body):
    message = json.loads(body.decode("utf-8"))
    print(f"[{datetime.utcnow().isoformat()}] Received action={message.get('action')}")
    print(json.dumps(message.get("payload"), ensure_ascii=False))
    channel.basic_ack(delivery_tag=method.delivery_tag)


def main() -> int:
    rabbitmq_url = os.getenv("RABBITMQ_URL")
    database_uri = get_database_uri()

    if not rabbitmq_url:
        print("RABBITMQ_URL is required", file=sys.stderr)
        return 1

    if not database_uri:
        print("Database URI is required", file=sys.stderr)
        return 1

    try:
        conn = psycopg2.connect(database_uri)
        conn.close()
    except Exception as exc:
        print(f"Database connection failed: {exc}", file=sys.stderr)
        return 1

    connection = pika.BlockingConnection(pika.URLParameters(rabbitmq_url))
    channel = connection.channel()
    channel.queue_declare(queue="firewall-rules-queue", durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue="firewall-rules-queue", on_message_callback=handle_message)

    print("Python worker is ready and waiting for messages")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
        connection.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

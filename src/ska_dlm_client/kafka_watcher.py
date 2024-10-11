"""Kafka watcher client."""

import argparse
import asyncio
import json
import logging

import aiokafka
import requests

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


def main():
    """Control the main execution of the program."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--kafka-server",
        nargs="*",
        default=["localhost:9092"],
        help="The host:port of the Kafka server(s) to bootstrap from",
    )
    parser.add_argument(
        "--kafka-topic",
        nargs="*",
        default=["ska-sdp-dataproduct-ingest"],
        help="The Kafka topic(s) to watch",
    )

    args = parser.parse_args()
    asyncio.run(watch(args.kafka_server, args.kafka_topics))


async def _start_consumer(consumer: aiokafka.AIOKafkaConsumer, max_retries: int = 5):
    """Start a Kafka consumer with multiple retries."""
    attempts = 0
    while attempts < max_retries:
        try:
            await consumer.start()
            return True  # Connection successful
        except aiokafka.errors.KafkaError as e:
            attempts += 1
            if attempts >= max_retries:
                raise aiokafka.errors.KafkaError(
                    f"Failed to connect to Kafka after {max_retries} retries"
                ) from e
            await asyncio.sleep(1)


async def post_dlm_data_item(data):
    """Stub HTTP POST call to DLM."""
    # Use requests library to simulate an HTTP call
    response = requests.post("http://dlm/api", json=data, timeout=5)
    logger.info("Mock HTTP call completed with status code: %d", response.status_code)
    logger.info("Response content: %s", response.json())


async def watch(servers: list[str], topics: list[str]):
    """
    Asynchronously consumes data product, create events from data queues, and notifies DLM.

    Args:
        servers (list[str]): Data queue servers.
        topics (list[str]): Data queue topics.
    """
    logger.debug("Connecting to Kafka server(s): %s", ", ".join(servers))
    logger.info("Watching %s topic(s) for dataproducts to process", ", ".join(topics))

    consumer = aiokafka.AIOKafkaConsumer(*topics, bootstrap_servers=servers)

    # Attempt to start the consumer once
    await _start_consumer(consumer)

    try:
        async for msg in consumer:
            try:
                data = json.loads(msg.value)
                logger.info("Consuming JSON message: %s", data)

                # Call the HTTP function (to be handled separately)
                await post_dlm_data_item(data)

            except requests.exceptions.RequestException as e:
                logger.error("Notifying DLM failed: %s", e)

            except json.JSONDecodeError:
                logger.warning(
                    "Unable to parse message as JSON. Raw message: %s", msg.value.decode("utf-8")
                )

    finally:
        await consumer.stop()


if __name__ == "__main__":
    # NOTE: we call main() here, and then let main() call watch()
    main()

"""Kafka watcher client."""

import argparse
import asyncio
import json
import logging
import sys

import aiokafka
import requests
from requests import Session

from . import CONFIG, ska_dlm_client

# from ska_dlm_client.openapi import api_client, configuration
# from ska_dlm_client.openapi.dlm_api import request_api, storage_api, gateway_api


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

    # check that a auth_token was found in CONFIG
    if CONFIG.auth_token == "":
        logger.error("No auth_token set in config.yaml. Unable to ingest data items")
        sys.exit(1)

    # begin a session with the DLM
    session, storage_id = ska_dlm_client.init_dlm_session()

    # start watching for kafka messages
    args = parser.parse_args()
    asyncio.run(watch(args.kafka_server, args.kafka_topic, session, storage_id))


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


async def watch(servers: list[str], topics: list[str], session: Session, storage_id: str):
    """
    Asynchronously consumes data product, create events from data queues, and notifies DLM.

    Args:
        servers (list[str]): Data queue servers.
        topics (list[str]): Data queue topics.
        session (Session): A requests.Session used to communicate with the DLM service.
        storage_id (str): The id of the storage into which new items will be placed.
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
                await ska_dlm_client.post_dlm_data_item(session, storage_id, data)

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

"""Kafka watcher client."""

import argparse
import asyncio
import json
import logging

import aiokafka

from ska_dlm_client.openapi import api_client, configuration
from ska_dlm_client.openapi.dlm_api import ingest_api
from ska_dlm_client.openapi.exceptions import OpenApiException

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


def main():
    """Control the main execution of the program."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--kafka-topic",
        nargs="*",
        default=["ska-sdp-dataproduct-ingest"],
        help="The Kafka topic(s) to watch",
    )
    parser.add_argument(
        "--kafka-broker-url",
        type=str,
        required=True,
        help="The URL of the Kafka broker.",
    )
    parser.add_argument(
        "--storage-name",
        type=str,
        required=True,
        help="The storage name to register data items against.",
    )
    parser.add_argument(
        "--ingest-server-url",
        type=str,
        required=True,
        help="Ingest server URL including the service port.",
    )

    args = parser.parse_args()
    asyncio.run(
        watch(
            kafka_broker_url=args.kafka_broker_url,
            kafka_topic=args.kafka_topic,
            ingest_server_url=args.ingest_server_url,
            storage_name=args.storage_name,
        )
    )


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


async def post_dlm_data_item(ingest_server_url: str, storage_name: str, data: dict):
    """HTTP POST call to DLM."""
    ingest_configuration = configuration.Configuration(host=ingest_server_url)
    with api_client.ApiClient(ingest_configuration) as ingest_api_client:
        api_ingest = ingest_api.IngestApi(ingest_api_client)
        try:
            # TODO: Need to fix item_name and data once correct message is sent via kafka
            post_data = json.dumps(data)
            response = api_ingest.register_data_item_ingest_register_data_item_post(
                item_name=post_data,
                storage_name=storage_name,
                body=data,
            )
            logger.info("item posted successfully with response %s", response)
        except OpenApiException as err:
            logger.error("OpenApiException caught during register_data_item\n%s", err)
            logger.error("HTTP call failed")
            logger.error("Ignoring and continueing.....")


async def watch(
    kafka_broker_url: list[str], kafka_topic: list[str], ingest_server_url: str, storage_name: str
):
    """
    Asynchronously consumes data product, create events from data queues, and notifies DLM.

    Args:
        servers (list[str]): Data queue servers.
        topics (list[str]): Data queue topics.
    """
    logger.debug("Connecting to Kafka server(s): %s", ", ".join(kafka_broker_url))
    logger.info("Watching %s topic(s) for dataproducts to process", ", ".join(kafka_broker_url))

    consumer = aiokafka.AIOKafkaConsumer(*kafka_topic, bootstrap_servers=kafka_broker_url)

    # Attempt to start the consumer once
    await _start_consumer(consumer)

    try:
        async for msg in consumer:
            try:
                data = json.loads(msg.value)
                logger.info("Consuming JSON message: %s", data)

                # Call the HTTP function (to be handled separately)
                await post_dlm_data_item(
                    ingest_server_url=ingest_server_url, storage_name=storage_name, data=data
                )

            except json.JSONDecodeError:
                logger.warning(
                    "Unable to parse message as JSON. Raw message: %s", msg.value.decode("utf-8")
                )

    finally:
        await consumer.stop()


if __name__ == "__main__":
    # NOTE: we call main() here, and then let main() call watch()
    main()

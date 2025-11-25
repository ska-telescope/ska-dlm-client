"""Kafka watcher client."""

import argparse
import asyncio
import json
import logging

import aiokafka

from ska_dlm_client.common_types import ItemType
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
        nargs="+",
        required=True,
        help="One or more Kafka broker URLs. E.g., ska-sdp-kafka.dp-shared:9092",
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
        help="Ingest server URL including the service port. E.g., http://ska-dlm-dev-ingest:80",
    )
    parser.add_argument(
        "--kafka-base-dir",
        type=str,
        required=False,
        default="",
        help="The base directory to be removed from the path of the file in the kafka message.",
    )
    parser.add_argument(
        "--check-rclone-access",
        action="store_true",  # Set to True if the flag is present, else this will be False.
        help="Optionally, check if DLM has rclone access to the data item.",
    )

    args = parser.parse_args()
    asyncio.run(
        watch(
            kafka_broker_url=args.kafka_broker_url,
            kafka_topic=args.kafka_topic,
            ingest_server_url=args.ingest_server_url,
            storage_name=args.storage_name,
            kafka_base_dir=args.kafka_base_dir,
            check_rclone_access=args.check_rclone_access,
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


async def post_dlm_data_item(
    ingest_server_url: str,
    storage_name: str,
    ingest_event_data: dict,
    kafka_base_dir: str,
    check_rclone_access: bool = True,
):
    """Call DLM via the OpenAPI spec."""
    ingest_configuration = configuration.Configuration(host=ingest_server_url)
    with api_client.ApiClient(ingest_configuration) as ingest_api_client:
        api_ingest = ingest_api.IngestApi(ingest_api_client)
        try:
            # Remove the kafka_base_dir from the start of the given file path.
            if kafka_base_dir == "":
                item_name = ingest_event_data["file"]
            else:
                item_name = ingest_event_data["file"].replace(f"{kafka_base_dir}", "")
            logger.info(
                "Calling DLM with item_name=%s, uri=%s, storage_name=%s, body=%s, \
                check_rclone_access=%s",
                item_name,
                ingest_event_data["file"],  # TODO: Kafka message content must be validated DMAN-74
                storage_name,
                ingest_event_data["metadata"],
                check_rclone_access,
            )
            response = api_ingest.register_data_item(
                item_name=item_name,
                uri=ingest_event_data["file"],
                item_type=ItemType.CONTAINER,
                storage_name=storage_name,
                request_body=ingest_event_data["metadata"],
                do_storage_access_check=check_rclone_access,
            )
            logger.info("item posted successfully with response %s", response)
        except OpenApiException as err:
            logger.error("OpenApiException caught during register_data_item\n%s", err)
            logger.error("Call to DLM failed")
            logger.error("Ignoring and continuing.....")


async def watch(  # pylint: disable=too-many-arguments, too-many-positional-arguments
    kafka_broker_url: list[str],
    kafka_topic: list[str],
    ingest_server_url: str,
    storage_name: str,
    kafka_base_dir: str,
    check_rclone_access: bool,
):
    """Asynchronously consumes data product, create events from data queues, and notifies DLM."""
    logger.debug("Connecting to Kafka server(s): %s", ", ".join(kafka_broker_url))
    logger.info("Watching %s topic(s) for dataproducts to process", ", ".join(kafka_broker_url))

    consumer = aiokafka.AIOKafkaConsumer(*kafka_topic, bootstrap_servers=kafka_broker_url)

    # Attempt to start the consumer once
    await _start_consumer(consumer)

    try:
        async for msg in consumer:
            logger.debug("Incoming message")
            try:
                ingest_event_data = json.loads(msg.value)
                logger.info("Consuming JSON message: %s", ingest_event_data)

                # Call the DLM (to be handled separately)
                logger.debug(
                    "calling DLM with ingest_server_url=%s, storage_name=%s, "
                    "ingest_event_data=%s, kafka_base_dir=%s, check_rclone_access=%s",
                    ingest_server_url,
                    storage_name,
                    ingest_event_data,
                    kafka_base_dir,
                    check_rclone_access,
                )
                await post_dlm_data_item(
                    ingest_server_url=ingest_server_url,
                    storage_name=storage_name,
                    ingest_event_data=ingest_event_data,
                    kafka_base_dir=kafka_base_dir,
                    check_rclone_access=check_rclone_access,
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

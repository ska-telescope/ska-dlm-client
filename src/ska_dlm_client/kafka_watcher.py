"""Kafka watcher client."""

import argparse
import asyncio
import json
import logging
import time

import aiokafka

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

    asyncio.run(_watch(args))


async def _try_start_consumer(consumer: aiokafka.AIOKafkaConsumer):
    """Start the Kafka consumer."""
    try:
        await consumer.start()
        return True
    except aiokafka.errors.KafkaError:
        return False


async def _watch(args): # do an http call every time it sees a message. Callan will show me how to do a mock of that.
    """Start watching the given Kafka topic."""
    logger.debug("Connecting to Kafka server(s): %s", ", ".join(args.kafka_server))
    logger.info("Watching %s topic(s) for dataproducts to process", ", ".join(args.kafka_topic))

    consumer = aiokafka.AIOKafkaConsumer(*args.kafka_topic, bootstrap_servers=args.kafka_server)

    try:
        attempts = 0
        while not await _try_start_consumer(consumer):
            attempts += 1
            if attempts > 5:
                raise RuntimeError(f"Unable to connect to {args.kafka_server}")
            time.sleep(1)

        async for msg in consumer:
            try:
                data = json.loads(msg.value)
                logger.info("Consuming JSON message: %s", data)
            except json.JSONDecodeError:
                logger.warning(
                    "Unable to parse message as JSON. Raw message: %s", msg.value.decode("utf-8")
                )

    finally:
        await consumer.stop()


if __name__ == "__main__":
    # NOTE: we call main() here, and then let main() call _start_watcher()
    main()

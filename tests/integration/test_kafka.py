"""Kafka integration tests."""

import asyncio
import json
import logging
from unittest import mock

import pytest
import pytest_asyncio
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from ska_dlm_client.kafka_watcher.main import watch

logger = logging.getLogger(__name__)

KAFKA_HOST = "localhost:9092"
TEST_TOPIC = "test-events"


@pytest_asyncio.fixture(name="producer")
async def producer_fixture():
    """Fixture to set up and tear down a Kafka producer."""
    p = AIOKafkaProducer(bootstrap_servers=KAFKA_HOST)
    await p.start()
    yield p
    await p.stop()


@pytest_asyncio.fixture(name="consumer")
async def consumer_fixture():
    """Fixture to set up and tear down a Kafka consumer."""
    consumer = AIOKafkaConsumer(TEST_TOPIC, bootstrap_servers=KAFKA_HOST)
    await consumer.start()
    yield consumer
    await consumer.stop()


@pytest.mark.asyncio
async def test_kafka_data_roundtrip(producer: AIOKafkaProducer, consumer: AIOKafkaConsumer):
    """Test sending and receiving messages between Kafka producer and consumer."""
    messages = ["one", "two", "three"]

    tasks = [
        asyncio.create_task(send_messages(producer, messages)),
        asyncio.create_task(receive_messages(consumer, max_num_messages=3)),
    ]
    done, pending = await asyncio.wait(tasks, timeout=5)

    assert len(pending) == 0
    assert len(done) == 2
    for task in done:
        assert task.exception() is None

    received_messages: list[bytes] = tasks[1].result()
    assert len(received_messages) == 3
    for expected_str, received_bytes in zip(messages, received_messages):
        assert expected_str.encode() == received_bytes


async def send_messages(producer: AIOKafkaProducer, msgs: list[str]):
    """Send a list of messages using the Kafka producer."""
    for msg in msgs:
        await producer.send_and_wait(TEST_TOPIC, msg.encode())


async def receive_messages(consumer: AIOKafkaConsumer, max_num_messages: int) -> list[str]:
    """Receive a specific number of messages from the Kafka consumer."""
    messages = []
    async for msg in consumer:
        messages.append(msg.value)
        if len(messages) == max_num_messages:
            return messages


# Send a real Kafka message to the Kafka watcher
@pytest.mark.asyncio
async def test_kafka_watcher(producer: AIOKafkaProducer, caplog):
    """Test that a Kafka message triggers a call to post_dlm_data_item()."""
    caplog.set_level(logging.INFO)
    bad_message = b"{ not: valid json ]"
    good_message = {
        "file": "/data/some/path/item1",
        "metadata": {"some": "value"},
        "extra": "unused_key",  # Check that additional unexpected keys don't break things
    }
    logger.debug("Setting up mock for post_dlm_data_item")

    # Mock post_dlm_data_item to verify that if a Kafka message is received,
    # it correctly calls post_dlm_data_item() with the expected arguments
    with mock.patch(
        "ska_dlm_client.kafka_watcher.main.post_dlm_data_item", new_callable=mock.AsyncMock
    ) as mock_post:
        logger.info("Launching Kafka watcher in background")

        # Launch the watcher in the background
        watcher_task = asyncio.create_task(
            watch(
                kafka_broker_url=[KAFKA_HOST],
                kafka_topic=[TEST_TOPIC],
                ingest_server_url="http://mockserver:8000",
                storage_name="test-storage",
                check_rclone_access=False,
            )
        )

        # Give the consumer a moment to start
        logger.debug("Waiting 1 second for Kafka consumer to start")
        await asyncio.sleep(1)

        # Send bad message
        logger.debug("Sending invalid Kafka message...")
        await producer.send_and_wait(TEST_TOPIC, bad_message)
        await asyncio.sleep(1)

        # post_dlm_data_item should NOT be called yet
        assert not mock_post.called
        assert any("Unable to parse message as JSON" in msg for msg in caplog.messages)

        # Send good message
        logger.debug("Sending valid Kafka message...")
        await producer.send_and_wait(TEST_TOPIC, json.dumps(good_message).encode())

        # Wait for the message to be processed (or timeout)
        logger.debug("Waiting to see if mock_post is called...")
        for i in range(10):
            await asyncio.sleep(0.5)
            if mock_post.called:
                logger.info("post_dlm_data_item was called!")
                break
            logger.info("Attempt %d to call post_dlm_data_item...", i + 1)

        # Cancel the watcher to clean up
        logger.info("Shutting down the watcher")
        watcher_task.cancel()
        try:
            await watcher_task
        except asyncio.CancelledError:
            logger.debug("Watcher task cancelled")

        # Check that the mock was called once with expected args
        logger.debug("Asserting that post_dlm_data_item was called once")
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        logger.debug("Called with args: %s, kwargs: %s", args, kwargs)
        assert kwargs["ingest_event_data"] == good_message
        assert kwargs["ingest_server_url"] == "http://mockserver:8000"
        assert kwargs["storage_name"] == "test-storage"
        assert kwargs["check_rclone_access"] is False

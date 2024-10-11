"""Kafka tests."""

import asyncio
import json
from unittest import mock
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
import pytest_mock
import requests
import requests_mock as rm
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from src.ska_dlm_client.kafka_watcher import watch

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


@pytest.fixture(name="mock_kafka_consumer")
def mock_kafka_consumer_fixture(mocker: pytest_mock.MockerFixture):
    """Create a mock for the Kafka consumer and simulate a single message."""
    mock_kafka_consumer = mocker.patch("aiokafka.AIOKafkaConsumer")
    mock_kafka_consumer_instance = mock_kafka_consumer.return_value
    mock_kafka_consumer_instance.start = AsyncMock()
    mock_kafka_consumer_instance.stop = AsyncMock()
    mock_kafka_consumer_instance.__aiter__.return_value = [
        mock.Mock(value=json.dumps({"key": "value"}).encode("utf-8"))
    ]
    yield mock_kafka_consumer_instance


@pytest.mark.asyncio
async def test_watch_post_success(requests_mock: rm.Mocker, mock_kafka_consumer: MagicMock):
    """Test that the _watch function correctly handles a successful HTTP call."""
    # Mock _start_consumer to return False first, then True to simulate retry logic
    mock_kafka_consumer.start.side_effect = [False, True]

    # Mock HTTP call to simulate a 200 response
    requests_mock.post("http://dlm/api", json={"success": True})
    await watch(servers=[KAFKA_HOST], topics=[TEST_TOPIC])

    # Assert that the HTTP call was made once
    assert requests_mock.call_count == 1

    # Assert the expected data was posted
    assert requests_mock.request_history[0].json() == {"key": "value"}

    # Assert that consumer.stop() was called
    mock_kafka_consumer.stop.assert_called_once()


@pytest.mark.asyncio
async def test_watch_http_failure(
    requests_mock: rm.Mocker,
    mock_kafka_consumer: MagicMock,
    caplog: pytest.LogCaptureFixture,
):
    """Test watch function handles HTTP call failures gracefully."""
    # Run the test and capture the logs
    with caplog.at_level("ERROR", logger="ska_dlm_client.kafka_watcher"):
        requests_mock.post(
            "http://dlm/api", exc=requests.exceptions.RequestException("HTTP call failed")
        )
        await watch(servers=[KAFKA_HOST], topics=[TEST_TOPIC])

        # Check that the error log was captured
        assert len(caplog.records) > 0  # Ensure there's at least one log entry
        assert "HTTP call failed" in caplog.text  # Check if the error message is present

    # Assert that the HTTP call was attempted
    assert requests_mock.call_count == 1

    # Ensure it was called with the expected data
    assert requests_mock.request_history[0].json() == {"key": "value"}

    # Assert that consumer.stop() was called even on failure
    mock_kafka_consumer.stop.assert_called_once()

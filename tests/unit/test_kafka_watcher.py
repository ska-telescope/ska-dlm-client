"""Kafka tests."""

import asyncio
import json
from dataclasses import dataclass
from unittest import mock

import pytest
import pytest_asyncio
import requests
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from src.ska_dlm_client.kafka_watcher import _watch

KAFKA_HOST = "localhost:9092"
TEST_TOPIC = "test-events"


@dataclass
class Args:
    """Configuration class for Kafka server and topic."""

    kafka_server = [KAFKA_HOST]
    kafka_topic = [TEST_TOPIC]


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


@pytest.mark.asyncio
@mock.patch("aiokafka.AIOKafkaConsumer")
@mock.patch("src.ska_dlm_client.kafka_watcher._try_start_consumer")
@mock.patch("src.ska_dlm_client.kafka_watcher.mock_http_call")  # Mock the HTTP call
async def test_watch_function_success(mock_http_call, mock_try_start_consumer, mock_kafka_consumer):
    """Test that the _watch function correctly handles a successful HTTP call."""
    # Create a mock for the Kafka consumer and simulate message consumption
    kafka_instance = mock_kafka_consumer.return_value
    kafka_instance.__aiter__.return_value = [
        mock.Mock(value=json.dumps({"key": "value"}).encode("utf-8"))
    ]

    # Mock consumer.stop() as an async function
    kafka_instance.stop = mock.AsyncMock()

    # Mock _try_start_consumer to return False first, then True to simulate retry logic
    mock_try_start_consumer.side_effect = [False, True]

    # Mock HTTP call to simulate a 200 response
    mock_http_call.return_value = asyncio.Future()
    mock_http_call.return_value.set_result(None)

    args = Args()
    await _watch(args)

    # Assert that the HTTP call was made once
    mock_http_call.assert_called_once()

    # Ensure it was called with the expected data
    mock_http_call.assert_called_with({"key": "value"})

    # Assert that consumer.stop() was called
    kafka_instance.stop.assert_called_once()


@pytest.mark.asyncio
@mock.patch("aiokafka.AIOKafkaConsumer")
@mock.patch("src.ska_dlm_client.kafka_watcher._try_start_consumer")
@mock.patch("src.ska_dlm_client.kafka_watcher.mock_http_call")  # Mock the HTTP call
async def test_watch_function_http_failure(mock_http_call, mock_try_start_consumer, mock_kafka_consumer, caplog):
    """Test that the _watch function handles HTTP call failures gracefully."""
    # Create a mock for the Kafka consumer and simulate message consumption
    kafka_instance = mock_kafka_consumer.return_value
    kafka_instance.__aiter__.return_value = [
        mock.Mock(value=json.dumps({"key": "value"}).encode("utf-8"))
    ]

    # Mock consumer.stop() as an async function
    kafka_instance.stop = mock.AsyncMock()

    # Mock _try_start_consumer to return True (successful connection)
    mock_try_start_consumer.side_effect = [True]

    # Mock HTTP call to simulate a failure (e.g., a non-200 response)
    mock_http_call.side_effect = requests.exceptions.RequestException("HTTP call failed")

    # Run the test and capture the logs
    with caplog.at_level("ERROR", logger="src.ska_dlm_client.kafka_watcher"):
        args = Args()
        await _watch(args)

        # Check that the error log was captured
        assert len(caplog.records) > 0  # Ensure there's at least one log entry
        assert "HTTP call failed" in caplog.text  # Check if the error message is present

    # Assert that the HTTP call was attempted
    mock_http_call.assert_called_once()

    # Ensure it was called with the expected data
    mock_http_call.assert_called_with({"key": "value"})

    # Assert that consumer.stop() was called even on failure
    kafka_instance.stop.assert_called_once()

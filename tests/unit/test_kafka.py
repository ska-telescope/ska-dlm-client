"""Kafka tests."""

import asyncio

import pytest
import pytest_asyncio
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

KAFKA_HOST = "localhost:9092"
TEST_TOPIC = "test-events"


@pytest_asyncio.fixture(name="producer")
async def producer_fixture():
    """Fixture to set up and tear down a Kafka producer."""
    p = AIOKafkaProducer(bootstrap_servers=KAFKA_HOST)
    await p.start()
    # TODO: Sometimes there is a 'KafkaConnectionError.' Based on experience, this might be
    # because the Kafka server is not quite running yet, i.e., the tests are starting too soon.
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

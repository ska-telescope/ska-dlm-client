"""Kafka unit tests."""

import json
from unittest import mock
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_mock
import requests
import requests_mock as rm

from src.ska_dlm_client.kafka_watcher import watch, main

KAFKA_HOST = "localhost:9092"
TEST_TOPIC = "test-events"


def test_main(mocker: pytest_mock.MockerFixture):
    """
    Test for the entrypoint function `main()`.

    This test ensures that:
    - Command-line arguments (kafka_server, kafka_topic) are parsed correctly.
    - `asyncio.run` is called with the expected arguments.
    - The `watch` function is triggered with the correct arguments without being executed.
    """
    # Mock the argparse.ArgumentParser to return simulated arguments
    mock_args = mock.Mock(kafka_server=[KAFKA_HOST], kafka_topic=[TEST_TOPIC])
    mocker.patch(
        "src.ska_dlm_client.kafka_watcher.argparse.ArgumentParser.parse_args",
        return_value=mock_args,
    )

    # Mock the `watch` function itself to verify it is called correctly
    mock_watch = mocker.patch("src.ska_dlm_client.kafka_watcher.watch")

    # Mock asyncio.run to prevent actual execution
    mock_asyncio_run = mocker.patch("src.ska_dlm_client.kafka_watcher.asyncio.run")

    # Call the main function
    main()

    # Verify that asyncio.run was called exactly once
    mock_asyncio_run.assert_called_once()

    # Verify that watch was called with the correct arguments
    mock_watch.assert_called_once_with(
        [KAFKA_HOST], [TEST_TOPIC]  # Expected kafka_server  # Expected kafka_topic
    )


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
    """Test that the watch function correctly handles a successful HTTP call."""
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

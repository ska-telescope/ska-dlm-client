"""Kafka unit tests."""

import json
import logging
from unittest import mock
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_mock

from ska_dlm_client.openapi.exceptions import OpenApiException
from src.ska_dlm_client.kafka_watcher.main import main, post_dlm_data_item, watch

KAFKA_HOST = "localhost:9092"
TEST_TOPIC = "test-events"
INGEST_HOST = "http://dlm/api"
STORAGE_NAME = "data"
KAFKA_MSG = {
    "file": "data/file_name",
    "time": "2025-02-05T14:23:45.678901",
    "metadata": {"eb_id": "eb-meta-20240723-00000"},
}


def test_main(mocker: pytest_mock.MockerFixture):
    """
    Test for the entrypoint function `main()`.

    This test ensures that:
    - Command-line arguments (kafka_server, kafka_topic) are parsed correctly.
    - `asyncio.run` is called with the expected arguments.
    - The `watch` function is triggered with the correct arguments without being executed.
    """
    # Mock the argparse.ArgumentParser to return simulated arguments
    mock_args = mock.Mock(
        kafka_broker_url=KAFKA_HOST,
        kafka_topic=[TEST_TOPIC],
        ingest_server_url=INGEST_HOST,
        storage_name=STORAGE_NAME,
        kafka_base_dir="",
        check_rclone_access=False,
    )
    mocker.patch(
        "src.ska_dlm_client.kafka_watcher.main.argparse.ArgumentParser.parse_args",
        return_value=mock_args,
    )

    # Mock the `watch` function itself to verify it is called correctly
    mock_watch = mocker.patch("src.ska_dlm_client.kafka_watcher.main.watch")

    # Mock asyncio.run to prevent actual execution
    mock_asyncio_run = mocker.patch("src.ska_dlm_client.kafka_watcher.main.asyncio.run")

    # Call the main function
    main()

    # Verify that asyncio.run was called exactly once
    mock_asyncio_run.assert_called_once()

    # Verify that watch was called with the correct arguments
    mock_watch.assert_called_once_with(
        kafka_broker_url=KAFKA_HOST,
        kafka_topic=[TEST_TOPIC],
        ingest_server_url=INGEST_HOST,
        storage_name=STORAGE_NAME,
        kafka_base_dir="",
        check_rclone_access=False,
    )


@pytest.fixture(name="mock_kafka_consumer")
def mock_kafka_consumer_fixture(mocker: pytest_mock.MockerFixture):
    """Create a mock for the Kafka consumer and simulate a single message."""
    mock_kafka_consumer = mocker.patch("aiokafka.AIOKafkaConsumer")
    mock_kafka_consumer_instance = mock_kafka_consumer.return_value
    mock_kafka_consumer_instance.start = AsyncMock()
    mock_kafka_consumer_instance.stop = AsyncMock()
    mock_kafka_consumer_instance.__aiter__.return_value = [
        mock.Mock(value=json.dumps(KAFKA_MSG).encode("utf-8"))
    ]
    yield mock_kafka_consumer_instance


@pytest.fixture(name="mock_apiingest")
def mock_api_ingest_fixture(mocker: pytest_mock.MockerFixture):
    """Create a mock for the OpenAPI ingest and simulate a single message."""
    mock_ingest_api = mocker.patch(
        "ska_dlm_client.openapi.dlm_api.ingest_api.IngestApi.register_data_item"
    )
    mock_ingest_api.return_value = {"Success": True}
    yield mock_ingest_api


@pytest.fixture(name="mock_apiingest_exception")
def mock_api_ingest_exception_fixture(mocker: pytest_mock.MockerFixture):
    """Create a mock for the OpenAPI ingest and simulate a single message."""
    mock_ingest_api = mocker.patch(
        "ska_dlm_client.openapi.dlm_api.ingest_api.IngestApi.register_data_item"
    )
    mock_ingest_api.side_effect = OpenApiException()
    pytest.raises(OpenApiException)


@pytest.mark.asyncio
async def test_watch_post_success(mock_apiingest: MagicMock, mock_kafka_consumer: MagicMock):
    """Test that the watch function correctly handles a successful HTTP call."""
    # Mock _start_consumer to return False first, then True to simulate retry logic
    mock_kafka_consumer.start.side_effect = [False, True]

    await watch(
        kafka_broker_url=KAFKA_HOST,
        kafka_topic=[TEST_TOPIC],
        ingest_server_url=INGEST_HOST,
        storage_name=STORAGE_NAME,
        kafka_base_dir="",
        check_rclone_access=False,
    )

    # Assert that the HTTP call was made once
    assert mock_apiingest.call_count == 1

    # Assert that consumer.stop() was called
    mock_kafka_consumer.stop.assert_called_once()


@pytest.mark.asyncio
async def test_watch_http_failure(
    mock_apiingest_exception: MagicMock,
    mock_kafka_consumer: MagicMock,
    caplog: pytest.LogCaptureFixture,
):  # pylint: disable=unused-argument
    """Test watch function for handling and OpenApiException."""
    # Run the test and capture the logs
    with caplog.at_level("ERROR", logger="ska_dlm_client.kafka_watcher.main"):
        await watch(
            kafka_broker_url=KAFKA_HOST,
            kafka_topic=[TEST_TOPIC],
            ingest_server_url=INGEST_HOST,
            storage_name=STORAGE_NAME,
            kafka_base_dir="",
            check_rclone_access=False,
        )

        # Check that the error log was captured
        assert len(caplog.records) > 0  # Ensure there's at least one log entry
        assert "Call to DLM failed" in caplog.text  # Check if the error message is present

    # Assert that consumer.stop() was called even on failure
    mock_kafka_consumer.stop.assert_called_once()


@pytest.mark.asyncio
async def test_post_dlm_data_item_success(mock_apiingest, caplog):
    """Test that post_dlm_data_item successfully calls the API and logs the success message."""
    caplog.set_level(logging.INFO)

    await post_dlm_data_item(INGEST_HOST, STORAGE_NAME, KAFKA_MSG, "")

    # Ensure API call was made with correct parameters
    mock_apiingest.assert_called_once_with(
        item_name="data/file_name",
        uri=KAFKA_MSG["file"],  # Assuming file is used as the URI
        item_type="container",
        storage_name=STORAGE_NAME,
        body=KAFKA_MSG["metadata"],
        do_storage_access_check=True,
    )

    # Assert: No warnings or errors in logs
    for record in caplog.records:
        assert record.levelname not in [
            "WARNING",
            "ERROR",
        ], f"Unexpected log level {record.levelname}: {record.message}"


@pytest.mark.asyncio
async def test_post_dlm_data_item_success_with_kafka_base_dir(mock_apiingest, caplog):
    """Test that post_dlm_data_item successfully calls the API and logs the success message."""
    caplog.set_level(logging.INFO)

    await post_dlm_data_item(INGEST_HOST, STORAGE_NAME, KAFKA_MSG, "data/")

    # Ensure API call was made with correct parameters
    mock_apiingest.assert_called_once_with(
        item_name="file_name",
        uri=KAFKA_MSG["file"],  # Assuming file is used as the URI
        item_type="container",
        storage_name=STORAGE_NAME,
        body=KAFKA_MSG["metadata"],
        do_storage_access_check=True,
    )

    # Assert: No warnings or errors in logs
    for record in caplog.records:
        assert record.levelname not in [
            "WARNING",
            "ERROR",
        ], f"Unexpected log level {record.levelname}: {record.message}"


@pytest.mark.asyncio
async def test_post_dlm_data_item_failure(mock_apiingest, caplog):
    """Test that post_dlm_data_item handles OpenApiException gracefully and logs errors."""
    caplog.set_level(logging.ERROR)

    # Simulate an API failure
    mock_apiingest.side_effect = OpenApiException("API Error")

    # Call function
    await post_dlm_data_item(INGEST_HOST, STORAGE_NAME, KAFKA_MSG, "")

    # Ensure the function attempted the call
    mock_apiingest.assert_called_once()

    # Assert errors are logged
    error_messages = [record.message for record in caplog.records if record.levelname == "ERROR"]

    expected_errors = [
        "OpenApiException caught during register_data_item\nAPI Error",
        "Call to DLM failed",
        "Ignoring and continuing.....",
    ]

    for expected in expected_errors:
        assert any(
            expected in msg for msg in error_messages
        ), f"Expected log message not found: {expected}"


@pytest.mark.asyncio
async def test_kafka_base_dir_command_line_parameter(mocker: pytest_mock.MockerFixture):
    """
    Test that the --kafka-base-dir command line parameter is correctly passed through \
    to where it's used in the code (around lines 102-105 in main.py).

    This test verifies that:
    1. The command-line argument --kafka-base-dir is parsed correctly
    2. The value is passed to the watch function
    3. The value is used in post_dlm_data_item to modify the file path
    """
    # Define a non-empty kafka_base_dir value
    test_kafka_base_dir = "data/"

    # First part: Test that the command-line argument is correctly passed to the watch function
    # Mock the argparse.ArgumentParser to return simulated arguments with non-empty kafka_base_dir
    mock_args = mock.Mock(
        kafka_broker_url=KAFKA_HOST,
        kafka_topic=[TEST_TOPIC],
        ingest_server_url=INGEST_HOST,
        storage_name=STORAGE_NAME,
        kafka_base_dir=test_kafka_base_dir,
        check_rclone_access=False,
    )
    mocker.patch(
        "src.ska_dlm_client.kafka_watcher.main.argparse.ArgumentParser.parse_args",
        return_value=mock_args,
    )

    # Mock the watch function to capture its arguments
    mock_watch = mocker.patch("src.ska_dlm_client.kafka_watcher.main.watch")

    # Mock asyncio.run to prevent actual execution
    mocker.patch("src.ska_dlm_client.kafka_watcher.main.asyncio.run")

    # Call the main function
    main()

    # Verify that watch was called with the correct kafka_base_dir argument
    mock_watch.assert_called_once()
    assert mock_watch.call_args[1]["kafka_base_dir"] == test_kafka_base_dir

    # Second part: Test that the kafka_base_dir parameter is used correctly in post_dlm_data_item
    # We'll create a test message and call post_dlm_data_item directly
    test_msg = {"file": "data/test_file", "metadata": {"test": "metadata"}}

    # Mock the API client and IngestApi
    mocker.patch("ska_dlm_client.openapi.api_client.ApiClient", return_value=mock.MagicMock())
    mock_ingest_api_instance = mock.MagicMock()
    mock_ingest_api_instance.register_data_item = AsyncMock(return_value={"Success": True})
    mocker.patch(
        "ska_dlm_client.openapi.dlm_api.ingest_api.IngestApi",
        return_value=mock_ingest_api_instance,
    )

    # Call post_dlm_data_item with our test message and the kafka_base_dir
    await post_dlm_data_item(
        ingest_server_url=INGEST_HOST,
        storage_name=STORAGE_NAME,
        ingest_event_data=test_msg,
        kafka_base_dir=test_kafka_base_dir,
    )

    # Verify that register_data_item was called with the correct item_name
    # The kafka_base_dir should be removed from the file path
    mock_ingest_api_instance.register_data_item.assert_called_once()
    call_args = mock_ingest_api_instance.register_data_item.call_args[1]

    # Verify that the kafka_base_dir was removed from the file path
    assert call_args["item_name"] == "test_file"
    assert call_args["uri"] == "data/test_file"

"""Tests for kafka_base_dir parameter in kafka_watcher."""

import json
from unittest import mock
from unittest.mock import AsyncMock, MagicMock

import pytest

from ska_dlm_client.kafka_watcher.main import main, post_dlm_data_item, watch

pytestmark = pytest.mark.skip(reason="The Kafka-watcher is deprecated!")

KAFKA_HOST = "localhost:9092"
TEST_TOPIC = "test-events"
INGEST_HOST = "http://dlm/api"
STORAGE_NAME = "kafka-watcher"
KAFKA_MSG = {
    "file": "/data/test/file_name",
    "time": "2025-02-05T14:23:45.678901",
    "metadata": {"eb_id": "eb-meta-20240723-00000"},
}


@pytest.mark.asyncio
async def test_kafka_base_dir_empty():
    """Test that when kafka_base_dir is empty, the file path is not modified."""
    # Mock the API client and IngestApi
    with mock.patch("ska_dlm_client.openapi.api_client.ApiClient") as mock_api_client, mock.patch(
        "ska_dlm_client.openapi.dlm_api.ingest_api.IngestApi"
    ) as mock_ingest_api:

        # Set up the mocks
        mock_api_client_instance = MagicMock()
        mock_api_client.return_value.__enter__.return_value = mock_api_client_instance

        mock_ingest_api_instance = MagicMock()
        mock_ingest_api.return_value = mock_ingest_api_instance
        mock_ingest_api_instance.register_data_item = AsyncMock(return_value={"Success": True})

        # Call post_dlm_data_item with empty kafka_base_dir
        await post_dlm_data_item(
            ingest_url=INGEST_HOST,
            storage_name=STORAGE_NAME,
            ingest_event_data=KAFKA_MSG,
            kafka_base_dir="",
        )

        # Verify that register_data_item was called with the original file path
        mock_ingest_api_instance.register_data_item.assert_called_once()
        call_args = mock_ingest_api_instance.register_data_item.call_args[1]

        # The item_name should be the original file path
        assert call_args["item_name"] == KAFKA_MSG["file"]
        assert call_args["uri"] == KAFKA_MSG["file"]


@pytest.mark.asyncio
async def test_kafka_base_dir_non_empty():
    """Test that when kafka_base_dir is not empty, it is removed from the file path."""
    # Mock the API client and IngestApi
    with mock.patch("ska_dlm_client.openapi.api_client.ApiClient") as mock_api_client, mock.patch(
        "ska_dlm_client.openapi.dlm_api.ingest_api.IngestApi"
    ) as mock_ingest_api:

        # Set up the mocks
        mock_api_client_instance = MagicMock()
        mock_api_client.return_value.__enter__.return_value = mock_api_client_instance

        mock_ingest_api_instance = MagicMock()
        mock_ingest_api.return_value = mock_ingest_api_instance
        mock_ingest_api_instance.register_data_item = AsyncMock(return_value={"Success": True})

        # Call post_dlm_data_item with non-empty kafka_base_dir
        kafka_base_dir = "/data/test/"
        await post_dlm_data_item(
            ingest_url=INGEST_HOST,
            storage_name=STORAGE_NAME,
            ingest_event_data=KAFKA_MSG,
            kafka_base_dir=kafka_base_dir,
        )

        # Verify that register_data_item was called with the modified file path
        mock_ingest_api_instance.register_data_item.assert_called_once()
        call_args = mock_ingest_api_instance.register_data_item.call_args[1]

        # The item_name should have the kafka_base_dir removed
        expected_item_name = KAFKA_MSG["file"].replace(kafka_base_dir, "")
        assert call_args["item_name"] == expected_item_name
        assert call_args["uri"] == KAFKA_MSG["file"]


@pytest.mark.asyncio
async def test_kafka_base_dir_from_command_line():
    """Test that kafka_base_dir from command line is passed to post_dlm_data_item."""
    # Define a non-empty kafka_base_dir value
    test_kafka_base_dir = "/data/test/"

    # Mock the argparse.ArgumentParser to return simulated arguments with non-empty kafka_base_dir
    mock_args = mock.Mock(
        kafka_broker_url=KAFKA_HOST,
        kafka_topic=[TEST_TOPIC],
        ingest_url=INGEST_HOST,
        storage_name=STORAGE_NAME,
        kafka_base_dir=test_kafka_base_dir,
        check_rclone_access=False,
    )

    # Mock the necessary components
    with mock.patch(
        "src.ska_dlm_client.kafka_watcher.main.argparse.ArgumentParser.parse_args",
        return_value=mock_args,
    ), mock.patch(
        "src.ska_dlm_client.kafka_watcher.main.asyncio.run"
    ) as mock_asyncio_run, mock.patch(
        "src.ska_dlm_client.kafka_watcher.main.watch", new_callable=AsyncMock
    ) as mock_watch:

        # Call the main function
        main()

        # Verify that watch was called with the correct kafka_base_dir argument
        mock_watch.assert_called_once()
        assert mock_watch.call_args[1]["kafka_base_dir"] == test_kafka_base_dir

        # Verify that asyncio.run was called with the result of calling watch
        # When an AsyncMock is called, it returns a coroutine object
        mock_asyncio_run.assert_called_once()


@pytest.mark.asyncio
async def test_kafka_base_dir_used_in_watch():
    """Test that kafka_base_dir is passed from watch to post_dlm_data_item."""
    # Define a non-empty kafka_base_dir value
    test_kafka_base_dir = "/data/test/"

    # Mock the necessary components
    with mock.patch("aiokafka.AIOKafkaConsumer") as mock_kafka_consumer, mock.patch(
        "src.ska_dlm_client.kafka_watcher.main._start_consumer"
    ) as mock_start_consumer, mock.patch(
        "src.ska_dlm_client.kafka_watcher.main.post_dlm_data_item"
    ) as mock_post_dlm_data_item:

        # Set up the mocks
        mock_kafka_consumer_instance = mock_kafka_consumer.return_value
        mock_kafka_consumer_instance.stop = AsyncMock()
        mock_kafka_consumer_instance.__aiter__.return_value = [
            mock.Mock(value=json.dumps(KAFKA_MSG).encode("utf-8"))
        ]

        mock_start_consumer.return_value = True
        mock_post_dlm_data_item.return_value = None

        # Call watch with non-empty kafka_base_dir
        await watch(
            kafka_broker_url=[KAFKA_HOST],
            kafka_topic=[TEST_TOPIC],
            ingest_url=INGEST_HOST,
            storage_name=STORAGE_NAME,
            kafka_base_dir=test_kafka_base_dir,
            check_rclone_access=False,
        )

        # Verify that post_dlm_data_item was called with the correct kafka_base_dir
        mock_post_dlm_data_item.assert_called_once()
        assert mock_post_dlm_data_item.call_args[1]["kafka_base_dir"] == test_kafka_base_dir

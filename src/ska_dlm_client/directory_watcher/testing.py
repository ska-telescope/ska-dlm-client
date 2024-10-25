"""Code related to testing of watcher."""

import logging
import sys

from ska_dlm_client.directory_watcher.configuration_details import WatchConfiguration
from ska_dlm_client.openapi import api_client, configuration
from ska_dlm_client.openapi.dlm_api import ingest_api, storage_api

logger = logging.getLogger(__name__)


def init_location_for_testing(storage_configuration: configuration) -> str:
    """Perform location initialisation to be used when testing."""
    with api_client.ApiClient(storage_configuration) as the_api_client:
        api_storage = storage_api.StorageApi(the_api_client)

        # get the location_id
        response = api_storage.query_location_storage_query_location_get(
            location_name=WatchConfiguration.LOCATION_NAME
        )
        logger.info("query_location_response: %s", response)
        if not isinstance(response, list):
            logger.error("Unexpected response from query_location_storage")
            sys.exit(1)
        if len(response) == 1:
            the_location_id = response[0]["location_id"]
        else:
            response = api_storage.init_location_storage_init_location_post(
                location_name=WatchConfiguration.LOCATION_NAME,
                location_type=WatchConfiguration.LOCATION_TYPE,
                location_country=WatchConfiguration.LOCATION_COUNTRY,
                location_city=WatchConfiguration.LOCATION_CITY,
                location_facility=WatchConfiguration.LOCATION_FACILITY,
            )
            the_location_id = response
        logger.info("location_id: %s", the_location_id)
    return the_location_id


def init_storage_for_testing(storage_configuration: configuration, the_location_id: str) -> str:
    """Perform storge initialisation to be used when testing."""
    assert the_location_id is not None
    with api_client.ApiClient(storage_configuration) as the_api_client:
        api_storage = storage_api.StorageApi(the_api_client)
        # Get the storage_id
        response = api_storage.query_storage_storage_query_storage_get(
            storage_name=WatchConfiguration.STORAGE_NAME
        )
        if not isinstance(response, list):
            logger.error("Unexpected response from query_storage_storage")
            sys.exit(1)
        if len(response) == 1:
            the_storage_id = response[0]["storage_id"]
        else:
            response = api_storage.init_storage_storage_init_storage_post(
                storage_name=WatchConfiguration.STORAGE_NAME,
                location_name=WatchConfiguration.LOCATION_NAME,
                location_id=the_location_id,
                storage_type=WatchConfiguration.STORAGE_TYPE,
            )
            the_storage_id = response
        logger.info("storage_id: %s", the_storage_id)

        # Setup the storage config
        response = api_storage.create_storage_config_storage_create_storage_config_post(
            body=WatchConfiguration.STORAGE_CONFIG,
            storage_id=the_storage_id,
            storage_name=WatchConfiguration.STORAGE_NAME,
            config_type="rclone",
        )
        storage_config_id = response
        logger.info("storage_config_id: %s", storage_config_id)
    return the_storage_id


def test_ingest_item(ingest_configuration: configuration, storage_id: str):
    """Test ingesting a single item."""
    with api_client.ApiClient(ingest_configuration) as the_api_client:
        api_ingest = ingest_api.IngestApi(the_api_client)
        the_path = "k"
        response = api_ingest.register_data_item_ingest_register_data_item_post(
            item_name=the_path,
            uri=the_path,
            storage_name=WatchConfiguration.STORAGE_NAME,
            storage_id=storage_id,
            eb_id=WatchConfiguration.EB_ID,
        )
        logger.info("register_data_item_response: %s", response)

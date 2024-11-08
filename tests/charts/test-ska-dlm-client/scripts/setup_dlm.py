"""Application to configure the DLM for integration/developer testing scenarios."""

import argparse
import dataclasses
import logging
import sys

from ska_dlm_client.openapi import api_client, configuration
from ska_dlm_client.openapi.dlm_api import ingest_api, storage_api

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class _WatcherTestConfiguration:
    """Configuration required during integration testing."""

    LOCATION_NAME = "ThisDLMClientLocationName"
    LOCATION_TYPE = "ThisDLMClientLocation"
    LOCATION_COUNTRY = "Australia"
    LOCATION_CITY = "Marksville"
    LOCATION_FACILITY = "ICRAR"
    STORAGE_CONFIG = {"name": "data", "type": "local", "parameters": {}}
    STORAGE_INTERFACE = "posix"
    STORAGE_TYPE = "disk"


def init_location_for_testing(storage_configuration: configuration) -> str:
    """Perform location initialisation to be used when testing."""
    with api_client.ApiClient(storage_configuration) as the_api_client:
        api_storage = storage_api.StorageApi(the_api_client)

        # get the location_id
        response = api_storage.query_location_storage_query_location_get(
            location_name=_WatcherTestConfiguration.LOCATION_NAME
        )
        logger.info("query_location_response: %s", response)
        if not isinstance(response, list):
            logger.error("Unexpected response from query_location_storage")
            sys.exit(1)
        if len(response) == 1:
            the_location_id = response[0]["location_id"]
            logger.info("location_id already exists in DLM")
        else:
            response = api_storage.init_location_storage_init_location_post(
                location_name=_WatcherTestConfiguration.LOCATION_NAME,
                location_type=_WatcherTestConfiguration.LOCATION_TYPE,
                location_country=_WatcherTestConfiguration.LOCATION_COUNTRY,
                location_city=_WatcherTestConfiguration.LOCATION_CITY,
                location_facility=_WatcherTestConfiguration.LOCATION_FACILITY,
            )
            the_location_id = response
        logger.info("location_id: %s", the_location_id)
    return the_location_id


def init_storage_for_testing(
    storage_name: str, storage_configuration: configuration, the_location_id: str
) -> str:
    """Perform storge initialisation to be used when testing."""
    assert the_location_id is not None
    with api_client.ApiClient(storage_configuration) as the_api_client:
        api_storage = storage_api.StorageApi(the_api_client)
        # Get the storage_id
        response = api_storage.query_storage_storage_query_storage_get(storage_name=storage_name)
        if not isinstance(response, list):
            logger.error("Unexpected response from query_storage_storage")
            sys.exit(1)
        if len(response) == 1:
            the_storage_id = response[0]["storage_id"]
            logger.info("storage_id already exists in DLM")
        else:
            response = api_storage.init_storage_storage_init_storage_post(
                storage_name=storage_name,
                storage_type=_WatcherTestConfiguration.STORAGE_TYPE,
                storage_interface=_WatcherTestConfiguration.STORAGE_INTERFACE,
                location_id=the_location_id,
                location_name=_WatcherTestConfiguration.LOCATION_NAME,
            )
            the_storage_id = response
        logger.info("storage_id: %s", the_storage_id)

        # Setup the storage config. Doesn't matter if it has been set before.
        response = api_storage.create_storage_config_storage_create_storage_config_post(
            body=_WatcherTestConfiguration.STORAGE_CONFIG,
            storage_id=the_storage_id,
            storage_name=storage_name,
            config_type="rclone",
        )
        storage_config_id = response
        logger.info("storage_config_id: %s", storage_config_id)
    return the_storage_id


def setup_testing(storage_name: str, storage_configuration: configuration.Configuration):
    """Complete configuration of the environment."""
    # TODO: It would be expected that the following config would already be
    # completed in prod but leaving in place for now.
    logger.info("Testing setup.")
    location_id = init_location_for_testing(storage_configuration)
    storage_id = init_storage_for_testing(
        storage_name=storage_name,
        storage_configuration=storage_configuration,
        the_location_id=location_id,
    )
    logger.info("location id %s and storage id %s", location_id, storage_id)


def create_parser() -> argparse.ArgumentParser:
    """Define a parser for all the command line parameters."""
    parser = argparse.ArgumentParser(prog="dlm_directory_watcher")

    # Adding optional argument.
    parser.add_argument(
        "-n",
        "--storage-name",
        type=str,
        required=True,
        help="The name by which the DLM system know the storage as.",
    )
    parser.add_argument(
        "-s",
        "--storage-url",
        type=str,
        required=True,
        help="Storage service URL, excluding any service name and port.",
    )
    parser.add_argument(
        "-p",
        "--storage-service-port",
        type=int,
        required=True,
        help="Storage service port",
    )
    return parser


def main():
    """Start the integration/developer setup test application."""
    parser = create_parser()
    args = parser.parse_args()
    storage_name = args.storage_name
    storage_base_url = args.storage_url
    storage_service_port = args.storage_service_port
    storage_url = f"{storage_base_url}:{storage_service_port}"
    storage_configuration = configuration.Configuration(host=storage_url)
    setup_testing(storage_name, storage_configuration)


if __name__ == "__main__":
    main()

"""Application to configure the DLM for integration/developer testing scenarios.

This code will create a basic configuration within DLM that can be used for further client
testing across various k8s clusters or configurations.

The usage expected is
helm install -f resources/dp-proj-user.yaml test-ska-dlm-client tests/charts/test-ska-dlm-client/
helm test test-ska-dlm-client
helm uninstall test-ska-dlm-client

NOTE: it is expected that the same values file can be used between this and the ska-dlm-client.

"""

import argparse
import logging
import sys

from ska_dlm_client.common_types import (
    LocationCountry,
    LocationType,
    StorageInterface,
    StorageType,
)
from ska_dlm_client.openapi import api_client
from ska_dlm_client.openapi.configuration import Configuration
from ska_dlm_client.openapi.dlm_api import storage_api

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Constants that can be used for testing.
LOCATION_NAME = "ThisDLMClientLocationName"
LOCATION_TYPE = LocationType.LOW_INTEGRATION
LOCATION_COUNTRY = LocationCountry.AU
LOCATION_CITY = "Marksville"
LOCATION_FACILITY = "local"  # TODO: query location_facility lookup table
STORAGE_CONFIG = {"name": "dir-watcher", "type": "local", "root_path": "", "parameters": {}}
STORAGE_INTERFACE = StorageInterface.POSIX
STORAGE_TYPE = StorageType.FILESYSTEM


def init_location_for_testing(storage_configuration: Configuration) -> str:
    """Perform location initialisation to be used when testing."""
    with api_client.ApiClient(storage_configuration) as the_api_client:
        api_storage = storage_api.StorageApi(the_api_client)

        # get the location_id
        response = api_storage.query_location(location_name=LOCATION_NAME)
        logger.info("query_location response: %s", response)
        if not isinstance(response, list):
            logger.error("Unexpected response from query_location_storage")
            sys.exit(1)
        if len(response) == 1:
            the_location_id = response[0]["location_id"]
            logger.info("location already exists in DLM")
        else:
            response = api_storage.init_location(
                location_name=LOCATION_NAME,
                location_type=LOCATION_TYPE,
                location_country=LOCATION_COUNTRY,
                location_city=LOCATION_CITY,
                location_facility=LOCATION_FACILITY,
            )
            the_location_id = response
            logger.info("location created in DLM")
        logger.info("location_id: %s", the_location_id)
    return the_location_id


def init_storage_for_testing(
    storage_name: str,
    storage_configuration: Configuration,
    storage_root_directory: str,
    the_location_id: str,
) -> str:
    """Perform storage initialisation to be used when testing."""
    assert the_location_id is not None
    with api_client.ApiClient(storage_configuration) as the_api_client:
        api_storage = storage_api.StorageApi(the_api_client)
        # Get the storage_id
        response = api_storage.query_storage(storage_name=storage_name)
        logger.info("query_storage response: %s", response)
        if not isinstance(response, list):
            logger.error("Unexpected response from query_storage_storage")
            sys.exit(1)
        if len(response) == 1:
            the_storage_id = response[0]["storage_id"]
            logger.info("storage_id already exists in DLM")
        else:
            response = api_storage.init_storage(
                storage_name=storage_name,
                storage_type=STORAGE_TYPE,
                storage_interface=STORAGE_INTERFACE,
                root_directory=storage_root_directory,
                location_id=the_location_id,
                location_name=LOCATION_NAME,
            )
            the_storage_id = response
            logger.info("Storage created in DLM")
        logger.info("storage_id: %s", the_storage_id)

        # Setup the storage config. Doesn't matter if it has been set before.
        response = api_storage.create_storage_config(
            body=STORAGE_CONFIG,
            storage_id=the_storage_id,
            storage_name=storage_name,
            config_type="rclone",
        )
        storage_config_id = response
        logger.info("storage_config_id: %s", storage_config_id)
    return the_storage_id


def setup_testing(
    storage_name: str, storage_configuration: Configuration, storage_root_directory: str
):
    """Complete configuration of the environment."""
    # TODO: It would be expected that the following config would already be
    # completed in prod but leaving in place for now.
    logger.info("Testing setup.")
    location_id = init_location_for_testing(storage_configuration)
    storage_id = init_storage_for_testing(
        storage_name=storage_name,
        storage_configuration=storage_configuration,
        storage_root_directory=storage_root_directory,
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
        "--storage-server-url",
        type=str,
        required=True,
        help="Storage service URL.",
    )
    parser.add_argument(
        "-r",
        "--storage-root-directory",
        type=str,
        required=True,
        help="Storage root directory.",
    )
    return parser


def main():
    """Start the integration/developer setup test application."""
    parser = create_parser()
    args = parser.parse_args()
    storage_configuration = Configuration(host=args.storage_url)
    setup_testing(args.storage_name, storage_configuration, args.storage_root_directory)


if __name__ == "__main__":
    main()

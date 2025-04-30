"""Initialize a location and a storage."""

import argparse
import logging
import sys

from ska_dlm_client.openapi import api_client
from ska_dlm_client.openapi.configuration import Configuration
from ska_dlm_client.openapi.dlm_api import storage_api

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Constants that can be used for testing.
LOCATION_NAME = "ThisDLMClientLocationName"
LOCATION_TYPE = "ThisDLMClientLocationType"
LOCATION_COUNTRY = "Australia"
LOCATION_CITY = "Kensington"
LOCATION_FACILITY = "SKA-Test"
STORAGE_CONFIG_FINAL_STORE = {
    "name": "final-store",
    "type": "alias",
    "parameters": {"remote": "/"},
}
STORAGE_CONFIG_PST_RT_DATA = {
    "name": "pst-rt-data",
    "type": "sftp",
    "parameters": {
        "host": "ska-dlm-client-ssh-sa-pst",
        "user": "dlm",
        "key_file": "/secrets/pst",
        "set_modtime": "false",
        "shell_type": "unix",
        "idle_timeout": "20s",
        "chunk_size": "254Ki",
        "ciphers": "aes256-ctr",
    },
}
STORAGE_INTERFACE = "posix"
STORAGE_TYPE = "disk"
STORAGE_NAME_FINAL = "final"


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
            the_storage_id_pst = response[0]["storage_id"]
            the_storage_id_final = response[0]["storage_id"]
            logger.info("storage_id already exists in DLM")
        else:
            # Create the storage from the command line
            response = api_storage.init_storage(
                storage_name=storage_name,
                storage_type=STORAGE_TYPE,
                storage_interface=STORAGE_INTERFACE,
                root_directory=storage_root_directory,
                location_id=the_location_id,
                location_name=LOCATION_NAME,
            )
            the_storage_id_pst = response
            logger.info("Storage created in DLM")
            logger.info("Now creating final store init_storage")
            response = api_storage.init_storage(
                storage_name=STORAGE_NAME_FINAL,
                storage_type=STORAGE_TYPE,
                storage_interface=STORAGE_INTERFACE,
                root_directory="/data",
                location_id=the_location_id,
                location_name=LOCATION_NAME,
            )
            the_storage_id_final = response
            logger.info("Storage created in DLM")
        logger.info("storage_id_pst: %s", the_storage_id_pst)
        logger.info("storage_id_final: %s", the_storage_id_final)

        # Setup the storage config. Doesn't matter if it has been set before.
        response = api_storage.create_storage_config(
            body=STORAGE_CONFIG_PST_RT_DATA,
            storage_id=the_storage_id_pst,
            storage_name=storage_name,
            config_type="rclone",
        )
        storage_config_id = response
        logger.info("working storage_config_id: %s", storage_config_id)
        logger.info("Now creating final store create_storage_config")
        response = api_storage.create_storage_config(
            body=STORAGE_CONFIG_FINAL_STORE,
            storage_id=the_storage_id_final,
            storage_name=STORAGE_NAME_FINAL,
            config_type="rclone",
        )
        storage_config_id = response
        logger.info("final storage_config_id: %s", storage_config_id)
    return the_storage_id_pst


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
    storage_configuration = Configuration(host=args.storage_server_url)
    try:
        setup_testing(args.storage_name, storage_configuration, args.storage_root_directory)
    except Exception as ex:  # pylint: disable=broad-exception-caught
        # We want to exit with 0 so k8s doesn't try to restart
        logger.error(ex)
        sys.exit(0)


if __name__ == "__main__":
    main()

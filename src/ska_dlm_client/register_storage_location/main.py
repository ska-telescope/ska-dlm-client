"""Initialize a location and a storage."""

import argparse
import logging
import os
import pwd
import shutil
import sys

from ska_dlm_client.common_types import (
    LocationCountry,
    LocationType,
    StorageInterface,
    StorageType,
)
from ska_dlm_client.directory_watcher.config import WatcherConfig
from ska_dlm_client.openapi import api_client
from ska_dlm_client.openapi.configuration import Configuration
from ska_dlm_client.openapi.dlm_api import storage_api

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Constants that can be used for testing.
LOCATION_NAME = "ThisDLMClientLocationName"
LOCATION_TYPE = LocationType.LOW_INTEGRATION
LOCATION_COUNTRY = LocationCountry.AU
LOCATION_CITY = "Kensington"
LOCATION_FACILITY = "local"
RCLONE_CONFIG_TARGET = {"name": "data", "type": "alias", "parameters": {"remote": "/data"}}
RCLONE_CONFIG_SOURCE = {"name": "dlm-client", "type": "sftp", "parameters":
    {
        "host": "dlm_directory_watcher",
        "key_file": "/root/.ssh/id_rsa",
        "shell_type": "unix",
        "type": "sftp",
        "user": "ska-dlm"
    }}
STORAGE_INTERFACE = "posix"
STORAGE_TYPE = "filesystem"

def get_or_init_location(
    api_configuration: Configuration,
    location:str=LOCATION_NAME,
    storage_url="http://dlm_storage:8003") -> str:
    """Perform location initialisation to be used when testing."""
    with api_client.ApiClient(api_configuration) as the_api_client:
        api_storage = storage_api.StorageApi(the_api_client)

        # get the location_id
        logger.info("Checking location: %s", location)
        api_storage.api_client.configuration.host = storage_url
        response = api_storage.query_location(location_name=location)
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

def get_or_init_storage(
    storage_name: str,
    api_configuration: Configuration,
    storage_root_directory: str,
    the_location_id: str,
    rclone_config:str
) -> str:
    """Get storage_id or perform storage initialisation based on the storage_name provided."""
    assert the_location_id is not None
    os.makedirs(storage_root_directory, exist_ok=True)
    logger.info("Watcher directory %s created (or already existed)", storage_root_directory)
    with api_client.ApiClient(api_configuration) as the_api_client:
        api_storage = storage_api.StorageApi(the_api_client)
        # Get the storage_id
        response = api_storage.query_storage(storage_name=storage_name)
        logger.info("query_storage response: %s", response)
        if not isinstance(response, list):
            logger.error("Unexpected response from query_storage_storage")
            sys.exit(1)
        if len(response) == 1:
            the_storage_id = response[0]["storage_id"]
            logger.info("storage %s already exists in DLM", storage_name)
            storage_config_id = api_storage.get_storage_config(the_storage_id)
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

            if rclone_config is not None:
                # Setup the storage config.
                response = api_storage.create_storage_config(
                    request_body=rclone_config,
                    storage_id=the_storage_id,
                    storage_name=storage_name,
                    config_type="rclone",
                )
                storage_config_id = response
                logger.info("Storage config created with id: %s", storage_config_id)

                # Retrieve and install the rclone ssh public key
                key = api_storage.get_ssh_public_key()
                with open(os.path.expanduser("~/.ssh/authorized_keys"), "a", encoding="utf-8") as key_file:
                    key_file.write(f"\n{key}\n")
                shutil.copyfile(os.path.expanduser("~/.ssh/authorized_keys"), "/home/ska-dlm/.ssh/authorized_keys")
                os.chown("/home/ska-dlm/.ssh/authorized_keys", pwd.getpwnam('ska-dlm').pw_uid,pwd.getpwnam('ska-dlm').pw_gid)
                os.chmod("/home/ska-dlm/.ssh/authorized_keys", 0o600)
                logger.info("rclone SSH public key installed.")
    return the_storage_id

def setup_volume(watcher_config:WatcherConfig, api_configuration: Configuration,
                 rclone_config: str=None,
                 location_id: str=None):
    """
    Register and configure a storage volume. This takes care of already existing 
    volumes.
    """
    if location_id is None:
        location_id = get_or_init_location(api_configuration,
                                           location=LOCATION_NAME
                                           )
    storage_id = get_or_init_storage(
        storage_name=watcher_config.storage_name,
        api_configuration=api_configuration,
        storage_root_directory=watcher_config.storage_root_directory,
        the_location_id=location_id,
        rclone_config=rclone_config
    )
    logger.info("location id %s and storage id %s", location_id, storage_id)
    return storage_id

def setup_testing(api_configuration: Configuration):
    """Configuration of a target storage endpoint for rclone."""
    # NOTE: This is only required for integration testing with the DLM
    # server.
    # The setup of the source volume is now performed during the startup
    # of the client. In future the setup of a default (archive) storage
    # endpoint will be performed during stratup of the DLM server and
    # then this can be removed as well.
    logger.info("Testing setup.")
    location_id = get_or_init_location(api_configuration, location=LOCATION_NAME)
    storage_id = get_or_init_storage(
        storage_name = RCLONE_CONFIG_TARGET["name"],
        api_configuration = api_configuration,
        storage_root_directory = RCLONE_CONFIG_TARGET["parameters"]["remote"],
        the_location_id = location_id,
        rclone_config = RCLONE_CONFIG_TARGET
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
    """If this is called as a CLI we just register the integration/developer setup volumes."""
    parser = create_parser()
    args = parser.parse_args()
    api_configuration = Configuration(host=args.storage_server_url)
    setup_testing(api_configuration)


if __name__ == "__main__":
    main()

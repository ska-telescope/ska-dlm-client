# pylint: disable=broad-exception-caught
"""Initialize a location and a storage."""

import argparse
import logging
import os
import pwd
import shutil
import sys

from ska_dlm_client.common_types import LocationCountry, LocationType
from ska_dlm_client.config import Config
from ska_dlm_client.openapi import api_client
from ska_dlm_client.openapi.configuration import Configuration
from ska_dlm_client.openapi.dlm_api import storage_api

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
logger.info(
    "[env] STORAGE_URL=%r INGEST_URL=%r SOURCE_NAME=%r",
    os.getenv("STORAGE_URL"),
    os.getenv("INGEST_URL"),
    os.getenv("SOURCE_NAME"),
)

# Constants that can be used for testing.
LOCATION_NAME = "ThisDLMClientLocationName"
LOCATION_TYPE = LocationType.LOW_INTEGRATION
LOCATION_COUNTRY = LocationCountry.AU
LOCATION_CITY = "Kensington"
LOCATION_FACILITY = "local"
RCLONE_CONFIG_TARGET = {
    "name": "dlm-archive",
    "type": "alias",
    "parameters": {"remote": "/dlm-archive"},
}
RCLONE_CONFIG_SOURCE = {
    "name": "dir-watcher",
    "type": "sftp",
    "parameters": {
        "host": "dlm_directory_watcher",
        "key_file": "/root/.ssh/id_rsa",
        "shell_type": "unix",
        "type": "sftp",
        "user": "ska-dlm",
    },
}
STORAGE_INTERFACE = "posix"
STORAGE_TYPE = "filesystem"


def get_or_init_location(
    api_configuration: Configuration,
    location: str = LOCATION_NAME,
    storage_url=None,
) -> str:
    """Perform location initialisation to be used when testing."""
    storage_url = api_configuration.host if storage_url is None else storage_url
    with api_client.ApiClient(api_configuration) as the_api_client:
        api_storage = storage_api.StorageApi(the_api_client)

        # get the location_id
        logger.info("Checking location: %s", location)
        api_storage.api_client.configuration.host = storage_url
        logger.info(
            "[get_or_init_location] calling query_location with host=%s",
            api_storage.api_client.configuration.host,
        )
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
    rclone_config: str,
) -> str:
    """Get storage_id or perform storage initialisation based on the storage_name provided."""
    assert the_location_id is not None
    if not os.path.exists(storage_root_directory):
        try:
            os.makedirs(storage_root_directory, exist_ok=True)
        except PermissionError as e:
            # we just log the error here
            logger.error(
                "Unable to create storage root directory %s: %s", storage_root_directory, e
            )
    logger.info("Data directory %s created (or already existed)", storage_root_directory)
    with api_client.ApiClient(api_configuration) as the_api_client:
        api_storage = storage_api.StorageApi(the_api_client)
        # Ensure storage API calls go to the storage service, not ingest
        api_storage.api_client.configuration.host = api_configuration.host
        logger.info(
            "[get_or_init_storage] calling query_storage with host=%s",
            api_storage.api_client.configuration.host,
        )
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
                try:
                    with open(
                        os.path.expanduser("~/.ssh/authorized_keys"), "a", encoding="utf-8"
                    ) as key_file:
                        key_file.write(f"\n{key}\n")
                    if (
                        "USER" not in os.environ or os.environ["USER"] == "root"
                    ):  # assume running inside a client container
                        shutil.copyfile(
                            os.path.expanduser("~/.ssh/authorized_keys"),
                            "/home/ska-dlm/.ssh/authorized_keys",
                        )
                        os.chown(
                            "/home/ska-dlm/.ssh/authorized_keys",
                            pwd.getpwnam("ska-dlm").pw_uid,
                            pwd.getpwnam("ska-dlm").pw_gid,
                        )
                        os.chmod("/home/ska-dlm/.ssh/authorized_keys", 0o600)
                        logger.info("rclone SSH public key installed.")
                    else:
                        logger.info("rclone SSH public key installed for current user.")
                except Exception as e:
                    logger.error("Unable to install SSH key: %s", e)
    return the_storage_id


def setup_volume(  # pylint: disable=too-many-arguments, too-many-positional-arguments
    watcher_config: Config,
    api_configuration: Configuration,
    rclone_config: str = None,
    location_id: str = None,
    storage_url: str = None,
    setup_target: bool = False,
):
    """Register and configure a storage volume. This takes care of already existing volumes."""
    storage_url = storage_url or os.getenv("STORAGE_URL") or "http://dlm_storage:8003"
    logger.info(
        "[setup_volume] storage_url resolved to: %s", storage_url
    )
    logger.info(
        "[setup_volume] api_configuration.host = %s", api_configuration.host
    )
    if location_id is None:
        location_id = get_or_init_location(
            api_configuration, location=LOCATION_NAME, storage_url=storage_url
        )
    if setup_target:
        storage_name = watcher_config.migration_destination_storage_name
        storage_root_directory = "/dlm-archive"
    else:
        storage_name = watcher_config.storage_name
        storage_root_directory = watcher_config.storage_root_directory
    storage_id = get_or_init_storage(
        storage_name=storage_name,
        api_configuration=api_configuration,
        storage_root_directory=storage_root_directory,
        the_location_id=location_id,
        rclone_config=rclone_config,
    )
    logger.info("location id %s and storage id %s", location_id, storage_id)
    return storage_id


def setup_testing(api_configuration: Configuration):
    """Configure a target storage endpoint for rclone."""
    # NOTE: This is only required for integration testing with the DLM
    # server.
    # The setup of the source volume is now performed during the startup
    # of the client. In future the setup of a default (archive) storage
    # endpoint will be performed during startup of the DLM server and
    # then this can be removed as well.
    logger.info("Testing setup.")
    storage_url = (
        f"{api_configuration.host}:8003"
        if api_configuration.host.find(":") == -1
        else api_configuration.host
    )
    location_id = get_or_init_location(
        api_configuration, location=LOCATION_NAME, storage_url=storage_url
    )
    storage_id = get_or_init_storage(
        storage_name=RCLONE_CONFIG_TARGET["name"],
        api_configuration=api_configuration,
        storage_root_directory=RCLONE_CONFIG_TARGET["parameters"]["remote"],
        the_location_id=location_id,
        rclone_config=RCLONE_CONFIG_TARGET,
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
    api_configuration = Configuration(host=args.storage_url)
    setup_testing(api_configuration)


if __name__ == "__main__":
    main()

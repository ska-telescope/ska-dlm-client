"""Initialize a location and a storage."""

import argparse
import logging
import os
import pwd
import shutil
import sys

from ska_dlm_client.common_types import LocationCountry, LocationType
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
RCLONE_CONFIG_SOURCE = {
    "name": "dlm-client",
    "type": "sftp",
    "parameters": {
        "host": "dlm_directory_watcher",
        "key_file": "/root/.ssh/id_rsa",  # <-- client PRIVATE key
        "shell_type": "unix",
        "type": "sftp",
        "user": "ska-dlm",
    },
}
STORAGE_INTERFACE = "posix"
STORAGE_TYPE = "filesystem"

# ---------------------------------------------------------------------------
# ConfigDB watcher demo storages
# ---------------------------------------------------------------------------

DEMO_SOURCE_STORAGE_NAME = "SDPBuffer"
DEMO_DEST_STORAGE_NAME = "dest_storage"

# As seen *inside* the ConfigDB watcher container
DEMO_SOURCE_ROOT_DIRECTORY = "/data/SDPBuffer"
DEMO_DEST_ROOT_DIRECTORY = "/data/dest_storage"

RCLONE_CONFIG_SDPBUFFER = {
    "name": DEMO_SOURCE_STORAGE_NAME,
    "type": "sftp",
    "parameters": {
        # Talk to your ConfigDB watcher container over SFTP
        "host": "dlm_configdb_watcher",
        "user": "ska-dlm",
        "key_file": "/root/.ssh/id_rsa",
        "shell_type": "unix",
        "type": "sftp",
        # NOTE: for sftp remotes, the path is usually specified at copy-time,
        # so we don't set "remote" here.
    },
}

RCLONE_CONFIG_DEST_STORAGE = {
    "name": DEMO_DEST_STORAGE_NAME,
    "type": "alias",
    "parameters": {
        # As seen from *rclone's* container; /data is already used in tests.
        "remote": DEMO_DEST_ROOT_DIRECTORY,
    },
}


def get_or_init_location(
    api_configuration: Configuration,
    location: str = LOCATION_NAME,
    storage_url: str = "http://dlm_storage:8003",
) -> str:
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
    rclone_config: dict | None,
) -> str:
    """Get storage_id or perform storage initialisation based on the storage_name provided."""
    assert the_location_id is not None
    try:
        os.makedirs(storage_root_directory, exist_ok=True)
    except OSError as err:
        logger.warning(
            "Could not create %s (likely read-only filesystem): %s",
            storage_root_directory,
            err,
        )
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
                with open(
                    os.path.expanduser("~/.ssh/authorized_keys"), "a", encoding="utf-8"
                ) as key_file:
                    key_file.write(f"\n{key}\n")
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
    return the_storage_id


def setup_volume(
    watcher_config: WatcherConfig,
    api_configuration: Configuration,
    rclone_config: str = None,
    location_id: str = None,
):
    """
    Register and configure a storage volume.

    This takes care of already existing volumes.
    """
    if location_id is None:
        location_id = get_or_init_location(api_configuration, location=LOCATION_NAME)
    storage_id = get_or_init_storage(
        storage_name=watcher_config.storage_name,
        api_configuration=api_configuration,
        storage_root_directory=watcher_config.storage_root_directory,
        the_location_id=location_id,
        rclone_config=rclone_config,
    )
    logger.info("location id %s and storage id %s", location_id, storage_id)
    return storage_id


def setup_configdb_demo(api_configuration: Configuration, storage_server_url: str):
    """Set up the ConfigDB watcher demo: SDPBuffer + dest_storage."""
    logger.info(
        "setup_configdb_demo: start. ConfigDB watcher demo setup: "
        "SDPBuffer -> dest_storage. storage_server_url=%s",
        storage_server_url,
    )
    location_id = get_or_init_location(
        api_configuration,
        location=LOCATION_NAME,
        storage_url=storage_server_url,
    )
    logger.info("setup_configdb_demo: using location_id=%s", location_id)

    # Source storage: SDPBuffer (SFTP into dlm_configdb_watcher:/data/SDPBuffer)
    logger.info(
        "setup_configdb_demo: setting up source storage %s at %s with rclone_config type=%s",
        DEMO_SOURCE_STORAGE_NAME,
        DEMO_SOURCE_ROOT_DIRECTORY,
        RCLONE_CONFIG_SDPBUFFER.get("type"),
    )
    sdpbuffer_storage_id = get_or_init_storage(
        storage_name=DEMO_SOURCE_STORAGE_NAME,
        api_configuration=api_configuration,
        storage_root_directory=DEMO_SOURCE_ROOT_DIRECTORY,
        the_location_id=location_id,
        rclone_config=RCLONE_CONFIG_SDPBUFFER,
    )
    logger.info(
        "setup_configdb_demo: source storage %s has storage_id=%s",
        DEMO_SOURCE_STORAGE_NAME,
        sdpbuffer_storage_id,
    )

    # Destination storage: dest_storage (alias /data/dest_storage in rclone)
    logger.info(
        "setup_configdb_demo: setting up destination storage %s at %s "
        "with rclone_config type=%s",
        DEMO_DEST_STORAGE_NAME,
        DEMO_DEST_ROOT_DIRECTORY,
        RCLONE_CONFIG_DEST_STORAGE.get("type"),
    )
    dest_storage_id = get_or_init_storage(
        storage_name=DEMO_DEST_STORAGE_NAME,
        api_configuration=api_configuration,
        storage_root_directory=DEMO_DEST_ROOT_DIRECTORY,
        the_location_id=location_id,
        rclone_config=RCLONE_CONFIG_DEST_STORAGE,
    )
    logger.info(
        "setup_configdb_demo: destination storage %s has storage_id=%s",
        DEMO_DEST_STORAGE_NAME,
        dest_storage_id,
    )

    logger.info(
        "ConfigDB demo setup complete: location id %s, source storage id %s, "
        "dest storage id %s",
        location_id,
        sdpbuffer_storage_id,
        dest_storage_id,
    )


def create_parser() -> argparse.ArgumentParser:
    """Define a parser for all the command line parameters."""
    parser = argparse.ArgumentParser(prog="dlm_directory_watcher")

    # NOTE: For the ConfigDB watcher demo we hard-code the storage names and
    # root directories (SDPBuffer and dest_storage). Only the storage service
    # URL is configurable from the CLI.
    parser.add_argument(
        "-s",
        "--storage-server-url",
        type=str,
        required=True,
        help="Storage service URL.",
    )
    return parser


def main():
    """If this is called as a CLI we just register the integration/developer setup volumes."""
    parser = create_parser()
    args = parser.parse_args()
    api_configuration = Configuration(host=args.storage_server_url)
    setup_configdb_demo(
        api_configuration,
        storage_server_url=args.storage_server_url,
    )


if __name__ == "__main__":
    main()

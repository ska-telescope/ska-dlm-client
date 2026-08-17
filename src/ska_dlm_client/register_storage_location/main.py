# pylint: disable=broad-exception-caught
# pylint: disable=invalid-name
# pylint: disable=too-many-arguments
# pylint: disable=too-many-positional-arguments
# pylint: disable=too-many-locals
"""Initialize a location and a storage."""

import logging
import os
import pwd
import shutil
import socket
import sys

import ska_ser_logging

from ska_dlm_client.common_types import LocationCountry, LocationName, LocationType
from ska_dlm_client.config import Config
from ska_dlm_client.openapi import api_client
from ska_dlm_client.openapi.configuration import Configuration
from ska_dlm_client.openapi.dlm_api import storage_api
from ska_dlm_client.openapi.exceptions import UnprocessableEntityException

logger = logging.getLogger(__name__)

# Constants that can be used for testing.
LOCATION_NAME = os.getenv("LOCATION_NAME", LocationName.LOCAL_DEV.value)
LOCATION_TYPE = os.getenv("LOCATION_TYPE", LocationType.LOCAL_DEV.value)
LOCATION_COUNTRY = os.getenv("LOCATION_COUNTRY", LocationCountry.AU.value)
LOCATION_CITY = os.getenv("LOCATION_CITY", "Perth")
LOCATION_FACILITY = os.getenv("LOCATION_FACILITY", "local")
TARGET_ROOT = os.getenv("TARGET_ROOT", "/dlm-archive")
TGT_STORAGE_PHASE = os.getenv("TARGET_PHASE", "SOLID")
RCLONE_CONFIG_SOURCE = {
    "name": f"{os.getenv('SOURCE_NAME', 'dir-watcher')}",
    "type": "sftp",
    "parameters": {
        "host": f"{os.getenv('WATCHER_HOSTNAME', socket.gethostname())}",
        "key_file": "/root/.ssh/id_rsa",
        "shell_type": "unix",
        "type": "sftp",
        "user": f"{os.getenv('USER', 'ska-dlm')}",
    },
}
STORAGE_INTERFACE = "posix"
STORAGE_TYPE = "filesystem"


def get_or_init_location(
    api_configuration: Configuration,
    storage_url: str,
    location_name: str = "",
    location_type: str = "",  # required by init_location
    location_country: str = "",  # required by init_location
    location_city: str = "",  # required by init_location
    location_facility: str = "",  # required by init_location
) -> str:
    """Get location_id or perform location initialisation based on the location_name provided."""
    with api_client.ApiClient(api_configuration) as the_api_client:
        api_storage = storage_api.StorageApi(the_api_client)

        # get the location_id
        logger.info("Checking location: %s", location_name)
        api_storage.api_client.configuration.host = storage_url
        response = api_storage.query_location(location_name=location_name)
        logger.info("query_location response: %s", response)
        if not isinstance(response, list):
            logger.error("Unexpected response from query_location_storage")
            sys.exit(1)
        if len(response) == 1:
            the_location_id = response[0]["location_id"]
            logger.info("location already exists in DLM")
        else:
            try:
                response = api_storage.init_location(
                    location_name=location_name,
                    location_type=location_type,
                    location_country=location_country,
                    location_city=location_city,
                    location_facility=location_facility,
                )
                the_location_id = response
                logger.info("Location created in DLM")
            except UnprocessableEntityException:
                # Another process may have created the location first (race condition)
                response = api_storage.query_location(location_name=location_name)
                if not isinstance(response, list) or len(response) != 1:
                    logger.error(
                        "Location creation failed. Query returned unexpected response: %s",
                        response,
                    )
                    raise
                the_location_id = response[0]["location_id"]
                logger.info(
                    "Location %s was created concurrently by another process",
                    location_name,
                )

            try:
                response = api_storage.init_location(
                    location_name=location_name,
                    location_type=location_type,
                    location_country=location_country,
                    location_city=location_city,
                    location_facility=location_facility,
                )
                the_location_id = response
                logger.info("Location created in DLM")
            except UnprocessableEntityException:
                # Another process may have created the location first (race condition)
                response = api_storage.query_location(location_name=location_name)
                the_location_id = response[0]["location_id"]
                logger.info(
                    "Location %s was created concurrently by another process",
                    location_name,
                )

        logger.info("location_id: %s", the_location_id)
    return the_location_id


def install_ssh_key(api_storage):
    """
    Retrieve and install the rclone ssh public key.

    Parameters
    ----------
    api_storage : ska_dlm_client.openapi.dlm_api.storage_api.StorageApi
        The storage API client to use to retrieve the key.
    """
    key = api_storage.get_ssh_public_key()
    try:
        with open(os.path.expanduser("~/.ssh/authorized_keys"), "a", encoding="utf-8") as key_file:
            key_file.write(f"\n{key}\n")
        if os.path.exists("/home/ska-dlm/.ssh") and (
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


def get_or_init_storage(
    # pylint: disable=too-many-arguments, disable=too-many-positional-arguments
    storage_name: str,
    storage_url: str,
    storage_root_directory: str,
    api_configuration: Configuration,
    the_location_id: str,
    rclone_config: dict,
    storage_type: str = "filesystem",  # enum | None?
    storage_interface: str = "posix",  # enum | None?
    location_name: str = "",
    storage_phase: str = "GAS",  # enum = StoragePhase.GAS.value?
) -> str:
    """Get storage_id or perform storage initialisation based on the storage_name provided."""
    assert the_location_id is not None

    if not os.path.exists(storage_root_directory):
        try:
            os.makedirs(storage_root_directory)
            os.chmod(storage_root_directory, 0o777)
            logger.info("Data directory %s created!", storage_root_directory)
        except PermissionError as e:
            # we just log the error here
            logger.error(
                "Unable to create storage root directory %s: %s", storage_root_directory, e
            )
    with api_client.ApiClient(api_configuration) as the_api_client:
        api_storage = storage_api.StorageApi(the_api_client)
        # Ensure storage API calls go to the storage service, not ingest
        api_storage.api_client.configuration.host = storage_url

        # Always install the ssh public key
        install_ssh_key(api_storage)

        store = api_storage.query_storage(storage_name=storage_name)
        logger.info("query_storage response: %s", store)
        if not store:
            storage_id = api_storage.init_storage(
                storage_name=storage_name,
                storage_type=storage_type,
                storage_interface=storage_interface,
                root_directory=storage_root_directory,
                location_id=the_location_id,
                location_name=location_name,
                storage_phase=storage_phase,
            )
            logger.info("Storage %s created in DLM", storage_name)
        else:
            storage_id = store[0]["storage_id"]

        if rclone_config is not None:
            store_config = api_storage.get_storage_config(storage_id=storage_id)
            if not store_config:
                # Setup the storage config.
                storage_config_id = api_storage.create_storage_config(
                    request_body=rclone_config,
                    storage_id=storage_id,
                    storage_name=storage_name,
                    config_type="rclone",  # change to enum
                )
                logger.info("Storage config created with id: %s", storage_config_id)
            else:
                # Refresh the rclone config even if the endpoint exists
                api_storage.create_rclone_config(request_body=rclone_config)
        else:
            logger.warning("No rclone configuration specified")

    return storage_id


def setup_volume(  # pylint: disable=too-many-arguments, too-many-positional-arguments
    watcher_config: Config,
    api_configuration: Configuration,
    rclone_config: dict,
    location_name: str = "",
    location_type: str = "",  # required by init_location
    location_country: str = "",  # required by init_location
    location_city: str = "",  # required by init_location
    location_facility: str = "",  # required by init_location
    location_id: str | None = None,
    storage_url: str = "",
    storage_type: str = "",
    storage_interface: str = "",  # required by init_storage
    setup_target: bool = False,
):
    """Register and configure a storage volume. This takes care of already existing volumes."""
    if location_id is None:
        logger.debug("trying get_or_init_location...")
        logger.debug("trying get_or_init_location...")
        location_id = get_or_init_location(
            api_configuration,
            storage_url=storage_url,
            location_name=location_name,
            location_type=location_type,
            location_country=location_country,
            location_city=location_city,
            location_facility=location_facility,
        )
    if setup_target:  # do we need this in this function?
        storage_name = watcher_config.target_name
        storage_root_directory = TARGET_ROOT
        storage_phase = TGT_STORAGE_PHASE
    else:
        storage_name = watcher_config.source_name
        storage_phase = watcher_config.source_phase
        storage_root_directory = watcher_config.directory_to_watch
    storage_id = get_or_init_storage(
        storage_name=storage_name,
        storage_phase=storage_phase,
        storage_url=storage_url,
        storage_type=storage_type,  # compulsory for init_storage
        storage_interface=storage_interface,  # compulsory for init_storage
        api_configuration=api_configuration,
        storage_root_directory=storage_root_directory,
        the_location_id=location_id,
        rclone_config=rclone_config,
    )
    logger.info("location id %s and storage id %s", location_id, storage_id)
    return storage_id


def main():
    """If this is called as a CLI we register the requested volumes.

    The CLI is now used also to start the client in operations.
    """
    LOGLEVEL = os.environ.get("LOGLEVEL", "INFO").upper()
    ska_ser_logging.configure_logging(LOGLEVEL)


if __name__ == "__main__":
    main()

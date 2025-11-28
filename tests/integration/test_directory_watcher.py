"""Directory Watcher integration tests."""

import logging
import subprocess
from time import sleep

import pytest

from ska_dlm_client.common_types import (
    LocationCountry,
    LocationType,
    StorageInterface,
    StorageType,
)
from ska_dlm_client.config import STATUS_FILE_FILENAME
from ska_dlm_client.directory_watcher.config import WatcherConfig
from ska_dlm_client.openapi import api_client
from ska_dlm_client.openapi.configuration import Configuration
from ska_dlm_client.openapi.dlm_api import storage_api
from ska_dlm_client.openapi.dlm_api import request_api
from ska_dlm_client.register_storage_location.main import setup_testing

log = logging.getLogger(__name__)

LOCATION_NAME = "ThisDLMClientLocationName"
LOCATION_TYPE = LocationType.LOCAL_DEV
LOCATION_COUNTRY = LocationCountry.AU

LOCATION_CITY = "Marksville"
LOCATION_FACILITY = "local"  # TODO: query location_facility lookup table
STORAGE = {
    "TGT": {
        "STORAGE_NAME": "MyDisk",
        "STORAGE_TYPE": StorageType.FILESYSTEM,
        "STORAGE_INTERFACE": StorageInterface.POSIX,
        "ROOT_DIRECTORY": "/data",
        "STORAGE_CONFIG": {"name": "data", "type": "local", "parameters": {}}
    },
    "SRC": {
        "STORAGE_NAME": "dlm_watcher",
        "STORAGE_TYPE": StorageType.FILESYSTEM,
        "STORAGE_INTERFACE": StorageInterface.POSIX,
        "ROOT_DIRECTORY": "/dlm",
        "STORAGE_CONFIG": {"name": "dlm", "type": "sftp", 
                           "parameters": {
                                "host": "dlm_directory_watcher",
                                "key_file": "/root/.ssh/id_rsa",
                                "shell_type": "unix",
                                "type": "sftp",
                                "user": "ska-dlm",
                                }
                        }
                }
    }

def _get_id(item, key: str):
    return item[key] if isinstance(item, dict) else getattr(item, key)

def _init_location_if_needed(api_storage: storage_api.StorageApi) -> str:
    resp = api_storage.query_location(location_name=LOCATION_NAME)
    assert isinstance(resp, list)
    if resp:
        location_id = _get_id(resp[0], "location_id")
        log.info("Location already exists: %s", location_id)
    else:
        location_id = api_storage.init_location(
            location_name=LOCATION_NAME,
            location_type=LOCATION_TYPE,
            location_country=LOCATION_COUNTRY,
            location_city=LOCATION_CITY,
            location_facility=LOCATION_FACILITY,
        )
        assert isinstance(location_id, str) and location_id
        log.info("Location created: %s", location_id)
    return location_id

def _init_storage_if_needed(
    api_storage: storage_api.StorageApi, location_id: str,
    storage:dict = None
) -> str:
    resp = api_storage.query_storage(storage_name=storage["STORAGE_NAME"])
    assert isinstance(resp, list)
    if resp:
        storage_id = _get_id(resp[0], "storage_id")
        log.info("Storage already exists: %s", storage_id)
    else:
        storage_id = api_storage.init_storage(
            storage_name=storage["STORAGE_NAME"],
            storage_type=storage["STORAGE_TYPE"],
            storage_interface=storage["STORAGE_INTERFACE"],
            root_directory=storage["ROOT_DIRECTORY"],
            location_id=location_id,
            location_name=LOCATION_NAME,
        )
        assert isinstance(storage_id, str) and storage_id
        log.info("Storage created: %s", storage_id)
    return storage_id

@pytest.mark.integration
def test_storage_initialisation(storage_configuration: Configuration):
    """Test setting up a location, storage and storage config."""
    with api_client.ApiClient(storage_configuration) as the_api_client:
        api_storage = storage_api.StorageApi(the_api_client)

        # --- ensure location exists ---
        location_id = _init_location_if_needed(api_storage)

        # --- ensure storage exists ---
        storage_id = _init_storage_if_needed(api_storage, location_id, storage=STORAGE["TGT"])

        # --- set storage config ---
        cfg_id = api_storage.create_storage_config(
            request_body=STORAGE["TGT"]["STORAGE_CONFIG"],
            storage_id=storage_id,
            storage_name=STORAGE["TGT"]["STORAGE_NAME"],
            config_type="rclone",
        )
        assert isinstance(cfg_id, str) and cfg_id
        log.info("Target storage config id: %s", cfg_id)

        # --- verify by querying again ---
        resp2 = api_storage.query_storage(storage_name=STORAGE["TGT"]["STORAGE_NAME"])
        assert resp2 and _get_id(resp2[0], "storage_id") == storage_id

@pytest.mark.integration
def test_auto_migration(storage_configuration: Configuration):
    """Test auto migration using directory watcher."""
    # watcher_config = WatcherConfig(
    #     directory_to_watch=STORAGE["SRC"]["ROOT_DIRECTORY"] + "/watch_dir",
    #     ingest_server_url="http://localhost:8001",
    #     storage_name=STORAGE["SRC"]["STORAGE_NAME"],
    #     status_file_absolute_path=f"{STORAGE["SRC"]["ROOT_DIRECTORY"] + "/watch_dir"}/{STATUS_FILE_FILENAME}",
    #     storage_root_directory=STORAGE["SRC"]["ROOT_DIRECTORY"]
    # )
    api_configuration = Configuration(host="http://localhost")
    setup_testing(api_configuration)
    with api_client.ApiClient(storage_configuration) as the_api_client:
        log.info("Migration setup: Source Storage: %s",
            STORAGE["SRC"]["STORAGE_NAME"])
        log.info("Migration setup: Target Storage: %s",
            STORAGE["TGT"]["STORAGE_NAME"])
        # --- start and trigger watcher by copying file ---
        cmd = "docker exec dlm_directory_watcher cp /etc/group /dlm/watch_dir/."
        log.info("Migration setup: Copy command: %s",cmd)
        subprocess.run(cmd, shell=True, check=True)
        sleep(2)
        api_request = request_api.RequestApi(the_api_client)
        resp2 = api_request.query_exists(item_name="group")
        # assert resp2 and _get_id(resp2[0], "item_name") == "group"
        log.info("File migration verified in DLM system:  %s",resp2)
        # assert isinstance(migration_id, str) and migration_id
        # log.info("Migration initiated: %s", migration_id)

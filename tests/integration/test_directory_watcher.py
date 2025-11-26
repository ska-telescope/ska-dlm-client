"""Directory Watcher integration tests."""

import logging
import subprocess

import pytest

from ska_dlm_client.common_types import (
    LocationCountry,
    LocationType,
    StorageInterface,
    StorageType,
)
from ska_dlm_client.openapi import api_client
from ska_dlm_client.openapi.configuration import Configuration
from ska_dlm_client.openapi.dlm_api import storage_api

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
        "STORAGE_NAME": "MyDisk1",
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
    with api_client.ApiClient(storage_configuration) as the_api_client:
        api_storage = storage_api.StorageApi(the_api_client)

        # --- Check whether source storage already configured ---
        resp2 = api_storage.query_storage(storage_name=STORAGE["TGT"]["STORAGE_NAME"])
        if resp2 and _get_id(resp2[0], "storage_id"):
            log.info("Target storage already configured, skipping setup.")
            location_id = _get_id(resp2[0], "location_id")
        else:
            # --- ensure location exists ---
            location_id = _init_location_if_needed(api_storage)

            # --- ensure source storage exists ---
            _ = _init_storage_if_needed(api_storage, location_id)

        # --- Check whether target storage already configured ---
        resp2 = api_storage.query_storage(storage_name=STORAGE["SRC"]["STORAGE_NAME"])
        if resp2 and _get_id(resp2[0], "storage_id"):
            log.info("Source Storage already configured, skipping setup.")
            tgt_storage_id = _get_id(resp2[0], "storage_id")
        else:
            # --- ensure storage exists ---
            tgt_storage_id = _init_storage_if_needed(api_storage, location_id, storage=STORAGE["SRC"])

        log.info("Source Storage ID: %s", tgt_storage_id)
    # --- start and trigger watcher by copying file ---
    subprocess.run("docker start dlm_directory_watcher", shell=True, check=True)
    cmd = "docker exec dlm_directory_watcher cp /etc/group /dlm/watch_dir/."
    subprocess.run(cmd, shell=True, check=True)
    # assert isinstance(migration_id, str) and migration_id
    # log.info("Migration initiated: %s", migration_id)

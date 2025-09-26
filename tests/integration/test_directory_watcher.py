"""Directory Watcher integration tests."""

import logging

import pytest

from ska_dlm_client.openapi import api_client
from ska_dlm_client.openapi.configuration import Configuration
from ska_dlm_client.openapi.dlm_api import storage_api
from ska_dlm_client.common_types import (
    LocationCountry,
    LocationType,
    StorageType,
    StorageInterface,
)

log = logging.getLogger(__name__)

LOCATION_NAME = "ThisDLMClientLocationName"
LOCATION_TYPE = LocationType.LOCAL_DEV
LOCATION_COUNTRY = LocationCountry.AU
LOCATION_CITY = "Marksville"
LOCATION_FACILITY = "local"  # TODO: query location_facility lookup table
STORAGE_NAME = "MyDisk"
STORAGE_TYPE = StorageType.FILESYSTEM
STORAGE_INTERFACE = StorageInterface.POSIX
ROOT_DIRECTORY = "/data"
STORAGE_CONFIG = {"name": "data", "type": "local", "parameters": {}}


def _get_id(item, key: str):
    return item[key] if isinstance(item, dict) else getattr(item, key)


@pytest.mark.integration
def test_storage_initialisation(storage_configuration: Configuration):
    """Test setting up a location, storage and storage config."""
    with api_client.ApiClient(storage_configuration) as the_api_client:
        api_storage = storage_api.StorageApi(the_api_client)

        # --- ensure location exists ---
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

        # --- ensure storage exists ---
        resp = api_storage.query_storage(storage_name=STORAGE_NAME)
        assert isinstance(resp, list)
        if resp:
            storage_id = _get_id(resp[0], "storage_id")
            log.info("Storage already exists: %s", storage_id)
        else:
            storage_id = api_storage.init_storage(
                storage_name=STORAGE_NAME,
                storage_type=STORAGE_TYPE,
                storage_interface=STORAGE_INTERFACE,
                root_directory=ROOT_DIRECTORY,
                location_id=location_id,
                location_name=LOCATION_NAME,
            )
            assert isinstance(storage_id, str) and storage_id
            log.info("Storage created: %s", storage_id)

        # --- set storage config ---
        cfg_id = api_storage.create_storage_config(
            request_body=STORAGE_CONFIG,
            storage_id=storage_id,
            storage_name=STORAGE_NAME,
            config_type="rclone",
        )
        assert isinstance(cfg_id, str) and cfg_id
        log.info("Storage config id: %s", cfg_id)

        # --- verify by querying again ---
        resp2 = api_storage.query_storage(storage_name=STORAGE_NAME)
        assert resp2 and _get_id(resp2[0], "storage_id") == storage_id

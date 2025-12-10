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
from ska_dlm_client.openapi import api_client
from ska_dlm_client.openapi.configuration import Configuration
from ska_dlm_client.openapi.dlm_api import request_api, storage_api
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
        "STORAGE_CONFIG": {"name": "dlm-watcher", "type": "local", "parameters": {}},
    },
    "SRC": {
        "STORAGE_NAME": "dlm-watcher",
        "STORAGE_TYPE": StorageType.FILESYSTEM,
        "STORAGE_INTERFACE": StorageInterface.POSIX,
        "ROOT_DIRECTORY": "/dlm",
        "STORAGE_CONFIG": {
            "name": "dlm",
            "type": "sftp",
            "parameters": {
                "host": "dlm_directory_watcher",
                "key_file": "/root/.ssh/id_rsa",
                "shell_type": "unix",
                "type": "sftp",
                "user": "ska-dlm",
            },
        },
    },
}


def _get_id(item, key: str):
    return item[key] if isinstance(item, dict) else getattr(item, key)

@pytest.mark.integration
def test_auto_migration(
    storage_configuration: Configuration, request_configuration: Configuration
):
    """Test auto migration using directory watcher."""
    api_configuration = Configuration(host="http://localhost")
    setup_testing(api_configuration)
    with api_client.ApiClient(storage_configuration) as the_api_client:
        log.info("Migration setup: Source Storage: %s", STORAGE["SRC"]["STORAGE_NAME"])
        log.info("Migration setup: Target Storage: %s", STORAGE["TGT"]["STORAGE_NAME"])
        # --- trigger watcher by copying file ---
        sleep(2)
        cmd = "docker exec dlm_directory_watcher cp /etc/group /dlm/watch_dir/."
        log.info("Migration initializtion copy command: %s", cmd)
        p = subprocess.run(cmd, capture_output=True, shell=True, check=True)
        if p.returncode != 0:
            log.info("[copy file STDOUT]: %s\n", p.stdout)
            log.error("[copy file STDERR]: %s\n", p.stderr)
    assert p.returncode == 0
    with api_client.ApiClient(request_configuration) as the_api_client:
        api_request = request_api.RequestApi(the_api_client)
        sleep(2)
        resp2 = api_request.query_data_item(item_name="group")
        assert len(resp2) == 2
        assert resp2 and _get_id(resp2[0], "item_name") == "group"
        assert resp2 and _get_id(resp2[1], "item_name") == "group"

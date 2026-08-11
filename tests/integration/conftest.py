# pylint: disable=redefined-outer-name
"""Shared pytest fixtures and service readiness checks for DLM integration tests."""

import logging
import os
import subprocess
from typing import Iterator
from urllib.parse import urlparse

import pytest
import requests

from ska_dlm_client.common_types import (
    LocationCountry,
    LocationName,
    LocationType,
    StorageInterface,
    StorageType,
)
from ska_dlm_client.openapi import api_client
from ska_dlm_client.openapi.api_client import ApiException
from ska_dlm_client.openapi.configuration import Configuration
from ska_dlm_client.openapi.dlm_api import request_api, storage_api
from ska_dlm_client.register_storage_location.main import get_or_init_location, get_or_init_storage

# URLs can be overridden in CI to hit the DinD host
INGEST_URL = os.getenv("INGEST_URL", "http://dlm_ingest:8001")
REQUEST_URL = os.getenv("REQUEST_URL", "http://dlm_request:8002")
STORAGE_URL = os.getenv("STORAGE_URL", "http://dlm_storage:8003")
MIGRATION_URL = os.getenv("MIGRATION_URL", "http://dlm_migration:8004")
POSTGREST_URL = os.getenv("POSTGREST_URL", "http://dlm_postgrest:3000")
RCLONE_BASE = os.getenv("RCLONE_BASE", "https://dlm_rclone:5572")
ETCD_URL = os.getenv("ETCD_URL", "http://etcd:2379")
LOCATION_NAME = LocationName.LOCAL_DEV.value
LOCATION_TYPE = LocationType.LOCAL_DEV.value
LOCATION_COUNTRY = LocationCountry.AU.value
LOCATION_CITY = "Marksville"
LOCATION_FACILITY = "local"  # TODO: query location_facility lookup table

STORAGE = {
    "SRC": {
        "STORAGE_NAME": "configdb-watcher",
        "STORAGE_TYPE": StorageType.FILESYSTEM,
        "STORAGE_INTERFACE": StorageInterface.POSIX,
        "ROOT_DIRECTORY": "/dlm/product_dir",
        "STORAGE_PHASE": "SOLID",
        "STORAGE_CONFIG": {
            "name": "configdb-watcher",
            "type": "sftp",
            "parameters": {
                "host": "dlm_configdb_watcher",
                "key_file": "/root/.ssh/id_rsa",
                "shell_type": "unix",
                "type": "sftp",
                "user": "ska-dlm",
            },
        },
    },
    "TGT": {
        "STORAGE_NAME": "dlm-archive",
        "STORAGE_TYPE": StorageType.FILESYSTEM,
        "STORAGE_INTERFACE": StorageInterface.POSIX,
        "ROOT_DIRECTORY": "/dlm/archive_dir",
        "STORAGE_PHASE": "SOLID",
        "STORAGE_CONFIG": {
            "name": f"{os.getenv('TARGET_NAME', 'dlm-archive')}",
            "type": "sftp",
            "parameters": {
                "host": "dlm_archive",
                "port": 2222,
                "key_file": "/root/.ssh/id_rsa",
                "shell_type": "unix",
                "type": "sftp",
                "user": "ska-dlm",
            },
        },
    },
}

SRC_HOST = STORAGE["SRC"]["STORAGE_CONFIG"]["parameters"]["host"]
WATCHER_SOURCE_DIR_ROOT = f"{STORAGE['SRC']['ROOT_DIRECTORY'].rstrip('/')}"


log = logging.getLogger(__name__)

# --- OpenAPI client deserialization patch (handles Optional[Dict[str, object]]) ---
# Original private method
__orig_deserialize = getattr(api_client.ApiClient, "_ApiClient__deserialize")


def _get_id(item, key: str) -> str:
    """Return a string ID from a dict or generated API model."""
    value = item[key] if isinstance(item, dict) else getattr(item, key)
    assert isinstance(value, str)
    return value


def _get_container_log(container_name: str) -> str:
    cmd = ["docker", "logs", "--since", "600s", container_name]
    p = subprocess.run(cmd, capture_output=True, text=True, check=True)
    if p.returncode != 0:
        log.error("Failed to get logs for container %s: %s", container_name, p.stderr)
        return p.stderr
    return p.stdout


def _init_location_if_needed(api_storage: storage_api.StorageApi) -> str:
    try:
        resp = api_storage.query_location(location_name=LOCATION_NAME)
        assert isinstance(resp, list)
    except ApiException as e:
        log.error("Failed to query location: %s", e)
        storage_log = _get_container_log("dlm_postgrest")
        log.info("Log from storage container: %s", storage_log)
        return ""
    if resp:
        location_id = _get_id(resp[0], "location_id")
        log.info("Location already exists: %s", location_id)
    else:
        try:
            location_id = api_storage.init_location(
                location_name=LOCATION_NAME,
                location_type=LOCATION_TYPE,
                location_country=LOCATION_COUNTRY,
                location_city=LOCATION_CITY,
                location_facility=LOCATION_FACILITY,
            )
            assert isinstance(location_id, str) and location_id
        except ApiException as e:
            log.error("Failed to create location: %s", e)
            storage_log = _get_container_log("dlm_storage")
            log.info("Log from storage container: %s", storage_log)
            return ""
        log.info("Location created: %s", location_id)
    return location_id


def _init_storage_if_needed(
    api_storage: storage_api.StorageApi, location_id: str, storage: dict
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
            storage_phase=storage["STORAGE_PHASE"],
            root_directory=storage["ROOT_DIRECTORY"],
            location_id=location_id,
            location_name=LOCATION_NAME,
        )
        assert isinstance(storage_id, str) and storage_id
        log.info("Storage created: %s %s", storage["STORAGE_NAME"], storage_id)
    return storage_id


def setup_testing(api_configuration: Configuration):
    """Configure a target storage endpoint for rclone."""
    # NOTE: This is only required for integration testing with the DLM
    # server.
    # The setup of the source volume is now performed during the startup
    # of the client. In future the setup of a default (archive) storage
    # endpoint will be performed during startup of the DLM server and
    # then this can be removed as well.
    storage_url = (
        f"{api_configuration.host}:8003"
        if api_configuration.host.find(":") == -1
        else api_configuration.host
    )
    location_id = get_or_init_location(
        api_configuration, storage_url=storage_url, location=LOCATION_NAME
    )
    _ = get_or_init_storage(
        storage_name=STORAGE["TGT"]["STORAGE_NAME"],
        storage_url=storage_url,
        storage_phase=STORAGE["TGT"]["STORAGE_PHASE"],
        api_configuration=api_configuration,
        storage_root_directory=STORAGE["TGT"]["ROOT_DIRECTORY"],
        the_location_id=location_id,
        rclone_config=STORAGE["TGT"]["STORAGE_CONFIG"],
    )


def __lenient_deserialize(self, data, klass):
    """Lenient deserializer patch for the OpenAPI client.

    Unwraps Optional[...] so Dict[...] / List[...] logic can run, and treats
    'object' as a passthrough (return raw JSON). This works around the
    generated type 'Optional[Dict[str, object]]' which the stock client
    can't resolve at runtime.
    """
    # Unwrap Optional[T] so Dict[...] logic can run
    if isinstance(klass, str) and klass.startswith("Optional[") and klass.endswith("]"):
        if data is None:
            return None
        klass = klass[len("Optional[") : -1]  # noqa: E203
    # Treat 'object' as a passthrough (no model lookup)
    if klass == "object":
        return data
    return __orig_deserialize(self, data, klass)


setattr(api_client.ApiClient, "_ApiClient__deserialize", __lenient_deserialize)
# TODO(regen): Fix generator so ApiClient.__deserialize unwraps Optional[...] and
# returns raw JSON for 'object' types; remove this test-time patch after regen.
# --- end patch ---


@pytest.fixture
def dlm_request_api(request_configuration: Configuration) -> Iterator[request_api.RequestApi]:
    """Reusable API request object."""
    with api_client.ApiClient(request_configuration) as client:
        yield request_api.RequestApi(client)


def _check_service(url: str, timeout_s: int = 2, verify: bool = True, ok=(200, 204, 301, 302)):
    """Check HTTP endpoints for server services and replace hostname if required."""
    url_parts = urlparse(url)
    orig_hostname = url_parts.hostname
    host_options = [orig_hostname] + ["localhost", "docker"]
    for host in host_options:
        check_url = f"{url_parts.scheme}://{host}:{url_parts.port}{url_parts.path}"
        try:
            log.info(">>>> Checking HTTP endpoint: %s for %s", check_url, orig_hostname)
            r = requests.get(check_url, timeout=timeout_s, verify=verify, allow_redirects=True)
            if r.status_code in ok:
                log.info("OK!")
                return
        except requests.RequestException:
            pass
    raise ValueError(f"None of the standard hosts reachable for {orig_hostname}")


@pytest.fixture(scope="session")
def dlm_service_readiness():
    """Check that DLM integration test services are reachable."""
    _check_service(POSTGREST_URL, timeout_s=2)
    _check_service(f"{INGEST_URL}/openapi.json", timeout_s=2)
    _check_service(f"{REQUEST_URL}/openapi.json", timeout_s=2)
    _check_service(f"{MIGRATION_URL}/openapi.json", timeout_s=2)
    _check_service(f"{STORAGE_URL}/openapi.json", timeout_s=2)
    yield


@pytest.fixture(scope="session")
def storage_configuration(request) -> Configuration:
    """Storage API client config."""
    request.getfixturevalue("dlm_service_readiness")
    return Configuration(host=STORAGE_URL)


@pytest.fixture(scope="session")
def request_configuration(request) -> Configuration:
    """Request API client config."""
    request.getfixturevalue("dlm_service_readiness")
    return Configuration(host=REQUEST_URL)

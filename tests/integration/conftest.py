"""
Integration test harness for ska_dlm_client.

Brings up a minimal DLM stack via Docker Compose using the server stack definitions
and locally defined overrides. Server components are pulled from published images.

Run with: `pytest -m integration`
"""

import logging
import os
from pathlib import Path
from urllib.parse import urlparse

import pytest
import requests

from ska_dlm_client.common_types import (
    LocationCountry, LocationType, StorageInterface, StorageType
)
from ska_dlm_client.openapi import api_client
from ska_dlm_client.openapi.dlm_api import storage_api
from ska_dlm_client.openapi.configuration import Configuration
from tests.integration.test_configdb_watcher import (
    _get_container_log, _get_id, _init_location_if_needed, _init_storage_if_needed
)

INGEST_URL = os.getenv("INGEST_URL", "http://dlm_ingest:8001")
STORAGE_URL = os.getenv("STORAGE_URL", "http://dlm_storage:8003")
MIGRATION_URL = os.getenv("MIGRATION_URL", "http://dlm_migration:8004")

LOCATION_NAME = "MyDLMClient"
LOCATION_TYPE = LocationType.LOCAL_DEV
LOCATION_COUNTRY = LocationCountry.AU

LOCATION_CITY = "Marksville"
LOCATION_FACILITY = "local"  # TODO: query location_facility lookup table
STORAGE = {
    "TGT": {
        "STORAGE_NAME": "dlm-archive",
        "STORAGE_TYPE": StorageType.FILESYSTEM,
        "STORAGE_INTERFACE": StorageInterface.POSIX,
        "ROOT_DIRECTORY": "/dlm-archive",
        "STORAGE_PHASE": "SOLID",
        "STORAGE_CONFIG": {
            "name": "dlm-archive",
            "type": "alias",  # type 'alias' or 'local'?
            "parameters": {"remote": "/"},
        },
    },
    "SRC": {
        "STORAGE_NAME": "sdp-watcher",
        "STORAGE_TYPE": StorageType.FILESYSTEM,
        "STORAGE_INTERFACE": StorageInterface.POSIX,
        "ROOT_DIRECTORY": "/dlm/product_dir",
        "STORAGE_PHASE": "GAS",
        "STORAGE_CONFIG": {
            "name": "dlm",
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
}

log = logging.getLogger(__name__)

# --- OpenAPI client deserialization patch (handles Optional[Dict[str, object]]) ---
# Original private method
__orig_deserialize = getattr(api_client.ApiClient, "_ApiClient__deserialize")


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

CLIENT_ROOT = Path(__file__).resolve().parents[2]

# URLs can be overridden in CI to hit the DinD host
REQUEST_URL = "http://dlm_request:8002"
INGEST_URL = os.getenv("INGEST_URL", "http://dlm_ingest:8001")
MIGRATION_URL = os.getenv("MIGRATION_URL", "http://dlm_migration:8004")
STORAGE_URL = os.getenv("STORAGE_URL", "http://dlm_storage:8003")
POSTGREST_URL = os.getenv("POSTGREST_URL", "http://dlm_postgrest:3000")
RCLONE_BASE = os.getenv("RCLONE_BASE", "https://dlm_rclone:5572")
SDP_CONFIG_HOST = os.environ.get("SDP_CONFIG_HOST", "etcd")
SDP_CONFIG_PORT = os.environ.get("SDP_CONFIG_PORT", "2379")
ETCD_URL = f"http://{SDP_CONFIG_HOST}:{SDP_CONFIG_PORT}"

os.environ["SDP_CONFIG_HOST"] = SDP_CONFIG_HOST
os.environ["SDP_CONFIG_PORT"] = SDP_CONFIG_PORT


def pytest_configure(config):
    """Register local pytest markers used by this suite."""
    config.addinivalue_line("markers", "integration: marks integration tests")


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
def dlm_stack():
    """Bring up the minimal DLM stack for integration tests and wait for readiness.

    Wait for the services to start and check hostname options
    """
    _check_service(POSTGREST_URL, timeout_s=2)
    _check_service(f"{INGEST_URL}/openapi.json", timeout_s=2)
    _check_service(f"{REQUEST_URL}/openapi.json", timeout_s=2)
    _check_service(f"{MIGRATION_URL}/openapi.json", timeout_s=2)
    _check_service(f"{STORAGE_URL}/openapi.json", timeout_s=2)
    yield


@pytest.fixture(scope="session")
def storage_configuration(request) -> Configuration:
    """Storage API client config."""
    request.getfixturevalue("dlm_stack")  # triggers setup
    return Configuration(host=STORAGE_URL)


@pytest.fixture(scope="session")
def request_configuration() -> Configuration:
    """Storage API client config."""
    return Configuration(host=REQUEST_URL)

def storage_initialisation(storage_config: Configuration):
    """set up a location, storage and storage config."""
    with api_client.ApiClient(storage_config) as the_api_client:
        api_storage = storage_api.StorageApi(the_api_client)

        # --- ensure location exists ---
        log.info(
            "Using storage configuration host for registering: %s", storage_config.host
        )
        os.environ["STORAGE_URL"] = storage_config.host
        storage_log = _get_container_log("dlm_storage")
        log.info("Log from storage container: %s", storage_log)
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

if __name__ == "__main__":
    """Run storage_initialisation standalone for manual testing."""
    config = Configuration(host=STORAGE_URL)
    storage_initialisation(config)

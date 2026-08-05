# pylint: disable=too-many-arguments
# pylint: disable=redefined-outer-name
# pylint: disable=dangerous-default-value
"""Shared pytest fixtures and service readiness checks for DLM integration tests."""

import logging
import os
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
from ska_dlm_client.openapi.configuration import Configuration
from ska_dlm_client.openapi.dlm_api import request_api
from ska_dlm_client.register_storage_location.main import get_or_init_location, get_or_init_storage

logger = logging.getLogger(__name__)

# URLs can be overridden in CI to hit the DinD host
INGEST_URL = os.getenv("INGEST_URL", "http://dlm_ingest:8001")
REQUEST_URL = os.getenv("REQUEST_URL", "http://dlm_request:8002")
STORAGE_URL = os.getenv("STORAGE_URL", "http://dlm_storage:8003")
MIGRATION_URL = os.getenv("MIGRATION_URL", "http://dlm_migration:8004")
POSTGREST_URL = os.getenv("POSTGREST_URL", "http://dlm_postgrest:3000")
RCLONE_BASE = os.getenv("RCLONE_BASE", "https://dlm_rclone:5572")
ETCD_URL = os.getenv("ETCD_URL", "http://etcd:2379")

# Test constants to set up common end points: SKA-DEV location and dlm-archive storage
LOCATION_NAME = os.getenv("LOCATION_NAME", LocationName.LOCAL_DEV.value)
LOCATION_TYPE = os.getenv("LOCATION_TYPE", LocationType.LOCAL_DEV.value)
LOCATION_COUNTRY = os.getenv("LOCATION_COUNTRY", LocationCountry.AU.value)
LOCATION_CITY = os.getenv("LOCATION_CITY", "Marksville")
LOCATION_FACILITY = os.getenv("LOCATION_FACILITY", "local")  # TODO: query lookup table
TARGET_ROOT = os.getenv("TARGET_ROOT", "/dlm-archive")
TGT_STORAGE_PHASE = os.getenv("TARGET_PHASE", "SOLID")
RCLONE_CONFIG_TARGET = {
    "name": "dlm-archive",
    "type": "alias",
    "root_path": "/",
    "parameters": {"remote": "/"},
}

STORAGE_INTERFACE = StorageInterface.POSIX
STORAGE_TYPE = StorageType.FILESYSTEM


def setup_testing(
    api_configuration: Configuration,
    *,
    location_name: str = LOCATION_NAME,
    location_type: str = LOCATION_TYPE,
    location_country: str = LOCATION_COUNTRY,
    location_city: str = LOCATION_CITY,
    location_facility: str = LOCATION_FACILITY,
    target_root: str = TARGET_ROOT,
    target_phase: str = TGT_STORAGE_PHASE,
    storage_type: str = STORAGE_TYPE,
    storage_interface: str = STORAGE_INTERFACE,
    rclone_config: dict = RCLONE_CONFIG_TARGET,
) -> tuple[str, str]:
    """Configure the common integration-test location and target storage."""
    # The setup of the source volume is now performed during the startup of the client.
    # In production, the setup of a default (archive) storage endpoint will be performed during
    # startup of the DLM server.

    logger.info("Setting up common integration-test endpoints.")
    location_id = get_or_init_location(
        api_configuration=api_configuration,
        storage_url=api_configuration.host,
        location_name=location_name,
        location_type=location_type,
        location_country=location_country,
        location_city=location_city,
        location_facility=location_facility,
    )

    storage_id = get_or_init_storage(
        storage_name=rclone_config["name"],
        storage_url=api_configuration.host,
        storage_root_directory=target_root,
        api_configuration=api_configuration,
        the_location_id=location_id,
        rclone_config=rclone_config,
        storage_type=storage_type,
        storage_interface=storage_interface,
        location_name=location_name,
        storage_phase=target_phase,
    )

    logger.info(
        "Common endpoints ready: location_id=%s, storage_id=%s",
        location_id,
        storage_id,
    )
    return location_id, storage_id


@pytest.fixture(scope="session")
def _common_dlm_endpoints(storage_configuration: Configuration) -> tuple[str, str]:
    """Ensure the shared location and archive storage exist."""
    logger.debug(">>> setup_testing() fixture called")
    return setup_testing(storage_configuration)


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


@pytest.fixture
def dlm_request_api(  # pylint: disable=redefined-outer-name
    request_configuration: Configuration,
) -> Iterator[request_api.RequestApi]:
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
            logger.info(">>>> Checking HTTP endpoint: %s for %s", check_url, orig_hostname)
            r = requests.get(check_url, timeout=timeout_s, verify=verify, allow_redirects=True)
            if r.status_code in ok:
                logger.info("OK!")
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

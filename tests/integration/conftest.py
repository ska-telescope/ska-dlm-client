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

import ska_dlm_client.openapi.api_client as _dlm_api_client
from ska_dlm_client.openapi.configuration import Configuration

logging.basicConfig(level=os.getenv("PYTEST_LOGLEVEL", "INFO"))
log = logging.getLogger(__name__)

# --- OpenAPI client deserialization patch (handles Optional[Dict[str, object]]) ---
# Original private method
__orig_deserialize = getattr(_dlm_api_client.ApiClient, "_ApiClient__deserialize")


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


setattr(_dlm_api_client.ApiClient, "_ApiClient__deserialize", __lenient_deserialize)
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
SDP_CONFIG_HOST = "etcd"
os.environ["SDP_CONFIG_HOST"] = SDP_CONFIG_HOST


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

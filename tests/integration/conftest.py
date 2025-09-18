"""
Integration test harness for ska_dlm_client.

Brings up a minimal DLM stack via Docker Compose using the server repo’s compose files
plus a local override. The server repo is assumed to be a sibling directory; override with
DLM_SERVER_DIR.

Run with: `pytest -m integration`
"""

import logging
import os
import shutil
import subprocess
import time
from pathlib import Path

import pytest
import requests

import ska_dlm_client.openapi.api_client as _dlm_api_client
from ska_dlm_client.openapi.configuration import Configuration

logging.basicConfig(level=os.getenv("PYTEST_LOGLEVEL", "INFO"))
log = logging.getLogger(__name__)

pytestmark = pytest.mark.integration

PROJECT_NAME = os.environ.get("COMPOSE_PROJECT_NAME", "integration-tests")

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

# Figure out repo roots in both local and CI layouts.
# For local, default to sibling: x/ska-dlm-client -> x/ska-data-lifecycle
CLIENT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BASE = Path(os.getenv("CI_PROJECT_DIR", str(CLIENT_ROOT))).parent
DEFAULT_SERVER_DIR = (DEFAULT_BASE / "ska-data-lifecycle").resolve()

# Allow CI/job to override explicitly
DLM_SERVER_DIR = Path(os.getenv("DLM_SERVER_DIR", str(DEFAULT_SERVER_DIR))).resolve()

SERVER_TESTS = DLM_SERVER_DIR / "tests"
OVERRIDE = Path(__file__).with_name("docker-compose.override.yaml")

COMPOSE_FILES = [
    SERVER_TESTS / "services.docker-compose.yaml",
    SERVER_TESTS / "dlm.docker-compose.yaml",
    OVERRIDE,
]

# URLs can be overridden in CI to hit the DinD host
STORAGE_URL = os.getenv("STORAGE_URL", "http://127.0.0.1:8003")
POSTGREST_URL = os.getenv("POSTGREST_URL", "http://127.0.0.1:3000")
RCLONE_BASE = os.getenv("RCLONE_BASE", "https://127.0.0.1:5572")

CERT_DIR = SERVER_TESTS / "integration" / "certs"
KEY_PATH = CERT_DIR / "selfsigned.key"
CRT_PATH = CERT_DIR / "selfsigned.cert"


def _require_server_repo() -> None:
    """Fail only when the integration stack is actually used."""
    if not DLM_SERVER_DIR.exists():
        pytest.skip(
            f"DLM_SERVER_DIR not found at {DLM_SERVER_DIR}. "
            "Set DLM_SERVER_DIR to your ska-data-lifecycle repo, or clone it as a sibling."
            "Skipping integration tests..."
        )


def _ensure_rclone_certs() -> None:
    """
    Ensure rclone RC TLS certs exist where the server compose expects.

    To keep HTTPS and avoid flakiness, we auto-create self-signed certs on first run in the server
    repo’s expected path.
    """
    CERT_DIR.mkdir(parents=True, exist_ok=True)

    # Guard file-vs-directory mistake
    for p in (KEY_PATH, CRT_PATH):
        if p.exists() and p.is_dir():
            raise RuntimeError(f"{p} is a directory; it must be a file. Delete/rename it.")

    if KEY_PATH.exists() and CRT_PATH.exists():
        return

    subprocess.run(
        [
            "openssl",
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-days",
            "365",
            "-subj",
            "/CN=dlm_rclone",
            "-keyout",
            str(KEY_PATH),
            "-out",
            str(CRT_PATH),
        ],
        check=True,
    )


def pytest_configure(config):
    """Register local pytest markers used by this suite."""
    config.addinivalue_line("markers", "integration: marks integration tests")


def _compose(*args: str):
    """Run `docker compose` with the merged compose files and proper env."""
    env = dict(os.environ)
    env.setdefault("COMPOSE_PROJECT_NAME", PROJECT_NAME)
    # Ensure compose var substitution works for ${DLM_SERVER_DIR} in an override
    env["DLM_SERVER_DIR"] = str(DLM_SERVER_DIR)

    cmd = ["docker", "compose"]
    for f in COMPOSE_FILES:
        cmd += ["-f", str(f)]
    cmd += list(args)

    p = subprocess.run(cmd, capture_output=True, text=True, env=env, check=True)
    if p.returncode != 0:
        print("[compose STDOUT]\n", p.stdout)
        print("[compose STDERR]\n", p.stderr)
        raise RuntimeError("docker compose failed")
    return p


def _wait_for_rclone(base="https://127.0.0.1:5572", timeout_s: int = 60):
    """Wait until rclone's Remote Control API responds (TLS + routing ready)."""
    end = time.time() + timeout_s
    while time.time() < end:
        try:
            r = requests.post(f"{base}/rc/noop", json={}, verify=False, timeout=2)
            if r.status_code == 200:
                return
        except requests.RequestException:
            pass
        time.sleep(0.5)
    raise TimeoutError(f"Timeout waiting for rclone RC at {base}")


def _wait_for_http(url: str, timeout_s: int = 120, verify: bool = True, ok=(200, 204, 301, 302)):
    """Wait for an HTTP endpoint to return a status in `ok`."""
    end = time.time() + timeout_s
    while time.time() < end:
        try:
            r = requests.get(url, timeout=2, verify=verify, allow_redirects=True)
            if r.status_code in ok:
                return
        except requests.RequestException:
            pass
        time.sleep(0.5)
    raise TimeoutError(f"Timeout waiting for {url}")


@pytest.fixture(scope="session")
def dlm_stack():
    """Bring up the minimal DLM stack for integration tests and wait for readiness.

    Starts only the services needed by the client tests (DB, PostgREST, rclone, storage),
    avoiding auth/gateway via `--no-deps`. Generates rclone TLS certs just-in-time so
    HTTPS remains enabled without manual steps.
    """
    log.info(
        "Initialising containers for %s…", os.environ.get("COMPOSE_PROJECT_NAME", PROJECT_NAME)
    )
    if not shutil.which("docker"):
        pytest.skip("Docker is required for integration tests.")
    missing = [f for f in COMPOSE_FILES if not f.exists()]
    if missing:
        pytest.skip("Compose file(s) not found: " + ", ".join(map(str, missing)))

    # We need the dlm server repo
    _require_server_repo()

    # Just-in-time cert generation
    _ensure_rclone_certs()

    # Start only what we need; --no-deps avoids auth/gateway
    _compose(
        "up",
        "-d",
        "--force-recreate",
        "--no-deps",
        "dlm_db",
        "dlm_postgrest",
        "dlm_rclone",
        "dlm_storage",
    )
    try:
        _wait_for_http(POSTGREST_URL, timeout_s=30)
        _wait_for_http(f"{STORAGE_URL}/openapi.json", timeout_s=30)
        _wait_for_rclone(base=RCLONE_BASE, timeout_s=30)
        yield
    finally:  # teardown
        _compose("down", "-v")


@pytest.fixture(scope="session")
def storage_configuration(request) -> Configuration:
    """Storage API client config."""
    request.getfixturevalue("dlm_stack")  # triggers setup
    return Configuration(host=STORAGE_URL)

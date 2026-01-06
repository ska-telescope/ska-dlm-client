"""Shared pytest fixtures for SDP ConfigDB unit tests."""

import os
import logging
from pathlib import Path
import pytest
import requests
import subprocess
import shutil
import time
from ska_sdp_config import Config

CLIENT_ROOT = Path(__file__).resolve().parents[2]
CLIENTS = CLIENT_ROOT / "tests/test-services.docker-compose.yml"
COMPOSE_FILES = [CLIENTS]
ETCD_URL = os.getenv("ETCD_URL", "http://127.0.0.1:2379")

log = logging.getLogger(__name__)

def _docker_run():
    """Run the ETCD container."""
    env = dict(os.environ)

    attr = [ 
            "/usr/bin/etcd", 
            "--advertise-client-urls=http://0.0.0.0:2379",
            "--listen-client-urls=http://0.0.0.0:2379",
            "--initial-advertise-peer-urls=http://0.0.0.0:2380",
            "--listen-peer-urls=http://0.0.0.0:2380", 
            "--initial-cluster=default=http://0.0.0.0:2380"]
    cmd = ["docker", "run", "--rm", "-d", "--name", "etcd", "-p", "2379:2379", 
            "artefact.skao.int/ska-sdp-etcd:3.5.9",]
    cmd += attr

    log.info("docker run command: %s", " ".join(cmd))
    p = subprocess.run(cmd, capture_output=True, text=True, env=env, check=False)
    if p.returncode != 0:
        log.info("[run STDOUT]: %s\n", p.stdout)
        log.error("[run STDERR] %s\n", p.stderr)
        raise RuntimeError("docker run failed")
    return p

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


@pytest.fixture(name="etcd", scope="session")
def dlm_configdb_watcher_stack():
    """Set up and tear down the DLM ConfigDB Watcher stack."""

    log.info(
        "Initialising ETCD container for ConfigDB Watcher tests..."
    )
    if not shutil.which("docker"):
        pytest.skip("Docker is required for integration tests.")
    missing = [f for f in COMPOSE_FILES if not f.exists()]
    if missing:
        pytest.skip("Compose file(s) not found: " + ", ".join(map(str, missing)))

    # Start only what we need; --no-deps avoids auth/gateway
    log.info("Attempting to start required server services...")
    _docker_run()
    try:
        _wait_for_http(f"{ETCD_URL}/version", timeout_s=30)
        yield
    finally:  # teardown
        log.info("Tearing down ETCD container...")
        cmd = ["docker", "rm", "-f", "etcd"]
        p = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if p.returncode != 0:
            log.info("[teardown STDOUT]: %s\n", p.stdout)
            log.error("[teardown STDERR]: %s\n", p.stderr)

@pytest.fixture(name="config")
def sdp_config_fixture(etcd: ETCD_URL):
    """Provide a clean SDP ConfigDB client for each test."""
    with Config(backend="etcd3") as cfg:
        # Clean before test
        cfg.backend.delete("/flow", recursive=True, must_exist=False)
        cfg.backend.delete("/eb", recursive=True, must_exist=False)
        cfg.backend.delete("/pb", recursive=True, must_exist=False)
        cfg.backend.delete("/dependency", recursive=True, must_exist=False)

        yield cfg

        # Clean after test (even if the test fails)
        cfg.backend.delete("/flow", recursive=True, must_exist=False)
        cfg.backend.delete("/eb", recursive=True, must_exist=False)
        cfg.backend.delete("/pb", recursive=True, must_exist=False)
        cfg.backend.delete("/dependency", recursive=True, must_exist=False)

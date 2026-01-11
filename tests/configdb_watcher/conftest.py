"""Shared pytest fixtures for SDP ConfigDB unit tests."""

import logging
import os
from pathlib import Path

import pytest
from ska_sdp_config import Config

CLIENT_ROOT = Path(__file__).resolve().parents[2]
CLIENTS = CLIENT_ROOT / "tests/test-services.docker-compose.yml"
COMPOSE_FILES = [CLIENTS]
SDP_CONFIG_HOST = "etcd"
SDP_CONFIG_PORT = "2379"

log = logging.getLogger(__name__)


@pytest.fixture(name="config")
def sdp_config_fixture():
    """Provide a clean SDP ConfigDB client for each test."""
    os.environ["SDP_CONFIG_HOST"] = SDP_CONFIG_HOST
    os.environ["SDP_CONFIG_PORT"] = SDP_CONFIG_PORT
    with Config(backend="etcd3", host=SDP_CONFIG_HOST, port=SDP_CONFIG_PORT) as cfg:
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

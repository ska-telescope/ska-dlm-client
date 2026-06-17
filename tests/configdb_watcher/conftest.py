"""Shared pytest fixtures for SDP ConfigDB unit tests."""

import logging
import os
import urllib

import pytest
from ska_sdp_config import Config

ETCD_URL = "http://etcd:2379"

log = logging.getLogger(__name__)


@pytest.fixture(name="config")
def sdp_config_fixture():
    """Provide a clean SDP ConfigDB client for each test."""
    etcd_url = os.environ.get("ETCD_URL", ETCD_URL)
    host = urllib.parse.urlparse(etcd_url).hostname
    port = urllib.parse.urlparse(etcd_url).port

    with Config(backend="etcd3", host=host, port=port) as cfg:
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

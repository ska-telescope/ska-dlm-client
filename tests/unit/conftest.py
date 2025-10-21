"""Shared pytest fixtures for SDP ConfigDB unit tests."""

from contextlib import suppress

import pytest
from ska_sdp_config import Config
from ska_sdp_config.entity.flow import Dependency


def clear_flow_dependencies(cfg: Config) -> None:
    """Delete all flow Dependency entities and their state."""
    for txn in cfg.txn():
        if not hasattr(txn.dependency, "list_keys"):
            return
        for dkey in txn.dependency.list_keys():
            dep = Dependency(key=dkey, expiry_time=-1, description=None)
            with suppress(Exception):
                txn.dependency.state(dep).delete()
            with suppress(Exception):
                txn.dependency.delete(dkey)
            with suppress(Exception):
                txn.dependency.delete(dep)


def clear_flows(cfg: Config) -> None:
    """Delete all flows."""
    for txn in cfg.txn():
        for key in txn.flow.list_keys():
            txn.flow.delete(key, recurse=True)


@pytest.fixture(name="config")
def sdp_config_fixture():
    """Provide a clean SDP ConfigDB client for each test."""
    cfg = Config(backend="etcd3")
    clear_flow_dependencies(cfg)
    clear_flows(cfg)
    try:
        yield cfg
    finally:
        clear_flow_dependencies(cfg)
        clear_flows(cfg)
        with suppress(Exception):
            cfg.revoke_lease()

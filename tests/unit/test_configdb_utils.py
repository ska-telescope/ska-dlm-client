"""Unit test module for configdb_utils."""

import logging
from types import SimpleNamespace

from ska_sdp_config import ConfigCollision

from ska_dlm_client.sdp_ingest.configdb_utils import (
    _initialise_dependency,
    log_flow_dependencies,
    update_dependency_state,
)

PB_ID = "pb-madeup-00000000-a"
NAME = "prod-a"


def test_update_dependency_state(config):
    """Test update_dependency_state creates then updates (covers ConfigCollision path)."""
    key = SimpleNamespace(pb_id=PB_ID, name=NAME)
    dep = _initialise_dependency(
        key, dep_kind="dlm-copy", origin="dlmtest", expiry_time=-1, description="unit"
    )
    # persist entity & empty state
    for txn in config.txn():
        try:
            txn.dependency.create(dep)
        except ConfigCollision:
            pass
        try:
            txn.dependency.state(dep).create({})
        except ConfigCollision:
            pass

    # first call should create status
    for txn in config.txn():
        update_dependency_state(txn, dep, "WORKING")
    for txn in config.txn():
        assert txn.dependency.state(dep).get()["status"] == "WORKING"

    # second call should hit update (ConfigCollision on create)
    for txn in config.txn():
        update_dependency_state(txn, dep, "FINISHED")
    for txn in config.txn():
        assert txn.dependency.state(dep).get()["status"] == "FINISHED"


def test_log_flow_dependencies(config, caplog):
    """Test log_flow_dependencies for none and one."""
    caplog.set_level(logging.INFO, logger="ska_dlm_client.configdb_watcher")
    key = SimpleNamespace(pb_id=PB_ID, name=NAME)
    dep = _initialise_dependency(
        key, dep_kind="dlm-copy", origin="dlmtest", expiry_time=-1, description="unit"
    )

    # No dependencies yet
    for txn in config.txn():
        log_flow_dependencies(txn, dep.key)
    assert f"No flow dependencies for {PB_ID}/{NAME}" in caplog.text

    # Create one dependency + state and log again
    for txn in config.txn():
        try:
            txn.dependency.create(dep)
        except ConfigCollision:
            pass
        try:
            txn.dependency.state(dep).create({"status": "WORKING"})
        except ConfigCollision:
            txn.dependency.state(dep).update({"status": "WORKING"})

    caplog.clear()
    for txn in config.txn():
        log_flow_dependencies(txn, dep.key)

    # Positive log line containing status
    assert f"Flow dependencies for {PB_ID}/{NAME}:" in caplog.text
    assert "status=WORKING" in caplog.text

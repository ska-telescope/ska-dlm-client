"""Unit test module for configdb_utils."""

import logging
import pathlib

import pytest
from ska_sdp_config import ConfigCollision
from ska_sdp_config.entity.common import PVCPath
from ska_sdp_config.entity.flow import DataProduct, Flow

from ska_dlm_client.sdp_ingest.configdb_utils import (
    _initialise_dependency,
    create_sdp_migration_dependency,
    get_data_product_dir,
    log_flow_dependencies,
    update_dependency_state,
)

PB_ID = "pb-madeup-00000000-a"
EB_ID = "eb-00000000"
NAME = "prod-a"
FLOW_NAME = "vis-receive-mswriter-processor"


@pytest.mark.asyncio
async def test_create_sdp_migration_dependency(config):
    """Test create_sdp_migration_dependency persists dep and empty state."""
    key = Flow.Key(pb_id=PB_ID, name=NAME)

    dep = await create_sdp_migration_dependency(config, key)

    # Returned dependency has expected key + metadata
    assert dep is not None
    assert dep.key.pb_id == PB_ID
    assert dep.key.name == NAME
    assert dep.key.kind == "dlm-copy"
    assert dep.key.origin == "ska-data-lifecycle-management"
    assert dep.expiry_time == -1
    assert dep.description == "DLM: lock data-product for copy"

    # Verify entity is persisted in ConfigDB
    for txn in config.txn():
        stored_dep = txn.dependency.get(dep.key)
        assert stored_dep is not None

        # State should exist and be an empty dict
        state = txn.dependency.state(dep).get()
        assert state == {}
        break


def test_update_dependency_state(config):
    """Test update_dependency_state creates then updates (covers ConfigCollision path)."""
    key = Flow.Key(pb_id=PB_ID, name=NAME)
    dep = _initialise_dependency(
        key, dep_kind="dlm-copy", origin="dlmtest", expiry_time=-1, description="unit"
    )
    # persist entity & empty state
    for txn in config.txn():
        txn.dependency.create_or_update(dep)
        ops = txn.dependency.state(dep)
        (ops.update if ops.exists() else ops.create)({})

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
    key = Flow.Key(pb_id=PB_ID, name=NAME)
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


def test_get_data_product_dir(config):
    """Test get_data_product_dir resolves PVCPath to container path."""
    key = Flow.Key(pb_id=PB_ID, name=FLOW_NAME)

    pvc = PVCPath(
        k8s_namespaces=[],
        k8s_pvc_name="pvc_name",
        pvc_mount_path="/data",
        pvc_subpath=pathlib.Path(f"product/{EB_ID}/ska-sdp/{PB_ID}"),
    )

    flow = Flow(
        key=key,
        data_model="Visibility",
        sink=DataProduct(
            data_dir=pvc,
            paths=[],
        ),
        sources=[],
    )

    # Persist the Flow in the config DB
    for txn in config.txn():
        txn.flow.create(flow)

    # Exercise the helper
    result = get_data_product_dir(config, key)

    assert str(result) == f"/data/product/{EB_ID}/ska-sdp/{PB_ID}"

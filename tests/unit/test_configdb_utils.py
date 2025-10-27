"""Unit test module for configdb_utils."""

import logging

import yaml
from ska_sdp_config import ConfigCollision
from ska_sdp_config.entity.flow import Flow

from ska_dlm_client.sdp_ingest.configdb_utils import (
    _initialise_dependency,
    check_flow_annotations,
    log_flow_dependencies,
    update_dependency_state,
)

PB_ID = "pb-madeup-00000000-a"
NAME = "prod-a"


def test_check_flow_annotations(caplog):  # WIP
    """check_flow_annotations logs the annotations block from YAML input."""
    # Peter's example:
    flow_yaml = """
key:
  pb_id: pb-xyz
  kind: data-product
  name: image-cube
sink:
  kind: data-product
  data_dir: /shared/fsx1/eb-xyz/ska-sdp/pb-xyz/vis/
  paths: []
data_model: Visibility
annotations:
  ska-data-lifecycle:
    expiry: "10d"
sources:
  - uri: "/flow/pb-xyz:plasma:visibilities"
    function: "ska-sdp-realtime-receive-processors:mswriter"
"""

    flow = yaml.safe_load(flow_yaml)

    caplog.set_level(logging.INFO)
    check_flow_annotations(flow)

    expected = '{"ska-data-lifecycle": {"expiry": "10d"}}'
    msgs = [rec.message for rec in caplog.records if rec.levelno == logging.INFO]
    assert any(m == expected for m in msgs), msgs


def test_initialise_dependency():
    """Test _initialise_dependency - happy path."""
    key = Flow.Key(pb_id=PB_ID, name=NAME)
    dep = _initialise_dependency(
        key, dep_kind="dlm-copy", origin="dlmtest", expiry_time=-1, description="unit"
    )
    assert dep is not None
    assert dep.key.pb_id == PB_ID
    assert dep.key.kind == "dlm-copy"
    assert dep.key.name == NAME
    assert dep.key.origin == "dlmtest"
    assert dep.expiry_time == -1
    assert dep.description == "unit"


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

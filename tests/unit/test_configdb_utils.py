"""Unit test module for configdb_utils."""

import logging
from pathlib import Path
from typing import cast

import pytest
from pydantic import AnyUrl
from ska_sdp_config import ConfigCollision
from ska_sdp_config.entity.flow import DataProduct, Flow, FlowSource

from ska_dlm_client.sdp_ingest.configdb_utils import (
    _initialise_dependency,
    has_flow_annotation,
    log_flow_dependencies,
    update_dependency_state,
)

PB_ID = "pb-madeup-00000000-a"
NAME = "prod-a"


def _mk_flow(annotations) -> Flow:
    return Flow(
        key=Flow.Key(pb_id=PB_ID, kind="data-product", name=NAME),
        sink=DataProduct(
            data_dir=Path("/data"),
            paths=[Path("scan_id.ms")],
        ),
        sources=[
            FlowSource(
                uri=cast(AnyUrl, "https://gitlab.com/ska-telescope/sdp/"),
            )
        ],
        data_model="Visibility",
        expiry_time=-1,
        annotations=annotations,
    )


@pytest.mark.parametrize(
    "annotations",
    [
        {"ska-data-lifecycle": None},  # annotations present, value None
        {"ska-data-lifecycle": {"other": "stuff"}},  # annotations present, contains any content
    ],
    ids=["no-annotations", "wrong-key"],
)
def test_has_flow_annotation_true(annotations):
    """True when `flow.annotations` exists and contains desired namespace. Value can be None."""
    flow = _mk_flow(annotations)
    assert has_flow_annotation(flow, "ska-data-lifecycle") is True


@pytest.mark.parametrize(
    "annotations",
    [
        None,  # annotations absent
        {"some-other-system": "some_key"},  # annotations present, desired key missing
    ],
    ids=["no-annotations", "wrong-key"],
)
def test_has_flow_annotation_false(annotations):
    """False when `annotations` is absent or missing the desired key."""
    flow = _mk_flow(annotations)
    assert has_flow_annotation(flow, "ska-data-lifecycle") is False


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

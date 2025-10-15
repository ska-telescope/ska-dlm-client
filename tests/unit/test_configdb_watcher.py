"""Unit test module for configdb_watcher."""

import asyncio
import logging
from contextlib import suppress
from types import SimpleNamespace
from typing import Final

import async_timeout
import pytest
from ska_sdp_config import Config, ConfigCollision
from ska_sdp_config.entity import ProcessingBlock, Script
from ska_sdp_config.entity.flow import DataProduct, Dependency, Flow

from ska_dlm_client.configdb_watcher import (
    _initialise_dependency,
    log_flow_dependencies,
    update_dependency_state,
    watch_dataproduct_status,
)

# pylint: disable=protected-access


def clear_flow_dependencies(config: Config) -> None:
    """Delete all flow Dependency entities and their state."""
    for txn in config.txn():
        if not hasattr(txn.dependency, "list_keys"):
            return  # backend doesn’t support enumeration
        for dkey in txn.dependency.list_keys():  # server-side enumeration
            dep = Dependency(key=dkey, expiry_time=-1, description=None)
            with suppress(Exception):
                txn.dependency.state(dep).delete()  # /dependency/<key>/state
            # Some versions accept either the key or the entity:
            with suppress(Exception):
                txn.dependency.delete(dkey)  # /dependency/<key>
            with suppress(Exception):
                txn.dependency.delete(dep)  # fallback


def clear_flows(config: Config):
    """Clear all flows (we avoid dependency collisions by using unique keys)."""
    for txn in config.txn():
        for key in txn.flow.list_keys():
            txn.flow.delete(key, recurse=True)


@pytest.fixture(name="config")
def sdp_config_fixture():
    """Create client to a clean SDP ConfigDB."""
    cfg = Config(backend="etcd3")
    clear_flow_dependencies(cfg)
    clear_flows(cfg)
    try:
        yield cfg
    finally:
        clear_flow_dependencies(cfg)
        clear_flows(cfg)
        cfg.revoke_lease()


SCRIPT = Script.Key(kind="batch", name="unit_test", version="0.0.0")
PB_ID = "pb-madeup-00000000-a"
NAME = "prod-a"


def test_initialise_dependency_happy_path():
    """Test _initialise_dependency - happy path."""
    key = SimpleNamespace(pb_id=PB_ID, name=NAME)
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


@pytest.mark.parametrize(
    "bad_key", [SimpleNamespace(pb_id=None, name=NAME), SimpleNamespace(pb_id=PB_ID, name=None)]
)
def test_initialise_dependency_missing_fields(bad_key, caplog):
    """Test _initialise_dependency - bad path."""
    caplog.set_level(logging.INFO, logger="ska_dlm_client.configdb_watcher")
    dep = _initialise_dependency(
        bad_key, dep_kind="dlm-copy", origin="dlmtest", expiry_time=-1, description="unit"
    )
    assert dep is None
    assert "Cannot build dependency" in caplog.text


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


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("create_first", "include_existing", "expected_count"),
    [
        (False, True, 1),
        (True, True, 1),
        (False, False, 1),
        (True, False, 0),
    ],
)
async def test_dataproduct_status_watcher(  # noqa: C901
    config, create_first: bool, include_existing: bool, expected_count: int
):
    """Verify the watcher emits FINISHED events and creates a DLM dependency once.

    For uniqueness across param cases we vary both the PB id and the flow name.
    When expected_count==1 we also assert that the dependency state exists.
    """
    # Unique, regex-compliant PB id and flow name per case
    # ^pb-[a-z0-9]+-[0-9]{8}-[a-z0-9]+$
    pb_id = f"pb-test{int(create_first)}{int(include_existing)}-00000000-0"
    flow_name = f"name-test{int(create_first)}{int(include_existing)}"

    # Ensure the producer PB exists
    for txn in config.txn():
        if txn.processing_block.get(pb_id) is None:
            txn.processing_block.create(ProcessingBlock(key=pb_id, eb_id=None, script=SCRIPT))

    # Our data-product flow
    test_dataproduct: Final = Flow(
        key=Flow.Key(pb_id=pb_id, kind="data-product", name=flow_name),
        sink=DataProduct(data_dir="/datapath", paths=[]),
        sources=[],
        data_model="Visibility",
    )

    timeout_s: Final = 0.5
    values: list[tuple[Flow.Key, str]] = []

    # Sanity check: no products yet
    for txn in config.txn():
        assert txn.flow.list_keys(kind="data-product") == []

    async def aput_flow():
        """Create the flow, then flip its state a few times. A little 'traffic generator'."""
        if not create_first:
            await asyncio.sleep(timeout_s)

        for txn in config.txn():
            txn.flow.create(test_dataproduct)
            txn.flow.state(test_dataproduct.key).create({"status": "WAITING"})
            txn.flow.state(test_dataproduct.key).update({"status": "FINISHED"})
            txn.flow.state(test_dataproduct.key).update({})
            txn.flow.state(test_dataproduct.key).update({"status": "WAITING"})
            txn.flow.state(test_dataproduct.key).update({"status": "FINISHED"})

    async def aget_single_state():
        """Consume the watcher and collect FINISHED events.

        If ``create_first`` is True, waits briefly before starting to simulate a pre-existing
        flow. Runs the data-product status watcher with the shared ``config`` and appends any
        ``(Flow.Key, "FINISHED")`` tuples to ``values`` until the timeout elapses. Timeouts are
        suppressed because some parameterizations may legitimately produce no events.
        """
        if create_first:
            await asyncio.sleep(timeout_s)

        with suppress(asyncio.TimeoutError):
            async with async_timeout.timeout(2 * timeout_s):
                # IMPORTANT: use the same Config handle as the writer
                # because Config is not thread-safe; using one shared instance keeps
                # all transactions and watcher events on the same client session
                async with watch_dataproduct_status(
                    config, "FINISHED", include_existing=include_existing
                ) as producer:
                    async for value in producer:
                        values.append(value)

    async with async_timeout.timeout(5 * timeout_s):
        await asyncio.gather(aget_single_state(), aput_flow())

    # Did we see the FINISHED event the expected number of times?
    assert len(values) == expected_count
    if expected_count:
        assert any(k == test_dataproduct.key and v.get("status") == "FINISHED" for k, v in values)

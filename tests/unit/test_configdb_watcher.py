"""Unit test module for configdb_watcher."""

import asyncio
from contextlib import suppress
from types import SimpleNamespace
from typing import Final

import async_timeout
import pytest
from ska_sdp_config import Config
from ska_sdp_config.entity import ProcessingBlock, Script
from ska_sdp_config.entity.flow import DataProduct, Dependency, Flow

from ska_dlm_client.configdb_watcher import DataProductStatusWatcher, watch_dataproduct_status

# pylint: disable=protected-access


def clear_dependencies(config: Config):
    """Clear all SDP ConfigDB dependencies."""
    for txn in config.txn():
        keys = txn.flow.list_keys()
        for key in keys:
            txn.flow.delete(key, recurse=True)


def clear_flows(config: Config):
    """Clear all flows (we avoid dependency collisions by using unique keys)."""
    for txn in config.txn():
        for key in txn.flow.list_keys():
            txn.flow.delete(key, recurse=True)


@pytest.fixture(name="config")
def sdp_config_fixture():
    """Create client to a clean SDP ConfigDB."""
    cfg = Config(backend="etcd3")
    clear_flows(cfg)
    try:
        yield cfg
    finally:
        clear_flows(cfg)


SCRIPT = Script.Key(kind="batch", name="unit_test", version="0.0.0")


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
        """Create the flow, then flip its state a few times. A little “traffic generator”."""
        if not create_first:
            await asyncio.sleep(timeout_s)

        for txn in config.txn():
            txn.flow.create(test_dataproduct)
            txn.flow.state(test_dataproduct.key).create({"status": "WORKING"})
            txn.flow.state(test_dataproduct.key).update({"status": "FINISHED"})
            txn.flow.state(test_dataproduct.key).update({})
            txn.flow.state(test_dataproduct.key).update({"status": "WORKING"})
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
                # IMPORTANT: use the SAME config handle as the writer
                async with watch_dataproduct_status(
                    config, "FINISHED", include_existing=include_existing
                ) as producer:
                    async for value in producer:
                        values.append(value)

    async with async_timeout.timeout(5 * timeout_s):
        await asyncio.gather(aget_single_state(), aput_flow())

    # Primary assertion: did we see the FINISHED event the expected number of times?
    assert len(values) == expected_count
    if expected_count:
        assert (test_dataproduct.key, "FINISHED") in values

    # Side-effect assertion: dependency exists only when we emitted
    # The watcher writes kind="dlm-copy", origin="dlm-client", and creates empty state {}
    dep = Dependency(
        key=Dependency.Key(pb_id=pb_id, kind="dlm-copy", name=flow_name, origin="dlm-client"),
        expiry_time=-1,
        description=None,
    )
    for txn in config.txn():
        dep_state = txn.dependency.state(dep).get()
        if expected_count:
            assert dep_state is not None and "status" not in dep_state
        else:
            assert dep_state is None


def test_create_dlm_dependency_metadata_only(config):
    """Build a Dependency for a product and persist it without a state."""
    watcher = DataProductStatusWatcher(config, status="FINISHED", include_existing=False)

    # Minimal product key stand-in; helper only needs pb_id and name.
    product_key = SimpleNamespace(pb_id="pb-madeup-00000000-a", name="prod-a")

    dep = watcher._create_dlm_dependency(
        product_key,
        dep_kind="dlm-copy",
        origin="dlmtest1",
        expiry_time=-1,
        description="unit: lock for copy",
    )

    # Persist the dependency by creating an *empty* state record.
    for txn in config.txn():
        txn.dependency.state(dep).create({})

    # Verify the dependency's state exists and has no 'status' yet.
    for txn in config.txn():
        state = txn.dependency.state(dep).get()
        assert state is not None
        assert "status" not in state

    # Sanity checks on the dependency we built.
    assert dep.key.pb_id == "pb-madeup-00000000-a"
    assert dep.key.kind == "dlm-copy"
    assert dep.key.name == "prod-a"
    assert dep.key.origin == "dlmtest1"
    assert dep.expiry_time == -1


def test_create_dlm_dependency_state_working(config):
    """Create a Dependency and set its state to WORKING."""
    watcher = DataProductStatusWatcher(config, status="FINISHED", include_existing=False)
    product_key = SimpleNamespace(pb_id="pb-madeup-00000000-b", name="prod-b")

    dep = watcher._create_dlm_dependency(
        product_key,
        dep_kind="dlm-copy",
        origin="dlmtest2",
        expiry_time=-1,
        description="unit: start copy",
    )

    # Persist with an initial state.
    for txn in config.txn():
        txn.dependency.state(dep).create({"status": "WORKING"})

    # Read back and assert state.
    for txn in config.txn():
        state = txn.dependency.state(dep).get()
        assert state["status"] == "WORKING"

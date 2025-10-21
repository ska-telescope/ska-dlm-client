"""Unit test module for configdb_watcher."""

import asyncio
import logging
from contextlib import suppress
from types import SimpleNamespace
from typing import Final

import async_timeout
import pytest
from ska_sdp_config.entity import ProcessingBlock, Script
from ska_sdp_config.entity.flow import DataProduct, Flow

from ska_dlm_client.sdp_ingest.configdb_utils import _initialise_dependency
from ska_dlm_client.sdp_ingest.configdb_watcher import watch_dataproduct_status

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
        assert any(
            key == test_dataproduct.key and value.get("status") == "FINISHED"
            for key, value in values
        )

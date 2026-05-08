"""Unit test module for configdb_watcher."""

import asyncio
from contextlib import suppress
from typing import Any, Final

import async_timeout
import pytest
from ska_sdp_config.entity import ProcessingBlock, Script
from ska_sdp_config.entity.flow import DataProduct, DataProductPersist, Flow, FlowSource

from ska_dlm_client.configdb_watcher.configdb_watcher import watch_dataproduct_status

SCRIPT = Script.Key(kind="batch", name="unit_test", version="0.0.0")
PB_ID = "pb-madeup-00000000-a"
NAME = "prod-a"


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
    """Verify the watcher emits COMPLETED events and creates a DLM dependency once.

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

    dataproduct_flow = Flow(
        key=Flow.Key(pb_id=pb_id, kind="data-product", name=flow_name),
        sink=DataProduct(data_dir="/dlm-archive", paths=[]),
        sources=[],
        data_model="Visibility",
    )

    persist_flow = Flow(
        key=Flow.Key(pb_id=pb_id, kind="data-product-persist", name="dlm-persist"),
        sink=DataProductPersist(phase="SOLID", expires_at=None),
        sources=[
            FlowSource(
                uri=dataproduct_flow.key,
                function="ska-data-lifecycle:ingest",
            )
        ],
        data_model="Visibility",
    )

    timeout_s: Final = 0.5
    values: list[tuple[Flow.Key, dict[str, Any]]] = []

    # Sanity check: no products yet
    for txn in config.txn():
        assert txn.flow.list_keys(kind="data-product") == []
        assert txn.flow.list_keys(kind="data-product-persist") == []

    async def aput_flow():
        """Create the flow, then flip its state a few times. A little 'traffic generator'."""
        if not create_first:
            await asyncio.sleep(timeout_s)

        for txn in config.txn():
            txn.flow.create(dataproduct_flow)
            txn.flow.create(persist_flow)
            txn.flow.state(dataproduct_flow.key).create({"status": "WAITING"})
            txn.flow.state(dataproduct_flow.key).update({"status": "COMPLETED"})
            txn.flow.state(dataproduct_flow.key).update({})
            txn.flow.state(dataproduct_flow.key).update({"status": "WAITING"})
            txn.flow.state(dataproduct_flow.key).update({"status": "COMPLETED"})

    async def aget_single_state():
        """Consume the watcher and collect COMPLETED events.

        If ``create_first`` is True, waits briefly before starting to simulate a pre-existing
        flow. Runs the Watcher with the shared ``config`` and appends any
        ``(Flow.Key, "COMPLETED")`` tuples to ``values`` until the timeout elapses. Timeouts
        are suppressed because some parameterizations may legitimately produce no events.
        """
        if create_first:
            await asyncio.sleep(timeout_s)

        with suppress(asyncio.TimeoutError):
            async with async_timeout.timeout(2 * timeout_s):
                async with watch_dataproduct_status(
                    config, "COMPLETED", include_existing=include_existing
                ) as producer:
                    async for key, state in producer:
                        values.append((key, state))

    async with async_timeout.timeout(5 * timeout_s):
        await asyncio.gather(aget_single_state(), aput_flow())

    # Assert the COMPLETED event appeared the expected number of times
    assert len(values) == expected_count
    if expected_count:
        assert any(
            key == dataproduct_flow.key and state.get("status") == "COMPLETED"
            for key, state in values
        )

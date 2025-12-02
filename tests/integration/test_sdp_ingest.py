"""SDP Ingest (ConfigDB Watcher) integration tests."""

import asyncio
import logging
import os

import pytest
from ska_sdp_config import Config
from ska_sdp_config.entity import ProcessingBlock, Script
from ska_sdp_config.entity.flow import DataProduct, Dependency, Flow

from ska_dlm_client.openapi.configuration import Configuration
from ska_dlm_client.sdp_ingest import main as sdp_ingest_main

PB_ID = "pb-test-00000000-a"
SCRIPT = Script.Key(kind="batch", name="test", version="0.0.0")
INGEST_SERVER_URL = os.getenv("INGEST_SERVER_URL", "http://localhost:8001")


def _get_cfg() -> Config:
    """Return a Config using the same env-based backend settings as the watcher."""
    return Config()


def _ensure_processing_block() -> None:
    """Create the ProcessingBlock if it doesn't already exist (idempotent)."""
    cfg = _get_cfg()
    for txn in cfg.txn():
        if txn.processing_block.get(PB_ID) is None:
            txn.processing_block.create(
                ProcessingBlock(
                    key=PB_ID,
                    eb_id=None,
                    script=SCRIPT,
                )
            )
            print(f"Created ProcessingBlock {PB_ID}")
        else:
            print(f"ProcessingBlock {PB_ID} already exists")


def _create_completed_flow(data_dir: str, flow_name_arg: str) -> None:
    """Create a Flow and set its state to COMPLETED."""
    cfg = _get_cfg()
    test_dataproduct = Flow(
        key=Flow.Key(pb_id=PB_ID, kind="data-product", name=flow_name_arg),
        sink=DataProduct(data_dir=data_dir, paths=[]),
        sources=[],
        data_model="Visibility",
    )

    for txn in cfg.txn():
        txn.flow.create(test_dataproduct)
        ops = txn.flow.state(test_dataproduct.key)
        ops.create({"status": "COMPLETED"})


def trigger_completed_flow(flow_name) -> None:
    """Ensure PB + Flow exist and mark Flow as COMPLETED."""
    _ensure_processing_block()
    # IMPORTANT: this must match what the watcher expects:
    #   - same `storage_root_directory`
    #   - points at a directory that actually contains the .ms + metadata
    _create_completed_flow(
        data_dir="tests/directory_watcher/test_registration_processor/testing1",
        flow_name_arg=flow_name,
    )


def _get_dependency_statuses_for_product(pb_id: str, name: str) -> list[str]:
    """Return all dependency statuses for a given data-product (by pb_id/name)."""
    cfg = _get_cfg()
    statuses: list[str] = []
    for txn in cfg.txn():
        dkeys = txn.dependency.list_keys(pb_id=pb_id, name=name)
        for dkey in dkeys:
            dep_obj = Dependency(key=dkey, expiry_time=-1, description=None)
            state = txn.dependency.state(dep_obj).get() or {}
            status = state.get("status")
            if status is not None:
                statuses.append(status)
    return statuses


@pytest.mark.asyncio
@pytest.mark.integration
async def test_watcher_starts_and_registers(caplog):
    """Run the real watcher, wait for success logs, then cancel it cleanly."""
    caplog.set_level(logging.INFO, logger="ska_dlm_client.sdp_ingest")

    ingest_config = sdp_ingest_main.SDPIngestConfig(
        include_existing=False,
        ingest_server_url=INGEST_SERVER_URL,
        ingest_configuration=Configuration(host=INGEST_SERVER_URL),
        source_storage="MyDisk",  # <- Should be registered by test_directory_watcher.py
        storage_root_directory="/data",
        migration_destination_storage_name="MyDisk",
    )

    task = asyncio.create_task(sdp_ingest_main.sdp_to_dlm_ingest_and_migrate(ingest_config))

    try:
        # 1) Wait for watcher to be READY
        ready_msg = "Watcher READY and looking for events."
        for _ in range(50):
            if ready_msg in caplog.text:
                break
            await asyncio.sleep(0.1)
        else:
            pytest.fail("Watcher did not log readiness within timeout")

        # 2) Trigger a COMPLETED Flow
        trigger_completed_flow(flow_name="test-flow")

        # 3) Wait for the "status set to WORKING" log
        working_msg = "status set to WORKING"
        for _ in range(100):
            if working_msg in caplog.text:
                break
            await asyncio.sleep(0.1)
        else:
            pytest.fail("Dependency was not marked WORKING within timeout")

    finally:
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    statuses = _get_dependency_statuses_for_product(PB_ID, "test-flow")
    assert "WORKING" in statuses


@pytest.mark.asyncio
@pytest.mark.integration
async def test_watcher_logs_failed_registration(caplog):
    """Run the watcher, trigger a Flow, and check failed registration is logged."""
    caplog.set_level(logging.INFO, logger="ska_dlm_client.sdp_ingest")

    # Deliberately use a bad storage name to trigger DLM registration failure
    ingest_config = sdp_ingest_main.SDPIngestConfig(
        include_existing=False,
        ingest_server_url=INGEST_SERVER_URL,
        ingest_configuration=Configuration(host=INGEST_SERVER_URL),
        source_storage="NonExistentStorage",  # <- not registered on DLM side
        storage_root_directory="/data",
        migration_destination_storage_name="MyDisk",
    )

    task = asyncio.create_task(sdp_ingest_main.sdp_to_dlm_ingest_and_migrate(ingest_config))

    try:
        # 1) Wait for watcher to be READY
        ready_msg = "Watcher READY and looking for events."
        for _ in range(50):
            if ready_msg in caplog.text:
                break
            await asyncio.sleep(0.1)
        else:
            pytest.fail("Watcher did not log readiness within timeout")

        # 2) Trigger a COMPLETED Flow
        trigger_completed_flow("test-flow-failure")

        # 3) Wait for the registration failure log
        failure_msg = "DLM registration failed"
        for _ in range(100):  # give it enough time for end-to-end path
            if failure_msg in caplog.text:
                break
            await asyncio.sleep(0.1)
        else:
            pytest.fail("Watcher did not log failed registration within timeout")

        assert "status set to FAILED" in caplog.text

    finally:
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    statuses = _get_dependency_statuses_for_product(PB_ID, "test-flow-failure")
    assert "FAILED" in statuses

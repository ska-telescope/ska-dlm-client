"""SDP Ingest (ConfigDB Watcher) integration tests."""

import asyncio
import logging
import os

import pytest
from ska_sdp_config import Config
from ska_sdp_config.entity import ProcessingBlock, Script
from ska_sdp_config.entity.flow import DataProduct, Flow

from ska_dlm_client.openapi.configuration import Configuration
from ska_dlm_client.sdp_ingest import main as sdp_ingest_main

PB_ID = "pb-test-00000000-a"
FLOW_NAME = "test-flow"
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


def _create_or_update_completed_flow(data_dir: str) -> None:
    """Create a Flow and set its state to COMPLETED."""
    cfg = _get_cfg()
    test_dataproduct = Flow(
        key=Flow.Key(pb_id=PB_ID, kind="data-product", name=FLOW_NAME),
        sink=DataProduct(data_dir=data_dir, paths=[]),
        sources=[],
        data_model="Visibility",
    )

    # Create the Flow
    for txn in cfg.txn():
        txn.flow.create(test_dataproduct)

    # Set Flow state to COMPLETED
    for txn in cfg.txn():
        ops = txn.flow.state(test_dataproduct.key)
        ops.create({"status": "COMPLETED"})


def trigger_completed_flow() -> None:
    """Ensure PB + Flow exist and mark Flow as COMPLETED."""
    _ensure_processing_block()
    # IMPORTANT: this must match what the watcher expects:
    #   - same `storage_root_directory`
    #   - points at a directory that actually contains the .ms + metadata
    _create_or_update_completed_flow(
        data_dir="tests/directory_watcher/test_registration_processor/testing1"
    )


@pytest.mark.asyncio
@pytest.mark.integration
async def test_watcher_starts_and_registers(caplog):
    """Run the real watcher, wait for success logs, then cancel it cleanly."""
    caplog.set_level(logging.INFO, logger="ska_dlm_client.sdp_ingest")

    ingest_config = sdp_ingest_main.SDPIngestConfig(
        include_existing=False,
        ingest_server_url=INGEST_SERVER_URL,
        ingest_configuration=Configuration(host=INGEST_SERVER_URL),
        source_storage="MyDisk",  # Should be registered by test_directory_watcher.py
        storage_root_directory="/data",
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
        trigger_completed_flow()

        # 3) Wait for the registration success log
        success_msg = "DLM registration successful"
        for _ in range(100):  # give it longer for end-to-end path
            if success_msg in caplog.text:
                break
            await asyncio.sleep(0.1)
        else:
            pytest.fail("Watcher did not log successful registration within timeout")

    finally:
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

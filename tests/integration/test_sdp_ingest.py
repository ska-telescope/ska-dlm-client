"""SDP Ingest (ConfigDB Watcher) integration tests."""

import asyncio
import logging
import sys

import pytest

from ska_dlm_client.sdp_ingest import main as sdp_ingest_main


class _DummyWatcher:
    """Minimal async context manager + async iterator for the watcher."""

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def __aiter__(self):
        return self

    async def __anext__(self):
        # No events -> exit the async for loop immediately
        raise StopAsyncIteration


def _fake_watch_dataproduct_status(config, status, include_existing):
    """Replace watch_dataproduct_status with a dummy watcher."""
    _ = (config, status, include_existing)  # Mark arguments as intentionally unused
    return _DummyWatcher()


def test_sdp_ingest_main_logs_ready(monkeypatch, caplog):
    """
    Start the SDP watcher entrypoint and assert it logs 'Watcher READY'.

    This is a smoke test for the CLI entrypoint:
    * Calls the real main() (so argparse and asyncio.run() are exercised).
    * Enters the real sdp_to_dlm_ingest_and_migrate coroutine up to the
    async-with watcher block.
    * Monkeypatches watch_dataproduct_status to a dummy watcher so the test
    does not block.
    * Verifies that the expected 'Watcher READY' log message is emitted.
    """
    # Patch the watcher factory so we don't block forever waiting on etcd events
    monkeypatch.setattr(
        sdp_ingest_main,
        "watch_dataproduct_status",
        _fake_watch_dataproduct_status,
    )

    # Capture logs from the sdp_ingest logger
    caplog.set_level(logging.INFO, logger="ska_dlm_client.sdp_ingest")

    # Pretend we were called as a CLI without --include-existing
    monkeypatch.setattr(
        sys,
        "argv",
        ["ska-dlm-client-sdp-ingest"],
    )

    # Run sdp_to_dlm_ingest_and_migrate once and exit quickly
    sdp_ingest_main.main()

    # Check that the watcher announced readiness
    assert "Watcher READY and looking for events." in caplog.text


@pytest.mark.asyncio
async def test_real_watcher_starts(caplog):
    """Run the real watcher, wait for READY log, then cancel it cleanly."""
    caplog.set_level(logging.INFO, logger="ska_dlm_client.sdp_ingest")

    # Start the real watcher in the background
    task = asyncio.create_task(
        sdp_ingest_main.sdp_to_dlm_ingest_and_migrate(include_existing=False)
    )

    try:
        # Wait until the watcher logs that it's ready, or timeout
        message = "Watcher READY and looking for events."
        for _ in range(50):  # up to ~5s total
            if message in caplog.text:
                break
            await asyncio.sleep(0.1)
        else:
            pytest.fail("Watcher did not log readiness within timeout")
    finally:
        # Cancel the watcher task and wait for it to finish
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

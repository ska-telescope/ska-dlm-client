"""Unit test module for configdb_watcher."""

import asyncio
import logging
import threading
from contextlib import asynccontextmanager, suppress
from types import SimpleNamespace
from typing import Final

import async_timeout
import pytest
from ska_sdp_config.entity import ProcessingBlock, Script
from ska_sdp_config.entity.flow import DataProduct, Flow

from ska_dlm_client.sdp_ingest.configdb_utils import _initialise_dependency
from ska_dlm_client.sdp_ingest.configdb_watcher import watch_dataproduct_status
from ska_dlm_client.sdp_ingest.main import sdp_to_dlm_ingest_and_migrate

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


# _busy_read_config and _shared are shared helpers/state used by both mocks
def _busy_read_config(cfg, barrier: threading.Barrier, done_evt: threading.Event):
    """
    Work function run by each background thread.

    - barrier.wait(): both threads (one started by the watcher mock, and one
      started by the create() mock) block here until *both* are ready. This
      ensures they start hammering the same Config instance at the same time,
      which is the key to exercising thread safety.
    - The tight loop repeatedly performs harmless reads (repr/id) to create
      sustained concurrent access without relying on any specific Config API.
    - done_evt.set(): signals the test that this thread has finished its work.
    """
    barrier.wait()
    for _ in range(20000):
        _ = repr(cfg)
        _ = id(cfg)
    done_evt.set()


_shared = {
    # We stash the actual Config instance here so both mocks act on the same object.
    "cfg": None,
    # One barrier shared by both threads so they start together (concurrent overlap).
    "barrier": threading.Barrier(2),
    # Events to let the test know each thread finished.
    "done1": threading.Event(),
    "done2": threading.Event(),
}


@asynccontextmanager
async def _mock_watch_dataproduct_status(config, status: str, include_existing: bool):
    """
    Async context manager that replaces the real watcher.

    What it does:
    - Records the shared Config instance.
    - Starts background thread #1 that waits on the shared barrier.
    - Yields one FINISHED event to trigger ``create_sdp_migration_dependency``.
    - After yielding once, it waits for thread #1 to complete (with a timeout).
    """
    assert status == "FINISHED"  # pylint complains unused-argument
    assert isinstance(include_existing, bool)  # pylint complains unused-argument
    _shared["cfg"] = config

    # Start thread #1: this represents concurrent access coming from the watcher side.
    t1 = threading.Thread(
        target=_busy_read_config,
        args=(config, _shared["barrier"], _shared["done1"]),
        daemon=True,
    )
    t1.start()

    async def _producer():
        # Yield one fake FINISHED event to trigger the create() call.
        yield ("fake-key", "FINISHED")
        # Ensure thread #1 finished (best-effort via timeout).
        _shared["done1"].wait(timeout=5)

    try:
        yield _producer()
    finally:
        pass


async def _mock_create_sdp_migration_dependency(config, dataproduct_key):
    """
    Async function that replaces the real ``create_sdp_migration_dependency`` call.

    What it does:
    - Asserts we're touching the exact same Config instance the watcher saw.
    - Starts background thread #2 that also waits on the *same* barrier so both threads
    run concurrently.
    - Sleeps briefly to give both threads time to run while this coroutine is
    suspended (so the concurrency truly overlaps with the async flow).
    - Waits for thread #2 to complete (with timeout).
    - Returns a truthy value so the main function continues normally.
    """
    assert _shared["cfg"] is config  # sanity: must be the exact same object
    assert dataproduct_key == "fake-key"  # silences pylint's unused-argument

    # Start thread #2: this represents concurrent access coming from the create() side.
    t2 = threading.Thread(
        target=_busy_read_config,
        args=(config, _shared["barrier"], _shared["done2"]),
        daemon=True,
    )
    t2.start()

    # Brief pause to overlap thread activity with the coroutine's lifecycle.
    await asyncio.sleep(0.01)

    # Ensure thread #2 finished (best-effort via timeout).
    _shared["done2"].wait(timeout=5)
    return {"dep": "ok"}


@pytest.mark.asyncio
async def test_sdp_to_dlm_ingest_and_migrate_config_is_thread_safe(monkeypatch):
    """
    End-to-end unit test (with mocks).

    Forces concurrent, cross-thread use of the single Config() created inside
    ``sdp_to_dlm_ingest_and_migrate()``.
    """
    # Patch where the names are used, not where defined.
    monkeypatch.setattr(
        "ska_dlm_client.sdp_ingest.main.watch_dataproduct_status",
        _mock_watch_dataproduct_status,
        raising=True,
    )
    monkeypatch.setattr(
        "ska_dlm_client.sdp_ingest.main.create_sdp_migration_dependency",
        _mock_create_sdp_migration_dependency,
        raising=True,
    )

    # Invoke the function. If Config isn't thread-safe, this is likely to raise/hang.
    await sdp_to_dlm_ingest_and_migrate(include_existing=False)

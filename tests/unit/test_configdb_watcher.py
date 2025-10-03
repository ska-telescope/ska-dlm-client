"""Unit test module for configdb_watcher."""

import asyncio
from contextlib import suppress
from typing import Final

import async_timeout
import pytest
from ska_sdp_config import Config
from ska_sdp_config.entity.flow import DataProduct, Flow

from ska_dlm_client.configdb_watcher import watch_dataproduct_status


def clear_dependencies(config: Config):
    """Clear all SDP ConfigDB dependencies."""
    for txn in config.txn():
        keys = txn.flow.list_keys()
        for key in keys:
            txn.flow.delete(key, recurse=True)


@pytest.fixture(name="config")
def sdp_config_fixture():
    """Create client to a clean SDP ConfigDB."""
    config = Config(backend="etcd3")
    clear_dependencies(config)
    yield config
    clear_dependencies(config)


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
async def test_dataproduct_status_watcher(
    config, create_first: bool, include_existing: bool, expected_count: int
):
    """Test SDP ConfigDB watching.

    Args:
        config: SDP ConfigDB client.
        create_first: create dependency state before watcher starts.
    """
    test_dataproduct: Final = Flow(
        key=Flow.Key(pb_id="pb-name-00000000-0", kind="data-product", name="name"),
        sink=DataProduct(data_dir="/datapath", paths=[]),
        sources=[],
        data_model="Visibility",
    )

    timeout_s: Final = 0.5
    values = []

    for txn in config.txn():
        assert txn.flow.list_keys(kind="data-product") == []

    async def aput_flow():
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
        if create_first:
            await asyncio.sleep(timeout_s)

        with suppress(asyncio.TimeoutError):
            async with async_timeout.timeout(2 * timeout_s):
                # NOTE: config not threadsafe
                async with watch_dataproduct_status(
                    Config(), "FINISHED", include_existing=include_existing
                ) as producer:
                    async for value in producer:
                        values.append(value)

    async with async_timeout.timeout(5 * timeout_s):
        await asyncio.gather(aget_single_state(), aput_flow())

    assert len(values) == expected_count
    if expected_count:
        assert (test_dataproduct.key, "FINISHED") in values

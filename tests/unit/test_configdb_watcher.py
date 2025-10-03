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
@pytest.mark.parametrize("create_first", [False, True])
async def test_dataproduct_status_watcher(config, create_first: bool):
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

    values = []

    for txn in config.txn():
        assert txn.flow.list_keys(kind="data-product") == []

    async def aget_single_state():
        if not create_first:
            await asyncio.sleep(0.5)

        with suppress(asyncio.TimeoutError):
            async with async_timeout.timeout(1):
                # NOTE: config not threadsafe
                async with watch_dataproduct_status(
                    Config(), "FINISHED", include_existing=True
                ) as producer:
                    async for value in producer:
                        values.append(value)

    async def aput_flow():
        if create_first:
            await asyncio.sleep(0.5)
        for txn in config.txn():
            txn.flow.create(test_dataproduct)
            txn.flow.state(test_dataproduct.key).create({"status": "WAITING"})
            txn.flow.state(test_dataproduct.key).update({"status": "FINISHED"})
            txn.flow.state(test_dataproduct.key).update({})
            txn.flow.state(test_dataproduct.key).update({"status": "WAITING"})
            txn.flow.state(test_dataproduct.key).update({"status": "FINISHED"})

    async with async_timeout.timeout(3):
        await asyncio.gather(aget_single_state(), aput_flow())

    assert values == [(test_dataproduct.key, "FINISHED")]

"""Unit test module for configdb_watcher."""

import asyncio
from contextlib import suppress
from typing import Final

import async_timeout
import pytest
from ska_sdp_config import Config
from ska_sdp_config.entity import Dependency

from ska_dlm_client.configdb_watcher import watch_dependency_status


def clear_dependencies(config: Config):
    """Clear all SDP ConfigDB dependencies."""
    for txn in config.txn():
        keys = txn.dependency.list_keys()
        for key in keys:
            txn.dependency.delete(key, recurse=True)


@pytest.fixture(name="config")
def sdp_config_fixture():
    """Create client to a clean SDP ConfigDB."""
    config = Config(backend="etcd3")
    clear_dependencies(config)
    yield config
    clear_dependencies(config)


@pytest.mark.asyncio
@pytest.mark.parametrize("create_first", [False, True])
async def test_configdb_watcher(config, create_first: bool):
    """Test SDP ConfigDB watching.

    Args:
        config: SDP ConfigDB client.
        create_first: create dependency state before watcher starts.
    """
    test_dep: Final = Dependency(
        key=Dependency.Key(pb_id="pb-name-00000000-0", kind="why", name="name", origin="origin"),
        expiry_time=10,
    )

    values = []

    async def aget_single_state():
        if not create_first:
            await asyncio.sleep(0.5)

        with suppress(asyncio.TimeoutError):
            async with async_timeout.timeout(1):
                # NOTE: config not threadsafe
                async with watch_dependency_status(
                    Config(), "FINISHED", include_existing=False
                ) as producer:
                    async for value in producer:
                        values.append(value)

    async def aput_dependency():
        if create_first:
            await asyncio.sleep(0.5)
        for txn in config.txn():
            txn.dependency.create(test_dep.model_copy())
            txn.dependency.state(test_dep.key).create({"status": "WAITING"})
            txn.dependency.state(test_dep.key).update({"status": "FINISHED"})
            txn.dependency.state(test_dep.key).update({})
            txn.dependency.state(test_dep.key).update({"status": "WAITING"})
            txn.dependency.state(test_dep.key).update({"status": "FINISHED"})

    async with async_timeout.timeout(3):
        await asyncio.gather(aget_single_state(), aput_dependency())

    assert values == [(test_dep.key, "FINISHED")]

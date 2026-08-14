"""Unit test module for configdb_utils."""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from unittest import mock

import pytest
from ska_sdp_config import ConfigCollision
from ska_sdp_config.entity.common import PVCPath
from ska_sdp_config.entity.flow import DataProduct, DataProductPersist, Flow, FlowSource

from ska_dlm_client.configdb_watcher.configdb_utils import (
    _initialise_dependency,
    create_sdp_migration_dependency,
    get_pvc_subpath,
    log_flow_dependencies,
    on_message_received,
    start_rabbitmq_consumer,
    update_dependency_state,
)

PB_ID = "pb-madeup-00000000-a"
EB_ID = "eb-00000000"
KIND = "data-product"
DP_FLOW_NAME = "prod-a"
FLOW_NAME = "vis-receive-mswriter-processor"
FUNCTION = "ska-dlm-client:ingest"

# pylint: disable=redefined-outer-name


# Note: This fixture mirrors the structure used in ska-sdp-config test_flow.py
@pytest.fixture
def dataproduct_flow(config):
    """Create a DataProduct Flow."""
    pvc = PVCPath(
        k8s_namespaces=[],
        k8s_pvc_name="shared",
        pvc_mount_path=Path("/data"),
        pvc_subpath=Path(f"product/{EB_ID}/ska-sdp/{PB_ID}"),
    )

    for txn in config.txn():
        flow = Flow(
            key=Flow.Key(
                pb_id=PB_ID,
                kind="data-product",
                name=DP_FLOW_NAME,
            ),
            sink=DataProduct(
                data_dir=pvc,
                paths=[Path("out-scan_id-id.ms")],
            ),
            sources=[
                FlowSource(
                    uri=Flow.Key(pb_id=PB_ID, kind="plasma", name="visibilities"),
                    function="ska-sdp-realtime-receive-processors:mswriter",
                )
            ],
            data_model="Visibility",
        )

        txn.flow.create(flow)

    return flow.key


@pytest.fixture
def dataproductpersist_flow(config):
    """Create a DataProductPersist Flow linked to a DataProduct Flow."""
    for txn in config.txn():
        flow = Flow(
            key=Flow.Key(
                pb_id=PB_ID,
                kind="data-product-persist",
                name="dlm-persist",
            ),
            sink=DataProductPersist(
                expires_at=datetime.now().astimezone(),
                phase="SOLID",
            ),
            sources=[
                FlowSource(
                    uri=Flow.Key(
                        pb_id=PB_ID,
                        kind=KIND,
                        name="visibilities",
                    ),
                    function=FUNCTION,
                )
            ],
            data_model="Visibility",
        )

        txn.flow.create(flow)

    return flow.key


@pytest.mark.asyncio
async def test_create_sdp_migration_dependency(config, dataproduct_flow):
    """Test create_sdp_migration_dependency persists dep and empty state."""
    dep = await create_sdp_migration_dependency(config, dataproduct_flow)

    # Returned dependency has expected key + metadata
    assert dep is not None
    assert dep.key.pb_id == PB_ID
    assert dep.key.name == DP_FLOW_NAME
    assert dep.key.kind == "dlm-copy"
    assert dep.key.origin == "ska-data-lifecycle-management"
    assert dep.expiry_time == -1
    assert dep.description == "DLM: lock data-product for copy"

    # Verify entity is persisted in ConfigDB
    for txn in config.txn():
        stored_dep = txn.dependency.get(dep.key)
        assert stored_dep is not None

        # State should exist and be an empty dict
        state = txn.dependency.state(dep).get()
        assert state == {}
        break


def test_update_dependency_state(config):
    """Test update_dependency_state creates then updates (covers ConfigCollision path)."""
    key = Flow.Key(pb_id=PB_ID, name=DP_FLOW_NAME)
    dep = _initialise_dependency(
        key, dep_kind="dlm-copy", origin="dlmtest", expiry_time=-1, description="unit"
    )
    # persist entity & empty state
    for txn in config.txn():
        txn.dependency.create_or_update(dep)
        ops = txn.dependency.state(dep)
        (ops.update if ops.exists() else ops.create)({})

    # first call should create status
    for txn in config.txn():
        update_dependency_state(txn, dep, "WORKING")
    for txn in config.txn():
        assert txn.dependency.state(dep).get()["status"] == "WORKING"

    # second call should hit update (ConfigCollision on create)
    for txn in config.txn():
        update_dependency_state(txn, dep, "FINISHED")
    for txn in config.txn():
        assert txn.dependency.state(dep).get()["status"] == "FINISHED"


def test_log_flow_dependencies(config, caplog):
    """Test log_flow_dependencies for none and one."""
    caplog.set_level(logging.INFO, logger="ska_dlm_client.configdb_watcher")
    key = Flow.Key(pb_id=PB_ID, name=DP_FLOW_NAME)
    dep = _initialise_dependency(
        key, dep_kind="dlm-copy", origin="dlmtest", expiry_time=-1, description="unit"
    )

    # No dependencies yet
    for txn in config.txn():
        log_flow_dependencies(txn, dep.key)
    assert f"No flow dependencies for {PB_ID}/{DP_FLOW_NAME}" in caplog.text

    # Create one dependency + state and log again
    for txn in config.txn():
        try:
            txn.dependency.create(dep)
        except ConfigCollision:
            pass
        try:
            txn.dependency.state(dep).create({"status": "WORKING"})
        except ConfigCollision:
            txn.dependency.state(dep).update({"status": "WORKING"})

    caplog.clear()
    for txn in config.txn():
        log_flow_dependencies(txn, dep.key)

    # Positive log line containing status
    assert f"Flow dependencies for {PB_ID}/{DP_FLOW_NAME}:" in caplog.text
    assert "status=WORKING" in caplog.text


def test_get_pvc_subpath(config, dataproduct_flow):
    """Test get_pvc_subpath extracts pvc_subpath from a DataProduct Flow."""
    result = get_pvc_subpath(config, dataproduct_flow)

    assert str(result) == f"product/{EB_ID}/ska-sdp/{PB_ID}"


def test_get_pvc_subpath_failure_non_pvcpath(config):
    """Test get_pvc_subpath raises if Flow.sink.data_dir is not a PVCPath."""
    key = Flow.Key(
        pb_id=PB_ID,
        kind="data-product",
        name=FLOW_NAME,
    )

    bad_flow = Flow(
        key=key,
        data_model="Visibility",
        sink=DataProduct(
            data_dir=Path("not/a/pvcpath"),
            paths=[],
        ),
        sources=[],
    )

    for txn in config.txn():
        txn.flow.create(bad_flow)

    with pytest.raises(TypeError, match=r"only PVCPath supported for flow data_dir"):
        get_pvc_subpath(config, key)


@pytest.mark.asyncio
async def test_on_message_received_acknowledges_valid_message() -> None:
    """Test that a valid message is acknowledged."""
    message = mock.MagicMock()
    message.body = json.dumps(
        {
            "complete": True,
            "job_status": {"success": True},
        }
    ).encode()
    message.ack = mock.AsyncMock()
    message.nack = mock.AsyncMock()

    await on_message_received(message)

    message.ack.assert_awaited_once()
    message.nack.assert_not_awaited()


@pytest.mark.asyncio
async def test_on_message_received_nacks_invalid_message() -> None:
    """Test that an invalid message is negatively acknowledged."""
    message = mock.MagicMock()
    message.body = b"not valid JSON"
    message.ack = mock.AsyncMock()
    message.nack = mock.AsyncMock()

    await on_message_received(message)

    message.ack.assert_not_awaited()
    message.nack.assert_awaited_once_with(requeue=True)


@pytest.mark.asyncio
async def test_start_rabbitmq_consumer_sets_up_consumer() -> None:
    """Test that the RabbitMQ consumer is configured correctly."""
    connection = mock.MagicMock()
    channel = mock.MagicMock()
    exchange = mock.MagicMock()
    queue = mock.MagicMock()

    connection.channel = mock.AsyncMock(return_value=channel)
    channel.set_qos = mock.AsyncMock()
    channel.declare_exchange = mock.AsyncMock(return_value=exchange)
    channel.declare_queue = mock.AsyncMock(return_value=queue)
    queue.bind = mock.AsyncMock()
    queue.consume = mock.AsyncMock()

    with (
        mock.patch(
            "ska_dlm_client.configdb_watcher.configdb_utils.aio_pika.connect_robust",
            new=mock.AsyncMock(return_value=connection),
        ) as connect_robust,
        mock.patch(
            "ska_dlm_client.configdb_watcher.configdb_utils.asyncio.Future",
            side_effect=asyncio.CancelledError,
        ),
        pytest.raises(asyncio.CancelledError),
    ):
        await start_rabbitmq_consumer(
            "amqp://dlm-user:dlm-password@rabbitmq/",
            "dlm_exchange",
        )

    connect_robust.assert_awaited_once_with("amqp://dlm-user:dlm-password@rabbitmq/")
    connection.channel.assert_awaited_once()
    channel.set_qos.assert_awaited_once_with(prefetch_count=10)
    channel.declare_exchange.assert_awaited_once_with(
        "dlm_exchange",
        passive=True,
    )
    channel.declare_queue.assert_awaited_once_with(
        "configdb_watcher_queue",
        durable=True,
    )
    queue.bind.assert_awaited_once_with(
        exchange,
        routing_key="dlm.migration.update",
    )
    queue.consume.assert_awaited_once_with(
        on_message_received,
        no_ack=False,
    )

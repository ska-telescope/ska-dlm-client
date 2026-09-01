# flake8: ignore=DAR101
"""Shared helper functions for the ConfigDB dependency lifecycle."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import urllib.parse
from typing import Optional

import aio_pika
import athreading
from ska_sdp_config import Config, ConfigCollision
from ska_sdp_config.backend.etcd3 import Etcd3Backend
from ska_sdp_config.entity.common import PVCPath
from ska_sdp_config.entity.common.path import RelativePurePath
from ska_sdp_config.entity.flow import DataProduct, Dependency, Flow

logger = logging.getLogger(__name__)


def _initialise_dependency(
    product_key: Flow.Key,
    *,
    dep_kind: str,
    origin: str = "ska-data-lifecycle-management",
    expiry_time: int = -1,
    description: Optional[str],
) -> Dependency:
    """Build a Dependency for a data-product Flow without setting its state.

    The Dependency is identified by a ``Dependency.Key``. ``Dependency.Key`` inherits
    ``pb_id`` and ``name`` from ``Flow.Key`` and adds the ``kind`` and ``origin`` fields.
    Therefore, the Dependency created here uses the ``pb_id`` and ``name`` from
    ``product_key``, together with the supplied ``dep_kind`` and ``origin``.

    Args:
        product_key: Flow key providing the Dependency's ``pb_id`` and ``name``.
        dep_kind: Kind of dependency, used as ``Dependency.Key.kind``.
        origin: Component creating the dependency, used as ``Dependency.Key.origin``.
        expiry_time: Time in seconds after which the dependency should be released.
        ``-1`` means no expiry.
        description: Optional description of the dependency.

    Returns:
        The Dependency object.

    Notes:
        - `dep_kind` is the sink/destination identifier (must match [A-Za-z0-9-]{1,96}).
        - `origin` identifies who issued the lock.
    """
    return Dependency(
        key=Dependency.Key(
            pb_id=product_key.pb_id,  # PB that produced the flow being locked
            kind=dep_kind,  # Kind of flow that is depended on
            name=product_key.name,  # Data product name
            origin=origin,  # who is placing the lock
        ),
        expiry_time=expiry_time,
        description=description,
    )


async def create_sdp_migration_dependency(config, dataproduct_key: Flow.Key) -> Dependency:
    """Create and persist a DLM migration Dependency for a data-product Flow.

    The Dependency is associated with the supplied Flow through its key: ``pb_id`` and
    ``name`` are inherited from ``dataproduct_key``, while ``kind`` is set to ``"dlm-copy"``
    and ``origin`` identifies DLM as the component creating the dependency.

    The Dependency and an initially empty Dependency state are persisted in ConfigDB.
    The state can subsequently be updated to WORKING, FINISHED, or FAILED.

    Args:
        config: SDP ConfigDB client.
        dataproduct_key: Flow key identifying the data product for which the Dependency
        is created.

    Returns:
        The created Dependency.
    """
    dep = _initialise_dependency(
        dataproduct_key,
        dep_kind="dlm-copy",
        origin="ska-data-lifecycle-management",
        expiry_time=-1,
        description="DLM: lock data-product for copy",
    )
    if dep is not None:
        for txn in config.txn():
            # Persist the dependency
            txn.dependency.create(dep)
            # Persist the dependency state (with no status for now)
            txn.dependency.state(dep).create({})
            logger.info("Created DLM dependency for %s/%s", dep.key.pb_id, dep.key.name)
    return dep


def get_pvc_subpath(config: Config, key: Flow.Key) -> RelativePurePath:
    """
    Get the PVC-internal subpath for a data product from the SDP ConfigDB.

    Expects Flow.sink.data_dir to be a mapping containing a 'pvc_subpath' key.

    Returns:
        Path relative to the root of the PVC.
    """
    flow: Flow | None
    for txn in config.txn():
        flow = txn.flow.get(key)

    if flow is None:
        raise KeyError(f"Flow key not found: {key}")

    if not isinstance(flow.sink, DataProduct):
        raise TypeError(f"Expected DataProduct sink for Flow key: {key}")

    data_dir = flow.sink.data_dir
    if not isinstance(data_dir, PVCPath):
        raise TypeError(
            "only PVCPath supported for flow data_dir. "
            f"Got: {type(data_dir).__module__}.{type(data_dir).__name__}"
        )

    return data_dir.pvc_subpath


def log_flow_dependencies(txn, product_key: Flow.Key) -> None:
    """Log any flow-level dependencies (locks) for this product (any kind/origin)."""
    pb_id = product_key.pb_id
    name = product_key.name
    if not pb_id or not name:
        logger.info(
            "Data-product %s missing pb_id or name; cannot inspect flow dependencies", product_key
        )
        return

    # Server-side filter by key fields
    dkeys = txn.dependency.list_keys(pb_id=pb_id, name=name)

    if not dkeys:
        logger.info("No flow dependencies for %s/%s", pb_id, name)
        return

    entries = []
    for dkey in dkeys:
        # State (status) if present
        dep_obj = Dependency(key=dkey, expiry_time=-1, description=None)
        state = txn.dependency.state(dep_obj).get() or {}
        status = state.get("status")

        # Entity metadata (expiry_time, description) if present
        dep_meta = txn.dependency.get(dkey)  # may be None if only state exists
        expiry_time = getattr(dep_meta, "expiry_time", None)
        description = getattr(dep_meta, "description", None)

        entries.append(
            f"(pb_id={dkey.pb_id}, kind={getattr(dkey, 'kind', None)}, "
            f"name={dkey.name}, origin={getattr(dkey, 'origin', None)}, "
            f"status={status}, expiry_time={expiry_time}, description={description})"
        )

    logger.info("Flow dependencies for %s/%s: %s", pb_id, name, "; ".join(entries))


def update_dependency_state(txn, dep: Dependency, status: str = "WORKING") -> None:
    """Create or update the dependency's state to the given status."""
    try:
        txn.dependency.state(dep).create({"status": status})
    except ConfigCollision:
        txn.dependency.state(dep).update({"status": status})


@athreading.call
def aupdate_dependency_state(
    configdb: Config,
    dependency_key: Dependency.Key,
    status: str,
) -> None:
    """Update the state of a ConfigDB dependency."""
    for txn in configdb.txn():
        dependency = txn.dependency.get(dependency_key)
        update_dependency_state(txn, dependency, status=status)
        state = txn.dependency.state(dependency).get()
        logger.info(
            "Dependency %s status set to %s.",
            dependency.key,
            state.get("status"),
        )


def log_configdb_backend_details(config: Config) -> None:
    """Log backend and environment details for the SDP ConfigDB connection."""
    backend = getattr(config, "_backend", None)

    etcd_url = os.getenv("ETCD_URL", "http://etcd:2379")
    sdp_host = urllib.parse.urlparse(etcd_url).hostname
    sdp_port = urllib.parse.urlparse(etcd_url).port
    sdp_backend = os.getenv("SDP_CONFIG_BACKEND")
    sdp_path = os.getenv("SDP_CONFIG_PATH")

    if isinstance(backend, Etcd3Backend):
        client = getattr(backend, "_client", None)
        root = getattr(backend, "_root", None)

        # MultiEndpointEtcd3Client usually has some notion of endpoints;
        # this is defensive so it won't explode if the attribute name changes.
        endpoints = None
        if client is not None:
            endpoints = getattr(client, "endpoints", None)
            if endpoints is None:
                endpoints = getattr(client, "_endpoints", None)

        logger.info(
            "ConfigDB backend: etcd3 "
            "(env backend=%r, host=%r, port=%r, path=%r, root=%r, endpoints=%r)",
            sdp_backend,
            sdp_host,
            sdp_port,
            sdp_path,
            root,
            endpoints,
        )
    else:
        logger.info(
            "ConfigDB backend: %s (env backend=%r, host=%r, port=%r, path=%r)",
            type(backend).__name__ if backend is not None else None,
            sdp_backend,
            sdp_host,
            sdp_port,
            sdp_path,
        )


async def on_message_received(
    message: aio_pika.abc.AbstractIncomingMessage,
    configdb: Config,
) -> None:
    """Process a DLM migration update received from RabbitMQ.

    Completed migration messages are correlated with their ConfigDB Dependency
    using the Dependency key stored with the migration. The Dependency state is
    updated to FINISHED or FAILED based on the migration outcome.

    Args:
        message: The incoming RabbitMQ migration update message.
        configdb: ConfigDB client used to retrieve and update the Dependency.
    """
    try:
        body = message.body.decode()
        logging.info(" [x] Received message: %s", body)

        migration_record = json.loads(body)
        # Correlate the completed migration with the Dependency stored in the migration table.
        if migration_record["complete"]:
            dependency_data = migration_record.get("dependency")

            if dependency_data is not None:
                outcome = migration_record["job_status"]["success"]
                status = "FINISHED" if outcome else "FAILED"

                # assumes the migration JSON contains a serialized rep. of the actual Pydantic Dep.
                dependency_key = Dependency.Key.model_validate_json(dependency_data)

                # Find/update this dependency directly in ConfigDB.
                await aupdate_dependency_state(configdb, dependency_key, status)

                logging.info(
                    "Migration completed: oid=%s, migration_id=%s, dependency=%s, success=%s",
                    migration_record["oid"],
                    migration_record["migration_id"],
                    dependency_key,
                    outcome,
                )
                logging.debug("Full migration result: %s", migration_record)

            else:
                logging.debug(
                    "Completed migration %s has no ConfigDB dependency; ignoring.",
                    migration_record["migration_id"],
                )

            logging.debug("Full migration result: %s", migration_record)

        await message.ack()

    except (UnicodeDecodeError, json.JSONDecodeError):
        logging.warning(
            "Received invalid/non-JSON RabbitMQ message; ignoring: %r",
            message.body,
        )
        await message.ack()

    except Exception as e:  # pylint: disable=broad-except
        logging.exception("Failed to process RabbitMQ message; requeueing. Exception: %s", e)
        # Requeue valid JSON messages that fail during processing
        await message.nack(requeue=True)


async def start_rabbitmq_consumer(
    queue_connection_string: str,
    exchange_name: str,
    configdb: Config,
    # migration_results: MigrationResultTracker,
):
    """Connect to RabbitMQ and consume DLM migration update messages."""
    try:
        logging.debug("Connecting to RabbitMQ...")
        connection = await aio_pika.connect_robust(queue_connection_string)
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=10)

        exchange = await channel.declare_exchange(exchange_name, passive=True)
        queue = await channel.declare_queue("configdb_watcher_queue", durable=True)
        await queue.bind(exchange, routing_key="dlm.migration.update")

        # Start consuming messages
        await queue.consume(lambda message: on_message_received(message, configdb), no_ack=False)

        # Keep the coroutine running to listen for messages
        await asyncio.Future()

    except Exception as e:  # pylint: disable=broad-except
        logging.warning(
            "RabbitMQ consumer could not be started: %s. "
            "ConfigDB watcher will continue without RabbitMQ. (WIP, DMAN-213)",
            e,
        )

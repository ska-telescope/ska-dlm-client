# flake8: ignore=DAR101
"""Shared helper functions for the ConfigDB dependency lifecycle."""

from __future__ import annotations

import logging
import os
from pathlib import Path, PurePath
from typing import Optional

from ska_sdp_config import Config, ConfigCollision
from ska_sdp_config.backend.etcd3 import Etcd3Backend
from ska_sdp_config.entity.common import PVCPath
from ska_sdp_config.entity.flow import DataProduct, Dependency, Flow

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


def _initialise_dependency(
    product_key: Flow.Key,
    *,
    dep_kind: str,
    origin: str = "ska-data-lifecycle-management",
    expiry_time: int = -1,
    description: Optional[str],
) -> Dependency:
    """Build a Flow.Dependency for this product without setting state.

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


async def create_sdp_migration_dependency(config, dataproduct_key: Flow.Key):
    """Create migration dependency (no state yet)."""
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


def get_pvc_subpath(config: Config, key: Flow.Key) -> Path:
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

    data_dir: PVCPath | PurePath = flow.sink.data_dir
    if not isinstance(data_dir, PVCPath):
        raise TypeError("only PVCPath supported for flow data_dir.")

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


def log_configdb_backend_details(config: Config) -> None:
    """Log backend and environment details for the SDP ConfigDB connection."""
    backend = getattr(config, "_backend", None)

    sdp_backend = os.getenv("SDP_CONFIG_BACKEND")
    sdp_host = os.getenv("SDP_CONFIG_HOST", "etcd")
    sdp_port = os.getenv("SDP_CONFIG_PORT", "2379")
    sdp_path = os.getenv("SDP_CONFIG_PATH")

    os.environ["SDP_CONFIG_HOST"] = sdp_host  # make sure that this is in sync

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

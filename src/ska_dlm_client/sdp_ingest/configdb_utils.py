# flake8: ignore=DAR101
"""Shared helper functions for the ConfigDB dependency lifecycle."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from ska_sdp_config import Config, ConfigCollision
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


def get_data_product_dir(config: Config, key: Flow.Key) -> Path:
    """
    Resolve the container path to the data-product directory for a Flow key.

    This uses `Flow.sink.data_dir`, which is a `PVCPath | AnyPurePath`.
    For `PVCPath`, `str(data_dir)` is `pvc_mount_path / pvc_subpath`.
    For example::

        PVCPath(
            pvc_mount_path="/data",
            pvc_subpath="product/<eb>/ska-sdp/<pb>",
        )

    The returned value is `Path("/data/product/<eb>/ska-sdp/<pb>")`.
    """
    flow: Flow | None
    for txn in config.txn():
        flow = txn.flow.get(key)
        if flow is None:
            msg = f"Flow key not found: {key}"
            raise KeyError(msg)
    assert isinstance(flow, Flow)

    if not isinstance(flow.sink, DataProduct):
        raise TypeError(f"Expected data product key: {key}")

    return Path(str(flow.sink.data_dir))


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

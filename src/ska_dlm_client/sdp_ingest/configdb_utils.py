"""Shared helper functions for the ConfigDB dependency lifecycle."""

from __future__ import annotations

import logging
from typing import Optional

from ska_sdp_config import ConfigCollision
from ska_sdp_config.entity.flow import Dependency, Flow

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
        The Dependency object, or None if required fields are missing.

    Notes:
        - `dep_kind` is the sink/destination identifier (must match [A-Za-z0-9-]{1,96}).
        - `origin` identifies who issued the lock.
    """
    pb_id = getattr(product_key, "pb_id", None)
    flow_name = getattr(product_key, "name", None)

    if not pb_id or not flow_name:
        logger.info("Cannot build dependency for %s: missing pb_id or name", product_key)
        return None

    return Dependency(
        key=Dependency.Key(
            pb_id=pb_id,  # PB that produced the flow being locked
            kind=dep_kind,  # Kind of flow that is depended on
            name=flow_name,  # Data product name
            origin=origin,  # who is placing the lock
        ),
        expiry_time=expiry_time,
        description=description,
    )


async def create_sdp_migration_dependency(config, dataproduct_key: Flow.Key):
    """Create migration dependency."""
    # TODO: Call dlm to initialize/register data item
    # create DLM dependency (no state yet)
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


def log_flow_dependencies(txn, key: Flow.Key) -> None:
    """Log any flow-level dependencies (locks) for this product (any kind/origin)."""
    pb_id = getattr(key, "pb_id", None)
    name = getattr(key, "name", None)
    if not pb_id or not name:
        logger.info("Data-product %s missing pb_id or name; cannot inspect flow dependencies", key)
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
            f"(pb_id={dkey.pb_id}, kind={getattr(dkey,'kind',None)}, "
            f"name={dkey.name}, origin={getattr(dkey,'origin',None)}, "
            f"status={status}, expiry_time={expiry_time}, description={description})"
        )

    logger.info("Flow dependencies for %s/%s: %s", pb_id, name, "; ".join(entries))


def update_dependency_state(txn, dep: Dependency, status: str = "WORKING") -> None:
    """Create or update the dependency's state to the given status."""
    try:
        txn.dependency.state(dep).create({"status": status})
    except ConfigCollision:
        txn.dependency.state(dep).update({"status": status})

"""Configuration Database watcher client."""

from __future__ import annotations

import logging
import threading
from abc import ABCMeta
from collections.abc import AsyncIterator, Generator
from contextlib import AbstractAsyncContextManager
from typing import Optional

import athreading
from overrides import override
from ska_sdp_config import Config
from ska_sdp_config.entity import Script
from ska_sdp_config.entity.flow import Dependency, Flow

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

DLM_SCRIPT = Script.Key(kind="batch", name="dlm_copy", version="0.0.0")  # WIP


def watch_dataproduct_status(config: Config, status: str, *, include_existing: bool):
    """Create AsyncGenerator for fetching existing and updated Flow status events.

    Args:
        config: configuration database client.
        status: desired status event.
        include_existing: first yield existing dataproduct keys with matching status.
    """
    return DataProductStatusWatcher(config, status, include_existing)


class DataProductStatusWatcher(
    AbstractAsyncContextManager["DataProductStatusWatcher"],
    AsyncIterator[tuple[Flow.Key, str]],
    metaclass=ABCMeta,
):
    """AsyncGenerator for fetching existing and updated Flow status events.

    Args:
        config: configuration database client.
        status: desired status event.
        include_existing: first yield existing dataproduct keys with matching status.
    """

    def __init__(self, config: Config, status: str, include_existing=True):
        """Initialize."""
        self._status = status
        self._include_existing = include_existing
        self.__config = config
        self.__trigger = lambda: None
        self.__aiter = self.__awatch()
        self.__stopped = threading.Event()

    @override
    async def __aenter__(self):
        await self.__aiter.__aenter__()  # pylint: disable=no-member
        return self

    @override
    async def __aexit__(self, *exc_info):
        self.__stopped.set()
        self.__trigger()
        await self.__aiter.__aexit__(*exc_info)  # pylint: disable=no-member

    @override
    async def __anext__(self) -> tuple[Flow.Key, str]:
        return await self.__aiter.__anext__()  # pylint: disable=no-member

    def _get_existing_data_products(self):
        keys = []
        for txn in self.__config.txn():
            keys = txn.flow.list_keys(kind="data-product")
        return keys

    def _check_and_log_dependencies(self, txn, key: Flow.Key) -> None:
        """Log the producing PB's dependencies (if any) for a given data-product key."""
        pb_id = getattr(key, "pb_id", None)
        if pb_id is None:
            logger.info(
                "Data-product %s has no pb_id on its key; cannot inspect PB dependencies", key
            )
            return

        pb = txn.processing_block.get(pb_id)
        if pb is None:
            logger.info("PB %s not found; cannot inspect dependencies", pb_id)
            return

        deps = pb.dependencies or []
        if not deps:
            logger.info("PB %s has no dependencies", pb_id)
            return

        dep_str = ", ".join(f"{d.pb_id} (kind={getattr(d, 'kind', [])})" for d in deps)
        logger.info("PB %s dependencies: %s", pb_id, dep_str)

    @staticmethod
    def _create_dlm_dependency(
        product_key: Flow.Key,
        *,
        dep_kind: str = "dlm-copy",
        origin: str = "dlm-client",
        expiry_time: int = -1,
        description: Optional[str] = "DLM: lock data-product for copy",
    ) -> Optional[Dependency]:
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
                kind=dep_kind,  # sink kind (e.g. "dlm-copy")
                name=flow_name,  # the data-product's flow name
                origin=origin,  # who is placing the lock
            ),
            expiry_time=expiry_time,
            description=description,
        )

    def _set_dependency_state(self, txn, dep: Dependency, status: str = "WORKING") -> None:
        """Persist the dependency's state (e.g. when migration starts).

        TODO: handle collisions (use update() if state already exists).
        """
        txn.dependency.state(dep).create({"status": status})

    # pylint: disable=too-many-nested-blocks
    @athreading.iterate
    def __awatch(self) -> Generator[Flow.Key, str, None, None]:  # noqa: C901
        """Watcher loop that yields matching data-product Flow status events.

        - Runs synchronously (wrapped by athreading.iterate).
        - Scans ConfigDB for 'data-product' Flow keys and reads their state.
        - Yields (Flow.Key, status) when status == self._status.
        - Honours include_existing by skipping pre-existing keys via ignored_keys.
        - For each match, logs PB dependencies and creates a DLM dependency (empty state).
        """
        ignored_keys = [] if self._include_existing else self._get_existing_data_products()

        for watcher in self.__config.watcher():
            # must break synchronous iterator on context exit
            if self.__stopped.is_set():
                break
            self.__trigger = watcher.trigger

            states = []
            for txn in watcher.txn():
                try:
                    # NOTE: with include_existing, this will be very slow if
                    # dependencies are not removed from the database
                    for key in txn.flow.list_keys(kind="data-product"):
                        if key not in ignored_keys:
                            state = txn.flow.state(key).get()
                            if status := state.get("status"):
                                if status == self._status:
                                    states.append((key, status))
                                    # TODO: Call dlm to initialize data item
                                    # --- log existing PB dependencies for this data-product ---
                                    self._check_and_log_dependencies(txn, key)
                                    # --- create DLM dependency (no state yet) ---
                                    dep = self._create_dlm_dependency(
                                        key,
                                        dep_kind="dlm-copy",
                                        origin="dlm-client",
                                        expiry_time=-1,
                                        description="DLM: lock data-product for copy",
                                    )
                                    if dep is not None:
                                        # Persist the dependency without a status for now
                                        # matches ska-sdp-config/tests/test_dependency.py pattern
                                        txn.dependency.state(dep).create({})
                                        logger.info(
                                            "Created DLM dependency for %s/%s",
                                            dep.key.pb_id,
                                            dep.key.name,
                                        )
                                    ignored_keys.append(key)
                except Exception:
                    logger.exception("Unexpected watcher exception")
                    raise
            yield from states

"""Configuration Database watcher client."""

from __future__ import annotations

import logging
import threading
from abc import ABCMeta
from collections.abc import AsyncIterator, Generator
from contextlib import AbstractAsyncContextManager
from typing import Any, TypeAlias

import athreading
from overrides import override
from ska_sdp_config import Config
from ska_sdp_config.entity.flow import Flow

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

DataProductKeyState: TypeAlias = tuple[Flow.Key, dict[str, Any]]


def watch_dataproduct_status(config: Config, status: str, *, include_existing: bool):
    """Create AsyncGenerator for fetching existing and updated Flow status events.

    Args:
        config: configuration database client.
        status: desired status event, e.g., COMPLETED
        include_existing: first yield existing dataproduct keys with matching status.
    """
    return DataProductStatusWatcher(config, status, include_existing)


class DataProductStatusWatcher(
    AbstractAsyncContextManager["DataProductStatusWatcher"],
    AsyncIterator[DataProductKeyState],
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
    async def __anext__(self) -> DataProductKeyState:
        return await self.__aiter.__anext__()  # pylint: disable=no-member

    def _get_existing_data_products(self):
        keys = []
        for txn in self.__config.txn():
            keys = txn.flow.list_keys(kind="data-product")
        return keys

    # pylint: disable=too-many-nested-blocks
    @athreading.iterate
    def __awatch(self) -> Generator[DataProductKeyState, None, None]:  # noqa: C901
        """Watcher loop that yields matching data-product Flow status events.

        - Runs synchronously (wrapped by athreading.iterate).
        - Scans ConfigDB for 'data-product' Flow keys and reads their state.
        - Yields (Flow.Key, status) when status == self._status.
        - Honours include_existing by skipping pre-existing keys via ignored_keys.
        - For each match, logs PB dependencies and creates a DLM dependency (empty state).

        typing.Generator[YIELD, SEND, RETURN]
        - We yield DataProductKeyState (tuple[Flow.Key, dict[...]])
        - We never .send() into this generator -> SEND is None
        - The generator doesn't return a final value -> RETURN is None
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
                            if state := txn.flow.state(key).get():
                                if state.get("status") == self._status:
                                    states.append((key, state))
                                    ignored_keys.append(key)
                except Exception:
                    logger.exception("Unexpected watcher exception")
                    raise
            yield from states

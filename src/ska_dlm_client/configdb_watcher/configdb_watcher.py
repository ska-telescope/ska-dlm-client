"""Application to watch the configuration database for Flows and call DLM."""

from __future__ import annotations

import logging
import threading
from abc import ABCMeta
from collections.abc import AsyncIterator, Generator
from contextlib import AbstractAsyncContextManager
from typing import Any, TypeAlias, cast

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

    def _get_data_products_from_persist_flows(self, txn) -> list[Flow.Key]:
        """Return data-product Flow.Keys referenced by data-product-persist flows."""
        keys = []
        for _persist_flow_key, persist_flow in txn.flow.list_values(kind="data-product-persist"):
            persist_flow = cast(Flow, persist_flow)

            for source in persist_flow.sources:
                if source.function != "ska-data-lifecycle:ingest":
                    logger.debug(
                        "Skipping persist source: function is %s, "
                        "expected 'ska-data-lifecycle:ingest'",
                        source.function,
                    )
                    continue

                if not isinstance(source.uri, Flow.Key):
                    logger.debug(
                        "Skipping persist source: source.uri is %s, expected Flow.Key",
                        source.uri,
                    )
                    continue

                if source.uri.kind != "data-product":
                    logger.debug(
                        "Skipping persist source: source.uri kind is %s, "
                        "expected 'data-product'",
                        source.uri.kind,
                    )
                    continue

                keys.append(source.uri)

        return keys

    # pylint: disable=too-many-nested-blocks
    @athreading.iterate
    def __awatch(self) -> Generator[tuple[Flow.Key, dict], None, None]:  # noqa: C901
        """Watcher loop that yields matching data-product Flow status events via persist flows.

        - Runs synchronously (wrapped by athreading.iterate).
        - Scans ConfigDB for 'data-product-persist' flows and follows ingest sources.
        - Extracts related 'data-product' Flow.Keys from persist_flow.sources.
        - Yields (Flow.Key, state) when state["status"] == self._status.
        - include_existing=True: also process existing matching flows.

        typing.Generator[YIELD, SEND, RETURN]
        - YIELD: tuple[Flow.Key, dict]
        - SEND: None
        - RETURN: None
        """
        ignored_keys = []  # TODO: look into using a set instead of a list
        if not self._include_existing:
            for txn in self.__config.txn():
                ignored_keys.extend(self._get_data_products_from_persist_flows(txn))

        for watcher in self.__config.watcher():
            if self.__stopped.is_set():
                break
            self.__trigger = watcher.trigger

            states = []
            for txn in watcher.txn():
                try:
                    for key in self._get_data_products_from_persist_flows(txn):
                        if key not in ignored_keys:
                            if state := txn.flow.state(key).get():
                                if state.get("status") == self._status:
                                    states.append((key, state))
                                    ignored_keys.append(key)

                except Exception:
                    logger.exception("Unexpected watcher exception")
                    raise

            yield from states

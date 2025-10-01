"""Configuration Database watcher client."""

import logging
import threading
from abc import ABCMeta
from collections.abc import AsyncIterator, Generator
from contextlib import AbstractAsyncContextManager

import athreading
from overrides import override
from ska_sdp_config import Config
from ska_sdp_config.entity import Dependency

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


def watch_dependency_status(config: Config, status: str):
    """Create AsyncGenerator for fetching existing and updated Dependency status events.

    Args:
        config: configuration database client.
        status: desired status event.
    """
    return DependencyStatusWatcher(config, status)


# pylint: disable=no-member
class DependencyStatusWatcher(
    AbstractAsyncContextManager["DependencyStatusWatcher"],
    AsyncIterator[Dependency.Key, str],
    metaclass=ABCMeta,
):
    """AsyncGenerator for fetching existing and updated Dependency status events.

    Args:
        config: configuration database client.
        status: desired status event.
    """

    def __init__(self, config: Config, status: str):
        """Initialize."""
        self._status = status
        self.__config = config
        self.__trigger = lambda: None
        self.__aiter = self.__awatch()
        self.__stopped = threading.Event()

    @override
    async def __aenter__(self):
        await self.__aiter.__aenter__()
        return self

    @override
    async def __aexit__(self, *exc_info):
        self.__stopped.set()
        self.__trigger()
        await self.__aiter.__aexit__(*exc_info)

    @override
    async def __anext__(self) -> tuple[Dependency.Key, str]:
        return await self.__aiter.__anext__()

    # pylint: disable=too-many-nested-blocks
    @athreading.iterate
    def __awatch(self) -> Generator[Dependency.Key, str, None, None]:
        for watcher in self.__config.watcher():
            # must break synchronous iterator on context exit
            if self.__stopped.is_set():
                break
            self.__trigger = watcher.trigger

            states = []
            sent_keys = []
            for txn in watcher.txn():
                try:
                    # NOTE: this will be very slow if dependencies are
                    # not removed from the database
                    for key in txn.dependency.list_keys():
                        if key not in sent_keys:
                            dependency_state = txn.dependency.state(key).get()
                            if status := dependency_state.get("status"):
                                if status == self._status:
                                    states.append((key, status))
                                    sent_keys.append(key)
                except Exception:
                    logger.exception("Unexpected dependency watcher exception")
                    raise
            yield from states

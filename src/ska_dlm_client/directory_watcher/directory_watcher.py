"""Class to perform directory watching tasks."""

import asyncio
import logging
import os
from abc import ABC, abstractmethod

from watchdog.events import DirCreatedEvent, FileCreatedEvent, FileSystemEvent
from watchdog.observers.api import EventQueue, ObservedWatch
from watchdog.observers.polling import DEFAULT_EMITTER_TIMEOUT, BaseObserver, PollingEmitter
from watchfiles import Change, awatch

from ska_dlm_client.directory_watcher.config import Config
from ska_dlm_client.directory_watcher.registration_processor import RegistrationProcessor
from ska_dlm_client.directory_watcher.watcher_event_handler import WatcherEventHandler

logger = logging.getLogger(__name__)


class LStatPollingEmitter(PollingEmitter):
    """Emitter that polls a directory to detect filesystem changes using `os.lstat`.

    NOTE: As of December 2024 a fix for this seems to be in the works but not yet available.
    """

    def __init__(
        self,
        event_queue: EventQueue,
        watch: ObservedWatch,
        timeout: float = DEFAULT_EMITTER_TIMEOUT,
        event_filter: list[type[FileSystemEvent]] | None = None,
    ) -> None:
        """Take in the same parameters as `PollingEmitter` but change stat to os.lstat."""
        super().__init__(
            event_queue=event_queue,
            watch=watch,
            timeout=timeout,
            event_filter=event_filter,
            stat=os.lstat,
        )


class DirectoryWatcher(ABC):  # pylint: disable=too-few-public-methods
    """Class for the running of the directory_watcher."""

    def __init__(self, config: Config, registration_processor: RegistrationProcessor):
        """Initialise with the given Config."""
        self._config = config
        self._event_handler = WatcherEventHandler(
            config=config, registration_processor=registration_processor
        )

    @abstractmethod
    async def watch(self) -> None:
        """Abstract method to watch, wait and take action on directory entry changes."""
        raise NotImplementedError("Method must be implemnted.")


class PollingDirectoryWatcher(DirectoryWatcher):  # pylint: disable=too-few-public-methods
    """DirectoryWatcher using filesystem polling."""

    async def watch(self):
        """Watch for changes in the defined directory and process each change found."""
        logger.info("with config parameters %s", self._config)
        logger.info("starting to watchdog %s", self._config.directory_to_watch)
        logger.info(
            "NOTE: MyPollingObserver has recursive=False, in case this matters in the future."
        )
        observer = BaseObserver(LStatPollingEmitter)
        observer.schedule(
            event_handler=self._event_handler,
            path=self._config.directory_to_watch,
            recursive=False,
        )
        observer.start()
        try:
            while True:
                # What is really needed here is "asyncio suspend" as not expected to ever return
                await asyncio.sleep(1)
        except (asyncio.CancelledError, KeyboardInterrupt):
            observer.stop()
            observer.join()
            raise


class INotifyDirectoryWatcher(DirectoryWatcher):  # pylint: disable=too-few-public-methods
    """Directory watcher using INotify filesytem events."""

    def _process_directory_entry_change(self, entry: tuple[Change, str]):
        """Take action for the directory entry Change type given.

        This will pass off the change to a `WatcherEventHandler`.
        """
        logger.info("in do _handle_directory_entry_change %s", entry)
        change_type = entry[0]
        change_path = entry[1]
        if change_type is Change.added:
            if os.path.isdir(change_path):
                event = DirCreatedEvent(src_path=change_path)
            else:
                event = FileCreatedEvent(src_path=change_path)
            self._event_handler.on_created(event)
        logger.info("Ignoring %s ", change_type)

    async def watch(self):
        """Watch for changes in the defined directory and process each change found."""
        logger.info("with config parameters %s", self._config)
        logger.info("starting to watch %s", self._config.directory_to_watch)
        logger.info(
            "NOTE: watchfiles.awatch has recursive=False, in case this matters in the futuer."
        )
        async for changes in awatch(
            self._config.directory_to_watch, recursive=False
        ):  # type: Set[tuple[Change, str]]
            for change in changes:
                logger.info("in main %s", change)
                self._process_directory_entry_change(change)

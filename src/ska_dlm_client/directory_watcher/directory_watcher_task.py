"""Class to perform directory watching tasks."""

import logging
import os

from watchdog.events import (
    DirCreatedEvent,
    DirDeletedEvent,
    DirModifiedEvent,
    DirMovedEvent,
    FileClosedEvent,
    FileClosedNoWriteEvent,
    FileCreatedEvent,
    FileDeletedEvent,
    FileModifiedEvent,
    FileMovedEvent,
    FileOpenedEvent,
    FileSystemEvent,
    FileSystemEventHandler,
)
from watchdog.observers.api import EventQueue, ObservedWatch
from watchdog.observers.polling import (
    DEFAULT_EMITTER_TIMEOUT,
    DEFAULT_OBSERVER_TIMEOUT,
    BaseObserver,
    PollingEmitter,
)
from watchfiles import Change, awatch

from ska_dlm_client.directory_watcher.config import Config
from ska_dlm_client.directory_watcher.registration_processor import RegistrationProcessor

logger = logging.getLogger(__name__)


class MyPollingEmitter(PollingEmitter):
    """Extends ```PollingEmitter``` to use os.lstat instead of os.stat.

    As of December 2024 a fix for this seems to be in the works but not yet available.
    """

    def __init__(
        self,
        event_queue: EventQueue,
        watch: ObservedWatch,
        timeout: float = DEFAULT_EMITTER_TIMEOUT,
        event_filter: list[type[FileSystemEvent]] | None = None,
    ) -> None:
        """Take in the same parameters as ```PollingEmitter``` but change stat to os.lstat."""
        super().__init__(
            event_queue=event_queue,
            watch=watch,
            timeout=timeout,
            event_filter=event_filter,
            stat=os.lstat,
        )


class MyPollingObserver(BaseObserver):
    """Class replacing ```PollingObserver``` for the use of a custom ```PollingEmitter```."""

    def __init__(self, *, timeout: float = DEFAULT_OBSERVER_TIMEOUT) -> None:
        """Instantiate class using our custom ```PollingEmitter```."""
        super().__init__(MyPollingEmitter, timeout=timeout)


class WatcherEventHandler(FileSystemEventHandler):
    """Either log or take action for all the possible events.

    Originally based on ```LoggingEventHandler```.
    """

    def __init__(
        self, config: Config, watcher_registration_processor: RegistrationProcessor
    ) -> None:
        """Initialise with the required config and registration_processor."""
        self._config = config
        self._registration_processor = watcher_registration_processor

    def _ignore_event(self, event: FileSystemEvent) -> bool:
        return self._config.status_file_full_filename == event.src_path

    def on_moved(self, event: DirMovedEvent | FileMovedEvent) -> None:
        """Take action when a moved event is captured."""
        super().on_moved(event)
        what = "directory" if event.is_directory else "file"
        logger.info(
            "Type %s: Moved %s: from %s to %s",
            event.event_type,
            what,
            event.src_path,
            event.dest_path,
        )

    def on_created(self, event: DirCreatedEvent | FileCreatedEvent) -> None:
        """Take action when a create event is captured."""
        super().on_created(event)
        what = "directory" if event.is_directory else "file"
        logger.info("Created %s: %s", what, event.src_path)
        if self._ignore_event(event):
            return
        full_path = event.src_path
        relative_path = full_path.replace(f"{self._config.directory_to_watch}/", "")
        self._registration_processor.add_path(full_path=full_path, relative_path=relative_path)

    def on_deleted(self, event: DirDeletedEvent | FileDeletedEvent) -> None:
        """Take action when a delete event is captured."""
        super().on_deleted(event)
        what = "directory" if event.is_directory else "file"
        logger.info("Deleted %s: %s", what, event.src_path)

    def on_modified(self, event: DirModifiedEvent | FileModifiedEvent) -> None:
        """Take action when a modified event is captured."""
        super().on_modified(event)
        what = "directory" if event.is_directory else "file"
        logger.info("Modified %s: %s", what, event.src_path)

    def on_closed(self, event: FileClosedEvent) -> None:
        """Take action when a closed event is captured."""
        super().on_closed(event)
        logger.info("Closed modified file: %s", event.src_path)

    def on_closed_no_write(self, event: FileClosedNoWriteEvent) -> None:
        """Take action when a closed with no write event is captured."""
        super().on_closed_no_write(event)
        logger.info("Closed read file: %s", event.src_path)

    def on_opened(self, event: FileOpenedEvent) -> None:
        """Take action when an open event is captured."""
        super().on_opened(event)
        logger.info("Opened file: %s", event.src_path)


class DirectoryWatcher:
    """Class for the running of the directory_watcher."""

    def __init__(self, config: Config, watcher_registration_processor: RegistrationProcessor):
        """Initialise with the given Config."""
        self._config = config
        self._event_handler = WatcherEventHandler(
            config=config, watcher_registration_processor=watcher_registration_processor
        )

    async def start_polling_watch(self):
        """Take action for the directory entry Change type given."""
        # from watchdog.observers.polling import PollingObserver
        # logger.info("with config parameters %s", self._config)
        # logger.info("starting to watchdog %s", self._config.directory_to_watch)
        logger.info(
            "NOTE: MyPollingObserver has recursive=False, in case this matters in the futuer."
        )
        observer = MyPollingObserver()
        # observer.schedule(event_handler, self._config.directory_to_watch, recursive=False)
        observer.schedule(
            event_handler=self._event_handler,
            path=self._config.directory_to_watch,
            recursive=False,
        )
        observer.start()
        # try:
        #    while True:
        #        time.sleep(1)
        # except KeyboardInterrupt:
        #    observer.stop()
        # observer.join()

    def _handle_directory_entry_change(self, entry: tuple[Change, str]):
        """Take action for the directory entry Change type given.

        This will pass off the change to a ```WatcherEventHandler```.
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
        # TODO: Change.deleted Change.modified mayh need support

    async def start_inotify_watch(self):
        """Start watching the given directory."""
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
                self._handle_directory_entry_change(change)

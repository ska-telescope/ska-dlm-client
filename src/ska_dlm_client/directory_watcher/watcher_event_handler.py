"""Class to process watcher directory change events."""

import logging
import os.path

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

from ska_dlm_client.directory_watcher.config import WatcherConfig
from ska_dlm_client.directory_watcher.registration_processor import RegistrationProcessor

logger = logging.getLogger(__name__)


class WatcherEventHandler(FileSystemEventHandler):
    """Either log or take action for all the possible events.

    Originally based on `LoggingEventHandler`.
    """

    def __init__(
        self, config: WatcherConfig, registration_processor: RegistrationProcessor
    ) -> None:
        """Initialise with the required config and registration_processor."""
        self._config = config
        self._registration_processor = registration_processor

    def _ignore_event(self, event: FileSystemEvent) -> bool:
        """Determine if an event should be ignored.

        An event is ignored if:
        - It targets a directory whose name starts with a dot ('.'), or
        - The event's path matches the configured status file path exactly.
        """
        basename = os.path.basename(event.src_path)
        logger.info("basename is %s", basename)
        if event.is_directory and os.path.basename(event.src_path).startswith("."):
            return True
        return self._config.status_file_absolute_path == event.src_path

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
        logger.info("event is %s and is_dir %s", event, event.is_directory)
        what = "directory" if event.is_directory else "file"
        logger.info("In event 'created' for %s: %s", what, event.src_path)
        if self._ignore_event(event):
            return
        absolute_path = event.src_path
        path_rel_to_watch_dir = absolute_path.replace(f"{self._config.directory_to_watch}/", "")
        self._registration_processor.add_path(
            absolute_path=absolute_path, path_rel_to_watch_dir=path_rel_to_watch_dir
        )

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

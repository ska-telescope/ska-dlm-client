"""Class to perform directory watching tasks."""

import logging

from watchfiles import Change, awatch

from ska_dlm_client.directory_watcher.config import Config
from ska_dlm_client.directory_watcher.registration_processor import RegistrationProcessor

logger = logging.getLogger(__name__)


class DirectoryWatcher:
    """Class for the running of the directory_watcher."""

    def __init__(self, config: Config, watcher_registration_processor: RegistrationProcessor):
        """Initialise with the given Config."""
        self._config = config
        self._registration_processor = watcher_registration_processor

    def process_directory_entry_change(self, entry: tuple[Change, str]):
        """TODO: Test function currently."""
        logger.info("in do process_directory_entry_change %s", entry)
        change_type = entry[0]
        full_path = entry[1]
        relative_path = full_path.replace(f"{self._config.directory_to_watch}/", "")
        if self._config.status_file_full_filename == full_path:
            return
        if change_type is Change.added:
            self._registration_processor.add_path(full_path=full_path, relative_path=relative_path)
        # TODO: Change.deleted Change.modified mayh need support

    async def start(self):
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
                self.process_directory_entry_change(change)

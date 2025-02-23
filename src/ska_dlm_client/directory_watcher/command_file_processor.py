"""Class to monitor command files and take action as required."""

import logging
import os

from ska_dlm_client.directory_watcher.registration_processor import RegistrationProcessor

logger = logging.getLogger(__name__)

COMMAND_ADD_FILENAME = ".data_products_to_add"


class CommandFileProcessor:
    """Monitor command files and take action as required."""

    command_file: str
    registration_processor: RegistrationProcessor
    watch_dir: str
    files: list[str]

    def __init__(self, registration_processor: RegistrationProcessor):
        """Init the class."""
        self.watch_dir = registration_processor.get_cofnig().directory_to_watch
        self.command_file = os.path.join(self.watch_dir, COMMAND_ADD_FILENAME)

    def _validate_file_names(self, file_names: list[str]) -> list[str]:
        """Validate each file name to pick out any obviously incorrectly formatted names."""
        # TODO Include a check that file exists
        new_file_list: list[str] = []
        for file_name in file_names:
            if not file_name.startswith("/"):
                new_file_list.append(file_name)
        return new_file_list

    def read_from_file(self):
        """Load the list of DirectoryWatcherEntry from a file in JSON format."""
        with open(self.command_file, "r", encoding="utf-8") as cmd_file:
            files = cmd_file.readlines()
            self.files = self._validate_file_names(file_names=files)

    def process_files(self):
        """Process the list of files."""
        for file_name in self.files:
            self.registration_processor.add_path(
                absolute_path=os.path.join(self.watch_dir, file_name),
                path_rel_to_watch_dir=file_name,
            )

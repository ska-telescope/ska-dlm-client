"""Look after the entries and the cached file for them."""

import json
from pathlib import Path, PosixPath


class DirectoryWatcherEntry:  # pylint: disable=too-few-public-methods
    """An individual entry."""

    def __init__(
        self,
        file_or_directory: PosixPath,
        dlm_storage_id: str,
        dlm_registration_id: str,
        time_registered: float,
    ):
        """Initialise this object."""
        self.directory_entry = file_or_directory
        self.dlm_storage_id = dlm_storage_id
        self.dlm_regsitration_id = dlm_registration_id
        self.time_registered = time_registered


class DirectoryWatcherEntries(list):
    """The list of entries to be managed."""

    def __init__(self, entries_file: Path, reload_from_cache: bool):
        """Init the class."""
        self.directory_watcher_entries = [DirectoryWatcherEntry]
        self.entries_file = entries_file
        if reload_from_cache:
            self.read_from_file()

    def append(self, entry: DirectoryWatcherEntry):
        """Override list append."""
        self.directory_watcher_entries.append(entry)

    def save_to_file(self):
        """Save the list of DirectoryWatcherEntry to a file in JSON format."""
        with open(self.entries_file, "w", encoding="utf-8") as the_file:
            json.dump(self.directory_watcher_entries, the_file, indent=4)

    def read_from_file(self):
        """Load the list of DirectoryWatcherEntry from a file in JSON format."""
        with open(self.entries_file, "r", encoding="utf-8") as the_file:
            self.directory_watcher_entries = json.load(the_file)

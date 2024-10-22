#
import json
from pathlib import Path, PosixPath

from ska_dlm_client.directory_watcher.directory_monitor import directory_watcher_entries


class DirectoryWatcherEntry:
    def __init__(
        self,
        file_or_directory: PosixPath,
        dlm_storage_id: str,
        dlm_registration_id: str,
        time_registered: float,
    ):
        self.directory_entry = file_or_directory
        self.dlm_storage_id = dlm_storage_id
        self.dlm_regsitration_id = dlm_registration_id
        self.time_registered = time_registered


class DirectoryWatcherEntries(list):

    def __init__(self, entries_file: Path, reload_from_cache: bool):
        self.directory_watcher_entries = [DirectoryWatcherEntry]
        self.entries_file = entries_file
        if reload_from_cache:
            self.read_from_file()

    def append(self, entry: DirectoryWatcherEntry):
        """
        Override list append.
        """
        directory_watcher_entries.append(entry)

    def save_to_file(self):
        """
        Save the list of DirectoryWatcherEntry to a file in JSON format.
        """
        with open(self.entries_file, "w") as the_file:
            json.dump(self.objects, the_file, indent=4)

    def read_from_file(self):
        """
        Load the list of DirectoryWatcherEntry from a file in JSON format.
        """
        with open(self.entries_file, "r") as the_file:
            self.directory_watcher_entries = json.load(the_file)

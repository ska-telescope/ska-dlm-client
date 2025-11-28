"""Look after the entries and the cached file for them."""

import dataclasses
import json


class DataclassJSONEncoder(json.JSONEncoder):
    """JSON encoder for dataclasses."""

    def default(self, o):
        """Override JSON default function."""
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


@dataclasses.dataclass
class DirectoryWatcherEntry:
    """An individual entry."""

    file_or_directory: str
    dlm_storage_name: str
    dlm_registration_id: str
    time_registered: float


class DirectoryWatcherEntries:
    """The list of entries to be managed."""

    directory_watcher_entries: list[DirectoryWatcherEntry]
    entries_file: str
    write_directory_entries_file: bool

    def __init__(
        self, entries_file: str, reload_from_status_file: bool, write_directory_entries_file: bool
    ):
        """Init the class."""
        self.directory_watcher_entries = []
        self.entries_file = entries_file
        self.write_directory_entries_file = write_directory_entries_file
        if reload_from_status_file:
            self.read_from_file()

    def add(self, entry: DirectoryWatcherEntry):
        """Override list append."""
        self.directory_watcher_entries.append(entry)

    def save_to_file(self):
        """Save the list of DirectoryWatcherEntry to a file in JSON format."""
        if self.write_directory_entries_file:
            with open(self.entries_file, "w", encoding="utf-8") as the_file:
                json.dump(
                    self.directory_watcher_entries, the_file, indent=4, cls=DataclassJSONEncoder
                )

    def read_from_file(self):
        """Load the list of DirectoryWatcherEntry from a file in JSON format."""
        with open(self.entries_file, "r", encoding="utf-8") as the_file:
            self.directory_watcher_entries = json.load(the_file)

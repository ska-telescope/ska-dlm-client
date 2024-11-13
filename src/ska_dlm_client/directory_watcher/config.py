"""Class to hold the configuration used by the directory_watcher package."""

from ska_dlm_client.directory_watcher.directory_watcher_entries import DirectoryWatcherEntries
from ska_dlm_client.openapi import configuration
from ska_dlm_client.openapi.configuration import Configuration

STATUS_FILE_FILENAME = ".directory_watcher_status.run"
DIRECTORY_IS_MEASUREMENT_SET_SUFFIX = ".ms"


class Config:  # pylint: disable=too-few-public-methods, disable=too-many-instance-attributes
    """Running configuration of the SKA DLM client directory watcher."""

    directory_to_watch: str
    ingest_server_url: str
    storage_name: str
    reload_status_file: bool
    status_file_full_filename: str
    use_status_file: bool
    directory_watcher_entries: DirectoryWatcherEntries
    ingest_configuration: Configuration

    def __init__(  # pylint: disable=too-many-arguments, disable=too-many-positional-arguments
        self,
        directory_to_watch: str,
        ingest_server_url: str,
        storage_name: str,
        reload_status_file: bool = False,
        status_file_full_filename: str = STATUS_FILE_FILENAME,
        use_status_file: bool = False,
    ):
        """Init the values required for correct operation of directory_watcher."""
        self.directory_to_watch = directory_to_watch
        self.ingest_server_url = f"{ingest_server_url}"
        self.storage_name = storage_name
        self.reload_status_file = reload_status_file
        self.status_file_full_filename = status_file_full_filename
        self.use_status_file = use_status_file
        self.directory_watcher_entries = DirectoryWatcherEntries(
            entries_file=self.status_file_full_filename,
            reload_from_status_file=self.reload_status_file,
        )
        self.ingest_configuration = configuration.Configuration(host=self.ingest_server_url)

    def __str__(self):
        """Create a string from this class."""
        return (
            f"directory_to_watch {self.directory_to_watch}\n"
            f"ingest_server_url {self.ingest_server_url}\n"
            f"storage_name {self.storage_name}\n"
            f"reload_status_file {self.reload_status_file}\n"
            f"status_file_full_filename {self.status_file_full_filename}\n"
            f"use_stat_file {self.use_status_file}\n"
            f"ingest_configuration {self.ingest_configuration}\n"
            f"directory_watcher_entries {self.directory_watcher_entries}\n"
        )

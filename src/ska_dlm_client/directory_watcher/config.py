# pylint: disable=too-many-instance-attributes
"""Class to hold the configuration used by the directory_watcher package."""
from dataclasses import dataclass, field
import os.path

from ska_dlm_client.directory_watcher.directory_watcher_entries import DirectoryWatcherEntries
from ska_dlm_client.openapi.configuration import Configuration

@dataclass
class WatcherConfig:
    """Running configuration of the SKA DLM client directory watcher.

    This class holds all configuration parameters needed for the directory watcher
    to monitor directories and register data items with the DLM.
    """

    directory_to_watch: str
    ingest_url: str
    storage_name: str
    migration_url: str
    migration_destination_storage_name: str
    storage_url: str
    status_file_absolute_path: str
    storage_root_directory: str
    reload_status_file: bool
    ingest_configuration: Configuration = field(init=False)
    migration_configuration: Configuration = field(init=False)
    directory_watcher_entries: DirectoryWatcherEntries = field(init=False)
    use_status_file: bool = False
    rclone_access_check_on_register: bool = False
    ingest_register_path_to_add: str = field(init=False)
    perform_actual_ingest_and_migration: bool = True

    def __post_init__(self):
        self.directory_watcher_entries = DirectoryWatcherEntries(
            entries_file=self.status_file_absolute_path,
            reload_from_status_file=self.reload_status_file,
            write_directory_entries_file=self.use_status_file,
        )
        self.ingest_configuration = Configuration(host=self.ingest_url)
        self.ingest_register_path_to_add = os.path.relpath(
            path=self.directory_to_watch, start=self.storage_root_directory
        )            
        # Migration related options
        self.migration_configuration = Configuration(host=self.migration_url)

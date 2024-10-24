"""Class to hold the configuration used by the directory_watcher package."""

from ska_dlm_client.directory_watcher.directory_watcher_entries import DirectoryWatcherEntries
from ska_dlm_client.openapi.configuration import Configuration


class Config:  # pylint: disable=too-few-public-methods
    """Running configuration of the SKA DLM client directory watcher."""

    directory_to_watch: str
    status_file_full_filename: str
    reload_status_file: bool
    ingest_url: str
    storage_url: str
    ingest_configuration: Configuration
    storage_configuration: Configuration
    storage_id: str
    directory_watcher_entries: DirectoryWatcherEntries

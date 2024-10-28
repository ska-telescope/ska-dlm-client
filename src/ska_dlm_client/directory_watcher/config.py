"""Class to hold the configuration used by the directory_watcher package."""

from ska_dlm_client.directory_watcher.directory_watcher_entries import DirectoryWatcherEntries
from ska_dlm_client.openapi import configuration
from ska_dlm_client.openapi.configuration import Configuration

STATUS_FILE_FILENAME = ".directory_watcher_status.run"
INGEST_SERVICE_NAME = "ingest"
STORAGE_SERVICE_NAME = "storage"
INGEST_SERVICE_PORT = 8001
STORAGE_SERVICE_PORT = 8003


class Config:  # pylint: disable=too-few-public-methods, disable=too-many-instance-attributes
    """Running configuration of the SKA DLM client directory watcher."""

    directory_to_watch: str
    status_file_full_filename: str
    reload_status_file: bool
    storage_name: str
    ingest_url: str
    storage_url: str
    ingest_configuration: Configuration
    storage_configuration: Configuration
    directory_watcher_entries: DirectoryWatcherEntries

    def __init__(  # pylint: disable=too-many-arguments
        self,
        directory_to_watch: str,
        storage_name: str,
        server_url: str,
        reload_status_file: bool = True,
        ingest_service_name: str = INGEST_SERVICE_NAME,
        storage_service_name: str = STORAGE_SERVICE_NAME,
        ingest_service_port: int = INGEST_SERVICE_PORT,
        storage_service_port: int = STORAGE_SERVICE_PORT,
        status_file_full_filename: str = "",
    ):
        """Init the values required for correct operation of directory_watcher."""
        self.directory_to_watch = directory_to_watch
        self.status_file_full_filename = (
            f"{self.directory_to_watch}/{STATUS_FILE_FILENAME}"
            if status_file_full_filename == ""
            else status_file_full_filename
        )
        self.reload_status_file = reload_status_file
        self.storage_name = storage_name
        self.ingest_url = f"{server_url}:{ingest_service_port[ingest_service_name]}"
        self.storage_url = f"{server_url}:{storage_service_port[storage_service_name]}"
        self.ingest_configuration = configuration.Configuration(host=self.ingest_url)
        self.storage_configuration = configuration.Configuration(host=self.storage_url)
        self.directory_watcher_entries = DirectoryWatcherEntries(
            entries_file=self.status_file_full_filename, reload_from_cache=self.reload_status_file
        )

"""Class to hold the configuration used by the directory_watcher package."""

from ska_dlm_client.directory_watcher.directory_watcher_entries import DirectoryWatcherEntries
from ska_dlm_client.openapi import configuration
from ska_dlm_client.openapi.configuration import Configuration

STATUS_FILE_FILENAME = ".directory_watcher_status.run"
DIRECTORY_IS_MEASUREMENT_SET_SUFFIX = ".ms"
# Based on
# https://confluence.skatelescope.org/display/SWSI/ADR-55+Definition+of+metadata+for+data+management+at+AA0.5
METADATA_FILENAME = "ska-data-product.yaml"
METADATA_EXECUTION_BLOCK_KEY = "execution_block"


class Config:  # pylint: disable=too-few-public-methods, disable=too-many-instance-attributes
    """Running configuration of the SKA DLM client directory watcher."""

    directory_to_watch: str
    ingest_server_url: str
    storage_name: str
    reload_status_file: bool
    status_file_absolute_path: str
    use_status_file: bool
    directory_watcher_entries: DirectoryWatcherEntries
    ingest_configuration: Configuration

    def __init__(  # pylint: disable=too-many-arguments, disable=too-many-positional-arguments
        self,
        directory_to_watch: str,
        ingest_server_url: str,
        storage_name: str,
        register_dir_prefix: str,
        status_file_absolute_path: str,
        reload_status_file: bool = False,
        use_status_file: bool = False,
    ):
        """Init the values required for correct operation of directory_watcher."""
        self.directory_to_watch = directory_to_watch
        self.ingest_server_url = f"{ingest_server_url}"
        self.storage_name = storage_name
        self.register_dir_prefix = register_dir_prefix
        self.reload_status_file = reload_status_file
        self.status_file_absolute_path = status_file_absolute_path
        self.use_status_file = use_status_file
        self.directory_watcher_entries = DirectoryWatcherEntries(
            entries_file=self.status_file_absolute_path,
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
            f"status_file_absolute_path {self.status_file_absolute_path}\n"
            f"use_stat_file {self.use_status_file}\n"
            f"ingest_configuration {self.ingest_configuration}\n"
            f"directory_watcher_entries {self.directory_watcher_entries}\n"
        )

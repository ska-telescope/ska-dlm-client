# pylint: disable=invalid-name
"""Module-level constants used by the DLM client."""
from dataclasses import dataclass, field
import os.path

from ska_dlm_client.directory_watcher.directory_watcher_entries import DirectoryWatcherEntries
from ska_dlm_client.openapi.configuration import Configuration

STATUS_FILE_FILENAME = ".directory_watcher_status.run"
DIRECTORY_IS_MEASUREMENT_SET_SUFFIX = ".ms"
# Based on
# https://confluence.skatelescope.org/display/SWSI/ADR-55+Definition+of+metadata+for+data+management+at+AA0.5
METADATA_FILENAME = "ska-data-product.yaml"  # TODO: import from from ska_sdp_dataproduct_metadata
METADATA_EXECUTION_BLOCK_KEY = "execution_block"

# pylint: disable=too-many-instance-attributes
"""Class to hold the configuration used by the directory_watcher package."""
@dataclass
class ClientConfig:
    """General configuration class of the SKA DLM clients.

    This class holds all configuration parameters needed for the DLM clients.
    Specific configurations for the individual clients are expanding this class.
    """

    directory_to_watch: str  # for the directory watcher this is /dlm/watch_dir
    source_name: str
    target_name: str
    ingest_url: str
    storage_url: str
    migration_url: str
    status_file_absolute_path: str
    reload_status_file: bool
    ingest_configuration: Configuration = field(init=False)
    migration_configuration: Configuration = field(init=False)
    directory_watcher_entries: DirectoryWatcherEntries = field(init=False)
    use_status_file: bool = False
    rclone_access_check_on_register: bool = False
    ingest_register_path_to_add: str = field(init=False)
    storage_root_directory: str = "/dlm/watch_dir"
    METADATA_FILENAME: str = METADATA_FILENAME
    METADATA_EXECUTION_BLOCK_KEY: str = METADATA_EXECUTION_BLOCK_KEY
    STATUS_FILE_FILENAME: str = STATUS_FILE_FILENAME
    DIRECTORY_IS_MEASUREMENT_SET_SUFFIX: str = DIRECTORY_IS_MEASUREMENT_SET_SUFFIX

    def __post_init__(self):
        self.status_file_absolute_path = f"{self.storage_root_directory}/{self.STATUS_FILE_FILENAME}"
        self.directory_watcher_entries = DirectoryWatcherEntries(
            entries_file=self.status_file_absolute_path,
            reload_from_status_file=self.reload_status_file,
            write_directory_entries_file=self.use_status_file,
        )
        self.ingest_configuration = Configuration(host=self.ingest_url)
        self.ingest_register_path_to_add = os.path.relpath(
            path=self.directory_to_watch
        )
        # Migration related options
        self.migration_configuration = Configuration(host=self.migration_url)


class WatcherConstants:  # pylint: disable=too-few-public-methods
    """Constants shared by Directory- and ConfigDB-watchers."""

    STATUS_FILE_FILENAME = STATUS_FILE_FILENAME
    DIRECTORY_IS_MEASUREMENT_SET_SUFFIX = DIRECTORY_IS_MEASUREMENT_SET_SUFFIX
    METADATA_FILENAME = METADATA_FILENAME
    METADATA_EXECUTION_BLOCK_KEY = METADATA_EXECUTION_BLOCK_KEY


# Backwards-compat alias for any existing imports of Config
Config = WatcherConstants

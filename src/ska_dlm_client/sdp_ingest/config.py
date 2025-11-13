"""Class to hold the configuration used by the sdp_ingest package."""

import os
from typing import Any

from ska_dlm_client.openapi.configuration import Configuration

# flake8: noqa
# pylint: disable=missing-function-docstring,too-many-instance-attributes,too-few-public-methods

# Constants used elsewhere in the client
DIRECTORY_IS_MEASUREMENT_SET_SUFFIX = ".ms"
METADATA_FILENAME = "ska-data-product.yaml"
METADATA_EXECUTION_BLOCK_KEY = "execution_block"


class _NoopDirectoryWatcherEntries:
    """Stub so RegistrationProcessor can call add()/save_to_file() without I/O."""

    def __init__(self) -> None:
        self._entries: list[Any] = []

    def add(self, entry: Any) -> None:
        self._entries.append(entry)

    def save_to_file(self) -> None:
        return


class DemoConfig:
    """Temporary configuration to demo ingest/migration via the ConfigDB Watcher."""

    # Required by RegistrationProcessor
    ingest_server_url: str
    storage_name: str
    storage_root_directory: str
    rclone_access_check_on_register: bool
    ingest_configuration: Configuration
    include_existing: bool

    migration_server_url: str
    migration_destination_storage_name: str
    perform_actual_ingest_and_migration: bool
    migration_configuration: Configuration

    directory_watcher_entries: _NoopDirectoryWatcherEntries
    directory_to_watch: str

    def __init__(self) -> None:
        # Direct manager endpoints (bypass gateway/auth for local demo)
        self.ingest_server_url = "http://localhost:8001"
        self.migration_server_url = "http://localhost:8004"

        # Hard-coded demo values
        self.storage_name = "SDPBuffer"
        self.storage_root_directory = "/data"
        self.rclone_access_check_on_register = False
        self.perform_actual_ingest_and_migration = True
        self.migration_destination_storage_name = "dest_storage"
        self.include_existing = False

        # OpenAPI client configurations
        self.ingest_configuration = Configuration(host=self.ingest_server_url)
        self.migration_configuration = Configuration(host=self.migration_server_url)

        # Minimal DW bookkeeping compatibility
        self.directory_watcher_entries = _NoopDirectoryWatcherEntries()
        self.directory_to_watch = os.getcwd()

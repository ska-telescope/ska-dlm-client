"""Class to hold the configuration used by the directory_watcher package."""

import os.path

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
    """Running configuration of the SKA DLM client directory watcher.

    This class holds all configuration parameters needed for the directory watcher
    to monitor directories and register data items with the DLM.
    """

    directory_to_watch: str
    ingest_server_url: str
    storage_name: str
    status_file_absolute_path: str
    storage_root_directory: str
    reload_status_file: bool
    use_status_file: bool
    rclone_access_check_on_register: bool
    directory_watcher_entries: DirectoryWatcherEntries
    ingest_configuration: Configuration
    ingest_register_path_to_add: str
    migration_server_url: str
    migration_destination_storage_name: str
    # This is used for dev testing reasons! When this value is false it will stop the watcher
    # from connecting to and sending messages to DLM server to ingest and then migrate the
    # found data item. All other logging continues.
    perform_actual_ingest_and_migration: bool

    def __init__(  # pylint: disable=too-many-arguments, disable=too-many-positional-arguments
        self,
        directory_to_watch: str,
        ingest_server_url: str,
        storage_name: str,
        status_file_absolute_path: str,
        storage_root_directory: str,
        reload_status_file: bool = False,
        use_status_file: bool = False,
        rclone_access_check_on_register: bool = True,
        migration_server_url: str = None,
        migration_destination_storage_name: str = None,
        perform_actual_ingest_and_migration: bool = True,
    ):
        """Initialize the configuration with values required for directory_watcher operation.

        Args:
            directory_to_watch: The directory path to monitor for new files/directories.
            ingest_server_url: The URL of the DLM ingest server.
            storage_name: The name of the storage location in DLM.
            status_file_absolute_path: The absolute path to the status file.
            storage_root_directory: The root directory of the storage location.
            reload_status_file: Whether to reload the status file on startup.
            use_status_file: Whether to use and update the status file.
            rclone_access_check_on_register: Whether to perform rclone access check during registration.
            migration_server_url: The URL of the DLM migration server.
            migration_destination_storage_name: The name of the destination storage for migration.
            perform_actual_ingest_and_migration: Whether to actually perform ingest and migration operations.
        """
        self.directory_to_watch = directory_to_watch
        self.ingest_server_url = f"{ingest_server_url}"
        self.storage_name = storage_name
        self.status_file_absolute_path = status_file_absolute_path
        self.storage_root_directory = storage_root_directory
        self.reload_status_file = reload_status_file
        self.use_status_file = use_status_file
        self.rclone_access_check_on_register = rclone_access_check_on_register
        self.directory_watcher_entries = DirectoryWatcherEntries(
            entries_file=self.status_file_absolute_path,
            reload_from_status_file=self.reload_status_file,
            write_directory_entries_file=use_status_file,
        )
        self.ingest_configuration = configuration.Configuration(host=self.ingest_server_url)
        # We need to know the relative path from the storage root directory to the watch directory
        # as this path is prepended to any found files/directories in the watch directory.
        self.ingest_register_path_to_add = os.path.relpath(
            path=self.directory_to_watch, start=self.storage_root_directory
        )

        # Migration related options
        self.migration_server_url = migration_server_url
        self.migration_configuration = configuration.Configuration(host=migration_server_url)
        self.migration_destination_storage_name = migration_destination_storage_name

        self.perform_actual_ingest_and_migration = perform_actual_ingest_and_migration

    def __str__(self):
        """Create a string representation of this configuration.

        Returns:
            A string containing all configuration parameters and their values.
        """
        return (
            f"directory_to_watch {self.directory_to_watch}\n"
            f"ingest_server_url {self.ingest_server_url}\n"
            f"storage_name {self.storage_name}\n"
            f"status_file_absolute_path {self.status_file_absolute_path}\n"
            f"storage_root_directory {self.storage_root_directory}\n"
            f"reload_status_file {self.reload_status_file}\n"
            f"use_status_file {self.use_status_file}\n"
            f"rclone_access_check_on_register {self.rclone_access_check_on_register}\n"
            f"ingest_configuration {self.ingest_configuration}\n"
            f"directory_watcher_entries {self.directory_watcher_entries}\n"
            f"ingest_register_path_to_add {self.ingest_register_path_to_add}\n"
            f"migration_server_url {self.migration_server_url}\n"
            f"migration_configuration {self.migration_configuration}\n"
            f"migration_destination_storage_name {self.migration_destination_storage_name}\n"
            f"perform_actual_ingest_and_migration {self.perform_actual_ingest_and_migration}\n"
        )

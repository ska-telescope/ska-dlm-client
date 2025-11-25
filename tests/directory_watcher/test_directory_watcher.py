"""Tests for directory watcher."""

import asyncio
import tempfile
from pathlib import Path

import pytest

from ska_dlm_client.config import STATUS_FILE_FILENAME
from ska_dlm_client.directory_watcher.directory_watcher import (
    INotifyDirectoryWatcher,
    PollingDirectoryWatcher,
)
from ska_dlm_client.directory_watcher.directory_watcher_entries import DirectoryWatcherEntries
from ska_dlm_client.directory_watcher.main import create_parser, process_args
from ska_dlm_client.openapi.configuration import Configuration
from ska_dlm_client.registration_processor import RegistrationProcessor


class MockCmdLineParameters:
    """Mock class for CmdLineParameters to use in tests."""

    def __init__(self):
        """Initialize with default values."""
        self.migration_server_url = None
        self.migration_destination_storage_name = None
        self.perform_actual_ingest_and_migration = True

    def parse_arguments(self, args):
        """Mock method that does nothing."""

    def set_application_ready(self):
        """Mock method that does nothing."""


class TestDirectoryWatcher:
    """DirectoryWatcher unit test stubs."""

    STORAGE_NAME = "data"
    INGREST_SERVER_URL = "http://localhost:8001"
    ROOT_DIRECTORY = "/dlm"

    add_path_successful = False

    @classmethod
    def setup_class(cls) -> None:
        """Set for the testing process."""
        cls.the_watch_dir = tempfile.mkdtemp()
        cls.parser = create_parser()
        cls.parsed = cls.parser.parse_args(
            [
                "--directory-to-watch",
                cls.the_watch_dir,
                "--ingest-server-url",
                cls.INGREST_SERVER_URL,
                "--storage-name",
                cls.STORAGE_NAME,
                "--storage-root-directory",
                cls.ROOT_DIRECTORY,
            ]
        )
        cls.cmd_line_parameters = MockCmdLineParameters()
        cls.cmd_line_parameters.parse_arguments(cls.parsed)
        cls.config = process_args(args=cls.parsed, cmd_line_parameters=cls.cmd_line_parameters)

    @classmethod
    def teardown_class(cls) -> None:
        """Tear down any setup."""
        Path(cls.the_watch_dir).rmdir()

    def test_process_args(self) -> None:
        """Test case for init_data_item_ingest_init_data_item_post."""
        assert self.parsed.directory_to_watch == self.the_watch_dir
        assert self.parsed.ingest_server_url == self.INGREST_SERVER_URL
        assert self.parsed.storage_name == self.STORAGE_NAME
        assert self.parsed.reload_status_file is False
        assert self.parsed.status_file_filename == STATUS_FILE_FILENAME
        assert self.parsed.use_status_file is False
        assert self.parsed.skip_rclone_access_check_on_register is False

    def test_config_generation(self) -> None:
        """Test the correct config is generated from the command line args."""
        assert self.config.directory_to_watch == self.the_watch_dir
        assert self.config.ingest_server_url == self.INGREST_SERVER_URL
        assert self.config.storage_name == self.STORAGE_NAME
        assert self.config.reload_status_file is False
        assert (
            self.config.status_file_absolute_path == f"{self.the_watch_dir}/{STATUS_FILE_FILENAME}"
        )
        assert self.config.use_status_file is False
        assert self.config.rclone_access_check_on_register is True
        assert isinstance(self.config.directory_watcher_entries, DirectoryWatcherEntries)
        assert isinstance(self.config.ingest_configuration, Configuration)

        # Test migration-related attributes
        assert self.config.migration_server_url is None
        assert self.config.migration_destination_storage_name is None
        assert self.config.perform_actual_ingest_and_migration is True

    @pytest.mark.asyncio
    @pytest.mark.parametrize("test_polling", [True, False])
    async def test_process_directory_entry_change_test(self, test_polling) -> None:
        """Test code for process_directory_entry_change both polling and non polling."""
        registration_processor = MockRegistrationProcessor(self.config)
        a_temp_file = tempfile.mktemp(dir=self.the_watch_dir)
        if test_polling:
            directory_watcher = PollingDirectoryWatcher(
                config=self.config,
                registration_processor=registration_processor,
                cmd_line_parameters=self.cmd_line_parameters,
            )
        else:
            directory_watcher = INotifyDirectoryWatcher(
                config=self.config,
                registration_processor=registration_processor,
                cmd_line_parameters=self.cmd_line_parameters,
            )
        asyncio.get_event_loop().create_task(directory_watcher.watch())
        # Now let the directory_watcher start and listen on given directory
        await asyncio.sleep(2)
        # Add a file to the watcher directory
        with open(a_temp_file, "w", encoding="utf-8") as the_file:
            the_file.write("nothing string")
        # Wait again now to allow the watcher to process the added file
        await asyncio.sleep(2)
        a_temp_file_relative_path = a_temp_file.replace(f"{self.the_watch_dir}/", "")
        # On MacOS the system messes with the path by adding a /private
        absolute_path = registration_processor.absolute_path.replace("/private", "")
        path_rel_to_watch_dir = registration_processor.path_rel_to_watch_dir.replace(
            "/private", ""
        )
        assert a_temp_file == absolute_path
        assert a_temp_file_relative_path == path_rel_to_watch_dir
        Path(a_temp_file).unlink()


class MockRegistrationProcessor(RegistrationProcessor):
    """A class to use for test of directory watcher."""

    absolute_path: str
    path_rel_to_watch_dir: str

    def __init__(self, config):
        """Initialize with default values."""
        super().__init__(config)
        self.absolute_path = ""
        self.path_rel_to_watch_dir = ""

    def add_path(self, absolute_path: str, path_rel_to_watch_dir: str):
        """Perform testing on the given paths."""
        self.absolute_path = absolute_path
        self.path_rel_to_watch_dir = path_rel_to_watch_dir

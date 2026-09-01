"""Tests for directory watcher."""

import argparse
import asyncio
import os
import tempfile
from pathlib import Path

import pytest
from ska_sdp_config.entity import Dependency

from ska_dlm_client.config import STATUS_FILE_FILENAME
from ska_dlm_client.directory_watcher.config import WatcherArgs
from ska_dlm_client.directory_watcher.directory_watcher import (
    INotifyDirectoryWatcher,
    PollingDirectoryWatcher,
)
from ska_dlm_client.directory_watcher.directory_watcher_entries import DirectoryWatcherEntries
from ska_dlm_client.directory_watcher.main import process_args
from ska_dlm_client.openapi.configuration import Configuration
from ska_dlm_client.registration_processor import RegistrationProcessor


def create_cmd_line_parameters() -> WatcherArgs:
    """Create command-line parameters for directory watcher tests."""
    return WatcherArgs()


def create_args() -> argparse.Namespace:
    """Create a test Namespace containing directory watcher arguments.

    Returns:
        An argparse.Namespace populated with the argument values required
        by the tests.
    """
    return argparse.Namespace(
        directory_to_watch="",
        source_name="",
        target_name="",
        storage_url="",
        migration_url="",
        ingest_url="",
        reload_status_file=True,
        status_file_filename=STATUS_FILE_FILENAME,
        skip_rclone_access_check_on_register=False,
        include_existing=False,
        dir_updates_wait_time=1,
        use_status_file=False,
    )


class TestDirectoryWatcher:
    """DirectoryWatcher unit test stubs."""

    SOURCE_NAME = "dir-watcher"
    INGEST_URL = os.getenv("INGEST_URL", "http://dlm_ingest:8001")

    add_path_successful = False

    @classmethod
    def setup_class(cls) -> None:
        """Set up the test environment."""
        cls.the_watch_dir = tempfile.mkdtemp()
        cls.cmd_line_parameters = create_cmd_line_parameters()
        cls.parsed = cls.cmd_line_parameters.parser.parse_args(
            [
                "--directory-to-watch",
                cls.the_watch_dir,
                "--ingest-url",
                cls.INGEST_URL,
                "--source-name",
                cls.SOURCE_NAME,
            ]
        )
        cls.cmd_line_parameters.parse_arguments(cls.parsed)
        cls.config = process_args(args=cls.parsed)

    @classmethod
    def teardown_class(cls) -> None:
        """Tear down any setup."""
        Path(cls.the_watch_dir).rmdir()

    def test_process_args(self) -> None:
        """Test case for init_data_item_ingest_init_data_item_post."""
        assert self.parsed.directory_to_watch == self.the_watch_dir
        assert self.parsed.ingest_url == self.INGEST_URL
        assert self.parsed.source_name == self.SOURCE_NAME
        assert self.parsed.reload_status_file is False
        assert self.parsed.status_file_filename == STATUS_FILE_FILENAME
        assert self.parsed.use_status_file is False
        assert self.parsed.skip_rclone_access_check_on_register is False

    def test_config_generation(self) -> None:
        """Test the correct config is generated from the command line args."""
        assert self.config.directory_to_watch == self.the_watch_dir
        assert self.config.ingest_url == self.INGEST_URL
        assert self.config.source_name == self.SOURCE_NAME
        assert self.config.reload_status_file is False
        assert (
            self.config.status_file_absolute_path == f"{self.the_watch_dir}/{STATUS_FILE_FILENAME}"
        )
        assert self.config.use_status_file is False
        assert self.config.rclone_access_check_on_register is True
        assert isinstance(self.config.directory_watcher_entries, DirectoryWatcherEntries)
        assert isinstance(self.config.ingest_configuration, Configuration)

        # Test migration-related attributes
        assert self.config.migration_url == "http://dlm_migration:8004"
        assert self.config.target_name == "dlm-archive"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("test_polling", [True, False])
    async def test_process_directory_entry_change_test(self, test_polling) -> None:
        """Test code for process_directory_entry_change both polling and non polling."""
        registration_processor = MockRegistrationProcessor(self.config)
        a_temp_file = tempfile.mktemp(dir=self.the_watch_dir)
        self.config.directory_to_watch = self.the_watch_dir
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
        await asyncio.sleep(2)  # TODO: DMAN-193
        # Add a file to the watcher directory
        with open(a_temp_file, "w", encoding="utf-8") as the_file:
            the_file.write("nothing string")
        # Wait again now to allow the watcher to process the added file
        await asyncio.sleep(2)  # TODO: DMAN-193
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

    def _get_storage_info_from_name(self, storage_name: str) -> tuple[str, str]:
        """Return fixed storage info without calling the real helper."""
        return ("test-target", "SOLID")

    def add_path(
        self,
        absolute_path: str,
        path_rel_to_watch_dir: str,
        dependency_key: Dependency.Key | None = None,
    ):
        """Perform testing on the given paths."""
        self.absolute_path = absolute_path
        self.path_rel_to_watch_dir = path_rel_to_watch_dir
        self.dependency_key = dependency_key

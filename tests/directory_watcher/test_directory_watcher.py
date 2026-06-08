"""Tests for directory watcher."""

import argparse
import asyncio
import os
import tempfile
from pathlib import Path

import pytest

from ska_dlm_client.config import STATUS_FILE_FILENAME
from ska_dlm_client.directory_watcher.directory_watcher import (
    INotifyDirectoryWatcher,
    PollingDirectoryWatcher,
)
from ska_dlm_client.directory_watcher.directory_watcher_entries import DirectoryWatcherEntries
from ska_dlm_client.directory_watcher.main import process_args
from ska_dlm_client.openapi.configuration import Configuration
from ska_dlm_client.registration_processor import RegistrationProcessor
from ska_dlm_client.utils import CmdLineParameters

def create_parser() -> argparse.ArgumentParser:
    """Define a parser for all the command line parameters.

    Creates and configures an ArgumentParser with all the command line options
    needed for the ska-dlm-client's various components.

    Returns:
        An ArgumentParser instance configured with all required and optional arguments.
    """
    cmd_line_parameters = CmdLineParameters(add_readiness_probe_file=True)
    cmd_line_parameters.parser.add_argument(
        "-d",
        "--directory-to-watch",
        type=str,
        required=True,
        help="Full path to directory to watch.",
    )
    cmd_line_parameters.directory_to_watch = ""
    cmd_line_parameters.parser.add_argument(
        "--use-polling-watcher",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="When defined using the polling watcher rather than iNotify event driven watcher.",
    )
    cmd_line_parameters.parser.add_argument(
        "--dir-updates-wait-time",
        default=1,
        help="If set, a directory will only be added once its contents has been static "
            + "for at least the given number of seconds.",
    )
    cmd_line_parameters.dir_updates_wait_time = True
    cmd_line_parameters.parser.add_argument(
        "--use-status-file",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Use the status file, default is NOT to use, this may change in a future release.",
    )
    cmd_line_parameters.use_status_file = False
    cmd_line_parameters.parser.add_argument(
        "--reload-status-file",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Reload the status file that already exists in the watch directory.",
    )
    cmd_line_parameters.reload_status_file = True
    cmd_line_parameters.parser.add_argument(
        "--status-file-filename",
        type=str,
        required=False,
        default=ska_dlm_client.config.STATUS_FILE_FILENAME,
        help="",
    )
    cmd_line_parameters.status_file_filename = ska_dlm_client.config.STATUS_FILE_FILENAME
    cmd_line_parameters.parser.add_argument(
        "--skip-rclone-access-check-on-register",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Skip performing the rclone access check when registering a data item with DLM.",
    )
    cmd_line_parameters.skip_rclone_access_check_on_register = False
    cmd_line_parameters.parser.add_argument(
        "--register-contents-of-watch-directory",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="First register each file/directory in the watch directory as a data product.",
    )
    cmd_line_parameters.register_contents_of_watch_directory = False
    return cmd_line_parameters


class MockCmdLineParameters:
    """Mock class for CmdLineParameters to use in tests."""

    def __init__(self):
        """Initialize with default values."""
        self.migration_url = None
        self.migration_destination_storage_name = None
        self.perform_actual_ingest_and_migration = True

    def parse_arguments(self, args):
        """Mock method that does nothing."""

    def set_application_ready(self):
        """Mock method that does nothing."""


class TestDirectoryWatcher:
    """DirectoryWatcher unit test stubs."""

    STORAGE_NAME = "dir-watcher"
    INGREST_URL = os.getenv("INGEST_URL", "http://dlm_ingest:8001")
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
                "--ingest-url",
                cls.INGREST_URL,
                "--source-name",
                cls.STORAGE_NAME,
                "--source-root",
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
        assert self.parsed.ingest_url == self.INGREST_URL
        assert self.parsed.source_name == self.STORAGE_NAME
        assert self.parsed.reload_status_file is False
        assert self.parsed.status_file_filename == STATUS_FILE_FILENAME
        assert self.parsed.use_status_file is False
        assert self.parsed.skip_rclone_access_check_on_register is False

    def test_config_generation(self) -> None:
        """Test the correct config is generated from the command line args."""
        assert self.config.directory_to_watch == self.the_watch_dir
        assert self.config.ingest_url == self.INGREST_URL
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
        assert self.config.migration_url is None
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

    def add_path(self, absolute_path: str, path_rel_to_watch_dir: str):
        """Perform testing on the given paths."""
        self.absolute_path = absolute_path
        self.path_rel_to_watch_dir = path_rel_to_watch_dir

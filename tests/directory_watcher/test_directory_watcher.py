"""Tests for directory watcher."""

import asyncio
import tempfile
import unittest
from pathlib import Path

import ska_dlm_client.directory_watcher.config
from ska_dlm_client.directory_watcher.directory_watcher import (
    DirectoryWatcher,
    create_parser,
    process_args,
)
from ska_dlm_client.directory_watcher.directory_watcher_entries import DirectoryWatcherEntries
from ska_dlm_client.directory_watcher.registration_processor import RegistrationProcessor
from ska_dlm_client.openapi.configuration import Configuration


class TestDirectoryWatcher(unittest.IsolatedAsyncioTestCase):
    """DirectoryWatcher unit test stubs."""

    STORAGE_NAME = "data"
    INGREST_SERVER_URL = "http://localhost:8001"

    add_path_successful = False

    def setUp(self) -> None:
        """Set for the testing process."""
        self.the_watch_dir = tempfile.mkdtemp()
        self.parser = create_parser()
        self.parsed = self.parser.parse_args(
            [
                "--directory-to-watch",
                self.the_watch_dir,
                "--ingest-server-url",
                self.INGREST_SERVER_URL,
                "--storage-name",
                self.STORAGE_NAME,
            ]
        )
        self.config = process_args(args=self.parsed)

    def tearDown(self) -> None:
        """Tear down any setup."""
        Path(self.the_watch_dir).rmdir()

    def test_process_args(self) -> None:
        """Test case for init_data_item_ingest_init_data_item_post."""
        self.assertEqual(self.parsed.directory_to_watch, self.the_watch_dir)
        self.assertEqual(self.parsed.ingest_server_url, self.INGREST_SERVER_URL)
        self.assertEqual(self.parsed.storage_name, self.STORAGE_NAME)
        self.assertEqual(self.parsed.reload_status_file, False)
        self.assertEqual(
            self.parsed.status_file_filename,
            ska_dlm_client.directory_watcher.config.STATUS_FILE_FILENAME,
        )
        self.assertEqual(self.parsed.use_status_file, False)

    def test_config_generation(self) -> None:
        """Test the correct config is generated from the command line args."""
        self.assertEqual(self.config.directory_to_watch, self.the_watch_dir)
        self.assertEqual(self.config.ingest_server_url, self.INGREST_SERVER_URL)
        self.assertEqual(self.config.storage_name, self.STORAGE_NAME)
        self.assertEqual(self.config.reload_status_file, False)
        self.assertEqual(
            self.config.status_file_full_filename,
            f"{self.the_watch_dir}/{ska_dlm_client.directory_watcher.config.STATUS_FILE_FILENAME}",
        )
        self.assertEqual(self.config.use_status_file, False)
        self.assertIsInstance(self.config.directory_watcher_entries, DirectoryWatcherEntries)
        self.assertIsInstance(self.config.ingest_configuration, Configuration)

    async def test_process_directory_entry_change(self) -> None:
        """Test case for process_directory_entry_change."""
        registration_processor = MockRegistrationProcessor(self.config)
        directory_watcher = DirectoryWatcher(self.config, registration_processor)
        a_temp_file = tempfile.mktemp(dir=self.the_watch_dir)
        asyncio.create_task(directory_watcher.start())
        # Now let the directory_watcher start and listen on given directory
        await asyncio.sleep(2)
        # Add a file to the watcher directory
        with open(a_temp_file, "w", encoding="utf-8") as the_file:
            the_file.write("nothing string")
        # Wait again now to allow the watcher to process the added file
        await asyncio.sleep(2)
        a_temp_file_relative_path = a_temp_file.replace(f"{self.the_watch_dir}/", "")
        # On MacOS the system messes with the path by adding a /private
        full_path = registration_processor.full_path.replace("/private", "")
        relative_path = registration_processor.relative_path.replace("/private", "")
        self.assertEqual(a_temp_file, full_path)
        self.assertEqual(a_temp_file_relative_path, relative_path)
        Path(a_temp_file).unlink()


class MockRegistrationProcessor(RegistrationProcessor):
    """A class to use for test of directory watcher."""

    full_path: str
    relative_path: str

    def add_path(self, full_path: str, relative_path: str):
        """Perform testing on the given paths."""
        self.full_path = full_path
        self.relative_path = relative_path


if __name__ == "__main__":
    unittest.main()

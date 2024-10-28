"""Tests for directory watcher."""

import unittest

import ska_dlm_client.directory_watcher.config
from ska_dlm_client.directory_watcher.directory_watcher import create_parser, process_args
from ska_dlm_client.directory_watcher.directory_watcher_entries import DirectoryWatcherEntries
from ska_dlm_client.openapi.configuration import Configuration


class TestDirectoryWatcher(unittest.TestCase):
    """DirectoryWatcher unit test stubs."""

    THE_WATCH_DIR = "/the_watch_dir"
    STORAGE_NAME = "data"
    SERVER_URL = "http://localhost"
    EXECUTION_BLOCK_ID = "exe_blk_id_0001"

    def setUp(self) -> None:
        """Set for the testing process."""
        self.parser = create_parser()
        self.parsed = self.parser.parse_args(
            [
                "-d",
                self.THE_WATCH_DIR,
                "-n",
                self.STORAGE_NAME,
                "-s",
                self.SERVER_URL,
                "-e",
                self.EXECUTION_BLOCK_ID,
            ]
        )

    def tearDown(self) -> None:
        """Tear down any setup."""

    def test_process_args(self) -> None:
        """Test case for init_data_item_ingest_init_data_item_post."""
        self.assertEqual(self.parsed.directory_to_watch, self.THE_WATCH_DIR)
        self.assertEqual(self.parsed.storage_name, self.STORAGE_NAME)
        self.assertEqual(self.parsed.server_url, self.SERVER_URL)
        self.assertEqual(self.parsed.execution_block_id, self.EXECUTION_BLOCK_ID)
        self.assertEqual(self.parsed.reload_status_file, False)
        self.assertEqual(self.parsed.ingest_service_port, 8001)
        self.assertEqual(self.parsed.storage_service_port, 8003)
        self.assertEqual(
            self.parsed.status_file_filename,
            ska_dlm_client.directory_watcher.config.STATUS_FILE_FILENAME,
        )

    def test_config_generation(self) -> None:
        """Test the correct config is generated from the command line args."""
        config = process_args(args=self.parsed)
        self.assertEqual(config.directory_to_watch, self.THE_WATCH_DIR)
        self.assertEqual(
            config.status_file_full_filename,
            f"{self.THE_WATCH_DIR}/{ska_dlm_client.directory_watcher.config.STATUS_FILE_FILENAME}",
        )
        self.assertEqual(config.reload_status_file, False)
        self.assertEqual(config.storage_name, self.STORAGE_NAME)
        self.assertEqual(config.ingest_url, f"{self.SERVER_URL}:8001")
        self.assertEqual(config.storage_url, f"{self.SERVER_URL}:8003")
        self.assertEqual(config.execution_block_id, self.EXECUTION_BLOCK_ID)
        self.assertIsInstance(config.ingest_configuration, Configuration)
        self.assertIsInstance(config.storage_configuration, Configuration)
        self.assertIsInstance(config.directory_watcher_entries, DirectoryWatcherEntries)

    def test_register_data_item_ingest_register_data_item_post(self) -> None:
        """Test case for register_data_item_ingest_register_data_item_post.

        Register Data Item
        """


if __name__ == "__main__":
    unittest.main()

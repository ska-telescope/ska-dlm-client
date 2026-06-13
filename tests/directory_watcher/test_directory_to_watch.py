"""Tests for directory_to_watch parameter in directory_watcher."""

import os
import tempfile
from pathlib import Path

from ska_dlm_client.directory_watcher.config import WatcherArgs, WatcherConfig
from ska_dlm_client.directory_watcher.main import process_args
from ska_dlm_client.registration_processor import Item, RegistrationProcessor


class TestDirectoryToWatch:
    """Test class for directory_to_watch parameter."""

    SOURCE_NAME = "test-storage"
    INGEST_URL = os.getenv("INGEST_URL", "http://dlm_ingest:8001")
    STORAGE_URL = os.getenv("STORAGE_URL", "http://dlm_storage:8003")

    @classmethod
    def setup_class(cls) -> None:
        """Set up for the testing process."""
        cls.the_watch_dir = tempfile.mkdtemp()
        cls.parser = WatcherArgs()

    @classmethod
    def teardown_class(cls) -> None:
        """Tear down any setup."""
        Path(cls.the_watch_dir).rmdir()

    def test_directory_to_watch_non_empty(self) -> None:
        """Test when directory_to_watch is not empty."""
        # Create a root directory that is a parent of the watch directory

        parsed = self.parser.parser.parse_args(
            [
                "--directory-to-watch",
                self.the_watch_dir,
                "--ingest-url",
                self.INGEST_URL,
                "--source-name",
                self.SOURCE_NAME,
                "--storage-url",
                self.STORAGE_URL,
                "--readiness-probe-file",
                "/tmp/probe",
            ]
        )

        config = process_args(args=parsed)

        assert config.directory_to_watch == self.the_watch_dir

    def test_directory_to_watch_used_in_registration(self) -> None:
        """Test that directory_to_watch is used when registering items with DLM."""
        # Create a root directory that is a parent of the watch directory

        # Create a test file in the watch directory
        test_file_name = "test_file.txt"
        test_file_path = os.path.join(self.the_watch_dir, test_file_name)
        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write("test content")

        # Create a mock registration processor that captures the URI
        class MockRegistrationProcessor(RegistrationProcessor):
            """A class to use for testing storage_root_directory."""

            def __init__(self, config: WatcherConfig):
                """Initialize with the given config."""
                super().__init__(config)
                self.register_data_item_args = None
                self.dry_run_for_debug = True  # Prevent actual API calls

            def _register_single_item(self, item: Item, migrate: bool = True) -> str | None:
                """Capture the URI that would be used for registration."""
                # Generate the uri relative to the root directory
                item_path_rel_to_watch_dir = item.path_rel_to_watch_dir
                uri = item_path_rel_to_watch_dir
                self.register_data_item_args = {
                    "item_name": item_path_rel_to_watch_dir,
                    "uri": uri,
                    "item_type": item.item_type,
                    "storage_name": self._config.source_name,
                }
                return "test-uuid"

        # Create config with non-empty storage_root_directory
        config = WatcherConfig(
            directory_to_watch=self.the_watch_dir,
            ingest_url=self.INGEST_URL,
            storage_url=self.STORAGE_URL,
        )

        # Create a registration processor with our config
        processor = MockRegistrationProcessor(config)

        # Register the test file
        processor.add_path(absolute_path=test_file_path, path_rel_to_watch_dir=test_file_name)

        assert processor.register_data_item_args is not None

        expected_uri = f"{test_file_name}"
        assert processor.register_data_item_args["uri"] == expected_uri
        assert processor.register_data_item_args["item_name"] == test_file_name

        # Clean up
        os.remove(test_file_path)

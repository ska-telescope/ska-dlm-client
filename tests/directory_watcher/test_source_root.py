"""Tests for storage_root_directory parameter in directory_watcher."""

import os
import tempfile
from pathlib import Path

from ska_dlm_client.config import STATUS_FILE_FILENAME
from ska_dlm_client.directory_watcher.config import WatcherConfig
from ska_dlm_client.directory_watcher.main import create_parser, process_args
from ska_dlm_client.registration_processor import RegistrationProcessor, Item
from ska_dlm_client.utils import CmdLineParameters


class TestSourceRootDirectory:
    """Test class for source_root_directory parameter."""

    STORAGE_NAME = "test-storage"
    INGEST_URL = os.getenv("INGEST_URL", "http://dlm_ingest:8001")
    STORAGE_URL = os.getenv("STORAGE_URL", "http://dlm_storage:8003")

    @classmethod
    def setup_class(cls) -> None:
        """Set up for the testing process."""
        cls.the_watch_dir = tempfile.mkdtemp()
        cls.parser = create_parser()

    @classmethod
    def teardown_class(cls) -> None:
        """Tear down any setup."""
        Path(cls.the_watch_dir).rmdir()

    def test_source_root_empty(self) -> None:
        """Test when source_root is empty."""
        parsed = self.parser.parse_args(
            [
                "--directory-to-watch",
                self.the_watch_dir,
                "--ingest-url",
                self.INGEST_URL,
                "--source-name",
                self.STORAGE_NAME,
                "--storage-url",
                self.STORAGE_URL,
                "--source-root",
                "",
            ]
        )
        cmd_line_parameters = CmdLineParameters(
            parser=self.parser,
            add_readiness_probe_file=True,
            add_do_not_perform_actual_ingest_and_migration=True,
            add_dir_updates_wait_time=True,
        )

        config = process_args(args=parsed, cmd_line_parameters=cmd_line_parameters)

        # When storage_root_directory is empty, ingest_register_path_to_add is a relative path
        # calculated from the current working directory to the watch directory
        assert config.storage_root_directory == ""

        # Verify that the path is a valid relative path
        # We can't assert the exact path because it depends on the current working directory
        # Instead, we'll verify that it's a valid path that points to the watch directory

        # Resolve the relative path to an absolute path
        absolute_path = os.path.normpath(
            os.path.join(os.getcwd(), config.ingest_register_path_to_add)
        )
        # Normalize both paths for comparison
        expected_path = os.path.normpath(self.the_watch_dir)
        assert absolute_path == expected_path

    def test_source_root_non_empty(self) -> None:
        """Test when source_root is not empty."""
        # Create a root directory that is a parent of the watch directory
        root_dir = os.path.dirname(self.the_watch_dir)
        watch_dir_name = os.path.basename(self.the_watch_dir)

        parsed = self.parser.parse_args(
            [
                "--directory-to-watch",
                self.the_watch_dir,
                "--ingest-url",
                self.INGEST_URL,
                "--source-name",
                self.STORAGE_NAME,
                "--storage-url",
                self.STORAGE_URL,
                "--source-root",
                root_dir,
                "--readiness-probe-file",
                "/tmp/probe",
            ]
        )
        cmd_line_parameters = CmdLineParameters(
            parser=self.parser,
            # add_readiness_probe_file=True,
            # add_do_not_perform_actual_ingest_and_migration=True,
            # add_dir_updates_wait_time=True,
        )

        config = process_args(args=parsed, cmd_line_parameters=cmd_line_parameters)

        # When storage_root_directory is not empty, ingest_register_path_to_add should be the
        # relative path
        assert config.storage_root_directory == root_dir
        assert config.ingest_register_path_to_add == watch_dir_name

    def test_source_root_used_in_registration(self) -> None:
        """Test that source_root is used when registering items with DLM."""
        # Create a root directory that is a parent of the watch directory
        root_dir = os.path.dirname(self.the_watch_dir)
        watch_dir_name = os.path.basename(self.the_watch_dir)

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

            def _register_single_item(self, item: Item, migrate: bool=True) -> str | None:
                """Capture the URI that would be used for registration."""
                # Generate the uri relative to the root directory
                item_path_rel_to_watch_dir = item.path_rel_to_watch_dir
                uri = (
                    item_path_rel_to_watch_dir
                    if self._config.ingest_register_path_to_add == ""
                    else f"{self._config.ingest_register_path_to_add}/{item_path_rel_to_watch_dir}"
                )
                self.register_data_item_args = {
                    "item_name": item_path_rel_to_watch_dir,
                    "uri": uri,
                    "item_type": item.item_type,
                    "storage_name": self._config.storage_name,
                }
                return "test-uuid"

        # Create config with non-empty storage_root_directory
        config = WatcherConfig(
            directory_to_watch=self.the_watch_dir,
            ingest_url=self.INGEST_URL,
            storage_name=self.STORAGE_NAME,
            storage_url=self.STORAGE_URL,
            status_file_absolute_path=f"{self.the_watch_dir}/{STATUS_FILE_FILENAME}",
            storage_root_directory=root_dir,
        )

        # Verify that ingest_register_path_to_add is calculated correctly
        assert config.ingest_register_path_to_add == watch_dir_name

        # Create a registration processor with our config
        processor = MockRegistrationProcessor(config)

        # Register the test file
        processor.add_path(absolute_path=test_file_path, path_rel_to_watch_dir=test_file_name)

        # Verify that the URI would include the ingest_register_path_to_add
        assert processor.register_data_item_args is not None

        # The URI should be the relative path from the storage root to the file
        expected_uri = f"{watch_dir_name}/{test_file_name}"
        assert processor.register_data_item_args["uri"] == expected_uri
        assert processor.register_data_item_args["item_name"] == test_file_name

        # Clean up
        os.remove(test_file_path)

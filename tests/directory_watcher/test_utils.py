"""Test utilities for ska_dlm_client.directory_watcher."""


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

"""
Code to provide the watchers with support functions to integrate a k8s readiness probe.

NOTE: In the future the CmdLineParameters should be broken out into its own module for
use by other applications making up the DLM Client.
"""

import argparse
import logging
import os
from pathlib import Path

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class CmdLineParameters:  # pylint: disable=too-many-instance-attributes
    """Class to contain the common/required command line parameters."""

    add_directory_to_watch: bool = False
    add_storage_name: bool = False
    add_ingest_server_url: bool = False
    add_request_server_url: bool = False
    add_readiness_probe_file: bool = False
    directory_to_watch: str = None
    storage_name: str = None
    ingest_server_url: str = None
    migration_server_url: str = None
    request_server_url: str = None
    readiness_probe_file: str = None
    migration_destination_storage_name: str = None
    dev_test_mode: bool = False
    do_not_perform_actual_ingest_and_migration: bool = False
    # This is not a settable command line param but required for code convenience
    perform_actual_ingest_and_migration: bool = True

    def __init__(  # pylint: disable=too-many-arguments, disable=too-many-positional-arguments
        self,
        parser: argparse.ArgumentParser,
        add_directory_to_watch: bool = False,
        add_storage_name: bool = False,
        add_ingest_server_url: bool = False,
        add_migration_server_url: bool = False,
        add_request_server_url: bool = False,
        add_readiness_probe_file: bool = False,
        add_migration_destination_storage_name: bool = False,
        add_dev_test_mode: bool = False,
        add_do_not_perform_actual_ingest_and_migration: bool = False,
    ):
        """Initiale with which parameters to include on the command line."""
        self._parser = parser
        if add_directory_to_watch:
            self.add_directory_to_watch_arguments(parser)
            self.add_directory_to_watch = True
        if add_storage_name:
            self.add_storage_name_arguments(parser)
            self.add_storage_name = True
        if add_ingest_server_url:
            self.add_ingest_server_url_arguments(parser)
            self.add_ingest_server_url = True
        if add_migration_server_url:
            self.add_migration_server_url_arguments(parser)
            self.add_migration_server_url = True
        if add_request_server_url:
            self.add_request_server_url_arguments(parser)
            self.add_request_server_url = True
        if add_readiness_probe_file:
            self.add_readiness_probe_file_arguments(parser)
            self.add_readiness_probe_file = True
        if add_migration_destination_storage_name:
            self.add_migration_destination_storage_name_arguments(parser)
            self.add_migration_destination_storage_name = True
        if add_dev_test_mode:
            self.add_dev_test_mode_arguments(parser)
            self.add_dev_test_mode = True
        if add_do_not_perform_actual_ingest_and_migration:
            self.add_do_not_perform_actual_ingest_and_migration_arguments(parser)
            self.add_do_not_perform_actual_ingest_and_migration = True

    def parse_arguments(self, args: argparse.Namespace = None):
        """Parse command line arguments and assign to class parameters."""
        if args is None:
            args = self._parser.parse_args()
        self.directory_to_watch = args.directory_to_watch if self.add_directory_to_watch else None
        self.storage_name = args.storage_name if self.add_storage_name else None
        self.ingest_server_url = args.ingest_server_url if self.add_ingest_server_url else None
        self.migration_server_url = (
            args.migration_server_url if self.add_migration_server_url else None
        )
        self.request_server_url = args.request_server_url if self.add_request_server_url else None
        self.readiness_probe_file = (
            args.readiness_probe_file if self.add_readiness_probe_file else None
        )
        self.migration_destination_storage_name = (
            args.migration_destination_storage_name
            if self.add_migration_destination_storage_name
            else None
        )
        if self.migration_destination_storage_name and not self.migration_server_url:
            error_msg = (
                "migration_destination_storage_name can only be used when "
                "migration_server_url is set"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
        self.dev_test_mode = args.dev_test_mode if self.add_dev_test_mode else False

        self.do_not_perform_actual_ingest_and_migration = (
            args.do_not_perform_actual_ingest_and_migration
            if self.add_do_not_perform_actual_ingest_and_migration
            else False
        )
        if self.do_not_perform_actual_ingest_and_migration and not self.dev_test_mode:
            error_msg = (
                "do_not_perform_actual_ingest_and_migration can only be used when "
                "dev_test_mode is True"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Set perform_actual_ingest_and_migration based on
        # do_not_perform_actual_ingest_and_migration
        if self.do_not_perform_actual_ingest_and_migration:
            self.perform_actual_ingest_and_migration = False
        else:
            self.perform_actual_ingest_and_migration = True

    def add_directory_to_watch_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Update a parser to a directory watcher file path."""
        parser.add_argument(
            "-d",
            "--directory-to-watch",
            type=str,
            required=True,
            help="Full path to directory to watch.",
        )

    def add_storage_name_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Update a parser to add a storage name argument."""
        parser.add_argument(
            "-n",
            "--storage-name",
            type=str,
            required=True,
            help="The name by which the DLM system knows the storage as.",
        )

    def add_ingest_server_url_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Update a parser to add an ingest server url argument."""
        parser.add_argument(
            "-i",
            "--ingest-server-url",
            type=str,
            required=True,
            help="Ingest server URL including the service port.",
        )

    def add_migration_server_url_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Update a parser to add an ingest server url argument."""
        parser.add_argument(
            "-m",
            "--migration-server-url",
            type=str,
            required=False,
            help="Migration server URL including the service port.",
        )

    def add_request_server_url_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Update a parser to add a request server url argument."""
        parser.add_argument(
            "--request-server-url",
            type=str,
            required=True,
            help="Request server URL including the service port.",
        )

    def add_readiness_probe_file_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Update a parser to a readiness probe file path."""
        parser.add_argument(
            "--readiness-probe-file",
            type=str,
            required=True,
            help="The path to the readiness probe file.",
        )

    def add_migration_destination_storage_name_arguments(
        self, parser: argparse.ArgumentParser
    ) -> None:
        """Update a parser to add a migration destination storage name argument."""
        parser.add_argument(
            "--migration-destination-storage-name",
            type=str,
            required=False,
            help="The DLM 'storage_name' to migrate to.",
        )

    def add_dev_test_mode_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Update a parser to add a dev test mode argument."""
        parser.add_argument(
            "--dev-test-mode",
            required=False,
            action="store_true",
            help="Optionally, add a dev test mode argument.",
        )

    def add_do_not_perform_actual_ingest_and_migration_arguments(
        self, parser: argparse.ArgumentParser
    ) -> None:
        """Update a parser to add a flag to disable actual ingest and migration."""
        parser.add_argument(
            "--do-not-perform-actual-ingest-and-migration",
            required=False,
            action="store_true",
            help="If set, do not perform actual ingest and migration operations.",
        )

    def set_application_ready(self):
        """Create the required file to indicate the application is ready."""
        if self.add_readiness_probe_file:
            Path(self.readiness_probe_file).touch()
            logger.info("The readiness probe file has been created %s.", self.readiness_probe_file)

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Delete the readiness file on deletion of the instance."""
        if self.add_readiness_probe_file:
            os.remove(self.readiness_probe_file)
            logger.info("The readiness probe file has been deleted %s.", self.readiness_probe_file)

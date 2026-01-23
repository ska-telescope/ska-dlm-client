"""
Code to provide the watchers with support functions to integrate a k8s readiness probe.

NOTE: In the future the CmdLineParameters should be broken out into its own module for
use by other applications making up the DLM Client.
"""

import argparse
from dataclasses import dataclass
import logging
import os
from pathlib import Path

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@dataclass
class CmdLineParameters:  # pylint: disable=too-many-instance-attributes
    """Class to contain the common/required command line parameters."""
    source_name: str = ""
    source_root: str = ""
    target_name: str = ""
    storage_url: str = ""
    ingest_url: str = ""
    request_url: str = ""
    migration_url: str = ""
    readiness_probe_file: str = ""
    do_not_perform_actual_ingest_and_migration: bool=False
    dev_test_mode: bool=False
    add_source_name: bool = True
    add_source_root: bool = True
    add_target_name: bool = True
    add_storage_url: bool = True
    add_ingest_url: bool = True
    add_request_url: bool = True
    add_migration_url: bool = True
    add_readiness_probe_file: bool = False
    add_do_not_perform_actual_ingest_and_migration: bool = False
    add_dev_test_mode: bool = False
    parser: argparse.ArgumentParser = argparse.ArgumentParser()

    def __post_init__(  # noqa: C901
        # pylint: disable=too-many-arguments, disable=too-many-positional-arguments
        self,
    ):
        """Initiale with which parameters to include on the command line."""
        self.parser = argparse.ArgumentParser()
        self.add_dev_test_mode = False
        self.add_do_not_perform_actual_ingest_and_migration = False
        self.perform_actual_ingest_and_migration = True
        if self.add_source_name:
            self.add_source_name_arguments()
            self.add_source_name = True
        if self.add_source_root:
            self.add_source_root_arguments()
            self.add_source_root = True
        if self.add_target_name:
            self.add_target_name_arguments()
            self.add_target_name = True
        if self.add_storage_url:
            self.add_storage_url_arguments()
            self.add_storage_url = True
        if self.add_ingest_url:
            self.add_ingest_url_arguments()
            self.add_ingest_url = True
        if self.add_migration_url:
            self.add_migration_url_arguments()
            self.add_migration_url = True
        if self.add_request_url:
            self.add_request_url_arguments()
            self.add_request_url = True
        if self.add_readiness_probe_file:
            self.add_readiness_probe_file_arguments()
            self.add_readiness_probe_file = False
        if self.add_dev_test_mode:
            self.add_dev_test_mode = self.add_dev_test_mode
        if self.add_do_not_perform_actual_ingest_and_migration:
            if not self.add_dev_test_mode:
                self.add_dev_test_mode_arguments()
                self.add_dev_test_mode = True
            self.add_do_not_perform_actual_ingest_and_migration_arguments()
            self.add_do_not_perform_actual_ingest_and_migration = True

    def parse_arguments(self, args: argparse.Namespace = None):
        """Parse command line arguments and assign to class parameters."""
        if args is None:
            args = self.parser.parse_args()
        self.source_name = args.source_name if self.add_source_name else None
        self.source_root = args.source_root if self.add_source_root else None
        self.target_name = args.target_name if self.add_target_name else None
        self.ingest_url = args.ingest_url if self.add_ingest_url else None
        self.storage_url = args.storage_url if self.add_storage_url else None
        self.migration_url = args.migration_url if self.add_migration_url else None
        self.request_url = args.request_url if self.add_request_url else None
        self.readiness_probe_file = (
            args.readiness_probe_file if self.add_readiness_probe_file else None
        )
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
            args.perform_actual_ingest_and_migration = True


    def add_directory_to_watch_arguments(self) -> None:
        """Update a parser to a directory watcher file path."""
        self.parser.add_argument(
            "-d",
            "--directory-to-watch",
            type=str,
            required=True,
            help="Full path to directory to watch.",
        )

    def add_source_name_arguments(self) -> None:
        """Update a parser to add a storage name argument."""
        self.parser.add_argument(
            "-n",
            "--source-name",
            type=str,
            required=True,
            help="The name by which the DLM system knows the source storage as.",
        )

    def add_source_root_arguments(self) -> None:
        """Update a parser to add a storage root argument."""
        self.parser.add_argument(
            "-o",
            "--source-root",
            type=str,
            required=True,
            help="The root directory of the source volume.",
        )

    def add_target_name_arguments(self) -> None:
        """Update a parser to add a target name argument."""
        self.parser.add_argument(
            "-t",
            "--target-name",
            type=str,
            required=True,
            help="The name by which the DLM system knows the target storage as.",
        )

    def add_storage_url_arguments(self) -> None:
        """Update a parser include the url to the storage service."""
        self.parser.add_argument(
            "-s",
            "--storage-url",
            type=str,
            required=True,
            help="Storage server URL including the service port.",
        )

    def add_migration_url_arguments(self) -> None:
        """Update a parser include the url to the migration service."""
        self.parser.add_argument(
            "-m",
            "--migration-url",
            type=str,
            required=True,
            help="Migration server URL including the service port.",
        )

    def add_ingest_url_arguments(self) -> None:
        """Update a parser to add an ingest server url argument."""
        self.parser.add_argument(
            "-i",
            "--ingest-url",
            type=str,
            required=True,
            help="Ingest server URL including the service port.",
        )

    def add_request_url_arguments(self) -> None:
        """Update a parser to add a request server url argument."""
        self.parser.add_argument(
            "-r",
            "--request-url",
            type=str,
            required=False,
            help="Request server URL including the service port.",
        )

    def add_readiness_probe_file_arguments(self) -> None:
        """Update a parser to a readiness probe file path."""
        self.parser.add_argument(
            "-p",
            "--readiness-probe-file",
            type=str,
            required=True,
            help="The path to the readiness probe file.",
        )

    def add_dev_test_mode_arguments(self) -> None:
        """Update a parser to add a dev test mode argument."""
        self.parser.add_argument(
            "--dev-test-mode",
            required=False,
            action="store_true",
            help="Optionally, add a dev test mode argument.",
        )

    def add_do_not_perform_actual_ingest_and_migration_arguments(
        self
    ) -> None:
        """Update a parser to add a flag to disable actual ingest and migration."""
        self.parser.add_argument(
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

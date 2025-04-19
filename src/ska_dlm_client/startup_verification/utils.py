"""Code to provide the watchers with support functions to integrate a k8s readiness probe."""

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
    request_server_url: str = None
    readiness_probe_file: str = None

    def __init__(  # pylint: disable=too-many-arguments, disable=too-many-positional-arguments
        self,
        parser: argparse.ArgumentParser,
        add_directory_to_watch: bool = False,
        add_storage_name: bool = False,
        add_ingest_server_url: bool = False,
        add_request_server_url: bool = False,
        add_readiness_probe_file: bool = False,
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
        if add_request_server_url:
            self.add_request_server_url_arguments(parser)
            self.add_request_server_url = True
        if add_readiness_probe_file:
            self.add_readiness_probe_file_arguments(parser)
            self.add_readiness_probe_file = True

    def parse_arguments(self, args: argparse.Namespace = None):
        """Parse command line arguments and assign to class parameters."""
        if args is None:
            args = self._parser.parse_args()
        self.directory_to_watch = args.directory_to_watch if self.add_directory_to_watch else None
        self.storage_name = args.storage_name if self.add_storage_name else None
        self.ingest_server_url = args.ingest_server_url if self.add_ingest_server_url else None
        self.request_server_url = args.request_server_url if self.add_request_server_url else None
        self.readiness_probe_file = (
            args.readiness_probe_file if self.add_readiness_probe_file else None
        )

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
        """Update a parser to a add storage name argument."""
        parser.add_argument(
            "-n",
            "--storage-name",
            type=str,
            required=True,
            help="The name by which the DLM system knows the storage as.",
        )

    def add_ingest_server_url_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Update a parser to a add ingest server url argument."""
        parser.add_argument(
            "-i",
            "--ingest-server-url",
            type=str,
            required=True,
            help="Ingest server URL including the service port.",
        )

    def add_request_server_url_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Update a parser to a add request server url argument."""
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
            help="The path to the readiness probe file",
        )

    def set_application_ready(self):
        """Create the required file to indicate the application ready."""
        if self.readiness_probe_file:
            Path(self.readiness_probe_file).touch()
            logger.info("The readiness probe file has been created %s.", self.readiness_probe_file)

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Delete the readiness file on deletion of the class."""
        if self.readiness_probe_file:
            os.remove(self.readiness_probe_file)
            logger.info("The readiness probe file has been deleted %s.", self.readiness_probe_file)

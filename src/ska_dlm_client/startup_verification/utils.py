"""Code to provide the watchers with support functions to integrate a k8s readiness probe."""

import argparse


class CmdLineParameters():
    """Class to contain the common/required command line parameters."""

    add_directory_to_watch: bool = False
    add_storage_name: bool = False
    add_ingest_server_url: bool = False
    add_readiness_probe: bool = False
    directory_to_watch: str = None
    storage_name: str = None
    ingest_server_url: str = None
    readiness_probe: bool = False

    def __init__(self, parser: argparse.ArgumentParser,
                 add_directory_to_watch: bool = False,
                 add_storage_name: bool = False,
                 add_ingest_server_url: bool = False,
                 add_readiness_probe: bool = False):
        self.parser = parser
        if add_directory_to_watch:
            self.add_directory_to_watch_arguments(parser)
            self.add_directory_to_watch = True
        if add_storage_name:
            self.add_storage_name_arguments(parser)
            self.add_storage_name = True
        if add_ingest_server_url:
            self.add_ingest_server_url_arguments(parser)
            self.add_ingest_server_url = True
        if add_readiness_probe:
            self.add_readiness_probe_arguments(parser)
            self.add_readiness_probe = True

    def parse_arguments(self):
        args = self.parser.parse_args()
        self.directory_to_watch = args.directory_to_watch if self.add_directory_to_watch else None
        self.storage_name = args.storage_name if self.add_storage_name else None
        self.ingest_server_url = args.ingest_server_url if self.add_ingest_server_url else None
        self.readiness_probe = args.readiness_probe if self.add_readiness_probe else False

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

    def add_readiness_probe_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Update a parser to a readiness probe file path."""
        parser.add_argument(
            "--readiness-probe-file",
            type=str,
            required=True,
            help="The path to the readiness probe file",
        )

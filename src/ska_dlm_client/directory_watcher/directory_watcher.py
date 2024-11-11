"""Application to watch a directory for changes and send to DLM."""

import argparse
import asyncio
import logging

import ska_dlm_client.directory_watcher.config
from ska_dlm_client.directory_watcher.config import Config
from ska_dlm_client.directory_watcher.directory_watcher_task import DirectoryWatcher
from ska_dlm_client.directory_watcher.registration_processor import RegistrationProcessor

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """Define a parser for all the command line parameters."""
    parser = argparse.ArgumentParser(prog="dlm_directory_watcher")

    # Adding optional argument.
    parser.add_argument(
        "-d",
        "--directory-to-watch",
        type=str,
        required=True,
        help="Full path to directory to watch.",
    )
    parser.add_argument(
        "-i",
        "--ingest-server-url",
        type=str,
        required=True,
        help="Ingest server URL including the service port.",
    )
    parser.add_argument(
        "-n",
        "--storage-name",
        type=str,
        required=True,
        help="The name by which the DLM system know the storage as.",
    )
    parser.add_argument(
        "--reload-status-file",
        type=bool,
        required=False,
        default=False,
        help="Reload the status file that already exists in the watch directory.",
    )
    parser.add_argument(
        "--status-file-filename",
        type=str,
        required=False,
        default=ska_dlm_client.directory_watcher.config.STATUS_FILE_FILENAME,
        help="",
    )
    parser.add_argument(
        "--use-status-file",
        type=bool,
        required=False,
        default=False,
        help="Use the status file, default is NOT to use, this may change in a future release.",
    )
    return parser


def process_args(args: argparse.Namespace) -> Config:
    """Collect up all command line parameters and return a Config."""
    config = Config(
        directory_to_watch=args.directory_to_watch,
        ingest_server_url=args.ingest_server_url,
        storage_name=args.storage_name,
        reload_status_file=args.reload_status_file,
        status_file_full_filename=f"{args.directory_to_watch}/{args.status_file_filename}",
        use_status_file=args.use_status_file,
    )
    return config


def setup_directory_watcher() -> DirectoryWatcher:
    """Perform setup tasks required to run the directory watcher."""
    parser = create_parser()
    config = process_args(args=parser.parse_args())
    registration_processor = RegistrationProcessor(config)
    return DirectoryWatcher(config, registration_processor)


def main():
    """Start the directory watcher application."""
    directory_watcher = setup_directory_watcher()
    asyncio.run(directory_watcher.start(), debug=None)


if __name__ == "__main__":
    main()

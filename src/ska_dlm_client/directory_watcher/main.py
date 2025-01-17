"""Application to watch a directory for changes and send to DLM."""

import argparse
import asyncio
import logging
import signal

import ska_dlm_client.directory_watcher.config
from ska_dlm_client.directory_watcher.config import Config
from ska_dlm_client.directory_watcher.directory_watcher import (
    DirectoryWatcher,
    INotifyDirectoryWatcher,
    PollingDirectoryWatcher,
)
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
        "-p",
        "--register-dir-prefix",
        type=str,
        required=False,
        default="",
        help="The prefix to add to any data item being registered.",
    )
    parser.add_argument(
        "--use-polling-watcher",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="When defined using the polling watcher rather than iNotify event driven watcher.",
    )
    parser.add_argument(
        "--use-status-file",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Use the status file, default is NOT to use, this may change in a future release.",
    )
    parser.add_argument(
        "--reload-status-file",
        action=argparse.BooleanOptionalAction,
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
    return parser


def process_args(args: argparse.Namespace) -> Config:
    """Collect up all command line parameters and return a Config."""
    config = Config(
        directory_to_watch=args.directory_to_watch,
        ingest_server_url=args.ingest_server_url,
        storage_name=args.storage_name,
        register_dir_prefix=args.register_dir_prefix,
        status_file_absolute_path=f"{args.directory_to_watch}/{args.status_file_filename}",
        reload_status_file=args.reload_status_file,
        use_status_file=args.use_status_file,
    )
    return config


def create_directory_watcher() -> DirectoryWatcher:
    """Create a `DirectoryWatcher` factory from the CLI arguments."""
    parser = create_parser()
    args = parser.parse_args()
    config = process_args(args=args)
    registration_processor = RegistrationProcessor(config)
    if args.use_polling_watcher:  # pylint: disable=no-else-return"
        return PollingDirectoryWatcher(config, registration_processor)
    else:
        return INotifyDirectoryWatcher(config, registration_processor)


def _setup_async_graceful_termination(
    signals=(signal.SIGINT, signal.SIGTERM),
):
    """
    Gracefully handles shutdown signals by cancelling all pending tasks.

    Can only be called from an async function.
    """

    async def _shutdown(sig: signal.Signals):
        """Canel the required tasks."""
        logger.info("handling %s", sig)
        for task in [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]:
            task.cancel()

    loop = asyncio.get_running_loop()
    for signame in signals:
        loop.add_signal_handler(
            signame,
            lambda the_signame=signame: asyncio.create_task(_shutdown(sig=the_signame)),
        )


async def amain():
    """Run main in asyncio."""
    _setup_async_graceful_termination()
    directory_watcher = create_directory_watcher()
    await directory_watcher.watch()


def main():
    """Run amain function in a new loop."""
    asyncio.run(amain())


if __name__ == "__main__":
    main()

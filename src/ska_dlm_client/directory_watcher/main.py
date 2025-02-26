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
        help="The name by which the DLM system knows the storage as.",
    )
    parser.add_argument(
        "-r",
        "--storage-root-directory",
        type=str,
        required=True,
        default="",
        help="The root directory of the assocated storage, used to match relative path names.",
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
    parser.add_argument(
        "--skip-rclone-access-check-on-register",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Skip performing the rclone access check when registering a data item with DLM.",
    )
    parser.add_argument(
        "--register-contents-of-watch-directory",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="First register each file/directory in the watch directory as a data product.",
    )
    return parser


def process_args(args: argparse.Namespace) -> Config:
    """Collect up all command line parameters and return a Config."""
    config = Config(
        directory_to_watch=args.directory_to_watch,
        ingest_server_url=args.ingest_server_url,
        storage_name=args.storage_name,
        status_file_absolute_path=f"{args.directory_to_watch}/{args.status_file_filename}",
        storage_root_directory=args.storage_root_directory,
        reload_status_file=args.reload_status_file,
        use_status_file=args.use_status_file,
        rclone_access_check_on_register=not args.skip_rclone_access_check_on_register,
    )
    return config


def create_directory_watcher() -> DirectoryWatcher:
    """Create a `DirectoryWatcher` factory from the CLI arguments."""
    parser = create_parser()
    args = parser.parse_args()
    config = process_args(args=args)
    registration_processor = RegistrationProcessor(config)
    if args.register_contents_of_watch_directory:
        registration_processor.register_data_products_from_watch_directory(dry_run_for_debug=False)
    if args.use_polling_watcher:
        return PollingDirectoryWatcher(
            config=config, registration_processor=registration_processor
        )
    else:
        return INotifyDirectoryWatcher(
            config=config, registration_processor=registration_processor
        )


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

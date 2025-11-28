"""Application to watch a directory for changes and send to DLM."""

import argparse
import asyncio
import functools
import logging
import signal

import ska_dlm_client.config
from ska_dlm_client.directory_watcher.directory_watcher import (
    DirectoryWatcher,
    INotifyDirectoryWatcher,
    PollingDirectoryWatcher,
)
from ska_dlm_client.register_storage_location.main import RCLONE_CONFIG_SOURCE, setup_volume
from ska_dlm_client.registration_processor import RegistrationProcessor
from ska_dlm_client.utils import CmdLineParameters

from .config import WatcherConfig

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """Define a parser for all the command line parameters.

    Creates and configures an ArgumentParser with all the command line options
    needed for the ska-dlm-clinet's various components.

    Returns:
        An ArgumentParser instance configured with all required and optional arguments.
    """
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
        help="The root directory of the associated storage, used to match relative path names.",
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
        default=ska_dlm_client.config.STATUS_FILE_FILENAME,
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


def process_args(
    args: argparse.Namespace, cmd_line_parameters: CmdLineParameters
) -> WatcherConfig:
    """Collect all command line parameters and create a Config object.

    Args:
        args: The parsed command line arguments from argparse.
        cmd_line_parameters: Additional command line parameters processed by CmdLineParameters.

    Returns:
        A Config object initialized with all the command line parameters.
    """
    config = WatcherConfig(
        directory_to_watch=args.directory_to_watch,
        ingest_server_url=args.ingest_server_url,
        storage_name=args.storage_name,
        status_file_absolute_path=f"{args.directory_to_watch}/{args.status_file_filename}",
        storage_root_directory=args.storage_root_directory,
        reload_status_file=args.reload_status_file,
        use_status_file=args.use_status_file,
        rclone_access_check_on_register=not args.skip_rclone_access_check_on_register,
        migration_server_url=cmd_line_parameters.migration_server_url,
        migration_destination_storage_name=cmd_line_parameters.migration_destination_storage_name,
        perform_actual_ingest_and_migration=(
            cmd_line_parameters.perform_actual_ingest_and_migration
        ),
    )
    return config


def create_directory_watcher() -> DirectoryWatcher:
    """Create a DirectoryWatcher instance from the command line arguments.

    Parses command line arguments, creates a Config object, and initializes
    a DirectoryWatcher (either INotifyDirectoryWatcher or PollingDirectoryWatcher
    depending on the arguments).

    Returns:
        A DirectoryWatcher instance configured with the parsed command line arguments.
    """
    parser = create_parser()
    cmd_line_parameters = CmdLineParameters(
        parser=parser,
        add_migration_server_url=True,
        add_migration_destination_storage_name=True,
        add_readiness_probe_file=True,
        add_do_not_perform_actual_ingest_and_migration=True,
        add_dir_updates_wait_time=True,
    )
    args = parser.parse_args()
    cmd_line_parameters.parse_arguments(args)
    config = process_args(args=args, cmd_line_parameters=cmd_line_parameters)

    # For the directory_watcher we need to register the volume where the watch
    # directory is located, if not registered already.
    logger.info("API Config: %s", config)
    _ = setup_volume(
        watcher_config=config,
        api_configuration=config.ingest_configuration,
        rclone_config=RCLONE_CONFIG_SOURCE,
    )
    registration_processor = RegistrationProcessor(config)
    if args.register_contents_of_watch_directory:
        registration_processor.register_data_products_from_watch_directory()
    # We want the watcher to set readiness probe file when ready so pass class during creation
    if args.use_polling_watcher:  # pylint: disable=no-else-return"
        return PollingDirectoryWatcher(
            config=config,
            registration_processor=registration_processor,
            cmd_line_parameters=cmd_line_parameters,
        )
    else:
        return INotifyDirectoryWatcher(
            config=config,
            registration_processor=registration_processor,
            cmd_line_parameters=cmd_line_parameters,
        )


async def amain():
    """Run the main application logic in an asyncio context.

    Creates a DirectoryWatcher, sets up signal handlers for graceful shutdown,
    and starts the directory watching process.
    """
    directory_watcher = create_directory_watcher()

    def stop_watcher(signo: signal.Signals):
        logger.info("Received %s, stopping directory watcher", signo.name)
        directory_watcher.stop()

    loop = asyncio.get_running_loop()
    for signo in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(signo, functools.partial(stop_watcher, signo))
    await directory_watcher.watch()


def main():
    """Run the application's main entry point.

    Creates a new asyncio event loop and runs the amain coroutine in it.
    This function is the entry point when the module is executed directly.
    """
    asyncio.run(amain())


if __name__ == "__main__":
    main()

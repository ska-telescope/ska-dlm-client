"""Application to watch a directory for changes and send to DLM."""

import argparse
import asyncio
import functools
import logging
import signal

import ska_ser_logging

from ska_dlm_client.directory_watcher.directory_watcher import (
    DirectoryWatcher,
    INotifyDirectoryWatcher,
    PollingDirectoryWatcher,
)
from ska_dlm_client.register_storage_location.main import RCLONE_CONFIG_SOURCE, setup_volume
from ska_dlm_client.registration_processor import RegistrationProcessor
from ska_dlm_client.directory_watcher.config import WatcherArgs

from .config import WatcherConfig

logger = logging.getLogger(__name__)


def process_args(args: argparse.Namespace) -> WatcherConfig:
    """Collect all command line parameters and create a Config object.

    Args:
        args: The parsed command line arguments from argparse.
        cmd_line_parameters: Additional command line parameters processed by CmdLineParameters.

    Returns:
        A Config object initialized with all the command line parameters.
    """
    if args.source_name:
        RCLONE_CONFIG_SOURCE["name"] = args.source_name
    # TODO: not all command line args are being processed below
    config = WatcherConfig(
        source_name=args.source_name,
        target_name=args.target_name,
        storage_url=args.storage_url,
        migration_url=args.migration_url,
        ingest_url=args.ingest_url,
        reload_status_file=args.reload_status_file,
        rclone_access_check_on_register=not args.skip_rclone_access_check_on_register,
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
    # parser = argparse.ArgumentParser(prog="dlm_directory_watcher")
    # This is only enabling the additional parameters required only for the directory watcher.
    # We want the watcher to set readiness probe file when ready so pass class during creation
    cmd_line_parameters = WatcherArgs()
    args = cmd_line_parameters.parser.parse_args()
    cmd_line_parameters.parse_arguments(args)
    config = process_args(args=args)

    # For the directory_watcher we need to register the volume where the watch directory is located
    _ = setup_volume(
        watcher_config=config,
        api_configuration=config.ingest_configuration,
        rclone_config=RCLONE_CONFIG_SOURCE,
        storage_url=config.storage_url,
    )
    registration_processor = RegistrationProcessor(config)
    if args.register_contents_of_watch_directory:
        registration_processor.register_data_products_from_watch_directory()
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
    ska_ser_logging.configure_logging(logging.INFO)
    asyncio.run(amain())


if __name__ == "__main__":
    main()

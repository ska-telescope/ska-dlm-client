"""Application to verify the state of the DLM client, intended for startup."""

import argparse
import asyncio
import logging
import signal

import ska_dlm_client.startup_verification.utils as utils
from ska_dlm_client.openapi import configuration

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """Define a parser for all the command line parameters."""
    parser = argparse.ArgumentParser(prog="dlm_directory_watcher")

    # Adding optional argument.
    utils.add_storage_name_arguments(parser)
    utils.add_ingest_server_arguments(parser)
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
    if args.use_polling_watcher:  # pylint: disable=no-else-return"
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




def main():
    """Run main in its own function."""
    parser = create_parser()
    args = parser.parse_args()
    directory_to_watch = args.directory_to_watch
    ingest_server_url = args.ingest_server_url
    storage_name = args.storage_name

    ingest_configuration = configuration.Configuration(host=ingest_server_url)




if __name__ == "__main__":
    main()

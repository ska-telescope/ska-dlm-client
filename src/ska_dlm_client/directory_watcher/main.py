"""Application to watch a directory for changes and send to DLM."""

import argparse
import asyncio
import functools
import logging
import signal

from ska_dlm_client.exception_handling_typer import ExceptionHandlingTyper
from ska_dlm_client.typer_types import JsonObjectOption
from ska_dlm_client.typer_utils import dump_short_stacktrace

import ska_dlm_client.directory_watcher.config
from ska_dlm_client.directory_watcher.config import Config
from ska_dlm_client.directory_watcher.directory_watcher import (
    DirectoryWatcher,
    INotifyDirectoryWatcher,
    PollingDirectoryWatcher,
)
from ska_dlm_client.directory_watcher.registration_processor import RegistrationProcessor
from ska_dlm_client.startup_verification.utils import CmdLineParameters

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

cli = ExceptionHandlingTyper()

@cli.command()
def create_directory_watcher(
    directory_to_watch: str,
    storage_name: str,
    ingest_server_url: str = "http://localhost:8080",
    request_server_url: str = "http://localhost:8081",
    storage_root_directory: str = "/tmp",
    use_polling_watcher: bool = False,
    use_status_file: bool = False,
    status_file_absolute_path: str = "/tmp/watch_dir/.dlm_status.json",
    status_file_filename: str = ska_dlm_client.directory_watcher.config.STATUS_FILE_FILENAME,
    reload_status_file: bool = False,
    skip_rclone_access_check_on_register: bool = False,
    register_contents_of_watch_directory: bool = False,
) -> DirectoryWatcher:
    """Create a `DirectoryWatcher` from the CLI arguments.

    The DLM directory watcher application watches a directory for new files and directories
    and registers them as data items with the DLM Ingest service. The directory to watch
    must be within a storage volume that has been registered with the DLM system under the name
    given by the storage_name parameter.

    Parameters
    ----------
    directory_to_watch
        The path to watch for new files/directories to register. If it is an absolute path
        it must be compatible with the root directory of the storage registered under storage_name.
    storage_name
        The name of the registered storage volume.
    ingest_server_url
        The URL of the DLM Ingest service including the port number.
    request_server_url
        The URL of the DLM Request service including the port number.
    storage_root_directory
        The root directory of the storage registered under storage_name.
    use_polling_watcher
        Use the polling directory watcher rather than the default iNotify event driven watcher.
    use_status_file
        Use a status file to track what has been registered.
    status_file_absolute_path
        The absolute path to the status file to use, if any.
    status_file_filename
        The name of the status file to use within the watch directory.
    reload_status_file
        If the status file already exists in the watch directory, reload it.
    skip_rclone_access_check_on_register
        Skip the rclone access check when registering a data item with DLM. This
        ensures that the DLM system can access the data item, thus it is not recommended
        to skip this check unless you are sure that the DLM system will be able to access
        the data item.
    register_contents_of_watch_directory
        When starting the directory watcher, first register each file/directory in the
        watch directory as a data product.

    Returns
    -------
    INotifyDirectoryWatcher or PollingDirectoryWatcher
        The directory watcher that will watch the directory and register new files/directories

    Raises
    ------
    InvalidQueryParameters

    """
    # parser = create_parser()
    # cmd_line_parameters = CmdLineParameters(parser, add_readiness_probe_file=True)
    # args = parser.parse_args()
    # config = process_args(args=args)
    # cmd_line_parameters.parse_arguments(args)
    config = Config(
        directory_to_watch=directory_to_watch,
        ingest_server_url=ingest_server_url,
        request_server_url=request_server_url,
        storage_name=storage_name,
        status_file_absolute_path=status_file_absolute_path,
        storage_root_directory=storage_root_directory,
        reload_status_file=reload_status_file,
        use_status_file=use_status_file,
        rclone_access_check_on_register=not skip_rclone_access_check_on_register
    )
    registration_processor = RegistrationProcessor(config)
    if register_contents_of_watch_directory:
        registration_processor.register_data_products_from_watch_directory(dry_run_for_debug=False)
    # We want the watcher to set readiness probe file when ready so pass class during creation
    if use_polling_watcher:  # pylint: disable=no-else-return"
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
    """Run main in asyncio."""
    app = ExceptionHandlingTyper(pretty_exceptions_show_locals=False, result_callback=print)
    app.add_typer(cli, name="directory-watcher", help="Watch directory for new data files.")
    # directory_watcher = create_directory_watcher()
    directory_watcher = app()

    def stop_watcher(signo: signal.Signals):
        logger.info("Received %s, stopping directory watcher", signo.name)
        directory_watcher.stop()

    loop = asyncio.get_running_loop()
    for signo in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(signo, functools.partial(stop_watcher, signo))
    await directory_watcher.watch()

def smain():
    """Run synchronously."""
    app = ExceptionHandlingTyper(pretty_exceptions_show_locals=False, result_callback=print)
    app.add_typer(cli, name="directory-watcher", help="Watch directory for new data files.")
    # directory_watcher = create_directory_watcher()
    directory_watcher = app()
    directory_watcher.watch()

def main():
    """Run amain function in a new loop."""
    # asyncio.run(amain())
    smain()


if __name__ == "__main__":
    main()

"""Application to watch a directory for changes and send to DLM."""

import argparse
import asyncio
import logging

from watchfiles import Change, awatch

import ska_dlm_client.directory_watcher.config
from ska_dlm_client.directory_watcher.config import Config
from ska_dlm_client.directory_watcher.registration_processor import RegistrationProcessor

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class DirectoryWatcher:
    """Class for the running of the directory_watcher."""

    def __init__(self, config: Config, watcher_registration_processor: RegistrationProcessor):
        """Initialise with the given Config."""
        self._config = config
        self._registration_processor = watcher_registration_processor

    def process_directory_entry_change(self, entry: tuple[Change, str]):
        """TODO: Test function currently."""
        logger.info("in do process_directory_entry_change %s", entry)
        change_type = entry[0]
        full_path = entry[1]
        relative_path = full_path.replace(f"{self._config.directory_to_watch}/", "")
        if self._config.status_file_full_filename == full_path:
            return
        if change_type is Change.added:
            self._registration_processor.add_path(full_path=full_path, relative_path=relative_path)
        # TODO: Change.deleted Change.modified mayh need support

    async def start(self):
        """Start watching the given directory."""
        async for changes in awatch(
            self._config.directory_to_watch
        ):  # type: Set[tuple[Change, str]]
            for change in changes:
                logger.info("in main %s", change)
                self.process_directory_entry_change(change)


def process_args():
    """Collect up all command line parameters."""
    parser = argparse.ArgumentParser(prog="dlm_directory_watcher")

    # Adding optional argument.
    parser.add_argument(
        "-d",
        "--directory_to_watch",
        type=str,
        required=True,
        help="Full path to directory to watch.",
    )
    parser.add_argument(
        "-n",
        "--storage_name",
        type=str,
        required=True,
        help="The name by which the DLM system know the storage as.",
    )
    parser.add_argument(
        "-s",
        "--server_url",
        type=str,
        required=True,
        help="Server URL excluding any service name and port.",
    )
    parser.add_argument(
        "--reload_status_file",
        type=bool,
        required=False,
        const=True,
        help="xxxxxxxxxxxxxxxxxxxxxx",
    )
    parser.add_argument(
        "--ingest_service_port",
        type=int,
        required=False,
        const=ska_dlm_client.directory_watcher.config.INGEST_SERVICE_PORT,
        help="",
    )
    parser.add_argument(
        "--storage_service_port",
        type=int,
        required=False,
        const=ska_dlm_client.directory_watcher.config.STORAGE_SERVICE_PORT,
        help="",
    )

    # Read arguments from command line
    args = parser.parse_args()

    return Config(
        directory_to_watch=args.directory_to_watch(),
        storage_name=args.storage_name,
        server_url=args.server_url,
        reload_status_file=args.reload_status_file,
        ingest_service_port=args.ingest_service_port,
        storage_service_port=args.storage_service_port,
        status_file_full_filename=args.status_file_full_filename,
    )


if __name__ == "__main__":
    main_config = process_args()
    registration_processor = RegistrationProcessor(main_config)
    directory_watcher = DirectoryWatcher(main_config, registration_processor)
    asyncio.run(directory_watcher.start(), debug=None)

"""Application to watch a directory for changes and send to DLM."""

import asyncio
import logging
import time
from os import listdir
from os.path import isdir, isfile, islink
from pathlib import Path

from watchfiles import Change, awatch

from ska_dlm_client.directory_watcher.configuration_details import (
    DLMConfiguration,
    WatchConfiguration,
)
from ska_dlm_client.directory_watcher.directory_watcher_entry import (
    DirectoryWatcherEntries,
    DirectoryWatcherEntry,
)
from ska_dlm_client.directory_watcher.testing import (
    init_location_for_testing,
    init_storage_for_testing,
)
from ska_dlm_client.openapi import api_client, configuration
from ska_dlm_client.openapi.dlm_api import ingest_api

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
ingest_configuration = configuration.Configuration(host=DLMConfiguration.INGEST_URL)
storage_configuration = configuration.Configuration(host=DLMConfiguration.STORAGE_URL)
directory_watcher_entries = DirectoryWatcherEntries(
    entries_file=WatchConfiguration.WATCHER_STATUS_FULL_FILENAME,
    reload_from_cache=WatchConfiguration.RELOAD_WATCHER_STATUS_FILE,
)


def follow_sym_link(path: Path) -> Path:
    """Return the real path after following the sysmlink."""
    if path.is_symlink():
        path.is_dir()
        path.is_file()


def register_entry(relative_path: str):
    """Register the given entry_path."""
    with api_client.ApiClient(ingest_configuration) as ingest_api_client:
        api_ingest = ingest_api.IngestApi(ingest_api_client)
        response = api_ingest.register_data_item_ingest_register_data_item_post(
            item_name=relative_path,
            uri=relative_path,
            storage_name=WatchConfiguration.STORAGE_NAME,
            storage_id=storage_id,
            eb_id=WatchConfiguration.EB_ID,
        )
    # TODO: decode JSON response
    dlm_registration_id = response
    time_registered = time.time()

    directory_watcher_entry = DirectoryWatcherEntry(
        file_or_directory=relative_path,
        dlm_storage_id=storage_id,
        dlm_registration_id=dlm_registration_id,
        time_registered=time_registered,
    )
    directory_watcher_entries.add(directory_watcher_entry)
    directory_watcher_entries.save_to_file()
    logger.info("entry %s added.", relative_path)


def add_path(full_path: str, relative_path: str):
    """Add the given relative_path to the DLM."""
    logger.info("in add_path with %s and %s", full_path, relative_path)
    if isfile(full_path):
        logger.info("entry is file")
        register_entry(relative_path=relative_path)
    elif isdir(full_path):
        logger.info("entry is directory")
        if relative_path.endswith(DLMConfiguration.DIRECTORY_IS_MEASUREMENT_SET_SUFFIX):
            # if a measurement set then just add directory
            register_entry(relative_path=relative_path)
        else:
            # otherwise add each file or directory
            dir_entries = listdir(full_path)
            for dir_entry in dir_entries:
                new_full_path = f"{full_path}/{dir_entry}"
                new_relative_path = f"{relative_path}/{dir_entry}"
                add_path(full_path=new_full_path, relative_path=new_relative_path)
    else:
        if islink(full_path):
            error_text = f"Symbolic links are currently not supported: {relative_path}"
        else:
            error_text = f"Unspported file/directory entry type: {relative_path}"
        logging.error(error_text)
        raise RuntimeError(error_text)


def process_directory_entry_change(entry: tuple[Change, str]):
    """TODO: Test function currently."""
    logger.info("in do process_directory_entry_change %s", entry)
    change_type = entry[0]
    full_path = entry[1]
    relative_path = full_path.replace(f"{WATCH_DIRECTORY}/", "")
    if WatchConfiguration.WATCHER_STATUS_FULL_FILENAME == full_path:
        return
    if change_type is Change.added:
        add_path(full_path=full_path, relative_path=relative_path)
    # TODO: Change.deleted Change.modified mayh need support


async def main():
    """Start watching the given directory."""
    async for changes in awatch(WATCH_DIRECTORY):  # type: Set[tuple[Change, str]]
        for change in changes:
            logger.info("in main %s", change)
            process_directory_entry_change(change)


WATCH_DIRECTORY = WatchConfiguration.DIRECTORY_TO_WATCH

# TODO: It would be expected that the following config would already be
# completed in prod but leaving in place for now.
location_id = init_location_for_testing(storage_configuration)
storage_id = init_storage_for_testing(storage_configuration, the_location_id=location_id)
# test_ingest_item()

asyncio.run(main(), debug=None)

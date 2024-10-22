"""Application to watch a directory for changes and send to DLM."""

import asyncio
import json
import logging
import time
from enum import Enum
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
from ska_dlm_client.openapi import api_client, configuration
from ska_dlm_client.openapi.dlm_api import ingest_api

logger = logging.getLogger(__name__)
ingest_configuration = configuration.Configuration(host=DLMConfiguration.INGEST_URL)
storage_configuration = configuration.Configuration(host=DLMConfiguration.STORAGE_URL)
directory_watcher_entries = DirectoryWatcherEntries(
    entries_file=(WatchConfiguration.WATCHER_STATUS_FULL_FILENAME),
    reload_from_cache=WatchConfiguration.RELOAD_WATCHER_STATUS_FILE,
)


class InternalState(Enum):
    """The internal state for each entry."""

    IN_QUEUE = 0
    INGESTING = 1
    INGESTED = 2
    BAD = 3


class PathType(Enum):
    """What does the entry path represent."""

    FILE = 0
    DIRECTORY = 1
    MEASUREMENT_SET = 2


# def support_path_type(path: Path) -> bool:
#    """Is the given path supported."""
#    pass


def follow_sym_link(path: Path) -> Path:
    """Return the real path after following the sysmlink."""
    if path.is_symlink():
        path.is_dir()
        path.is_file()


def register_entry(entry_path: Path):
    """Register the given entry_path."""
    full_path = entry_path.resolve()
    # is_measurement_set = False
    # if entry_path.is_dir() and entry_path.as_posix().endswith(
    #     DLMConfiguration.DIRECTORY_IS_MEASUREMENT_SET_SUFFIX
    # ):
    #     is_measurement_set = True
    with api_client.ApiClient(ingest_configuration) as the_api_client:
        api_ingest = ingest_api.IngestApi(the_api_client)
        response = api_ingest.register_data_item_ingest_register_data_item_post(
            item_name="",
            uri=full_path,
            storage_name=None,
            storage_id="needed",
            item_format=None,
            eb_id="needed????",
            authorization="bearer token",
            body="what is this meant to be ???",
        )
    # TODO: decode JSON response
    json.dumps(response)
    dlm_registration_id = ""
    time_registered = time.time()

    directory_watcher_entry = DirectoryWatcherEntry(
        file_or_directory=full_path,
        dlm_storage_id=WatchConfiguration.STORAGE_ID_FOR_REGISTRATION,
        dlm_registration_id=dlm_registration_id,
        time_registered=time_registered,
    )
    directory_watcher_entries.append(directory_watcher_entry)


def do_something_with_new_entry(entry: tuple[Change, str]):
    """TODO: Test function currently."""
    print("in do something " + entry)
    entry_path = Path(entry[1])
    print(entry_path)
    #    pp = PosixPath(entry[1])
    #    print(pp)
    if entry[0] is Change.added:
        register_entry(entry_path)
    if entry[0] is not Change.deleted:
        path = entry_path.resolve()
        if path.exists():
            stat = path.stat()
            print(stat)
        else:
            print("Cannot find resolved path " + path)


async def main():
    """Start watching the given directory."""
    async for changes in awatch(WATCH_DIRECTORY):  # type: Set[tuple[Change, str]]
        for change in changes:
            print("in main " + change)
            do_something_with_new_entry(change)


# with api_client.ApiClient(storage_configuration) as api_client:
#    api_storage = storage_api.StorageApi(api_client)
# with api_client.ApiClient(ingest_configuration) as api_client:
#    api_ingest = ingest_api.IngestApi(api_client)


WATCH_DIRECTORY = WatchConfiguration.DIRECTORY_TO_WATCH
DLM_STORAGE_ID = WatchConfiguration.STORAGE_ID_FOR_REGISTRATION

asyncio.run(main(), debug=None)

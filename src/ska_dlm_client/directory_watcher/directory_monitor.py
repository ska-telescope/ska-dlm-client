#
import asyncio
import json
import logging
import time
from enum import Enum
from pathlib import Path
from typing import Set

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
    IN_QUEUE = 0
    INGESTING = 1
    INGESTED = 2
    BAD = 3


class PathType(Enum):
    FILE = 0
    DIRECTORY = 1
    MEASUREMENT_SET = 2


def supportPathType(path: Path) -> bool:
    pass


def followSymLink(path: Path) -> Path:
    if path.is_symlink():
        path.is_dir()
        path.is_file()


def registerEntry(entry_path: Path):
    full_path = entry_path.resolve()
    is_measurement_set = False
    if entry_path.is_dir() and entry_path.as_posix().endswith(
        DLMConfiguration.DIRECTORY_IS_MEASUREMENT_SET_SUFFIX
    ):
        is_measurement_set = True
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


def doSomethingWithNewEntry(entry: tuple[Change, str]):
    print("in do something " + entry.__str__())
    entry_path = Path(entry[1])
    print(entry_path)
    #    pp = PosixPath(entry[1])
    #    print(pp)
    if entry[0] is Change.added:
        registerEntry(entry_path)
    if entry[0] is not Change.deleted:
        path = entry_path.resolve()
        if path.exists():
            stat = path.stat()
            print(stat)
        else:
            print("Cannot find resolved path " + path.__str__())


def load_or_instantiate_directory_entries():
    watcher_status_file = (
        f"{WatchConfiguration.DIRECTORY_TO_WATCH}/"
        f"{WatchConfiguration.WATCHER_STATUS_FILENAME})"
    )


async def main():
    async for changes in awatch(watch_directory):  # type: Set[tuple[Change, str]]
        for change in changes:
            print("in main " + change.__str__())
            doSomethingWithNewEntry(change)


# with api_client.ApiClient(storage_configuration) as api_client:
#    api_storage = storage_api.StorageApi(api_client)
# with api_client.ApiClient(ingest_configuration) as api_client:
#    api_ingest = ingest_api.IngestApi(api_client)


watch_directory = WatchConfiguration.DIRECTORY_TO_WATCH
dlm_storage_id = WatchConfiguration.STORAGE_ID_FOR_REGISTRATION

asyncio.run(main(), debug=None)

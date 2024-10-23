"""Application to watch a directory for changes and send to DLM."""

import asyncio
import json
import logging
import sys
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
from ska_dlm_client.openapi.dlm_api import ingest_api, storage_api

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
    with api_client.ApiClient(ingest_configuration) as ingest_api_client:
        api_ingest = ingest_api.IngestApi(ingest_api_client)
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
        dlm_storage_id=storage_id,
        dlm_registration_id=dlm_registration_id,
        time_registered=time_registered,
    )
    directory_watcher_entries.append(directory_watcher_entry)


def do_something_with_new_entry(entry: tuple[Change, str]):
    """TODO: Test function currently."""
    logger.info("in do something %s", entry)
    entry_path = Path(entry[1])
    logger.info(entry_path)
    #    pp = PosixPath(entry[1])
    #    print(pp)
    if entry[0] is Change.added:
        register_entry(entry_path)
    if entry[0] is not Change.deleted:
        path = entry_path.resolve()
        if path.exists():
            stat = path.stat()
            logger.info(stat)
        else:
            logger.info("Cannot find resolved path %s", path)


def init_location_for_testing() -> str:
    """Perform location initialisation to be used when testing."""
    with api_client.ApiClient(storage_configuration) as the_api_client:
        api_storage = storage_api.StorageApi(the_api_client)

        # get the location_id
        response = api_storage.query_location_storage_query_location_get(
            location_name=WatchConfiguration.LOCATION_NAME
        )
        logger.info("query_location_response: %s", response)
        if not isinstance(response, list):
            logger.error("Unexpected response from query_location_storage")
            sys.exit(1)
        if len(response) == 1:
            the_location_id = response[0]["location_id"]
        else:
            response = api_storage.init_location_storage_init_location_post(
                location_name=WatchConfiguration.LOCATION_NAME,
                location_type=WatchConfiguration.LOCATION_TYPE,
                location_country=WatchConfiguration.LOCATION_COUNTRY,
                location_city=WatchConfiguration.LOCATION_CITY,
                location_facility=WatchConfiguration.LOCATION_FACILITY,
            )
            the_location_id = response
        logger.info("location_id: %s", the_location_id)
    return the_location_id


def init_storage_for_testing(the_location_id: str) -> str:
    """Perform storge initialisation to be used when testing."""
    assert the_location_id is not None
    with api_client.ApiClient(storage_configuration) as the_api_client:
        api_storage = storage_api.StorageApi(the_api_client)
        # Get the storage_id
        response = api_storage.query_storage_storage_query_storage_get(
            storage_name=WatchConfiguration.STORAGE_NAME
        )
        if not isinstance(response, list):
            logger.error("Unexpected response from query_storage_storage")
            sys.exit(1)
        if len(response) == 1:
            the_storage_id = response[0]["storage_id"]
        else:
            response = api_storage.init_storage_storage_init_storage_post(
                storage_name=WatchConfiguration.STORAGE_NAME,
                location_name=WatchConfiguration.LOCATION_NAME,
                location_id=the_location_id,
                storage_type=WatchConfiguration.STORAGE_TYPE,
            )
            the_storage_id = response
        logger.info("storage_id: %s", the_storage_id)

        # Setup the storage config
        response = api_storage.create_storage_config_storage_create_storage_config_post(
            storage_id=the_storage_id, config=WatchConfiguration.STORAGE_CONFIG
        )
        storage_config_id = response
        logger.info("storage_config_id: %s", storage_config_id)
    return the_storage_id


def test_ingest_item():
    """Test ingesting a single item."""
    with api_client.ApiClient(ingest_configuration) as the_api_client:
        api_ingest = ingest_api.IngestApi(the_api_client)
        the_path = "k"
        response = api_ingest.register_data_item_ingest_register_data_item_post(
            item_name=the_path,
            uri=the_path,
            storage_name=WatchConfiguration.STORAGE_NAME,
            storage_id=storage_id,
            eb_id=WatchConfiguration.EB_ID
        )
        logger.info("register_data_item_response: %s", response)


async def main():
    """Start watching the given directory."""
    async for changes in awatch(WATCH_DIRECTORY):  # type: Set[tuple[Change, str]]
        for change in changes:
            logger.info("in main %s", change)
            do_something_with_new_entry(change)


WATCH_DIRECTORY = WatchConfiguration.DIRECTORY_TO_WATCH

# TODO: It would be expected that the following config would already be
# completed in prod but leaving in place for now.
location_id = init_location_for_testing()
storage_id = init_storage_for_testing(the_location_id=location_id)
test_ingest_item()

asyncio.run(main(), debug=None)

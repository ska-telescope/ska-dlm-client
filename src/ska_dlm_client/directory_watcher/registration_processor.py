"""Register the given file or directory with the DLM."""

import logging
import os
import time
from os.path import isdir, isfile, islink
from pathlib import Path

import ska_dlm_client.directory_watcher.config
from ska_dlm_client.directory_watcher.config import Config
from ska_dlm_client.directory_watcher.data_product_metadata import DataProductMetadata
from ska_dlm_client.directory_watcher.directory_watcher_entries import DirectoryWatcherEntry
from ska_dlm_client.openapi import api_client
from ska_dlm_client.openapi.dlm_api import ingest_api
from ska_dlm_client.openapi.exceptions import OpenApiException

logger = logging.getLogger(__name__)


class RegistrationProcessor:
    """The class used for processing of the registration."""

    _config: Config

    def __init__(self, config: Config):
        """Nothing to current currently init."""
        self._config = config

    def set_config(self, config: Config):
        """Set/reset the config."""
        self._config = config

    def _follow_sym_link(self, path: Path) -> Path:
        """Return the real path after following the symlink."""
        if path.is_symlink():
            path.resolve()
        return path

    def _register_entry(self, relative_path: str, metadata: dict):
        """Register the given entry_path."""
        with api_client.ApiClient(self._config.ingest_configuration) as ingest_api_client:
            api_ingest = ingest_api.IngestApi(ingest_api_client)
            try:
                uri = (
                    relative_path
                    if self._config.register_dir_prefix == ""
                    else f"{self._config.register_dir_prefix}/{relative_path}"
                )
                response = api_ingest.register_data_item_ingest_register_data_item_post(
                    item_name=relative_path,
                    uri=uri,
                    storage_name=self._config.storage_name,
                    body=metadata,
                )
            except OpenApiException as err:
                logger.error("OpenApiException caught during register_data_item\n%s", err)
                logger.error("Ignoring and continueing.....")
                return

        # TODO: decode JSON response
        dlm_registration_id = str(response)
        time_registered = time.time()

        directory_watcher_entry = DirectoryWatcherEntry(
            file_or_directory=relative_path,
            dlm_storage_name=self._config.storage_name,
            dlm_registration_id=dlm_registration_id,
            time_registered=time_registered,
        )
        self._config.directory_watcher_entries.add(directory_watcher_entry)
        self._config.directory_watcher_entries.save_to_file()
        logger.info("entry %s added.", relative_path)

    def add_path(self, full_path: str, relative_path: str):
        """Add the given relative_path to the DLM.

        If full_path is a file, a single file will be registered with the DLM.
        If full_path is a directory, and it is an MS, then ingest a single data
        item for the whole directory.
        If full_path is a directory, and it is NOT an MS, then recursively ingest
        all files and subdirectories
        If full_path is a symlink, then not currently supported.
        """
        logger.info("in add_path with %s and %s", full_path, relative_path)
        data_items, metadata = paths_and_metadata(full_path=full_path, relative_path=relative_path)
        logger.info("data_items %s", data_items)
        logger.info("metadata %s", metadata)
        if data_items is None or metadata is None:
            logging.error("No files and/or metadata found, NOT added to DLM!")
        else:
            for data_item in data_items:
                # Send the same metadata for each data item
                self._register_entry(relative_path=data_item, metadata=metadata)


def _directory_contains_only_files(full_path: str) -> bool:
    """Return True if the given directory contains only files."""
    for entry in os.listdir(full_path):
        if os.path.isdir(full_path + entry):
            return False
    return True


def _directory_list_minus_metadata_file(full_path: str, relative_path: str) -> list[str]:
    """Return a listing of the given full_path directory without the metadata file."""
    path_list: list[str] = []
    for entry in os.listdir(full_path):
        if not entry == ska_dlm_client.directory_watcher.config.METADATA_FILENAME:
            path_list.append(os.path.join(relative_path, entry))
    return path_list


def paths_and_metadata(full_path: str, relative_path: str) -> (list[str], dict):
    """Return the list of data items and their associated metadata."""
    logger.info("working with path %s", full_path)
    path_list = None
    metadata = None
    if isfile(full_path):
        logger.info("entry is file")
        path_list = [relative_path]
        metadata = DataProductMetadata(full_path).as_dict()
    elif isdir(full_path):
        if islink(full_path):
            linked_path = os.readlink(full_path)
            logger.info("entry is symbolic link to a directory %s -> %s", full_path, linked_path)
        else:
            logger.info("entry is directory")

        # if a measurement set then just add directory
        if relative_path.lower().endswith(
            ska_dlm_client.directory_watcher.config.DIRECTORY_IS_MEASUREMENT_SET_SUFFIX
        ):
            path_list = [relative_path]
            metadata = DataProductMetadata(full_path).as_dict()
        else:
            path_list = _directory_list_minus_metadata_file(
                full_path=full_path, relative_path=relative_path
            )
            logger.info("%s: %s", full_path, path_list)
            if _directory_contains_only_files(full_path):
                metadata = DataProductMetadata(full_path).as_dict()
            else:
                logger.error("subdirectories of data_item path does not support subdirecories.")
    elif islink(full_path):
        logger.error("entry is symbolic link NOT pointing to a drectory, this is not handled")
    else:
        logger.error("entry is unknown")
    return path_list, metadata

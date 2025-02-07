"""Register the given file or directory with the DLM."""

import logging
import os
import time
from dataclasses import dataclass
from enum import Enum
from os.path import isdir, isfile, islink
from pathlib import Path

from typing_extensions import Self

import ska_dlm_client.directory_watcher.config
from ska_dlm_client.directory_watcher.config import Config
from ska_dlm_client.directory_watcher.data_product_metadata import DataProductMetadata
from ska_dlm_client.directory_watcher.directory_watcher_entries import DirectoryWatcherEntry
from ska_dlm_client.openapi import api_client
from ska_dlm_client.openapi.dlm_api import ingest_api
from ska_dlm_client.openapi.exceptions import OpenApiException

logger = logging.getLogger(__name__)


class ItemType(str, Enum):
    """Data Item on the filesystem."""

    UNKOWN = "unkown"
    """A single file."""
    FILE = "file"
    """A single file."""
    CONTAINER = "container"
    """A directory superset with parents."""


@dataclass
class Item:
    """Data Item related information to aid registration."""

    path_rel_to_watch_dir: str
    item_type: ItemType
    metadata: DataProductMetadata
    parent: Self
    uuid: str = None

    def __init__(
        self,
        path_rel_to_watch_dir: str,
        item_type: ItemType,
        metadata: DataProductMetadata,
        parent: Self = None,
    ):
        """Initialise the Item with required values.

        The uuid is updated after being registered.
        """
        self.path_rel_to_watch_dir = path_rel_to_watch_dir
        self.item_type = item_type
        self.metadata = metadata
        self.parent = parent


class RegistrationProcessor:
    """The class used for processing of the registration."""

    _config: Config

    def __init__(self, config: Config):
        """Initialise the RegistrationProcessor with the given config."""
        self._config = config

    def set_config(self, config: Config):
        """Set/reset the config."""
        self._config = config

    def _follow_sym_link(self, path: Path) -> Path:
        """Return the real path after following the symlink."""
        if path.is_symlink():
            path.resolve()
        return path

    def _register_entry(self, path_rel_to_watch_dir: str, metadata: dict):
        """Register the given entry_path."""
        with api_client.ApiClient(self._config.ingest_configuration) as ingest_api_client:
            api_ingest = ingest_api.IngestApi(ingest_api_client)
            try:
                # Generate the uri relative to the root directory.
                uri = (
                    path_rel_to_watch_dir
                    if self._config.ingest_register_path_to_add == ""
                    else f"{self._config.ingest_register_path_to_add}/{path_rel_to_watch_dir}"
                )
                response = api_ingest.register_data_item_ingest_register_data_item_post(
                    item_name=path_rel_to_watch_dir,
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
            file_or_directory=path_rel_to_watch_dir,
            dlm_storage_name=self._config.storage_name,
            dlm_registration_id=dlm_registration_id,
            time_registered=time_registered,
        )
        self._config.directory_watcher_entries.add(directory_watcher_entry)
        self._config.directory_watcher_entries.save_to_file()
        logger.info("entry %s added.", path_rel_to_watch_dir)

    def add_path(self, absolute_path: str, path_rel_to_watch_dir: str):
        """Add the given path_rel_to_watch_dir to the DLM.

        If absolute_path is a file, a single file will be registered with the DLM.
        If absolute_path is a directory, and it is an MS, then ingest a single data
        item for the whole directory.
        If absolute_path is a directory, and it is NOT an MS, then recursively ingest
        all files and subdirectories
        """
        logger.info("in add_path with %s and %s", absolute_path, path_rel_to_watch_dir)
        data_item_relative_path_list, metadata = generate_paths_and_metadata(
            absolute_path=absolute_path, path_rel_to_watch_dir=path_rel_to_watch_dir
        )
        logger.info("data_item_relative_path_list %s", data_item_relative_path_list)
        logger.info("metadata %s", metadata)
        if data_item_relative_path_list is None or metadata is None:
            logging.error("No files and/or metadata found, NOT added to DLM!")
        else:
            for data_item_relative_path in data_item_relative_path_list:
                # Send the same metadata for each data item
                self._register_entry(
                    path_rel_to_watch_dir=data_item_relative_path, metadata=metadata
                )


def _directory_contains_only_files(absolute_path: str) -> bool:
    """Return True if the given directory contains only files."""
    for entry in os.listdir(absolute_path):
        if os.path.isdir(absolute_path + entry):
            return False
    return True


def _directory_list_minus_metadata_file(
    absolute_path: str, path_rel_to_watch_dir: str
) -> list[str]:
    """Return a listing of the given absolute_path directory without the metadata file."""
    path_list: list[str] = []
    for entry in os.listdir(absolute_path):
        if not entry == ska_dlm_client.directory_watcher.config.METADATA_FILENAME:
            path_list.append(os.path.join(path_rel_to_watch_dir, entry))
    return path_list


def _item_list_minus_metadata_file(
    absolute_path: str, path_rel_to_watch_dir: str, metadata: DataProductMetadata, parent: Item
) -> list[Item]:
    """Return a listing of the given absolute_path directory without the metadata file."""
    item_list: list[Item] = []
    for entry in os.listdir(absolute_path):
        if not entry == ska_dlm_client.directory_watcher.config.METADATA_FILENAME:
            item_list.append(
                Item(
                    path_rel_to_watch_dir=os.path.join(path_rel_to_watch_dir, entry),
                    item_type=ItemType.FILE,
                    metadata=metadata,
                    parent=parent,
                )
            )
    return item_list


def generate_paths_and_metadata(
    absolute_path: str, path_rel_to_watch_dir: str
) -> tuple[list[str], dict]:
    """Return the list of relative paths to data items and their associated metadata."""
    logger.info("working with path %s", absolute_path)
    relative_path_list = None
    item_list = [Item]
    metadata = None
    if isfile(absolute_path):
        logger.info("entry is file")
        relative_path_list = [path_rel_to_watch_dir]
        metadata = DataProductMetadata(absolute_path)
        item_list.append(
            Item(
                path_rel_to_watch_dir=path_rel_to_watch_dir,
                item_type=ItemType.FILE,
                metadata=metadata,
            )
        )
    elif isdir(absolute_path):
        if islink(absolute_path):
            linked_path = os.readlink(absolute_path)
            logger.info(
                "entry is symbolic link to a directory %s -> %s", absolute_path, linked_path
            )
        else:
            logger.info("entry is directory")

        # if a measurement set then just add directory
        if path_rel_to_watch_dir.lower().endswith(
            ska_dlm_client.directory_watcher.config.DIRECTORY_IS_MEASUREMENT_SET_SUFFIX
        ):
            relative_path_list = [path_rel_to_watch_dir]
            metadata = DataProductMetadata(absolute_path)
            item_list.append(
                Item(
                    path_rel_to_watch_dir=path_rel_to_watch_dir,
                    item_type=ItemType.CONTAINER,
                    metadata=metadata,
                )
            )
        else:
            relative_path_list = _directory_list_minus_metadata_file(
                absolute_path=absolute_path, path_rel_to_watch_dir=path_rel_to_watch_dir
            )
            logger.info("%s: %s", absolute_path, relative_path_list)
            if _directory_contains_only_files(absolute_path):
                metadata = DataProductMetadata(absolute_path)
            else:
                logger.error("subdirectories of data_item path does not support subdirectories.")
            item_list.append(
                Item(
                    path_rel_to_watch_dir=path_rel_to_watch_dir,
                    item_type=ItemType.CONTAINER,
                    metadata=metadata,
                )
            )
    elif islink(absolute_path):
        logger.error("entry is symbolic link NOT pointing to a directory, this is not handled")
    else:
        logger.error("entry is unknown")
    return relative_path_list, metadata.as_dict()

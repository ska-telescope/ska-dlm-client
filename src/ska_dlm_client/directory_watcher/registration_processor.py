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
from ska_dlm_client.openapi import ApiException, api_client
from ska_dlm_client.openapi.dlm_api import ingest_api
from ska_dlm_client.openapi.exceptions import OpenApiException

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class ItemType(str, Enum):
    """Data Item on the filesystem."""

    UNKOWN = "unknown"
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
        metadata: DataProductMetadata | None,
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
    dry_run_for_debug: bool = False

    def __init__(self, config: Config):
        """Initialise the RegistrationProcessor with the given config."""
        self._config = config

    def get_config(self):
        """Get the Config being used by the RegistrationProcessor."""
        return self._config

    def set_config(self, config: Config):
        """Set/reset the config."""
        self._config = config

    def _follow_sym_link(self, path: Path) -> Path:
        """Return the real path after following the symlink."""
        if path.is_symlink():
            path.resolve()
        return path

    def _register_single_item(self, item: Item) -> str | None:
        """Register the given item returning its uuid in the DLM."""
        with api_client.ApiClient(self._config.ingest_configuration) as ingest_api_client:
            api_ingest = ingest_api.IngestApi(ingest_api_client)
            try:
                # Generate the uri relative to the root directory.
                item_path_rel_to_watch_dir = item.path_rel_to_watch_dir
                uri = (
                    item_path_rel_to_watch_dir
                    if self._config.ingest_register_path_to_add == ""
                    else f"{self._config.ingest_register_path_to_add}/{item_path_rel_to_watch_dir}"
                )
                response = None
                if not self.dry_run_for_debug:
                    response = api_ingest.register_data_item(
                        item_name=item_path_rel_to_watch_dir,
                        uri=uri,
                        item_type=item.item_type,
                        storage_name=self._config.storage_name,
                        do_storage_access_check=self._config.rclone_access_check_on_register,
                        body=None if item.metadata is None else item.metadata.as_dict(),
                    )
            except OpenApiException as err:
                logger.error("OpenApiException caught during register_container_parent_item")
                if isinstance(err, ApiException):
                    logger.error("ApiException: %s", err.body)
                logger.error("%s", err)
                logger.error("Ignoring and continuing.....")
                return None

        dlm_registration_uuid = str(response)
        time_registered = time.time()

        directory_watcher_entry = DirectoryWatcherEntry(
            file_or_directory=item_path_rel_to_watch_dir,
            dlm_storage_name=self._config.storage_name,
            dlm_registration_id=dlm_registration_uuid,
            time_registered=time_registered,
        )
        self._config.directory_watcher_entries.add(directory_watcher_entry)
        self._config.directory_watcher_entries.save_to_file()
        logger.info(
            "Added to DLM %s %s metadata and path %s",
            item.item_type,
            "without" if item.metadata is None else "with",
            item_path_rel_to_watch_dir,
        )
        return dlm_registration_uuid

    def _register_container_items(self, item_list: list[Item]):
        """Register the given item returning its uuid in the DLM."""
        with api_client.ApiClient(self._config.ingest_configuration) as ingest_api_client:
            api_ingest = ingest_api.IngestApi(ingest_api_client)
            for item in item_list:
                try:
                    # Generate the uri relative to the root directory.
                    item_path_rel_to_watch_dir = item.path_rel_to_watch_dir
                    uri = (
                        item_path_rel_to_watch_dir
                        if self._config.ingest_register_path_to_add == ""
                        else f"{self._config.ingest_register_path_to_add}/"
                        f"{item_path_rel_to_watch_dir}"
                    )
                    response = None
                    if not self.dry_run_for_debug:
                        response = api_ingest.register_data_item(
                            item_name=item_path_rel_to_watch_dir,
                            uri=uri,
                            item_type=item.item_type,
                            storage_name=self._config.storage_name,
                            do_storage_access_check=self._config.rclone_access_check_on_register,
                            parents=None if item.parent is None else item.parent.uuid,
                            body=None if item.metadata is None else item.metadata.as_dict(),
                        )
                except OpenApiException as err:
                    logger.error("OpenApiException caught during _register_container_items")
                    if isinstance(err, ApiException):
                        logger.error("ApiException: %s", err.body)
                    logger.error("%s", err)
                    logger.error("Ignoring and continuing.....")
                    return

                dlm_registration_uuid = str(response)
                time_registered = time.time()

                directory_watcher_entry = DirectoryWatcherEntry(
                    file_or_directory=item_path_rel_to_watch_dir,
                    dlm_storage_name=self._config.storage_name,
                    dlm_registration_id=dlm_registration_uuid,
                    time_registered=time_registered,
                )
                self._config.directory_watcher_entries.add(directory_watcher_entry)
                self._config.directory_watcher_entries.save_to_file()
                logger.info(
                    "Added to DLM %s %s metadata and path %s",
                    item.item_type,
                    "without" if item.metadata is None else "with",
                    item_path_rel_to_watch_dir,
                )
                time.sleep(0.01)

    def add_path(self, absolute_path: str, path_rel_to_watch_dir: str):
        """Add the given path_rel_to_watch_dir to the DLM.

        If absolute_path is a file, a single file will be registered with the DLM.
        If absolute_path is a directory, and it is an MS, then ingest a single data
        item for the whole directory.
        If absolute_path is a directory, and it is NOT an MS, then recursively ingest
        all files and subdirectories
        """
        logger.info("in add_path with %s and %s", absolute_path, path_rel_to_watch_dir)
        item_list = _generate_paths_and_metadata(
            absolute_path=absolute_path, path_rel_to_watch_dir=path_rel_to_watch_dir
        )
        logger.info("data_item_relative_path_list %s", item_list)
        if item_list is None or len(item_list) == 0:
            logger.error("No data items found, NOT added to DLM!")
            return
        if len(item_list) == 1:
            item = item_list[0]
            if item.item_type is ItemType.FILE:
                self._register_single_item(item)
            else:
                logger.error("Single data item to add but is not a file, not added to DLM!")
        else:
            # Register the container directory first so that its uuid can be used for the files.
            parent_item = item_list[0]
            self._register_single_item(parent_item)
            time.sleep(2)
            item_list.remove(parent_item)
            self._register_container_items(item_list=item_list)

    def register_data_products_from_watch_directory(self, dry_run_for_debug: bool = False):
        """Provide a mechanism to register the contents of the directory to watch."""
        logger.info("\n##############################\n")
        self.dry_run_for_debug = dry_run_for_debug
        for item in os.listdir(self._config.directory_to_watch):
            self.add_path(
                absolute_path=os.path.join(self._config.directory_to_watch, item),
                path_rel_to_watch_dir=item,
            )
            logger.info("\n\n##############################\n")


def _generate_item_list_for_data_product(
    absolute_path: str, path_rel_to_watch_dir: str
) -> list[Item]:
    """Return the list of relative paths to data items given a directory."""
    item_list: list[Item] = []
    # Case with metadata being at same level as container directory

    # Working with a single directory (or link to a directory) containing only files
    metadata = DataProductMetadata(absolute_path)
    container_item = None
    # Case when NOT MeasurementSet
    if metadata.dp_metadata_loaded_from_a_file:
        ms_name = _measurement_set_directory_in(absolute_path=absolute_path)
        if ms_name:  # if not None or empty
            absolute_path = os.path.join(absolute_path, ms_name)
            path_rel_to_watch_dir = os.path.join(path_rel_to_watch_dir, ms_name)
        container_item = Item(
            path_rel_to_watch_dir=path_rel_to_watch_dir,
            item_type=ItemType.CONTAINER,
            metadata=metadata,
        )
        # The container must be registered first so that the uid of the container can be
        # assigned to all the files in the directory/container.
        item_list.append(container_item)

    for entry in os.listdir(absolute_path):
        new_path = os.path.join(absolute_path, entry)
        if os.path.isdir(new_path):
            net_path_rel_to_watch_dir = os.path.join(path_rel_to_watch_dir, entry)
            additional_items = _item_list_minus_metadata_file(
                container_item=container_item,
                absolute_path=new_path,
                path_rel_to_watch_dir=net_path_rel_to_watch_dir,
            )
            item_list.extend(additional_items)
            logger.info("%s: %s", absolute_path, additional_items)
        elif not entry == ska_dlm_client.directory_watcher.config.METADATA_FILENAME:
            item = Item(
                path_rel_to_watch_dir=os.path.join(path_rel_to_watch_dir, entry),
                item_type=ItemType.FILE,
                metadata=None,  # Set to know as Container has this file's metadata
                parent=container_item,
            )
            item_list.append(item)

    return item_list


def _generate_paths_and_metadata_for_direcotry(
    absolute_path: str, path_rel_to_watch_dir: str
) -> list[Item]:
    """Return the list of relative paths to data items given a directory."""
    item_list: list[Item] = []
    # Determine first if the given path is the head of a data item or of a directory containing
    # other data items. Exclude any configurations not currently supported
    if not _directory_contains_only_files(absolute_path):
        if _directory_contains_only_directories(absolute_path):
            logger.info("Direcory %s contains only directories, processing.", absolute_path)
        elif _directory_contains_metadata_file(absolute_path):
            item_list = _generate_item_list_for_data_product(
                absolute_path=absolute_path, path_rel_to_watch_dir=path_rel_to_watch_dir
            )
            return item_list
        else:
            logger.error(
                "data_item path does not support subdirectories and files in the same"
                "directory without a metadata file."
            )
            return item_list
    elif _directory_contains_metadata_file(absolute_path):
        dir_list = _directory_list_minus_metadata_file(absolute_path)
        if len(dir_list) == 1:
            absolute_path = os.path.join(absolute_path, dir_list[0])
            path_rel_to_watch_dir = os.path.join(path_rel_to_watch_dir, dir_list[0])
            item_list.append(
                _item_for_single_file_with_metadata(
                    absolute_path=absolute_path, path_rel_to_watch_dir=path_rel_to_watch_dir
                )
            )
            return item_list

    if not _directory_contains_only_directories(absolute_path):
        # Working with a single directory (or link to a directory) containing only files
        metadata = DataProductMetadata(absolute_path)
        # YAN-1976: if directory has its own metadata then treat directory as container
        container_item = None
        if metadata.dp_metadata_loaded_from_a_file:
            container_item = Item(
                path_rel_to_watch_dir=path_rel_to_watch_dir,
                item_type=ItemType.CONTAINER,
                metadata=metadata,
            )
            # The container must be registered first so that the uid of the container can be
            # assigned to all the files in the directory/container.
            item_list.append(container_item)

        # When not just a measurement set then add files from directory
        if not path_rel_to_watch_dir.lower().endswith(
            ska_dlm_client.directory_watcher.config.DIRECTORY_IS_MEASUREMENT_SET_SUFFIX
        ):
            additional_items = _item_list_minus_metadata_file(
                container_item=container_item,
                absolute_path=absolute_path,
                path_rel_to_watch_dir=path_rel_to_watch_dir,
            )
            item_list.extend(additional_items)
            logger.info("%s: %s", absolute_path, item_list)
    else:
        # From previous test we know that each entry must be directory
        for entry in os.listdir(absolute_path):
            local_abs_path = os.path.join(absolute_path, entry)
            local_rel_path = os.path.join(path_rel_to_watch_dir, entry)
            new_items = _generate_paths_and_metadata_for_direcotry(
                absolute_path=local_abs_path, path_rel_to_watch_dir=local_rel_path
            )
            item_list.extend(new_items)
    return item_list


def _generate_paths_and_metadata(absolute_path: str, path_rel_to_watch_dir: str) -> list[Item]:
    """Return the list of relative paths to data items and their associated metadata."""
    logger.info("working with path %s", absolute_path)
    item_list: list[Item] = []
    if isfile(absolute_path):
        logger.info("entry is file")
        item_list.append(
            _item_for_single_file_with_metadata(
                absolute_path=absolute_path, path_rel_to_watch_dir=path_rel_to_watch_dir
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

        item_list = _generate_paths_and_metadata_for_direcotry(
            absolute_path=absolute_path, path_rel_to_watch_dir=path_rel_to_watch_dir
        )
    elif islink(absolute_path):
        logger.error("entry is symbolic link NOT pointing to a directory, this is not handled")
    else:
        logger.error("entry is unknown")
    return item_list


def _item_for_single_file_with_metadata(absolute_path: str, path_rel_to_watch_dir: str) -> Item:
    """Create an Item for a file by itself adding any metadata to it."""
    metadata = DataProductMetadata(absolute_path)
    item = Item(
        path_rel_to_watch_dir=path_rel_to_watch_dir,
        item_type=ItemType.FILE,
        metadata=metadata,
    )
    logger.info("Created single item with metadata %s", item)
    return item


def _directory_contains_only_directories(absolute_path: str) -> bool:
    """Return True if the given directory contains only directories."""
    for entry in os.listdir(absolute_path):
        if not os.path.isdir(os.path.join(absolute_path, entry)):
            return False
    return True


def _directory_contains_only_files(absolute_path: str) -> bool:
    """Return True if the given directory contains only files."""
    for entry in os.listdir(absolute_path):
        if not os.path.isfile(os.path.join(absolute_path, entry)):
            return False
    return True


def _directory_contains_metadata_file(absolute_path: str) -> bool:
    """Return True if the given directory contains only files."""
    for entry in os.listdir(absolute_path):
        if entry == ska_dlm_client.directory_watcher.config.METADATA_FILENAME:
            return True
    return False


def _measurement_set_directory_in(absolute_path: str) -> str | None:
    """Return the name of the measurement set directory or None if nothing found."""
    for entry in os.listdir(absolute_path):
        if entry.lower().endswith(
            ska_dlm_client.directory_watcher.config.DIRECTORY_IS_MEASUREMENT_SET_SUFFIX
        ):
            return entry
    return None


def _directory_list_minus_metadata_file(absolute_path: str) -> list[str]:
    """Return the list of relative minus the metadata file name."""
    dir_list = os.listdir(absolute_path)
    if ska_dlm_client.directory_watcher.config.METADATA_FILENAME in dir_list:
        dir_list.remove(ska_dlm_client.directory_watcher.config.METADATA_FILENAME)
    return dir_list


def _item_list_minus_metadata_file(
    container_item: Item, absolute_path: str, path_rel_to_watch_dir: str
) -> list[Item]:
    """Return a listing of the given absolute_path directory without the metadata file."""
    item_list: list[Item] = []
    for entry in _directory_list_minus_metadata_file(absolute_path):
        item = Item(
            path_rel_to_watch_dir=os.path.join(path_rel_to_watch_dir, entry),
            item_type=ItemType.FILE,
            metadata=None,  # Set to know as Container has this file's metadata
            parent=container_item,
        )
        item_list.append(item)
        logger.info("new item %s", item.path_rel_to_watch_dir)
    return item_list

"""Register the given file or directory with the DLM."""

import logging
import os
import time
from dataclasses import dataclass
from os.path import isdir, isfile, islink
from pathlib import Path
from typing import Any

from typing_extensions import Self

import ska_dlm_client.config
from ska_dlm_client.common_types import ItemType
from ska_dlm_client.data_product_metadata import DataProductMetadata
from ska_dlm_client.directory_watcher.directory_watcher_entries import DirectoryWatcherEntry
from ska_dlm_client.openapi import ApiException, api_client
from ska_dlm_client.openapi.dlm_api import ingest_api, migration_api
from ska_dlm_client.openapi.exceptions import OpenApiException

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


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
    """Processes the registration of data items with the DLM.

    This class handles the registration of data items with the DLM system,
    including sending registration requests to the DLM API and handling
    the migration of data items between storage locations.
    """

    _config: Any

    def __init__(self, config: Any) -> None:
        """Initialize the RegistrationProcessor with the given configuration.

        Args:
            config: The configuration object containing DLM connection settings
                and other parameters needed for registration and migration.
        """
        self._config = config
        self.last_migration_result: str | None = None

    def get_config(self) -> Any:
        """Get the configuration being used by the RegistrationProcessor.

        Returns:
            The current configuration object.
        """
        return self._config

    def set_config(self, config: Any) -> None:
        """Set or reset the configuration used by the RegistrationProcessor.

        Args:
            config: The new configuration object to use.
        """
        self._config = config

    def _follow_sym_link(self, path: Path) -> Path:
        """Return the real path after following the symlink.

        Args:
            path: The path that might be a symlink.

        Returns:
            The resolved path if it was a symlink, otherwise the original path.
        """
        if path.is_symlink():
            path.resolve()
        return path

    def _copy_data_item_to_new_storage(self, uid: str, item_name: str = "") -> str | None:
        """Send migration request to DLM.

        Args:
            uid: The unique identifier of the data item to copy.
            item_name: The name of the item (only used for a log message)

        Returns:
            The UUID of the migrated data item, or None if migration was skipped or failed.
        """
        if not uid:
            logger.warning("Skipping migration due to missing uid")
            return None

        cfg = self._config

        destination_storage_name = getattr(
            cfg,
            "migration_destination_storage_name",
            None,
        )
        if not destination_storage_name:
            logger.warning("Skipping migration due to missing destination storage name")
            return None

        if not getattr(cfg, "perform_actual_ingest_and_migration", True):
            logger.warning("Migration is disabled in configuration!")
            return None

        # Require an explicit migration_configuration with a host
        migration_configuration = getattr(cfg, "migration_configuration", None)
        if migration_configuration is None:
            logger.error(
                "Skipping migration because migration_configuration is not set on "
                "the RegistrationProcessor config",
            )
            return None

        if getattr(migration_configuration, "host", None) is None:
            logger.error(
                "Skipping migration because migration_configuration.host is not set",
            )
            return None

        result: str | None = None
        with api_client.ApiClient(migration_configuration) as migration_api_client:
            logger.info(
                "Initiating migration of data_item '%s' to %s", item_name, destination_storage_name
            )
            api_migration = migration_api.MigrationApi(migration_api_client)
            api_migration.api_client.configuration.host = migration_configuration.host
            try:
                response = api_migration.copy_data_item(
                    uid=uid,
                    destination_name=destination_storage_name,
                )
                logger.info("Migration response: %s", response)
                result = str(response)
            except OpenApiException as err:
                logger.error("OpenApiException caught during copy_data_item")
                if isinstance(err, ApiException):
                    logger.error("ApiException: %s", err.body)
                logger.error("%s", err)
                logger.error("Ignoring and continuing.....")

        return result

    def _register_single_item(self, item: Item) -> str | None:  # pylint: disable=too-many-locals
        """Register a single data item with the DLM.

        Sends a registration request to the DLM API for the given item,
        and optionally migrates the registered item to a new storage location.

        Args:
            item: The data item to register with the DLM.

        Returns:
            The UUID of the registered data item, or None if registration failed.
        """
        cfg = self._config

        # --- Common config needed by BOTH Directory Watcher and ConfigDB Watcher
        ingest_configuration = getattr(cfg, "ingest_configuration", None)
        ingest_url = getattr(cfg, "ingest_url", None)

        # storage_name for Directory Watcher; source_storage for ConfigDB Watcher
        storage_name = getattr(cfg, "storage_name", None)
        if storage_name is None:
            storage_name = getattr(cfg, "source_storage", None)

        if ingest_configuration is None or ingest_url is None or storage_name is None:
            logger.error(
                "RegistrationProcessor config missing required ingest settings "
                "(ingest_configuration=%r, ingest_url=%r, storage_name=%r)",
                ingest_configuration,
                ingest_url,
                storage_name,
            )
            return None

        # These are Directory-Watcher-specific; provide safe defaults if absent
        perform_actual_ingest_and_migration = getattr(
            cfg, "perform_actual_ingest_and_migration", True
        )
        rclone_access_check_on_register = getattr(cfg, "rclone_access_check_on_register", False)

        with api_client.ApiClient(ingest_configuration) as ingest_api_client:
            api_ingest = ingest_api.IngestApi(ingest_api_client)
            api_ingest.api_client.configuration.host = ingest_url
            try:
                logger.info(
                    "Using URI: %s for data_item registration",
                    item.path_rel_to_watch_dir,
                )
                response = None
                if perform_actual_ingest_and_migration:
                    response = api_ingest.register_data_item(
                        item_name=item.path_rel_to_watch_dir,
                        uri=item.path_rel_to_watch_dir,
                        item_type=item.item_type,
                        storage_name=storage_name,
                        do_storage_access_check=rclone_access_check_on_register,
                        request_body=(None if item.metadata is None else item.metadata.as_dict()),
                    )
                    logger.debug("register_data_item response: %s", response)
                else:
                    logger.warning("Skipping register_data_item due to config")
            except OpenApiException as err:
                logger.error(
                    "OpenApiException caught during register_container_parent_item",
                )
                if isinstance(err, ApiException):
                    logger.error("ApiException: %s", err.body)
                logger.error("%s", err)
                logger.error("Ignoring and continuing.....")
                return None

        dlm_registration_uuid = str(response) if response is not None else None

        # Attempt to migrate the data item to the new storage
        migration_result = self._copy_data_item_to_new_storage(
            uid=dlm_registration_uuid,
            item_name=item.path_rel_to_watch_dir,
        )
        self.last_migration_result = migration_result
        time_registered = time.time()

        # DirectoryWatcher-specific bookkeeping is only done if the config has it
        directory_watcher_entries = getattr(cfg, "directory_watcher_entries", None)
        if directory_watcher_entries is not None:
            directory_watcher_entry = DirectoryWatcherEntry(
                file_or_directory=item.path_rel_to_watch_dir,
                dlm_storage_name=storage_name,
                dlm_registration_id=dlm_registration_uuid,
                time_registered=time_registered,
            )
            directory_watcher_entries.add(directory_watcher_entry)
            directory_watcher_entries.save_to_file()
            logger.info(
                "Added to DLM %s %s metadata, path %s, migration result: %s",
                item.item_type,
                "without" if item.metadata is None else "with",
                item.path_rel_to_watch_dir,
                migration_result,
            )
        else:
            # ConfigDB watcher path – no directory_watcher_entries
            logger.info(
                "Registered and migrated item %s (%s); migration_result=%s",
                item.path_rel_to_watch_dir,
                item.item_type,
                migration_result,
            )

        return dlm_registration_uuid

    def _register_container_items(self, item_list: list[Item]):
        """Register a list of data items with the DLM.

        Sends registration requests to the DLM API for each item in the list,
        and optionally migrates each registered item to a new storage location.

        Args:
            item_list: A list of data items to register with the DLM.
        """
        with api_client.ApiClient(self._config.ingest_configuration) as ingest_api_client:
            api_ingest = ingest_api.IngestApi(ingest_api_client)
            for item in item_list:
                try:
                    # Generate the uri relative to the root directory.
                    logger.info(
                        "Using URI: %s for data_item registration", item.path_rel_to_watch_dir
                    )
                    response = None
                    if self._config.perform_actual_ingest_and_migration:
                        response = api_ingest.register_data_item(
                            item_name=item.path_rel_to_watch_dir,
                            uri=item.path_rel_to_watch_dir,
                            item_type=item.item_type,
                            storage_name=self._config.storage_name,
                            do_storage_access_check=self._config.rclone_access_check_on_register,
                            parents=None if item.parent is None else item.parent.uuid,
                            request_body=(
                                None if item.metadata is None else item.metadata.as_dict()
                            ),
                        )
                        logger.debug("register_data_item response: %s", response)
                    else:
                        logger.warning("Skipping register_data_item due to config")
                except OpenApiException as err:
                    logger.error("OpenApiException caught during _register_container_items")
                    if isinstance(err, ApiException):
                        logger.error("ApiException: %s", err.body)
                    logger.error("%s", err)
                    logger.error("Ignoring and continuing.....")
                    return

                dlm_registration_uuid = str(response) if response is not None else None
                # Attempt to migrate the data item to the new storage
                migration_result = self._copy_data_item_to_new_storage(
                    uid=dlm_registration_uuid, item_name=item.path_rel_to_watch_dir
                )
                time_registered = time.time()

                directory_watcher_entry = DirectoryWatcherEntry(
                    file_or_directory=item.path_rel_to_watch_dir,
                    dlm_storage_name=self._config.storage_name,
                    dlm_registration_id=dlm_registration_uuid,
                    time_registered=time_registered,
                )
                self._config.directory_watcher_entries.add(directory_watcher_entry)
                self._config.directory_watcher_entries.save_to_file()
                logger.info(
                    "Added to DLM %s %s metadata, path %s, migration result: %s",
                    item.item_type,
                    "without" if item.metadata is None else "with",
                    item.path_rel_to_watch_dir,
                    migration_result,
                )
                time.sleep(0.01)

    def add_path(self, absolute_path: str, path_rel_to_watch_dir: str):
        """Add the given path to the DLM.

        If absolute_path is a file, a single file will be registered with the DLM.
        If absolute_path is a directory, and it is an MS, then ingest a single data
        item for the whole directory.
        If absolute_path is a directory, and it is NOT an MS, then recursively ingest
        all files and subdirectories.

        Args:
            absolute_path: The absolute path to the file or directory to register.
            path_rel_to_watch_dir: The path relative to the watch directory.
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
            logger.info("Finished adding data items %s", parent_item)
        logger.info("Finished add_path %s", path_rel_to_watch_dir)

    def register_data_products_from_watch_directory(self):
        """Register all data products found in the watch directory with the DLM.

        Iterates through all items in the configured watch directory and registers
        each one with the DLM using the add_path method.
        """
        logger.info("\n##############################\n")
        for item in os.listdir(self._config.directory_to_watch):
            self.add_path(
                absolute_path=os.path.join(self._config.directory_to_watch, item),
                path_rel_to_watch_dir=item,
            )
            logger.info("\n\n##############################\n")


def _generate_item_list_for_data_product(
    absolute_path: str, path_rel_to_watch_dir: str
) -> list[Item]:
    """Generate a list of Item objects for a data product directory.

    Analyzes the directory structure and metadata to create Item objects
    representing the data product and its components.

    Args:
        absolute_path: The absolute path to the data product directory.
        path_rel_to_watch_dir: The path relative to the watch directory.

    Returns:
        A list of Item objects representing the data product and its components.
    """
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
        elif not entry == ska_dlm_client.config.METADATA_FILENAME:
            item = Item(
                path_rel_to_watch_dir=os.path.join(path_rel_to_watch_dir, entry),
                item_type=ItemType.FILE,
                metadata=None,  # Set to know as Container has this file's metadata
                parent=container_item,
            )
            item_list.append(item)

    return item_list


def _generate_paths_and_metadata_for_directory(
    absolute_path: str, path_rel_to_watch_dir: str
) -> list[Item]:
    """Generate a list of Item objects for a directory.

    Analyzes the directory structure to determine if it contains data products
    and creates appropriate Item objects.

    Args:
        absolute_path: The absolute path to the directory.
        path_rel_to_watch_dir: The path relative to the watch directory.

    Returns:
        A list of Item objects representing the directory contents.
    """
    item_list: list[Item] = []
    # Determine first if the given path is the head of a data item or of a directory containing
    # other data items. Exclude any configurations not currently supported
    if not _directory_contains_only_files(absolute_path):
        if _directory_contains_only_directories(absolute_path):
            logger.info("Directory %s contains only directories, processing.", absolute_path)
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
            ska_dlm_client.config.DIRECTORY_IS_MEASUREMENT_SET_SUFFIX
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
            new_items = _generate_paths_and_metadata_for_directory(
                absolute_path=local_abs_path, path_rel_to_watch_dir=local_rel_path
            )
            item_list.extend(new_items)
    return item_list


def _generate_paths_and_metadata(absolute_path: str, path_rel_to_watch_dir: str) -> list[Item]:
    """Generate a list of Item objects with their associated metadata.

    Determines whether the path is a file or directory and creates appropriate
    Item objects with metadata.

    Args:
        absolute_path: The absolute path to the file or directory.
        path_rel_to_watch_dir: The path relative to the watch directory.

    Returns:
        A list of Item objects with their associated metadata.
    """
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

        item_list = _generate_paths_and_metadata_for_directory(
            absolute_path=absolute_path, path_rel_to_watch_dir=path_rel_to_watch_dir
        )
    elif islink(absolute_path):
        logger.error("entry is symbolic link NOT pointing to a directory, this is not handled")
    else:
        logger.error("entry is unknown")
    return item_list


def _item_for_single_file_with_metadata(absolute_path: str, path_rel_to_watch_dir: str) -> Item:
    """Create an Item object for a single file with its metadata.

    Extracts metadata for the file and creates an Item object of type FILE.

    Args:
        absolute_path: The absolute path to the file.
        path_rel_to_watch_dir: The path relative to the watch directory.

    Returns:
        An Item object representing the file with its metadata.
    """
    metadata = DataProductMetadata(absolute_path)
    item = Item(
        path_rel_to_watch_dir=path_rel_to_watch_dir,
        item_type=ItemType.FILE,
        metadata=metadata,
    )
    logger.info("Created single item with metadata %s", item)
    return item


def _directory_contains_only_directories(absolute_path: str) -> bool:
    """Check if a directory contains only subdirectories and no files.

    Args:
        absolute_path: The absolute path to the directory to check.

    Returns:
        True if the directory contains only subdirectories, False otherwise.
    """
    for entry in os.listdir(absolute_path):
        if not os.path.isdir(os.path.join(absolute_path, entry)):
            return False
    return True


def _directory_contains_only_files(absolute_path: str) -> bool:
    """Check if a directory contains only files and no subdirectories.

    Args:
        absolute_path: The absolute path to the directory to check.

    Returns:
        True if the directory contains only files, False otherwise.
    """
    for entry in os.listdir(absolute_path):
        if not os.path.isfile(os.path.join(absolute_path, entry)):
            return False
    return True


def _directory_contains_metadata_file(absolute_path: str) -> bool:
    """Check if a directory contains a metadata file.

    Looks for the presence of a file with the name defined in
    ska_dlm_client.directory_watcher.config.METADATA_FILENAME.

    Args:
        absolute_path: The absolute path to the directory to check.

    Returns:
        True if the directory contains a metadata file, False otherwise.
    """
    for entry in os.listdir(absolute_path):
        if entry == ska_dlm_client.config.METADATA_FILENAME:
            return True
    return False


def _measurement_set_directory_in(absolute_path: str) -> str | None:
    """Find a measurement set directory within the given directory.

    Looks for a directory with a name ending with the suffix defined in
    ska_dlm_client.directory_watcher.config.DIRECTORY_IS_MEASUREMENT_SET_SUFFIX.

    Args:
        absolute_path: The absolute path to the directory to search in.

    Returns:
        The name of the measurement set directory if found, None otherwise.
    """
    for entry in os.listdir(absolute_path):
        if entry.lower().endswith(ska_dlm_client.config.DIRECTORY_IS_MEASUREMENT_SET_SUFFIX):
            return entry
    return None


def _directory_list_minus_metadata_file(absolute_path: str) -> list[str]:
    """Get a list of directory contents excluding the metadata file.

    Returns a list of all files and directories in the given directory,
    excluding the metadata file defined in
    ska_dlm_client.directory_watcher.config.METADATA_FILENAME.

    Args:
        absolute_path: The absolute path to the directory to list.

    Returns:
        A list of filenames in the directory, excluding the metadata file.
    """
    dir_list = os.listdir(absolute_path)
    if ska_dlm_client.config.METADATA_FILENAME in dir_list:
        dir_list.remove(ska_dlm_client.config.METADATA_FILENAME)
    return dir_list


def _item_list_minus_metadata_file(
    container_item: Item, absolute_path: str, path_rel_to_watch_dir: str
) -> list[Item]:
    """Create Item objects for all files in a directory, excluding the metadata file.

    Creates Item objects of type FILE for each file in the directory, excluding
    the metadata file. Each Item is linked to the provided container_item as its parent.

    Args:
        container_item: The parent Item object representing the container directory.
        absolute_path: The absolute path to the directory to process.
        path_rel_to_watch_dir: The path relative to the watch directory.

    Returns:
        A list of Item objects representing the files in the directory, excluding the
        metadata file.
    """
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

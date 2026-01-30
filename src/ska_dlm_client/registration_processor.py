"""Register the given file or directory with the DLM."""

import logging
import os
import time
from dataclasses import dataclass
from os.path import isfile
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

    def _execute_migration_checks(self, uid: str) -> bool:
        """Determine if migration should/can be performed based on the configuration."""
        if not getattr(self._config, "perform_actual_ingest_and_migration", True):
            logger.warning("Migration is disabled in configuration!")
            return False

        # Require an explicit migration_configuration with a host
        migration_configuration = getattr(self._config, "migration_configuration", None)
        if migration_configuration is None:
            logger.error(
                "Skipping migration because migration configuration is not available "
                "in the RegistrationProcessor configuration.",
            )
            return False

        if getattr(migration_configuration, "host", None) is None:
            logger.error(
                "Skipping migration because MIGRATION_SERVER has not been specified",
            )
            return False

        destination_storage_name = getattr(
            self._config,
            "migration_destination_storage_name",
            None,
        )
        if not destination_storage_name:
            logger.warning("Skipping migration due to missing destination storage name")
            return False

        if not uid:
            logger.warning("Skipping migration due to missing uid")
            return False

        return True

    def _initiate_migration(self, uid: str, item_name: str = "") -> str | None:
        """Send migration request to DLM.

        Args:
            uid: The unique identifier of the data item to copy.
            item_name: The name of the item (only used for a log message)

        Returns:
            The UUID of the migrated data item, or None if migration was skipped or failed.
        """
        cfg = self._config
        migration_configuration = getattr(cfg, "migration_configuration", None)
        if self._execute_migration_checks(uid) is False:
            return None

        result: str | None = None
        destination_storage_name = getattr(
            cfg,
            "migration_destination_storage_name",
            None,
        )
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

    def _bookkeeping_after_registration(
        self, item: Item, dlm_registration_uuid: str, storage_name: str, migration_result: str
    ) -> None:
        time_registered = time.time()

        # DirectoryWatcher-specific bookkeeping is only done if the config has it
        directory_watcher_entries = getattr(self._config, "directory_watcher_entries", None)
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

    def _migrate_item(self, migrate, item, uuid, api_ingest) -> None:
        """Migrate the last registered item."""
        source_storage = getattr(self._config, "storage_name", None)
        if migrate:
            # We are only migrating the top-level containers, since rclone is
            # performing a sync including all children.
            migration_result = self._initiate_migration(
                uid=uuid,
                item_name=item.path_rel_to_watch_dir,
            )
            self.last_migration_result = migration_result
            self._bookkeeping_after_registration(
                item=item,
                dlm_registration_uuid=uuid,
                storage_name=source_storage,
                migration_result=migration_result,
            )
        else:
            # register not explicitly migrated items on target storage
            target_storage = getattr(
                self._config,
                "migration_destination_storage_name",
                None,
            )
            try:
                response = api_ingest.register_data_item(
                    item_name=str(item.path_rel_to_watch_dir),
                    uri=str(item.path_rel_to_watch_dir),
                    item_type=item.item_type,
                    storage_name=target_storage,
                    do_storage_access_check=False,
                    request_body=(None if item.metadata is None else item.metadata.as_dict()),
                )
                logger.debug("register_data_item response: %s", response)
            except OpenApiException as err:
                logger.error(
                    "OpenApiException caught during register_container_parent_item",
                )
                if isinstance(err, ApiException):
                    logger.error("ApiException: %s", err.body)
                logger.error("%s", err)
                logger.error("Ignoring and continuing.....")
        # The return value is the UUID of the top level item.

    def _register_single_item(self, item: Item, migrate: bool = True) -> str | None:
        """Register a single data item with the DLM.

        Sends a registration request to the DLM API for the given item,
        and optionally migrates the registered item to a new storage location.

        Args:
            item: The data item to register with the DLM.
            migrate: Whether to migrate the item. This is being used to make sure that
            the top-level container item is synced including the whole sub-tree,
            but not each item individually in addition.

        Returns:
            The UUID of the registered data item, or None if registration failed.
        """
        cfg = self._config

        # These are Directory-Watcher-specific; provide safe defaults if absent
        perform_actual_ingest_and_migration = getattr(
            cfg, "perform_actual_ingest_and_migration", True
        )
        rclone_access_check_on_register = getattr(cfg, "rclone_access_check_on_register", False)

        # --- Common config needed by BOTH Directory Watcher and ConfigDB Watcher
        ingest_configuration = getattr(cfg, "ingest_configuration", None)
        ingest_url = getattr(cfg, "ingest_url", None)

        # storage_name for Directory Watcher; source_storage for ConfigDB Watcher
        source_storage = getattr(cfg, "storage_name", None)
        if source_storage is None:
            source_storage = getattr(cfg, "source_storage", None)

        if ingest_configuration is None or ingest_url is None or source_storage is None:
            logger.error(
                "RegistrationProcessor config missing required ingest settings "
                "(ingest_configuration=%r, ingest_url=%r, source_storage=%r)",
                ingest_configuration,
                ingest_url,
                source_storage,
            )
            return None

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
                        item_name=str(item.path_rel_to_watch_dir),
                        uri=str(item.path_rel_to_watch_dir),
                        item_type=item.item_type,
                        storage_name=source_storage,
                        do_storage_access_check=rclone_access_check_on_register,
                        request_body=(None if item.metadata is None else item.metadata.as_dict()),
                    )
                    logger.debug("register_data_item response: %s", response)
                else:
                    logger.warning(
                        "Skipping regisdlm_registration_uuidter_data_item due to config"
                    )
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

        # This should be refactored out and made an asic transaction.
        self._migrate_item(
            migrate=(migrate and perform_actual_ingest_and_migration),
            item=item,
            uuid=dlm_registration_uuid,
            api_ingest=api_ingest,
        )
        return dlm_registration_uuid

    def _register_container_items(self, item_list: list[Item]):
        """Register a list of data items with the DLM.

        Sends registration requests to the DLM API for each item in the list,
        and optionally migrates each registered item to a new storage location.

        Args:
            item_list: A list of data items to register with the DLM.
        """
        migrate = True
        for item in item_list:
            _ = self._register_single_item(item=item, migrate=migrate)
            migrate = False  # Only the top-level container item triggers migration
            time.sleep(0.01)

    def add_path(self, absolute_path: str, path_rel_to_watch_dir: str) -> str | None:
        """Add the given path to the DLM.

        The logic is as follows:
        1) If absolute_path is a file, it will be registered with the DLM without metadata
        2) If absolute_path is a MS directory it will be registered without metadata (TBC).
        3) If absolute_path is a directory it will be registered as a container with metadata if
        found. All files within it will be registered as children. Any subdirectory
        will be treated recursively using the same logic.

        Args:
            absolute_path: The absolute path to the file or directory to register.
            path_rel_to_watch_dir: The path relative to the watch directory.
        """
        logger.info("add_path %s from %s", absolute_path, path_rel_to_watch_dir)
        item_list = _generate_dir_item_list(
            absolute_path=absolute_path, path_rel_to_watch_dir=path_rel_to_watch_dir
        )
        if item_list is None or len(item_list) == 0:
            logger.error("No data items found in %s, NOT added to DLM!", absolute_path)
            return None
        logger.info("Items identified in %s: %s", absolute_path, item_list)
        # Register the container directory first so that its uuid can be used for the files.
        parent_item = item_list[0]
        parent_uuid = self._register_single_item(parent_item)
        # TODO: Check whether the parent_uuid is actually used!
        time.sleep(1)
        item_list.remove(parent_item)
        self._register_container_items(item_list=item_list)
        logger.info("Finished adding %s data items for %s", len(item_list), parent_item)
        return parent_uuid

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


def _generate_dir_item_list(absolute_path: str, path_rel_to_watch_dir: str) -> list[Item]:
    """Generate a list of Item objects for a directory.

    Analyzes the directory structure and metadata to create Item objects
    representing the contained items.

    This is a recursive function that will explore subdirectories as needed.
    If the top-level directory points to a nested data product structure, the
    sub-product metadata files will also be considered.

    Args:
        absolute_path: The absolute path to a directory.
        path_rel_to_watch_dir: The path relative to the watch directory.

    Returns:
        A list of Item objects representing the directory and its children.
    """
    item_list: list[Item] = []
    if not os.path.exists(absolute_path):
        logger.error("Path does not exist: %s", absolute_path)
        return item_list

    # We have to make sure that symlinked dirs are treated correctly
    if isfile(os.path.realpath(absolute_path)):
        # Single file case – no metadata
        item = Item(
            path_rel_to_watch_dir=path_rel_to_watch_dir,
            item_type=ItemType.FILE,
            metadata=None,
        )
        item_list.append(item)
        return item_list
    # Get metadata from directory
    metadata = DataProductMetadata(absolute_path)
    container_item = Item(
        path_rel_to_watch_dir=path_rel_to_watch_dir,
        item_type=ItemType.CONTAINER,
        metadata=metadata,
    )
    # The container itself must be registered first so that the uid can be
    # assigned to all the children in the directory/container.
    item_list.append(container_item)

    for entry in os.listdir(absolute_path):
        if entry == ska_dlm_client.config.METADATA_FILENAME:
            continue
        item_type = ItemType.FILE
        entry_path = os.path.join(absolute_path, entry)
        entry_rel_path = os.path.join(path_rel_to_watch_dir, entry)
        if entry.lower().endswith(ska_dlm_client.config.DIRECTORY_IS_MEASUREMENT_SET_SUFFIX):
            item_type = ItemType.CONTAINER
        elif os.path.isdir(os.path.realpath(entry_path)):
            # Found a non-MS subdirectory
            # recursion !!
            item_list += _generate_dir_item_list(entry_path, entry_rel_path)
            continue
        item = Item(
            path_rel_to_watch_dir=entry_rel_path,
            item_type=item_type,
            metadata=None,  # Set to None as Container has this file's metadata
            parent=container_item,
        )
        item_list.append(item)

    return item_list


def directory_contains_metadata_file(absolute_path: str) -> bool:
    """Check if the given directory contains a metadata file.

    Args:
        absolute_path: The absolute path to the directory.
    Returns:
        True if the metadata file exists in the directory, False otherwise.
    """
    metadata_file_path = os.path.join(absolute_path, ska_dlm_client.config.METADATA_FILENAME)
    return os.path.isfile(metadata_file_path)

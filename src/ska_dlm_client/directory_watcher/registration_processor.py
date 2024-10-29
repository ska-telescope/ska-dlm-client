"""Register the given file or directory with the DLM."""

import logging
import time
from os import listdir
from os.path import isdir, isfile, islink
from pathlib import Path

import ska_dlm_client.directory_watcher.config
from ska_dlm_client.directory_watcher.config import Config
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
        """Return the real path after following the sysmlink."""
        if path.is_symlink():
            path.is_dir()
            path.is_file()

    def _register_entry(self, relative_path: str):
        """Register the given entry_path."""
        with api_client.ApiClient(self._config.ingest_configuration) as ingest_api_client:
            api_ingest = ingest_api.IngestApi(ingest_api_client)
            try:
                response = api_ingest.register_data_item_ingest_register_data_item_post(
                    item_name=relative_path,
                    uri=relative_path,
                    storage_name=self._config.storage_name,
                    eb_id=self._config.execution_block_id,
                )
            except OpenApiException as err:
                logger.error("OpenApiException caught during register_data_item\n%s", err)
                logger.error("Ignoring and continueing.....")
                return

        # TODO: decode JSON response
        dlm_registration_id = response
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
        if isfile(full_path):
            logger.info("entry is file")
            self._register_entry(relative_path=relative_path)
        elif isdir(full_path):
            logger.info("entry is directory")
            if relative_path.endswith(
                ska_dlm_client.directory_watcher.config.DIRECTORY_IS_MEASUREMENT_SET_SUFFIX
            ):
                # if a measurement set then just add directory
                self._register_entry(relative_path=relative_path)
            else:
                # otherwise add each file or directory
                dir_entries = listdir(full_path)
                for dir_entry in dir_entries:
                    new_full_path = f"{full_path}/{dir_entry}"
                    new_relative_path = f"{relative_path}/{dir_entry}"
                    self.add_path(full_path=new_full_path, relative_path=new_relative_path)
        else:
            if islink(full_path):
                error_text = f"Symbolic links are currently not supported: {relative_path}"
            else:
                error_text = f"Unspported file/directory entry type: {relative_path}"
            logging.error(error_text)
            # TODO: Do we throw this or just log here, raise RuntimeError(error_text)

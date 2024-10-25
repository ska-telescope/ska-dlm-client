"""This is expected to be replaced based on what final deployment looks like."""

import dataclasses

from ska_dlm_client.directory_watcher.config import Config
from ska_dlm_client.openapi import configuration

CONFIG = Config()


@dataclasses.dataclass
class DLMConfiguration:
    """Configuration of the DLM, to be replaced in the future."""

    SERVER = "http://localhost"
    DLM_ENTRY_POINTS = {
        "gateway": 8000,
        "ingest": 8001,
        "request": 8002,
        "storage": 8003,
        "migration": 8004,
    }
    GATEWAY_URL = f"{SERVER}:{DLM_ENTRY_POINTS['gateway']}"
    INGEST_URL = f"{SERVER}:{DLM_ENTRY_POINTS['ingest']}"
    REQUEST_URL = f"{SERVER}:{DLM_ENTRY_POINTS['request']}"
    STORAGE_URL = f"{SERVER}:{DLM_ENTRY_POINTS['storage']}"
    MIGRATION_URL = f"{SERVER}:{DLM_ENTRY_POINTS['migration']}"
    DIRECTORY_IS_MEASUREMENT_SET_SUFFIX = ".ms"


@dataclasses.dataclass
class WatchConfiguration:
    """Configuration of the watcher, to be replaced in the future."""

    DIRECTORY_TO_WATCH = "/Users/00077990/yanda/pi24/watch_dir"
    STORAGE_NAME_FOR_REGISTRATION = "b"
    DELETE_DIR_ENTRIES_REGISTERED_SECS_AGO = 3600
    STATUS_FILE_FILENAME = ".directory_watcher_status.run"
    STATUS_FILE_FULL_FILENAME = f"{DIRECTORY_TO_WATCH}/{STATUS_FILE_FILENAME}"
    RELOAD_STATUS_FILE = True
    # These should not be required in final system
    LOCATION_NAME = "ThisDLMClientLocationName"
    LOCATION_TYPE = "ThisDLMClientLocation"
    LOCATION_COUNTRY = "Australia"
    LOCATION_CITY = "Marksville"
    LOCATION_FACILITY = "ICRAR"
    STORAGE_NAME = "data"
    STORAGE_TYPE = "disk"
    STORAGE_CONFIG = {"name":"data","type":"local", "parameters":{}}
    EB_ID = "test_eb_id"


def get_config() -> Config:
    """Build the configuration."""
    print(CONFIG)
    # if CONFIG.directory_to_watch is not None:
    # return CONFIG

    CONFIG.directory_to_watch = WatchConfiguration.DIRECTORY_TO_WATCH
    CONFIG.status_file_full_filename = WatchConfiguration.STATUS_FILE_FULL_FILENAME
    CONFIG.reload_status_file = WatchConfiguration.RELOAD_STATUS_FILE
    CONFIG.ingest_url = DLMConfiguration.INGEST_URL
    CONFIG.storage_url = DLMConfiguration.STORAGE_URL
    CONFIG.storage_name = WatchConfiguration.STORAGE_NAME
    CONFIG.ingest_configuration = configuration.Configuration(host=DLMConfiguration.INGEST_URL)
    CONFIG.storage_configuration = configuration.Configuration(host=DLMConfiguration.STORAGE_URL)
    return CONFIG

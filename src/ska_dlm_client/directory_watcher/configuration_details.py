"""This is expected to be replaced based on what final deployment looks like."""

import sys


class DLMConfiguration:  # pylint: disable=too-few-public-methods
    """Configuration of the DLM."""

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


class WatchConfiguration:  # pylint: disable=too-few-public-methods
    """Configuration of the watcher."""

    DIRECTORY_TO_WATCH = "/Users/00077990/yanda/pi24/watch_dir"
    STORAGE_ID_FOR_REGISTRATION = "b"
    DELETE_DIR_ENTRIES_REGISTERED_SECS_AGO = 3600
    WATCHER_STATUS_FILENAME = f"{sys.modules[__name__]}.run"
    WATCHER_STATUS_FULL_FILENAME = f"{DIRECTORY_TO_WATCH}/{WATCHER_STATUS_FILENAME})"
    RELOAD_WATCHER_STATUS_FILE = True

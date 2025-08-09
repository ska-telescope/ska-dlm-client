"""Directory watcher package for ska-dlm-client.

This package provides functionality to watch directories for changes and
register data products with the Data Lifecycle Management (DLM) system.
"""

__author__ = """Mark Boulton"""
__email__ = "mark.boulton@uwa.edu.au"
__version__ = "1.0.0"

from ska_dlm_client.directory_watcher.config import Config
from ska_dlm_client.directory_watcher.directory_watcher import (
    DirectoryWatcher,
    INotifyDirectoryWatcher,
    LStatPollingEmitter,
    PollingDirectoryWatcher,
)
from ska_dlm_client.directory_watcher.registration_processor import RegistrationProcessor
from ska_dlm_client.directory_watcher.watcher_event_handler import WatcherEventHandler

__all__ = [
    "DirectoryWatcher",
    "INotifyDirectoryWatcher",
    "PollingDirectoryWatcher",
    "LStatPollingEmitter",
    "Config",
    "RegistrationProcessor",
    "WatcherEventHandler",
]

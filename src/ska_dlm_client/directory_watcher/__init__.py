"""Directory watcher package for ska-dlm-client.

This package provides functionality to watch directories for changes and
register data products with the Data Lifecycle Management (DLM) system.
"""

__author__ = """Mark Boulton"""
__email__ = "mark.boulton@uwa.edu.au"
__version__ = "1.1.0"

from ska_dlm_client.directory_watcher.config import WatcherConfig
from ska_dlm_client.directory_watcher.directory_watcher import (
    DirectoryWatcher,
    INotifyDirectoryWatcher,
    LStatPollingEmitter,
    PollingDirectoryWatcher,
)
from ska_dlm_client.directory_watcher.watcher_event_handler import WatcherEventHandler
from ska_dlm_client.registration_processor import RegistrationProcessor

__all__ = [
    "DirectoryWatcher",
    "INotifyDirectoryWatcher",
    "PollingDirectoryWatcher",
    "LStatPollingEmitter",
    "WatcherConfig",
    "RegistrationProcessor",
    "WatcherEventHandler",
]

"""Directory watcher package for ska-dlm-client.

This package provides functionality to watch directories for changes and
register data products with the Data Lifecycle Management (DLM) system.
"""

__author__ = """Mark Boulton"""
__email__ = "mark.boulton@uwa.edu.au"
__version__ = "1.1.0"

from .config import WatcherConfig

__all__ = [
    "WatcherConfig",
]

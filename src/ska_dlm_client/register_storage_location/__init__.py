"""Register storage location package for ska-dlm-client.

This package provides functionality to initialize and register storage locations
with the Data Lifecycle Management (DLM) system. It is used during startup of
the DLM clients to ensure that the necessary storage locations are registered
and configured for rclone.
"""

__author__ = """Mark Boulton"""
__email__ = "mark.boulton@uwa.edu.au"
__version__ = "1.0.0"

from ska_dlm_client.register_storage_location.main import (
    get_or_init_location,
    get_or_init_storage,
    main,
    setup_testing,
)

__all__ = [
    "main",
    "setup_testing",
    "get_or_init_location",
    "get_or_init_storage",
]

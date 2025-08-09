"""Register storage location package for ska-dlm-client.

This package provides functionality to initialize and register storage locations
with the Data Lifecycle Management (DLM) system. It is primarily used for
testing and development setup.
"""

__author__ = """Mark Boulton"""
__email__ = "mark.boulton@uwa.edu.au"
__version__ = "1.0.0"

from ska_dlm_client.register_storage_location.main import (
    init_location_for_testing,
    init_storage_for_testing,
    main,
    setup_testing,
)

__all__ = [
    "main",
    "setup_testing",
    "init_location_for_testing",
    "init_storage_for_testing",
]

"""Register storage location package for ska-dlm-client.

This package provides functionality to initialize and register storage locations
with the Data Lifecycle Management (DLM) system. It is used during startup of
the DLM clients to ensure that the necessary storage locations are registered
and configured for rclone.
"""

__author__ = """Mark Boulton"""
__email__ = "mark.boulton@uwa.edu.au"
__version__ = "1.0.0"

__all__ = [
    "main",
    # "setup_testing",
    # "get_or_init_location",
    # "get_or_init_storage",
]


# def __getattr__(name: str):
#     """Lazily expose helpers without importing main at package import time."""
#     if name in __all__:
#         from ska_dlm_client.register_storage_location import main as _main

#         return getattr(_main, name)
#     raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

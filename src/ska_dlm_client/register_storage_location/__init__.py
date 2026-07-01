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
]

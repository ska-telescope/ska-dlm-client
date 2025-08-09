"""Startup verification package for ska-dlm-client.

This package provides functionality to verify the proper operation of the
Data Lifecycle Management (DLM) client during startup. It creates test data
and verifies that it is properly registered with the DLM system.
"""

__author__ = """Mark Boulton"""
__email__ = "mark.boulton@uwa.edu.au"
__version__ = "1.0.0"

from ska_dlm_client.startup_verification.main import StartupVerification, main
from ska_dlm_client.startup_verification.utils import CmdLineParameters

__all__ = [
    "main",
    "StartupVerification",
    "CmdLineParameters",
]

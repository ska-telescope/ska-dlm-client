"""Top-level package for ska-dlm-client."""

import shutil
from pathlib import Path

import yaml
from benedict import benedict

__author__ = """Mark Boulton"""
__email__ = "mark.boulton@uwa.edu.au"
__version__ = "0.0.1"

DLM_CLIENT_LIB_DIR = Path(__file__).parent
"""The library install path of dlm-client."""

DLM_CLIENT_HOME = Path.home() / ".dlm_client/"
"""The configuration path of dlm-client."""


def read_config(user_config_file: Path = DLM_CLIENT_HOME / "config.yaml") -> benedict:
    """Read the config file and return the config dictionary."""
    if not user_config_file.exists():
        # create the default user config in DLM_HOME if it does not already exist
        print(f"DLM config file {user_config_file} not found - creating and using default")
        user_config_file.parent.mkdir(exist_ok=True)
        default_user_config_file = DLM_CLIENT_LIB_DIR / "config.yaml"
        shutil.copy(default_user_config_file, user_config_file)

    with open(user_config_file, "r", encoding="utf-8") as file:
        return benedict(yaml.safe_load(file))


CONFIG = read_config()

__all__ = [
    "DLM_CLIENT_HOME",
    "DLM_CLIENT_LIB_DIR",
    "CONFIG",
]

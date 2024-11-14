"""Class to handle various operations related to metadata for data items/products.

Refer to https://confluence.skatelescope.org/display/SWSI/\
ADR-55+Definition+of+metadata+for+data+management+at+AA0.5
for additional details.

"""

import logging
from pathlib import Path

import yaml
from benedict import benedict

import ska_dlm_client.directory_watcher.config

logger = logging.getLogger(__name__)


class DataProductMetadata:
    """Class handling metadata for data item(s)."""

    metadata_file_path: Path
    dp_metadata: dict

    def __init__(self, metadata_file_path: Path):
        """Init the class."""
        if metadata_file_path.exists():
            self.metadata_file_path = metadata_file_path
        else:
            raise FileNotFoundError(f"The metadata file {metadata_file_path} does not exist.")
        self.load_metadata()

    def load_metadata(self):
        """Read in the metadata file."""
        with open(self.metadata_file_path, "r", encoding="utf-8") as file:
            self.dp_metadata = benedict(yaml.safe_load(file))

    def get_execution_block_id(self):
        """Return the executin block as defined in the metadata file.

        Returns
        -------
        str | None
            Returns the execution block as in the metadata file or None if not found.
        """
        if (
            ska_dlm_client.directory_watcher.config.METADATA_EXECUTION_BLOCK_KEY
            in self.dp_metadata
        ):
            return self.dp_metadata[
                ska_dlm_client.directory_watcher.config.METADATA_EXECUTION_BLOCK_KEY
            ]
        return None

"""Class to handle various operations related to metadata for data items/products.

Refer to https://confluence.skatelescope.org/display/SWSI/\
ADR-55+Definition+of+metadata+for+data+management+at+AA0.5
for additional details.

This is similar to https://gitlab.com/ska-telescope/sdp/ska-sdp-dataproduct-metadata
but is SDP specific hence it is not the preferred option here.

"""

import logging

import yaml

from ska_dlm_client.directory_watcher import config

logger = logging.getLogger(__name__)


class DataProductMetadata:
    """Class handling metadata for data item(s)."""

    filepath: str
    root: dict

    def __init__(self, filepath: str):
        """Init the class."""
        self.filepath = filepath
        self.load_metadata()

    def load_metadata(self):
        """Read in the metadata file.

        Raises
        ------
        TypeError
            If during the loading/reading of the given metadata file an unexpected condition
            is found then this exception will be raised. Refer to the error message for details.

        """
        # Log that the metadata filename does not match the expected naming convention.
        # An error is not raised in order to allow for the best chance of the metadata being
        # stored with its data product. An exception is not raised as the file may still be a
        # valid format with a valid key.
        if not self.filepath.endswith(config.METADATA_FILENAME):
            logger.warning(
                "Expected metadata file name to with %s but got %s",
                config.METADATA_FILENAME,
                self.filepath,
            )
        with open(self.filepath, "r", encoding="utf-8") as file:
            metadata = yaml.safe_load(file)
            if not isinstance(metadata, dict):
                raise TypeError(
                    f"Metadata file {self.filepath} does contain a dictionary root element."
                )
            self.root = metadata

    def get_execution_block_value(self):
        """Return the executin block value/attribute/id as defined in the metadata file.

        Returns
        -------
        str | None
            Returns the execution block as in the metadata file or None if not found.
        """
        return self.root.get(config.METADATA_EXECUTION_BLOCK_KEY, None)

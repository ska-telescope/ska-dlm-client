"""Class to handle various operations related to metadata for data items/products."""

import logging
import os

import yaml

from ska_dlm_client.directory_watcher import config
from ska_dlm_client.minimal_metadata_generator import minimal_metadata_generator

logger = logging.getLogger(__name__)


class DataProductMetadata:
    """Class to load or create metadata for the given data products.

    Refer to https://confluence.skatelescope.org/display/SWSI/\
    ADR-55+Definition+of+metadata+for+data+management+at+AA0.5
    for additional details related to conventions used in the class.

    For a given data product a set of rules are followed to load its associated metadata file.
    If a metadata file cannot be found then metadata is generated for the data product in order
    that the data products can be stored with a minimal set of metadata.

    The rules followed for searching for a metadata file are:
    * If data product is a file then look in the same directory as the data product for a file
    with the name ```config.METADATA_FILENAME```
    * If data product is a directory then look inside that same directory for a file with the
    name ```config.METADATA_FILENAME```
    * minimal_metadata_generator is used to generate metadata if a metadata file cannot be found.

    NOTE: Any created metadata is held in this class and written out to disk as DLM client only
    needs it to register the data product.

    The found metadata file must:
    * be YAML compliant
    * contain only a single dictionary document
    * use only the JSON subset of YAML values

    This is similar to https://gitlab.com/ska-telescope/sdp/ska-sdp-dataproduct-metadata
    but is SDP specific hence it is not the preferred option here.

    """

    dp_path: str
    dp_metadata_loaded_from_a_file: bool
    root: dict

    def __init__(self, dp_path: str):
        """Init the class."""
        self.dp_path = dp_path
        if not os.path.exists(self.dp_path):
            raise FileNotFoundError(f"File not found {self.dp_path}")
        dir_path = ""
        if os.path.isfile(self.dp_path):
            dir_path = os.path.dirname(self.dp_path)
        elif os.path.isdir(self.dp_path):
            dir_path = self.dp_path
        metadata_path = os.path.join(dir_path, config.METADATA_FILENAME)
        if os.path.exists(metadata_path):
            self.load_metadata(metadata_path)
            self.dp_metadata_loaded_from_a_file = True
        else:
            self.root = minimal_metadata_generator(dp_path)
            self.dp_metadata_loaded_from_a_file = False

    def load_metadata(self, metadata_path: str):
        """Read in the metadata file.

        Raises
        ------
        FileNotFoundError
            https://docs.python.org/3/library/exceptions.html#FileNotFoundError
        OSError
            https://docs.python.org/3/library/exceptions.html#OSError
        TypeError
            Root document element in the read file is not a dictionary.
        ScannerError
            File is not yaml compliant.
        ComposerError
            Multiple metadata documents in a single yaml file is not supported.

        """
        # Log that the metadata filename does not match the expected naming convention.
        # An error is not raised in order to allow for the best chance of the metadata being
        # stored with its data product. An exception is not raised as the file may still be a
        # valid format with a valid key.
        if not metadata_path.endswith(config.METADATA_FILENAME):
            logger.warning(
                "Expected metadata file name to be %s but got %s",
                config.METADATA_FILENAME,
                metadata_path,
            )
        with open(metadata_path, "r", encoding="utf-8") as file:
            metadata = yaml.safe_load(file)
            if not isinstance(metadata, dict):
                raise TypeError(
                    f"Metadata file {metadata_path} does not contain a dictionary root element."
                )
            self.root = metadata

    def get_execution_block_value(self) -> str | None:
        """Return the execution block value/attribute/id as defined in the metadata file.

        Returns
        -------
        str | None
            Returns the execution block as in the metadata file or None if not found.
        """
        return self.root.get(config.METADATA_EXECUTION_BLOCK_KEY, None)

    def as_dict(self) -> dict:
        """Return a dictitonary representation of the metadata."""
        return self.root

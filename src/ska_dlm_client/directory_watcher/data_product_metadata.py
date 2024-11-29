"""Class to handle various operations related to metadata for data items/products."""

import logging
import os
from os import listdir
from os.path import isdir, isfile, islink

import yaml

from ska_dlm_client.directory_watcher import config
from ska_dlm_client.directory_watcher.minimal_metadata_generator import minimal_metadata_generator

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

    _dp_path: str
    _found_metadata_filename: str = None
    root: dict

    def __init__(self, dp_path: str):
        """Init the class."""
        self._dp_path = dp_path
        if not os.path.exists(self._dp_path):
            raise FileNotFoundError(f"File not found {self._dp_path}")
        dir_path = ""
        if os.path.isfile(self._dp_path):
            dir_path = os.path.dirname(self._dp_path)
        elif os.path.isdir(self._dp_path):
            dir_path = self._dp_path
        metadata_path = os.path.join(dir_path, config.METADATA_FILENAME)
        if os.path.exists(metadata_path):
            self.load_metadata(metadata_path)
            self._found_metadata_filename = metadata_path
        else:
            self.root = minimal_metadata_generator(dp_path)

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

    def is_generated_metadata(self):
        """Let the caller know if metadata file is generated or not."""
        return self._found_metadata_filename is None

    def found_metadata_filename(self):
        """Return the path found to the metadata file."""
        return self._found_metadata_filename

    def as_dict(self) -> dict:
        """Return a dictitonary representation of the metadata."""
        return self.root


def directory_is_measurement_set(full_path: str) -> bool:
    """Return true if path points to a measurement set."""
    return os.path.isdir(full_path) and full_path.lower().endswith(
        config.DIRECTORY_IS_MEASUREMENT_SET_SUFFIX
    )


def is_metadata_file(filename: str) -> bool:
    """Return True if if given file is a data product metadata file.

    NOTE: This will need work as more 'rules' on what is metadata are discovered.
    """
    if str is None:
        return False
    return filename.endswith(config.METADATA_FILENAME) and os.path.exists(filename)


def data_product_root(full_path: str):
    """Return the root directory of the data product."""
    # found_metadata = False
    if isfile(full_path):
        logger.info("searching for metadata for file %s", full_path)
        # metadata_filename = os.path.join(os.path.dirname(full_path), config.METADATA_FILENAME)
        # found_metadata = is_metadata_file(metadata_filename)
    elif isdir(full_path):
        logger.info("searching for metadata for directory %s", full_path)
        if directory_is_measurement_set(full_path):
            # if a measurement set then just add directory
            # TODO: handle case for measurement set
            logger.error("Found measurement set but don't know where to look for metadata file.")
            logger.error("^^^^^^^^^^^^^^^^^^^^^^")
        else:
            # otherwise see if metadata file exists
            dir_entries = listdir(full_path)
            for dir_entry in dir_entries:
                new_full_path = f"{full_path}/{dir_entry}"
                logger.info("still implementing %s", new_full_path)
                # new_relative_path = f"{relative_path}/{dir_entry}"
                # self.add_path(full_path=new_full_path, relative_path=new_relative_path)
    else:
        if islink(full_path):
            error_text = f"Symbolic links are currently not supported: {full_path}"
        else:
            error_text = f"Unspported file/directory entry type: {full_path}"
        logging.error(error_text)
        # TODO: Do we throw this or just log here, raise RuntimeError(error_text)

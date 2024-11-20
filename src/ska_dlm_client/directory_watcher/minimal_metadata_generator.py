"""This module is called when the dataproduct is an unidentified filetype."""

import binascii
import logging
import os
from datetime import datetime

from benedict import benedict
from ska_sdp_dataproduct_metadata import MetaData

FOUR_BYTE_PAD: int = 0xFFFFFFFF
logger = logging.getLogger(__name__)


def _file_or_dir_size(path: str) -> int:
    """Calculate file size in kB for a single file or directory."""
    try:
        total_size = 0
        if os.path.isfile(path) and not os.path.islink(path):  # Exclude symbolic links
            total_size = os.path.getsize(path)
        elif os.path.isdir(path):
            for dirpath, _, filenames in os.walk(path):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    if not os.path.islink(file_path):  # Exclude symbolic links
                        total_size += os.path.getsize(file_path)
        final_size = total_size / 1024.0
        return final_size if final_size >= 1.0 else 1.0
    except OSError as err:
        logger.error("Failed to get size for %s with exception %s", file_path, err)
        return 0


def _file_crc32(file_path: str, chunksize: int = 0x10000) -> str:
    """Compute CRC32 from file path as a hexidecimal string.

    Parameters
    ----------
    file_path: str
        existing file to calculate crc32 for.
    chunksize: int
        number of bytes to buffer, default is 64KiB.

    Returns
    -------
    str
        CRC32 formatted string of 8 hexadecimal characters.
    """
    with open(file_path, "rb") as file_reader:
        checksum = 0
        while chunk := file_reader.read(chunksize):
            checksum = binascii.crc32(chunk, checksum)
        return f"{checksum:08x}"


def _file_dict(file_path: str, relative_path: str, description: str) -> dict:
    """Build the dict of file attribute for metadata."""
    try:
        size = os.path.getsize(file_path)
    except OSError as err:
        logger.error("Failed to get size for %s with exception %s", file_path, err)
        size = 0

    try:
        crc = _file_crc32(file_path)
    except OSError as err:
        logger.error("Failed to get CRC for %s with exception %s", file_path, err)
        crc = f"{FOUR_BYTE_PAD:08x}"

    return {
        "crc": crc,
        "description": description,
        "path": relative_path,
        "size": size,
        "status": "done",  # file status: working, done or failure
    }


def _build_files_list(path: str, description: str) -> list[dict]:
    """Build a list of all files within a given directory or a single file."""
    files_list = []

    if os.path.isfile(path):
        file_path = os.path.abspath(path)
        file_dict = _file_dict(
            file_path=file_path, relative_path=os.path.basename(file_path), description=description
        )
        files_list.append(file_dict)
    elif os.path.isdir(path):
        for root, _, files in os.walk(path, topdown=False):
            for name in files:
                file_path = os.path.join(root, name)
                relative_path = os.path.relpath(file_path, path)
                file_dict = _file_dict(
                    file_path=file_path, relative_path=relative_path, description=description
                )
                files_list.append(file_dict)
    else:
        raise ValueError("Path must be a file or directory.")
    return files_list


def minimal_metadata_generator(dataproduct_path: str) -> MetaData:
    """Given the dataproduct_path, file or directory, generate a MetaData object.

    This function is intended to build a minimal MetaData from a single file or from a
    directory of files.

    MetaData is returned as the caller is likely calling this as the real file representing
    MetaData is not available.

    No metadata file will be physically created it is just returned as a MetaData object.

    The fields of the MetaData that are filled include:
        * execution_block_id based on date and time for uniqueness but readability
        * data.files   NOTE: a file entry will be created for each file in a directory
            * crc
            * description
            * path of a file
            * size in bytes
            * status current hard coded to "done"
        * data.obscore.access_estsize of file or contents of directory

    Some internal exceptions are caught and logged with some "defaults" being put in their place
    so that a MetaData can always be generated. This will likely need refinement.

    Raises
    ------
    ValueError
        When the dataproduct_path is not a file or directory. Not expected during normal
        operation but problems in this area are being looked at in
        https://jira.skatelescope.org/browse/YAN-1893
    OSError
        https://docs.python.org/3/library/exceptions.html#OSError

    """
    meta = MetaData()
    now = datetime.now()  # current date and time
    pseudo_eb_id = now.strftime("unknow-metadata-%Y/%m/%-d%H:%M:%S-%f")
    meta.set_execution_block_id(execution_block_id=pseudo_eb_id)
    data: benedict = meta.get_data()
    description = f"Metadata generated by {__name__} as {pseudo_eb_id} because no metadata found."
    data.files = _build_files_list(dataproduct_path, description)
    data.obscore.access_estsize = _file_or_dir_size(dataproduct_path)

    return meta

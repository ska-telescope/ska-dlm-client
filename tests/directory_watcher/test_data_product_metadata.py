"""Metadata related tests."""

import os
import shutil
from shutil import copytree

import pytest

from ska_dlm_client.data_product_metadata import DataProductMetadata
from ska_dlm_client.directory_watcher import config

METADATA_FILE_EB_ID = "eb-m001-20191031-12345"
TEST_DATA_PRODUCT_FILE = "a_data_product.ext"
TEST_DATA_PRODUCT_DIRECTORY = "some_path"
TEST_EB_ID = "eb-m001-20191031-12345"
UNKNOWN_EB_ID = "unknown-metadata-"


@pytest.fixture(autouse=True)
def datadir(tmp_path, request):
    """Copy the metadata file to the test location."""
    filename = request.module.__file__
    src_dir, _ = os.path.splitext(filename)

    if os.path.isdir(src_dir):
        copytree(src=src_dir, dst=tmp_path, dirs_exist_ok=True)
    print(os.listdir(tmp_path))


def test_data_product_metadata(tmp_path):
    """Test the DataProductMetadata class."""
    # Raises exception when file not found
    with pytest.raises(FileNotFoundError):
        DataProductMetadata(f"{tmp_path}/a-dummy-file")

    absolute_path_to_dp_file = f"{tmp_path}/{TEST_DATA_PRODUCT_FILE}"
    absolute_path_to_metadata_file = f"{tmp_path}/{config.METADATA_FILENAME}"

    # Given a data product load the metadata file and check the eb_id
    dpm = DataProductMetadata(absolute_path_to_dp_file)
    assert dpm.get_execution_block_value() == TEST_EB_ID

    # If a directory does not contain metadata check that some is created
    absolute_path_to_dp_dir = f"{tmp_path}/{TEST_DATA_PRODUCT_DIRECTORY}"
    dpm = DataProductMetadata(absolute_path_to_dp_dir)
    assert dpm.get_execution_block_value().startswith(UNKNOWN_EB_ID)

    # If a directory does contain metadata check it is found and loaded
    dst_file = os.path.join(absolute_path_to_dp_dir, config.METADATA_FILENAME)
    shutil.copyfile(src=absolute_path_to_metadata_file, dst=dst_file)
    dpm = DataProductMetadata(absolute_path_to_dp_dir)
    assert dpm.get_execution_block_value() == TEST_EB_ID

    # Given a data product load the metadata file and check the eb_id
    os.remove(absolute_path_to_metadata_file)
    dpm = DataProductMetadata(absolute_path_to_dp_file)
    assert dpm.get_execution_block_value().startswith(UNKNOWN_EB_ID)

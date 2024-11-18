"""Metadata related tests."""

import os
from shutil import copytree

import pytest

from ska_dlm_client.directory_watcher import config
from ska_dlm_client.directory_watcher.data_product_metadata import DataProductMetadata


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
    with pytest.raises(FileNotFoundError):
        DataProductMetadata(f"{tmp_path}/a-dummy-file")

    dpm = DataProductMetadata(f"{tmp_path}/{config.METADATA_FILENAME}")
    assert dpm.get_execution_block_value() == "eb-m001-20191031-12345"

    dpm = DataProductMetadata(f"{tmp_path}/invalid-{config.METADATA_FILENAME}")
    assert dpm.get_execution_block_value() is None

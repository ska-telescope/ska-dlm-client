"""Registration processor related tests."""

import os
from unittest import mock

import pytest

from ska_dlm_client.data_product_metadata import DataProductMetadata
from ska_dlm_client.directory_watcher.config import WatcherConfig
from ska_dlm_client.directory_watcher.directory_watcher_entries import DirectoryWatcherEntries
from ska_dlm_client.openapi.configuration import Configuration
from ska_dlm_client.openapi.exceptions import OpenApiException
from ska_dlm_client.registration_processor import (
    Item,
    ItemType,
    RegistrationProcessor,
    _directory_contains_metadata_file,
    _directory_contains_only_directories,
    _directory_contains_only_files,
    _directory_list_minus_metadata_file,
    _generate_dir_item_list,
    _generate_paths_and_metadata,
    _generate_paths_and_metadata_for_directory,
    _item_for_single_file_with_metadata,
    _item_list_minus_metadata_file,
    _measurement_set_directory_in,
)


def returned_items_match(test_path: str, dir_entries: list[Item]):
    """Perform asserts on generated item list."""
    assert dir_entries[0].path_rel_to_watch_dir == test_path
    assert dir_entries[0].item_type == ItemType.CONTAINER
    assert dir_entries[0].metadata is not None
    assert dir_entries[1].path_rel_to_watch_dir == f"{test_path}/weights" or f"{test_path}/dlm"
    assert dir_entries[1].item_type == ItemType.FILE
    assert dir_entries[1].parent == dir_entries[0]
    assert dir_entries[1].metadata is None
    assert dir_entries[2].path_rel_to_watch_dir == f"{test_path}/weights" or f"{test_path}/dlm"
    assert dir_entries[2].item_type == ItemType.FILE
    assert dir_entries[2].parent == dir_entries[0]
    assert dir_entries[2].metadata is None


def test_registration_processor(request):
    """Test the registration_processor module."""
    # Determine path where test files are stored.
    filename = request.module.__file__
    test_dir, _ = os.path.splitext(filename)

    # Setup what would be the directory to watch.
    watch_dir = os.path.join(test_dir, "watch_dir")

    # Test when path to add is a file.
    absolute_path = os.path.join(watch_dir, "data_item_file_only")
    rel_path = os.path.split(absolute_path)[1]
    dir_entries = _generate_paths_and_metadata(absolute_path, rel_path)
    assert dir_entries[0].path_rel_to_watch_dir == "data_item_file_only"

    # Test when path to add is symlink.
    test_path = "symbolic_link_path"
    absolute_path = os.path.join(watch_dir, test_path)
    rel_path = os.path.split(absolute_path)[1]
    dir_entries = _generate_paths_and_metadata(absolute_path, rel_path)
    returned_items_match(test_path=test_path, dir_entries=dir_entries)

    # Test when path to add is a directory.
    test_path = "directory_entry"
    absolute_path = os.path.join(watch_dir, test_path)
    rel_path = os.path.split(absolute_path)[1]
    dir_entries = _generate_paths_and_metadata(absolute_path, rel_path)
    returned_items_match(test_path=test_path, dir_entries=dir_entries)


def test_directory_helper_functions(request):
    """Test the directory helper functions."""
    # Determine path where test files are stored.
    filename = request.module.__file__
    test_dir, _ = os.path.splitext(filename)

    # Setup what would be the directory to watch.
    watch_dir = os.path.join(test_dir, "watch_dir")

    # Test _directory_contains_only_directories
    # Create a temporary directory with only directories
    temp_dir_path = os.path.join(test_dir, "temp_dir_only_dirs")
    os.makedirs(temp_dir_path, exist_ok=True)
    os.makedirs(os.path.join(temp_dir_path, "dir1"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir_path, "dir2"), exist_ok=True)

    assert _directory_contains_only_directories(temp_dir_path) is True

    # Add a file to the directory
    with open(os.path.join(temp_dir_path, "file1"), "w", encoding="utf-8") as f:
        f.write("test")

    assert _directory_contains_only_directories(temp_dir_path) is False

    # Clean up
    os.remove(os.path.join(temp_dir_path, "file1"))
    os.rmdir(os.path.join(temp_dir_path, "dir1"))
    os.rmdir(os.path.join(temp_dir_path, "dir2"))
    os.rmdir(temp_dir_path)

    # Test _directory_contains_only_files
    # Create a temporary directory with only files
    temp_dir_path = os.path.join(test_dir, "temp_dir_only_files")
    os.makedirs(temp_dir_path, exist_ok=True)
    with open(os.path.join(temp_dir_path, "file1"), "w", encoding="utf-8") as f:
        f.write("test")
    with open(os.path.join(temp_dir_path, "file2"), "w", encoding="utf-8") as f:
        f.write("test")

    assert _directory_contains_only_files(temp_dir_path) is True

    # Add a directory to the directory
    os.makedirs(os.path.join(temp_dir_path, "dir1"), exist_ok=True)

    assert _directory_contains_only_files(temp_dir_path) is False

    # Clean up
    os.rmdir(os.path.join(temp_dir_path, "dir1"))
    os.remove(os.path.join(temp_dir_path, "file1"))
    os.remove(os.path.join(temp_dir_path, "file2"))
    os.rmdir(temp_dir_path)

    # Test _directory_contains_metadata_file
    # The directory_entry directory should contain a metadata file
    directory_entry_path = os.path.join(watch_dir, "directory_entry")
    assert _directory_contains_metadata_file(directory_entry_path) is True

    # Create a temporary directory without a metadata file
    temp_dir_path = os.path.join(test_dir, "temp_dir_no_metadata")
    os.makedirs(temp_dir_path, exist_ok=True)
    with open(os.path.join(temp_dir_path, "file1"), "w", encoding="utf-8") as f:
        f.write("test")

    assert _directory_contains_metadata_file(temp_dir_path) is False

    # Clean up
    os.remove(os.path.join(temp_dir_path, "file1"))
    os.rmdir(temp_dir_path)

    # Test _directory_list_minus_metadata_file
    # The directory_entry directory should contain a metadata file
    directory_entry_path = os.path.join(watch_dir, "directory_entry")
    dir_list = _directory_list_minus_metadata_file(directory_entry_path)
    assert "ska-data-product.yaml" not in dir_list
    assert "data" in dir_list
    assert "weights" in dir_list


def test_item_for_single_file_with_metadata(request):
    """Test the _item_for_single_file_with_metadata function."""
    # Determine path where test files are stored.
    filename = request.module.__file__
    test_dir, _ = os.path.splitext(filename)

    # Setup what would be the directory to watch.
    watch_dir = os.path.join(test_dir, "watch_dir")

    # Test with a file
    file_path = os.path.join(watch_dir, "data_item_file_only")
    rel_path = os.path.split(file_path)[1]

    item = _item_for_single_file_with_metadata(file_path, rel_path)

    assert item.path_rel_to_watch_dir == rel_path
    assert item.item_type == ItemType.FILE
    assert item.metadata is not None
    assert item.parent is None


def test_item_list_minus_metadata_file(
    request, mock_data_product_metadata
):  # pylint: disable=redefined-outer-name
    """Test the _item_list_minus_metadata_file function."""
    # Determine path where test files are stored.
    filename = request.module.__file__
    test_dir, _ = os.path.splitext(filename)

    # Setup what would be the directory to watch.
    watch_dir = os.path.join(test_dir, "watch_dir")

    # Create a container item
    container_item = Item(
        path_rel_to_watch_dir="container",
        item_type=ItemType.CONTAINER,
        metadata=mock_data_product_metadata.return_value,
    )

    # Test with a directory
    directory_path = os.path.join(watch_dir, "directory_entry")
    rel_path = os.path.split(directory_path)[1]

    item_list = _item_list_minus_metadata_file(container_item, directory_path, rel_path)

    assert len(item_list) == 2
    for item in item_list:
        assert item.item_type == ItemType.FILE
        assert item.metadata is None
        assert item.parent == container_item
        assert item.path_rel_to_watch_dir in [f"{rel_path}/data", f"{rel_path}/weights"]


def test_measurement_set_directory_in(request, monkeypatch):
    """Test the _measurement_set_directory_in function."""
    # Determine path where test files are stored.
    filename = request.module.__file__
    test_dir, _ = os.path.splitext(filename)

    # Setup what would be the directory to watch.
    watch_dir = os.path.join(test_dir, "watch_dir")

    # Mock the config.DIRECTORY_IS_MEASUREMENT_SET_SUFFIX
    monkeypatch.setattr("ska_dlm_client.config.DIRECTORY_IS_MEASUREMENT_SET_SUFFIX", ".ms")

    # Create a temporary directory with a measurement set directory
    temp_dir_path = os.path.join(test_dir, "temp_dir_with_ms")
    os.makedirs(temp_dir_path, exist_ok=True)
    os.makedirs(os.path.join(temp_dir_path, "test.ms"), exist_ok=True)

    ms_dir = _measurement_set_directory_in(temp_dir_path)
    assert ms_dir == "test.ms"

    # Test with a directory without a measurement set directory
    directory_path = os.path.join(watch_dir, "directory_entry")
    ms_dir = _measurement_set_directory_in(directory_path)
    assert ms_dir is None

    # Clean up
    os.rmdir(os.path.join(temp_dir_path, "test.ms"))
    os.rmdir(temp_dir_path)


def test_generate_item_list_for_data_product(request):
    """Test the _generate_item_list_for_data_product function."""
    # Determine path where test files are stored.
    filename = request.module.__file__
    test_dir, _ = os.path.splitext(filename)

    # Setup what would be the directory to watch.
    watch_dir = os.path.join(test_dir, "watch_dir")

    # Test with a directory containing a metadata file
    directory_path = os.path.join(watch_dir, "directory_entry")
    rel_path = os.path.split(directory_path)[1]

    item_list = _generate_dir_item_list(directory_path, rel_path)

    assert len(item_list) == 3
    assert item_list[0].item_type == ItemType.CONTAINER
    assert item_list[0].metadata is not None
    assert item_list[0].parent is None
    assert item_list[1].item_type == ItemType.FILE
    assert item_list[1].metadata is None
    assert item_list[1].parent == item_list[0]
    assert item_list[2].item_type == ItemType.FILE
    assert item_list[2].metadata is None
    assert item_list[2].parent == item_list[0]


def test_generate_paths_and_metadata_for_directory(request):
    """Test the _generate_paths_and_metadata_for_directory function."""
    # Determine path where test files are stored.
    filename = request.module.__file__
    test_dir, _ = os.path.splitext(filename)

    # Setup what would be the directory to watch.
    watch_dir = os.path.join(test_dir, "watch_dir")

    # Test with a directory containing a metadata file
    directory_path = os.path.join(watch_dir, "directory_entry")
    rel_path = os.path.split(directory_path)[1]

    item_list = _generate_paths_and_metadata_for_directory(directory_path, rel_path)

    assert len(item_list) == 3
    assert item_list[0].item_type == ItemType.CONTAINER
    assert item_list[0].metadata is not None
    assert item_list[0].parent is None
    assert item_list[1].item_type == ItemType.FILE
    assert item_list[1].metadata is None
    assert item_list[1].parent == item_list[0]
    assert item_list[2].item_type == ItemType.FILE
    assert item_list[2].metadata is None
    assert item_list[2].parent == item_list[0]


@pytest.fixture
def mock_config():
    """Create a mock Config object for testing."""
    config = mock.MagicMock(spec=WatcherConfig)
    config.directory_to_watch = "/test/watch/dir"
    config.storage_name = "test-storage"
    config.ingest_register_path_to_add = ""
    config.perform_actual_ingest_and_migration = True
    config.rclone_access_check_on_register = False
    config.migration_destination_storage_name = "test-destination-storage"
    config.directory_watcher_entries = mock.MagicMock(spec=DirectoryWatcherEntries)
    config.ingest_url = "http://test-ingest:8000"

    # Use real Configuration instances instead of MagicMocks
    config.ingest_configuration = Configuration(host="http://test-ingest:8000")
    config.migration_configuration = Configuration(host="http://test-migration:8000")

    return config


@pytest.fixture
def mock_api_client():
    """Create a mock ApiClient for testing."""
    with mock.patch("ska_dlm_client.registration_processor.api_client.ApiClient") as mock_client:
        # Return a context manager that can be used with 'with' statements
        mock_instance = mock.MagicMock()
        mock_client.return_value.__enter__.return_value = mock_instance
        yield mock_client


@pytest.fixture
def mock_ingest_api():
    """Create a mock IngestApi for testing."""
    with mock.patch("ska_dlm_client.registration_processor.ingest_api.IngestApi") as mock_api:
        mock_api.return_value.register_data_item.return_value = "test-uuid"
        yield mock_api


@pytest.fixture
def mock_migration_api():
    """Create a mock MigrationApi for testing."""
    with mock.patch(
        "ska_dlm_client.registration_processor.migration_api.MigrationApi"
    ) as mock_api:
        mock_api.return_value.copy_data_item.return_value = "test-migration-uuid"
        yield mock_api


@pytest.fixture
def mock_data_product_metadata():
    """Create a mock DataProductMetadata for testing."""
    with mock.patch("ska_dlm_client.registration_processor.DataProductMetadata") as mock_dpm:
        mock_metadata = mock.MagicMock(spec=DataProductMetadata)
        mock_metadata.as_dict.return_value = {"test": "metadata"}
        mock_metadata.dp_metadata_loaded_from_a_file = True
        mock_dpm.return_value = mock_metadata
        yield mock_dpm


def test_registration_processor_init(mock_config):  # pylint: disable=redefined-outer-name
    """Test the RegistrationProcessor initialization."""
    processor = RegistrationProcessor(mock_config)
    assert processor.get_config() == mock_config


def test_registration_processor_set_config(mock_config):  # pylint: disable=redefined-outer-name
    """Test the RegistrationProcessor set_config method."""
    processor = RegistrationProcessor(mock.MagicMock(spec=WatcherConfig))
    processor.set_config(mock_config)
    assert processor.get_config() == mock_config


def test_registration_processor_follow_sym_link():
    """Test the RegistrationProcessor _follow_sym_link method."""
    processor = RegistrationProcessor(mock.MagicMock(spec=WatcherConfig))

    # Test with a non-symlink path
    path = mock.MagicMock()
    path.is_symlink.return_value = False
    result = processor._follow_sym_link(path)  # pylint: disable=protected-access
    assert result == path
    path.resolve.assert_not_called()

    # Test with a symlink path
    path = mock.MagicMock()
    path.is_symlink.return_value = True
    result = processor._follow_sym_link(path)  # pylint: disable=protected-access
    assert result == path
    path.resolve.assert_called_once()


def test_registration_processor_copy_data_item_to_new_storage(
    mock_config, mock_migration_api
):  # pylint: disable=protected-access, redefined-outer-name
    """Test the RegistrationProcessor _copy_data_item_to_new_storage method."""
    processor = RegistrationProcessor(mock_config)

    # Test with migration enabled
    result = processor._initiate_migration("test-uuid")
    assert result == "test-migration-uuid"
    mock_migration_api.return_value.copy_data_item.assert_called_once_with(
        uid="test-uuid", destination_name=mock_config.migration_destination_storage_name
    )

    # Test with migration disabled
    mock_config.perform_actual_ingest_and_migration = False
    result = processor._initiate_migration("test-uuid")
    assert result is None

    # Test with missing destination storage name
    mock_config.perform_actual_ingest_and_migration = True
    mock_config.migration_destination_storage_name = None
    result = processor._initiate_migration("test-uuid")
    assert result is None

    # Test with API exception
    mock_config.migration_destination_storage_name = "test-destination-storage"
    mock_migration_api.return_value.copy_data_item.side_effect = OpenApiException("Test error")
    result = processor._initiate_migration("test-uuid")
    assert result is None


def test_registration_processor_register_single_item(
    mock_config, mock_ingest_api, mock_migration_api, mock_data_product_metadata
):  # pylint: disable=protected-access, redefined-outer-name, unused-argument
    """Test the RegistrationProcessor _register_single_item method."""
    processor = RegistrationProcessor(mock_config)

    # Create a test item
    item = Item(
        path_rel_to_watch_dir="test-item",
        item_type=ItemType.FILE,
        metadata=mock_data_product_metadata.return_value,
    )

    # Test with registration enabled
    result = processor._register_single_item(item)
    assert result == "test-uuid"
    mock_ingest_api.return_value.register_data_item.assert_called_once_with(
        item_name="test-item",
        uri="test-item",
        item_type=ItemType.FILE,
        storage_name=mock_config.storage_name,
        do_storage_access_check=mock_config.rclone_access_check_on_register,
        request_body=item.metadata.as_dict(),
    )

    # Test with registration disabled
    mock_config.perform_actual_ingest_and_migration = False
    result = processor._register_single_item(item)
    # When perform_actual_ingest_and_migration is False, response is None
    assert result is None

    # Test with API exception
    mock_config.perform_actual_ingest_and_migration = True
    mock_ingest_api.return_value.register_data_item.side_effect = OpenApiException("Test error")
    result = processor._register_single_item(item)
    assert result is None


def test_registration_processor_register_container_items(
    mock_config, mock_ingest_api, mock_migration_api, mock_data_product_metadata
):  # pylint: disable=protected-access, redefined-outer-name, unused-argument
    """Test the RegistrationProcessor _register_container_items method."""
    processor = RegistrationProcessor(mock_config)

    # Create a parent item
    parent_item = Item(
        path_rel_to_watch_dir="parent-item",
        item_type=ItemType.CONTAINER,
        metadata=mock_data_product_metadata.return_value,
    )
    parent_item.uuid = "parent-uuid"

    # Create child items
    child_item1 = Item(
        path_rel_to_watch_dir="child-item1",
        item_type=ItemType.FILE,
        metadata=None,
        parent=parent_item,
    )

    child_item2 = Item(
        path_rel_to_watch_dir="child-item2",
        item_type=ItemType.FILE,
        metadata=None,
        parent=parent_item,
    )

    # Test with registration enabled
    processor._register_container_items([child_item1, child_item2])
    assert mock_ingest_api.return_value.register_data_item.call_count == 2
    mock_ingest_api.return_value.register_data_item.assert_any_call(
        item_name="child-item1",
        uri="child-item1",
        item_type=ItemType.FILE,
        storage_name=mock_config.storage_name,
        do_storage_access_check=mock_config.rclone_access_check_on_register,
        parents=parent_item.uuid,
        request_body=None,
    )
    mock_ingest_api.return_value.register_data_item.assert_any_call(
        item_name="child-item2",
        uri="child-item2",
        item_type=ItemType.FILE,
        storage_name=mock_config.storage_name,
        do_storage_access_check=mock_config.rclone_access_check_on_register,
        parents=parent_item.uuid,
        request_body=None,
    )

    # Test with registration disabled
    mock_ingest_api.reset_mock()
    mock_config.perform_actual_ingest_and_migration = False
    processor._register_container_items([child_item1, child_item2])
    mock_ingest_api.return_value.register_data_item.assert_not_called()

    # Test with API exception
    mock_ingest_api.reset_mock()
    mock_config.perform_actual_ingest_and_migration = True
    mock_ingest_api.return_value.register_data_item.side_effect = OpenApiException("Test error")
    processor._register_container_items([child_item1, child_item2])
    mock_ingest_api.return_value.register_data_item.assert_called_once()


@mock.patch("ska_dlm_client.registration_processor._generate_paths_and_metadata")
def test_registration_processor_add_path(
    mock_generate, mock_config, mock_data_product_metadata
):  # pylint: disable=protected-access, redefined-outer-name
    """Test the RegistrationProcessor add_path method."""
    processor = RegistrationProcessor(mock_config)

    # Mock the _register_single_item and _register_container_items methods
    processor._register_single_item = mock.MagicMock(return_value="test-uuid")
    processor._register_container_items = mock.MagicMock()

    # Test with a single file item
    file_item = Item(
        path_rel_to_watch_dir="file-item",
        item_type=ItemType.FILE,
        metadata=mock_data_product_metadata.return_value,
    )
    mock_generate.return_value = [file_item]

    processor.add_path("/test/abs/path", "rel/path")
    mock_generate.assert_called_once_with(
        absolute_path="/test/abs/path", path_rel_to_watch_dir="rel/path"
    )
    processor._register_single_item.assert_called_once_with(file_item)
    processor._register_container_items.assert_not_called()

    # Test with a single container item
    mock_generate.reset_mock()
    processor._register_single_item.reset_mock()
    container_item = Item(
        path_rel_to_watch_dir="container-item",
        item_type=ItemType.CONTAINER,
        metadata=mock_data_product_metadata.return_value,
    )
    mock_generate.return_value = [container_item]

    processor.add_path("/test/abs/path", "rel/path")
    processor._register_single_item.assert_not_called()

    # Test with multiple items (container + files)
    mock_generate.reset_mock()
    processor._register_single_item.reset_mock()
    processor._register_container_items.reset_mock()

    container_item = Item(
        path_rel_to_watch_dir="container-item",
        item_type=ItemType.CONTAINER,
        metadata=mock_data_product_metadata.return_value,
    )
    file_item1 = Item(
        path_rel_to_watch_dir="file-item1",
        item_type=ItemType.FILE,
        metadata=None,
        parent=container_item,
    )
    file_item2 = Item(
        path_rel_to_watch_dir="file-item2",
        item_type=ItemType.FILE,
        metadata=None,
        parent=container_item,
    )
    mock_generate.return_value = [container_item, file_item1, file_item2]

    # Mock time.sleep to avoid waiting
    with mock.patch("time.sleep"):
        processor.add_path("/test/abs/path", "rel/path")

    processor._register_single_item.assert_called_once_with(container_item)
    processor._register_container_items.assert_called_once_with(item_list=[file_item1, file_item2])

    # Test with no items
    mock_generate.reset_mock()
    processor._register_single_item.reset_mock()
    processor._register_container_items.reset_mock()
    mock_generate.return_value = []

    processor.add_path("/test/abs/path", "rel/path")
    processor._register_single_item.assert_not_called()
    processor._register_container_items.assert_not_called()


@mock.patch("os.listdir")
@mock.patch("os.path.join")
def test_registration_processor_register_data_products_from_watch_directory(
    mock_join, mock_listdir, mock_config
):  # pylint: disable=redefined-outer-name
    """Test the RegistrationProcessor register_data_products_from_watch_directory method."""
    processor = RegistrationProcessor(mock_config)

    # Mock the add_path method
    processor.add_path = mock.MagicMock()

    # Mock os.listdir to return a list of items
    mock_listdir.return_value = ["item1", "item2", "item3"]

    # Mock os.path.join to return the expected paths
    mock_join.side_effect = lambda *args: "/".join(args)

    # Call the method
    processor.register_data_products_from_watch_directory()

    # Check that add_path was called for each item
    assert processor.add_path.call_count == 3
    processor.add_path.assert_any_call(
        absolute_path=f"{mock_config.directory_to_watch}/item1",
        path_rel_to_watch_dir="item1",
    )
    processor.add_path.assert_any_call(
        absolute_path=f"{mock_config.directory_to_watch}/item2",
        path_rel_to_watch_dir="item2",
    )
    processor.add_path.assert_any_call(
        absolute_path=f"{mock_config.directory_to_watch}/item3",
        path_rel_to_watch_dir="item3",
    )

"""Registration processor related tests."""

import os

from ska_dlm_client.directory_watcher.registration_processor import (
    Item,
    ItemType,
    _generate_paths_and_metadata,
)


def returned_items_match(test_path: str, dir_entries: list[Item]):
    """Perform asserts on generated item list."""
    assert dir_entries[0].path_rel_to_watch_dir == test_path
    assert dir_entries[0].item_type == ItemType.CONTAINER
    assert dir_entries[0].metadata is not None
    assert dir_entries[1].path_rel_to_watch_dir == f"{test_path}/weights" or f"{test_path}/data"
    assert dir_entries[1].item_type == ItemType.FILE
    assert dir_entries[1].parent == dir_entries[0]
    assert dir_entries[1].metadata is None
    assert dir_entries[2].path_rel_to_watch_dir == f"{test_path}/weights" or f"{test_path}/data"
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

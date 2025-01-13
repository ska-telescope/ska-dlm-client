"""Registration processor related tests."""

import os

from ska_dlm_client.directory_watcher.registration_processor import paths_and_metadata

SYMBOLIC_LINKED_DIR_ENTRIES = ["data", "weights"]


def test_registration_processor(request):
    """Test the registration_processor module."""
    # Determine path where test files are stored.
    filename = request.module.__file__
    test_dir, _ = os.path.splitext(filename)

    # Setup what would be the directory to watch.
    watch_dir = os.path.join(test_dir, "watch_dir")

    # Test when path to add is a file.
    full_path = os.path.join(watch_dir, "data_item_file_only")
    rel_path = os.path.split(full_path)[1]
    dir_entries, _ = paths_and_metadata(full_path, rel_path)
    assert dir_entries == ["data_item_file_only"]

    # Test when path to add is symlink.
    full_path = os.path.join(watch_dir, "symbolic_link_path")
    rel_path = os.path.split(full_path)[1]
    dir_entries, _ = paths_and_metadata(full_path, rel_path)
    assert set(dir_entries) == set(SYMBOLIC_LINKED_DIR_ENTRIES)

    # Test when path to add directory.
    full_path = os.path.join(watch_dir, "directory_entry")
    rel_path = os.path.split(full_path)[1]
    dir_entries, _ = paths_and_metadata(full_path, rel_path)
    assert set(dir_entries) == set(SYMBOLIC_LINKED_DIR_ENTRIES)

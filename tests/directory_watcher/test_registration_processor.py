"""Registration processor related tests."""

import os

from ska_dlm_client.directory_watcher.registration_processor import generate_paths_and_metadata

DIR_ENTRIES = ["data", "weights"]


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
    dir_entries, _ = generate_paths_and_metadata(absolute_path, rel_path)
    assert dir_entries == ["data_item_file_only"]

    # Test when path to add is symlink.
    test_path = "symbolic_link_path"
    absolute_path = os.path.join(watch_dir, test_path)
    rel_path = os.path.split(absolute_path)[1]
    dir_entries, _ = generate_paths_and_metadata(absolute_path, rel_path)
    expected_relative_path_entries: list[str] = []
    for dir_entry in DIR_ENTRIES:
        expected_relative_path_entries.append(os.path.join(test_path, dir_entry))
    assert sorted(dir_entries) == sorted(expected_relative_path_entries)

    # Test when path to add directory.
    test_path = "directory_entry"
    absolute_path = os.path.join(watch_dir, test_path)
    rel_path = os.path.split(absolute_path)[1]
    dir_entries, _ = generate_paths_and_metadata(absolute_path, rel_path)
    expected_relative_path_entries.clear()
    for dir_entry in DIR_ENTRIES:
        expected_relative_path_entries.append(os.path.join(test_path, dir_entry))
    assert sorted(dir_entries) == sorted(expected_relative_path_entries)

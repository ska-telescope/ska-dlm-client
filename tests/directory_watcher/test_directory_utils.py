"""Tests for the directory_utils module."""

import os
import time
import tempfile
import shutil
import threading
import pytest
from pathlib import Path
from watchdog.utils.dirsnapshot import DirectorySnapshot

from ska_dlm_client.directory_watcher.directory_utils import (
    monitor_directory_with_watchdog,
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    dir_path = tempfile.mkdtemp()
    yield dir_path
    shutil.rmtree(dir_path)


def test_monitor_directory_with_watchdog(temp_dir):
    """Test monitoring a directory with watchdog until it's stable."""
    # Create initial file
    with open(os.path.join(temp_dir, "file.txt"), "w") as f:
        f.write("initial content")

    # Create an event to signal when the thread has completed its work
    thread_done = threading.Event()

    # Start a background thread to modify the directory after a delay
    def modify_directory():
        # Wait a bit before making changes
        time.sleep(0.2)

        # Make some changes
        with open(os.path.join(temp_dir, "file.txt"), "w") as f:
            f.write("modified content")

        # Wait again
        time.sleep(0.2)

        # Make more changes
        with open(os.path.join(temp_dir, "new_file.txt"), "w") as f:
            f.write("new file content")

        # Signal that the thread has completed its work
        thread_done.set()

    thread = threading.Thread(target=modify_directory)
    thread.daemon = True
    thread.start()

    # Wait for the thread to complete its work
    thread_done.wait(timeout=5)

    # Give the filesystem a moment to register the changes
    time.sleep(0.5)

    # Monitor the directory with a short wait time
    final_snapshot = monitor_directory_with_watchdog(
        temp_dir, wait_time=0.5, recursive=True
    )

    # Check that the final snapshot is a DirectorySnapshot object
    assert isinstance(final_snapshot, DirectorySnapshot)

    # Check that the final snapshot contains all expected files
    # Convert paths to strings for easier comparison
    paths = [str(p) for p in final_snapshot.paths]

    # Check that our files are in the snapshot
    file1_path = os.path.join(temp_dir, "file.txt")
    file2_path = os.path.join(temp_dir, "new_file.txt")

    assert file1_path in paths
    assert file2_path in paths

    # Check file sizes
    assert final_snapshot.size(file1_path) == len("modified content")
    assert final_snapshot.size(file2_path) == len("new file content")

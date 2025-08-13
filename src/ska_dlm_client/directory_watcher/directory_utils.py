"""Utilities for monitoring directories and detecting changes."""

import logging
import time
from datetime import datetime

from watchdog.events import FileSystemEventHandler
from watchdog.observers.polling import PollingObserver
from watchdog.utils.dirsnapshot import DirectorySnapshot, DirectorySnapshotDiff

logger = logging.getLogger(__name__)


def monitor_directory_with_watchdog(
    directory: str, wait_time: float = 5.0, recursive: bool = True
) -> DirectorySnapshot:
    """
    Monitor a directory using watchdog.observers.polling until no changes are detected.

    This implementation uses watchdog's DirectorySnapshot and DirectorySnapshotDiff
    to efficiently detect changes.

    Args:
        directory: The directory to monitor
        wait_time: The time to wait between scans (in seconds)
        recursive: Whether to scan subdirectories recursively

    Returns:
        The final directory snapshot
    """
    logger.info("Starting to monitor directory with watchdog: %s", directory)

    # Get initial snapshot using DirectorySnapshot
    current_dir_snapshot = DirectorySnapshot(path=directory, recursive=recursive)
    logger.info("Initial snapshot contains %d entries", len(current_dir_snapshot.paths))

    class ChangeDetector(FileSystemEventHandler):
        """
        A file system event handler that detects any changes in the monitored directory.

        This class extends watchdog's FileSystemEventHandler and sets a flag when any
        file system event (creation, deletion, modification, or movement) is detected.
        The flag is used by the monitoring loop to determine if the directory is stable.

        Attributes:
            changes_detected: A boolean flag indicating whether any changes have been
                             detected in the monitored directory.
        """

        def __init__(self):
            self.changes_detected = False

        def on_any_event(self, event):
            self.changes_detected = True

    # Monitor until stable
    iteration = 0
    while True:
        iteration += 1
        logger.info("Iteration %d: Waiting %s seconds for changes", iteration, wait_time)

        # Set up the observer with our change detector
        change_detector = ChangeDetector()
        observer = PollingObserver(timeout=wait_time)
        observer.schedule(change_detector, directory, recursive=recursive)
        observer.start()

        # Wait for the specified time
        time.sleep(wait_time)

        # Stop the observer
        observer.stop()
        observer.join()

        # Get a new snapshot
        new_dir_snapshot = DirectorySnapshot(path=directory, recursive=recursive)

        # If no changes were detected by watchdog, double-check with DirectorySnapshotDiff
        if not change_detector.changes_detected:
            # Use DirectorySnapshotDiff to compare snapshots
            diff = DirectorySnapshotDiff(current_dir_snapshot, new_dir_snapshot)

            # Check if there are any changes by verifying all change collections are empty
            change_attributes = [
                diff.files_created,
                diff.files_deleted,
                diff.files_modified,
                diff.files_moved,
                diff.dirs_created,
                diff.dirs_deleted,
                diff.dirs_modified,
                diff.dirs_moved,
            ]
            if all(not changes for changes in change_attributes):

                logger.info(
                    "No changes detected after %d iterations. Directory is stable.", iteration
                )
                return new_dir_snapshot

        # Log changes if any were detected
        log_changes_with_diff(current_dir_snapshot, new_dir_snapshot)

        # Update the current snapshot
        current_dir_snapshot = new_dir_snapshot

    # This point should never be reached
    return current_dir_snapshot


def log_changes_with_diff(  # noqa: C901
    old_snapshot: DirectorySnapshot, new_snapshot: DirectorySnapshot
) -> None:
    """
    Log the changes between two directory snapshots using DirectorySnapshotDiff.

    This function compares two directory snapshots and logs detailed information about
    all detected changes, including:
    - Created files (with size and modification time)
    - Created directories (with modification time)
    - Modified files (with old/new size and modification time)
    - Modified directories (with old/new modification time)
    - Deleted files
    - Deleted directories
    - Moved files
    - Moved directories

    The function uses DirectorySnapshotDiff to efficiently detect changes between
    the snapshots and handles exceptions that might occur when trying to access
    file information (such as FileNotFoundError or PermissionError).

    The function contains several helper functions that are only used within this method:
    - log_file_created: Logs details about newly created files
    - log_dir_created: Logs details about newly created directories
    - log_files_modified: Logs details about modified files with size and time changes
    - log_dirs_modified: Logs details about modified directories with time changes
    - log_list_with_messages: Generic function for logging deleted and moved items

    Args:
        old_snapshot: The previous directory snapshot containing information about
                     files and directories at an earlier point in time
        new_snapshot: The current directory snapshot containing information about
                     files and directories at the current point in time
    """
    # Helper functions

    # Helper function to log details about newly created files
    def log_file_created():
        logger.info("Found %d new files:", len(diff.files_created))
        for path in diff.files_created:
            try:
                size = new_snapshot.size(path)
                mtime = new_snapshot.mtime(path)
                logger.info(
                    "  New file: %s (size: %s, mtime: %s)",
                    path,
                    size,
                    datetime.fromtimestamp(mtime),
                )
            except (FileNotFoundError, PermissionError) as e:
                logger.warning("Error accessing %s: %s", path, e)

    # Helper function to log details about newly created directories
    def log_dir_created():
        logger.info("Found %d new directories:", len(diff.dirs_created))
        for path in diff.dirs_created:
            try:
                mtime = new_snapshot.mtime(path)
                logger.info("  New directory: %s (mtime: %s)", path, datetime.fromtimestamp(mtime))
            except (FileNotFoundError, PermissionError) as e:
                logger.warning("Error accessing %s: %s", path, e)

    # Helper function to log details about modified files
    def log_files_modified():
        logger.info("Found %d modified files:", len(diff.files_modified))
        for path in diff.files_modified:
            try:
                old_size = old_snapshot.size(path)
                new_size = new_snapshot.size(path)
                old_mtime = old_snapshot.mtime(path)
                new_mtime = new_snapshot.mtime(path)
                logger.info(
                    "  Modified file: %s (size: %s -> %s, mtime: %s -> %s)",
                    path,
                    old_size,
                    new_size,
                    datetime.fromtimestamp(old_mtime),
                    datetime.fromtimestamp(new_mtime),
                )
            except (FileNotFoundError, PermissionError) as e:
                logger.warning("Error accessing %s: %s", path, e)

    # Helper function to log details about modified directories
    def log_dirs_modified():
        logger.info("Found %d modified directories:", len(diff.dirs_modified))
        for path in diff.dirs_modified:
            try:
                old_mtime = old_snapshot.mtime(path)
                new_mtime = new_snapshot.mtime(path)
                logger.info(
                    "  Modified directory: %s (mtime: %s -> %s)",
                    path,
                    datetime.fromtimestamp(old_mtime),
                    datetime.fromtimestamp(new_mtime),
                )
            except (FileNotFoundError, PermissionError) as e:
                logger.warning("Error accessing %s: %s", path, e)

    # Helper function to log deleted and moved items
    def log_list_with_messages(paths, msg_type):
        logger.info("Found %d %s:", len(paths), msg_type)
        for path in paths:
            logger.info("  %s: %s", msg_type, path)

    diff = DirectorySnapshotDiff(old_snapshot, new_snapshot)

    # Define a mapping of diff attributes to their corresponding logging functions
    change_handlers = [
        (diff.files_created, log_file_created),
        (diff.dirs_created, log_dir_created),
        (diff.files_modified, log_files_modified),
        (diff.dirs_modified, log_dirs_modified),
        (diff.files_deleted, lambda: log_list_with_messages(diff.files_deleted, "Deleted file:")),
        (
            diff.dirs_deleted,
            lambda: log_list_with_messages(diff.dirs_deleted, "Deleted directory:"),
        ),
        (diff.files_moved, lambda: log_list_with_messages(diff.files_moved, "Moved file:")),
        (diff.dirs_moved, lambda: log_list_with_messages(diff.dirs_moved, "Moved directory:")),
    ]

    # Process each type of change
    for changes, handler in change_handlers:
        if changes:
            handler()


if __name__ == "__main__":
    # Configure logging when run as a main application
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    result = monitor_directory_with_watchdog(
        directory="/tmp/test_dir", wait_time=15.0, recursive=True
    )
    print(f"Final snapshot: {result}")

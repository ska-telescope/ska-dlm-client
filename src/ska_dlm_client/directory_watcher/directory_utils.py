"""Utilities for monitoring directories and detecting changes."""

import time
import logging
from datetime import datetime
from watchdog.observers.polling import PollingObserver
from watchdog.utils.dirsnapshot import DirectorySnapshot, DirectorySnapshotDiff
from watchdog.events import FileSystemEventHandler

logger = logging.getLogger(__name__)


def monitor_directory_with_watchdog(
    directory: str,
    wait_time: float = 5.0,
    recursive: bool = True
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
    logger.info(f"Starting to monitor directory with watchdog: {directory}")

    # Get initial snapshot using DirectorySnapshot
    current_dir_snapshot = DirectorySnapshot(path=directory, recursive=recursive)
    logger.info(f"Initial snapshot contains {len(current_dir_snapshot.paths)} entries")

    # Create a simple event handler to detect any changes
    class ChangeDetector(FileSystemEventHandler):
        def __init__(self):
            self.changes_detected = False

        def on_any_event(self, event):
            self.changes_detected = True

    # Monitor until stable
    iteration = 0
    while True:
        iteration += 1
        logger.info(f"Iteration {iteration}: Waiting {wait_time} seconds for changes")

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

            # Check if there are any changes
            if (not diff.files_created and not diff.files_deleted and
                not diff.files_modified and not diff.files_moved and
                not diff.dirs_created and not diff.dirs_deleted and
                not diff.dirs_modified and not diff.dirs_moved):

                logger.info(f"No changes detected after {iteration} iterations. Directory is stable.")
                return new_dir_snapshot

        # Log changes if any were detected
        log_changes_with_diff(current_dir_snapshot, new_dir_snapshot)

        # Update the current snapshot
        current_dir_snapshot = new_dir_snapshot

    # This point should never be reached
    return current_dir_snapshot


def log_changes_with_diff(old_snapshot: DirectorySnapshot, new_snapshot: DirectorySnapshot) -> None:
    """
    Log the changes between two directory snapshots using DirectorySnapshotDiff.

    Args:
        old_snapshot: The previous directory snapshot
        new_snapshot: The current directory snapshot
    """
    diff = DirectorySnapshotDiff(old_snapshot, new_snapshot)

    if diff.files_created:
        logger.info(f"Found {len(diff.files_created)} new files:")
        for path in diff.files_created:
            try:
                size = new_snapshot.size(path)
                mtime = new_snapshot.mtime(path)
                logger.info(f"  New file: {path} (size: {size}, mtime: {datetime.fromtimestamp(mtime)})")
            except (FileNotFoundError, PermissionError) as e:
                logger.warning(f"Error accessing {path}: {e}")

    if diff.dirs_created:
        logger.info(f"Found {len(diff.dirs_created)} new directories:")
        for path in diff.dirs_created:
            try:
                mtime = new_snapshot.mtime(path)
                logger.info(f"  New directory: {path} (mtime: {datetime.fromtimestamp(mtime)})")
            except (FileNotFoundError, PermissionError) as e:
                logger.warning(f"Error accessing {path}: {e}")

    if diff.files_modified:
        logger.info(f"Found {len(diff.files_modified)} modified files:")
        for path in diff.files_modified:
            try:
                old_size = old_snapshot.size(path)
                new_size = new_snapshot.size(path)
                old_mtime = old_snapshot.mtime(path)
                new_mtime = new_snapshot.mtime(path)
                logger.info(
                    f"  Modified file: {path} "
                    f"(size: {old_size} -> {new_size}, "
                    f"mtime: {datetime.fromtimestamp(old_mtime)} -> {datetime.fromtimestamp(new_mtime)})"
                )
            except (FileNotFoundError, PermissionError) as e:
                logger.warning(f"Error accessing {path}: {e}")

    if diff.dirs_modified:
        logger.info(f"Found {len(diff.dirs_modified)} modified directories:")
        for path in diff.dirs_modified:
            try:
                old_mtime = old_snapshot.mtime(path)
                new_mtime = new_snapshot.mtime(path)
                logger.info(
                    f"  Modified directory: {path} "
                    f"(mtime: {datetime.fromtimestamp(old_mtime)} -> {datetime.fromtimestamp(new_mtime)})"
                )
            except (FileNotFoundError, PermissionError) as e:
                logger.warning(f"Error accessing {path}: {e}")

    if diff.files_deleted:
        logger.info(f"Found {len(diff.files_deleted)} deleted files:")
        for path in diff.files_deleted:
            logger.info(f"  Deleted file: {path}")

    if diff.dirs_deleted:
        logger.info(f"Found {len(diff.dirs_deleted)} deleted directories:")
        for path in diff.dirs_deleted:
            logger.info(f"  Deleted directory: {path}")

    if diff.files_moved:
        logger.info(f"Found {len(diff.files_moved)} moved files:")
        for old_path, new_path in diff.files_moved:
            logger.info(f"  Moved file: {old_path} -> {new_path}")

    if diff.dirs_moved:
        logger.info(f"Found {len(diff.dirs_moved)} moved directories:")
        for old_path, new_path in diff.dirs_moved:
            logger.info(f"  Moved directory: {old_path} -> {new_path}")


if __name__ == "__main__":
    # Configure logging when run as a main application
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    result = monitor_directory_with_watchdog(directory='/tmp/test_dir', wait_time=15.0, recursive=True)
    print(f"Final snapshot: {result}")

"""Directory watcher integration test setup.

The purpose here is to generate data in a shared volume to test that it is processed
correctly by the directory watcher.

This program intentianally doesn't use any ska-dlm-client code so it can stand in isolation
for testing.

NOTE: This does not test the results, ie that it has appeared in the database and the data
has been transferred by rclone correctly.
"""

import logging
import os
import os.path
import shutil
import sys
import time

DATA_FILE_SIZE_BYTES = 8 * 1024
METADATA_FILENAME = "ska-data-product.yaml"
PST_FILES = ["data", "weights"]
TEST_DIRS = ["dlm-clinet-test-dir1", "dlm-clinet-test-dir2", "dlm-clinet-test-dir3"]
SYMLINKS = ["dlm-client-sym-one", "dlm-client-sym-two", "dlm-client-sym-three"]

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def create_verify_dir_symlink_names(data_dir: str, symlink_dir: str) -> (list[str], list[str]):
    """Create directory and symlink names from given base directories, exit if any exist."""
    symlinks: list[str] = []
    for symlink in SYMLINKS:
        sym = os.path.join(symlink_dir, symlink)
        if os.path.exists(sym):
            logging.error("symlink wanted for testing already exists %s", sym)
            sys.exit(1)
        symlinks.append(sym)
    test_dirs: list[str] = []
    for test_dir in TEST_DIRS:
        the_dir = os.path.join(data_dir, test_dir)
        if os.path.exists(the_dir):
            logging.error("Directory wanted for testing already exists %s", dir)
            sys.exit(1)
        test_dirs.append(the_dir)
    return test_dirs, symlinks


def popluate_data_items(
    symlink_dir: str, data_dir: str, sleep_time: int, delete_on_completion: bool
):
    """Generate required directory structure and files for integration testing."""
    # Directory and symlinks must not exist at startup, test for this during setup
    # If they do exist then exit before creating anything!
    test_dirs, symlinks = create_verify_dir_symlink_names(data_dir, symlink_dir)

    for test_dir in test_dirs:
        os.mkdir(test_dir)
        for pst_file in PST_FILES:
            data_file = os.path.join(test_dir, pst_file)
            with open(data_file, "wb") as output_file:
                output_file.write(os.urandom(DATA_FILE_SIZE_BYTES))

    for n, symlink in enumerate(symlinks):
        src = test_dirs[n]
        os.symlink(src, symlink)
        time.sleep(sleep_time)

    if delete_on_completion:
        # wait another sleep_time before deletion
        time.sleep(sleep_time)
        for test_dir in test_dirs:
            shutil.rmtree(test_dir)
        for symlink in symlinks:
            os.unlink(symlink)

"""Directory watcher integration test setup.

The purpose here is to generate data in a shared volume to test that it is processed
correctly by the directory watcher.

This program intentianally doesn't use any ska-dlm-client code so it can stand in isolation
for testing.

NOTE: This does not test the results, ie that it has appeared in the database and the data
has been transferred by rclone correctly.
"""

import argparse
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


def create_parser() -> argparse.ArgumentParser:
    """Define a parser for all the command line parameters."""
    parser = argparse.ArgumentParser(prog="dlm_directory_watcher")

    parser.add_argument(
        "--directory-to-create-symlinks",
        type=str,
        required=False,
        default="/shared/watch_dir",
        help="Full path to directory where symbolic link is to be created.",
    )
    parser.add_argument(
        "--directory-to-create-data-items",
        type=str,
        required=False,
        default="/shared/testing2",
        help="Full path to directory where data items are to be located.",
    )
    parser.add_argument(
        "--time-between-data-item-creations",
        type=int,
        required=False,
        default=5,
        help="Time in seconds between data item creations.",
    )
    parser.add_argument(
        "--delete-on-completion",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Delete all created directories, files and symlinks at completion.",
    )
    return parser


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


def popluate_data_items(args: argparse.Namespace):
    """Collect up all command line parameters and generate required structure."""
    symlink_dir = args.directory_to_create_symlinks
    data_dir = args.directory_to_create_data_items
    sleep_time = args.time_between_data_item_creations

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

    if args.delete_on_completion:
        # wait another sleep_time before deletion
        time.sleep(sleep_time)
        for test_dir in test_dirs:
            shutil.rmtree(test_dir)
        for symlink in symlinks:
            os.unlink(symlink)


def main():
    """Perform the required steps to read args and generate data items."""
    parser = create_parser()
    args = parser.parse_args()
    popluate_data_items(args)


if __name__ == "__main__":
    main()

"""Directory watcher integration test setup."""

import argparse

from populate_data_for_directory_watcher import popluate_data_items


def create_parser() -> argparse.ArgumentParser:
    """Define a parser for all the command line parameters."""
    parser = argparse.ArgumentParser(prog="dlm-client-integration-verification")

    parser.add_argument(
        "--directory-to-create-symlinks",
        type=str,
        required=False,
        default="/Users/00077990/yanda/shared/watch_dir",
        help="Full path to directory where symbolic link is to be created.",
    )
    parser.add_argument(
        "--directory-to-create-data-items",
        type=str,
        required=False,
        default="/Users/00077990/yanda/shared/testing2",
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


def main():
    """Perform the required steps to read args and generate data products."""
    parser = create_parser()
    args = parser.parse_args()
    # Collect up all command line parameters and generate required structure.
    popluate_data_items(
        symlink_dir=args.directory_to_create_symlinks,
        data_dir=args.directory_to_create_data_items,
        sleep_time=args.time_between_data_item_creations,
        delete_on_completion=args.delete_on_completion,
    )


if __name__ == "__main__":
    main()

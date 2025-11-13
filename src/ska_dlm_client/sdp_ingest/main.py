"""
Main entry-point for Configuration Database watcher.

This module starts the watcher, and calls registration processor when a data-product is found
"""

from __future__ import annotations

import argparse
import asyncio
import logging
from pathlib import Path

from ska_sdp_config import Config

from ska_dlm_client.registration_processor import (
    RegistrationProcessor,
    _directory_contains_metadata_file,
    _item_for_single_file_with_metadata,
    _measurement_set_directory_in,
)
from ska_dlm_client.sdp_ingest.config import DemoConfig
from ska_dlm_client.sdp_ingest.configdb_utils import (
    create_sdp_migration_dependency,
    update_dependency_state,
)
from ska_dlm_client.sdp_ingest.configdb_watcher import watch_dataproduct_status

logger = logging.getLogger("ska_dlm_client.sdp_ingest")

# flake8: noqa
# pylint: disable=protected-access,


async def sdp_to_dlm_ingest_and_migrate(
    *,
    include_existing: bool = False,
    src_path: Path,  # I don't think we need source path – at least not here
    dest_storage: str,
) -> str | None:
    """
    Call the DLM server to register an SDP data-product.

    Watch the SDP Config database for FINISHED data products, and for each FINISHED data-product:
    * Create a DLM dependency with state WORKING
    * Invoke DLM ingest and DLM migration
    * If migration is successful, transition dependency state to FINISHED
    * If any DLM call fails, transition state to FAILED

    Returns
    -------
    Registration UUID on success, else None.
    """
    # config = Config()  # Share one handle between writer & watcher
    config = Config(
        host="tests-etcd-1", port=2379
    )  # For docker: use the compose container name + port
    logger.info(
        "Starting SDP Config watcher (include_existing=%s, src_path=%s, dest_storage=%s)...",
        include_existing,
        src_path,
        dest_storage,
    )

    # instantiate RegistrationProcessor with the demo config:
    rp_config = DemoConfig()
    rp_config.ingest_server_url = "http://dlm_ingest:8001"
    rp_config.migration_server_url = "http://dlm_migration:8004"
    rp_config.ingest_configuration.host = rp_config.ingest_server_url
    rp_config.migration_configuration.host = rp_config.migration_server_url
    # define absolute path here
    processor = RegistrationProcessor(rp_config)

    async with watch_dataproduct_status(
        config, status="FINISHED", include_existing=include_existing
    ) as producer:
        logger.info("Watcher READY and listening for events.")

        async for dataproduct_key, _ in producer:
            # Create DLM dependency with state WORKING
            new_dep = await create_sdp_migration_dependency(config, dataproduct_key)

            # define the path
            absolute_path = (
                "/data/SDPBuffer"  # in reality I'll get the source path from data_dir in the Flow
            )

            # identify the .ms file:
            ms_file_name = _measurement_set_directory_in(absolute_path)
            print("ms_file:", ms_file_name)

            # Check if the .ms has a metadata file:
            if not _directory_contains_metadata_file(absolute_path):
                logger.error("No metadata file found!")  # call minimal metadata generator?
                return

            logger.info("Got the metadata file!")  # temporary debugging
            item = _item_for_single_file_with_metadata(
                absolute_path=absolute_path,
                path_rel_to_watch_dir=ms_file_name,  # just the name of the ms file?
            )

            # Registration (blocking) -> run in thread
            dlm_migrated_uuid = await asyncio.to_thread(processor._register_single_item, item)
            # _register_single_item attempts to inititate a copy to
            # _config.migration_destination_storage_name
            logger.info("dlm_migrated_uuid")
            logger.info(dlm_migrated_uuid)

            if not dlm_migrated_uuid:
                # _register_single_item has its own success/error logs; mark dependency FAILED.
                _set_dependency_state(config, new_dep, "FAILED")
            else:
                _set_dependency_state(config, new_dep, "FINISHED")
                logger.info(
                    "Dependency %s set to FINISHED (migrated_id=%s)",
                    getattr(new_dep, "key", "<unknown>"),
                    dlm_migrated_uuid,
                )


def _set_dependency_state(
    config: Config, dep, status: str
) -> None:  # do not confuse with Flow state
    """Helper to update dependency state using a Config transaction."""
    for txn in config.txn():
        update_dependency_state(txn, dep, status)


def create_parser() -> argparse.ArgumentParser:
    """Define a parser for all the command line parameters."""
    parser = argparse.ArgumentParser(prog="dlm_configdb_watcher")

    parser.add_argument(
        "--include-existing",
        action="store_true",
        help=("If set, first yield existing dataproduct keys with matching status."),
    )
    parser.add_argument(
        "--src-path",
        type=Path,
        required=True,
        help="Filesystem path to the source data product.",
    )
    parser.add_argument(
        "--dest-storage",
        type=str,
        required=True,
        help="Destination storage NAME (e.g. 'longterm-archive').",
    )
    return parser


async def main() -> None:
    """Control the main execution of the program."""
    parser = create_parser()
    args = parser.parse_args()

    await sdp_to_dlm_ingest_and_migrate(
        include_existing=args.include_existing,
        src_path=args.src_path,
        dest_storage=args.dest_storage,
    )


if __name__ == "__main__":
    asyncio.run(main())

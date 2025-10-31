"""Main entry-point for Configuration Database watcher."""

from __future__ import annotations

import argparse
import asyncio
import logging
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ska_sdp_config import Config

from ska_dlm_client.sdp_ingest.configdb_utils import (  # update_dependency_state,
    create_sdp_migration_dependency,
)
from ska_dlm_client.sdp_ingest.configdb_watcher import watch_dataproduct_status
from ska_dlm_client.sdp_ingest.data_product_registration import register_data_product

logger = logging.getLogger("ska_dlm_client.sdp_ingest")


async def sdp_to_dlm_ingest_and_migrate(
    *,
    include_existing: bool = False,
    src_path: Path,
    dest_storage: str,
) -> None:
    """Ingests and migrates SDP dataproduct using DLM."""
    # watch sdp config database for finished data products
    # and for each finished dataproduct:
    # * register a dlm dependency with state WORKING
    # * invoke dlm-ingest and dlm-migration
    # * move dependency state to FINISHED
    #
    # If any DLM call fails, reliably transition state to FAILED
    config = Config()  # Share one handle between writer & watcher
    logger.info(
        "Starting SDP Config watcher (include_existing=%s, src_path=%s, dest_storage=%s)...",
        include_existing,
        src_path,
        dest_storage,
    )

    async with watch_dataproduct_status(
        config, status="FINISHED", include_existing=include_existing
    ) as producer:
        logger.info("Watcher READY and listening for events.")

        async for dataproduct_key, _ in producer:
            # 1) Create DLM dependency with state WORKING
            new_dep = await create_sdp_migration_dependency(config, dataproduct_key)

            # TODO: figure out how to pick up the metadata
            metadata: Mapping[str, Any] | None = (None,)

            # 2) Invoke sync registration without blocking the loop
            reg_id = await asyncio.to_thread(
                register_data_product,
                str(src_path),
                destination_storage=dest_storage,
                metadata=metadata,
                do_storage_access_check=False,
            )

            if not reg_id:
                logger.error("Registration returned no id for %s", src_path)
                # TODO: dependency state -> FAILED (persist)
                # await update_dependency_state(config, new_dep, "FAILED")
                continue

            logger.info("Registered data-product '%s' as id=%s", src_path.name, reg_id)

            # 3) TODO: invoke dlm-migration using reg_id
            migrate_ok = True  # placeholder. e.g., await run_migration(reg_id, dest_storage)

            # 4) TODO: move dependency state to FINISHED/FAILED
            if migrate_ok:
                # dependency state -> FINISHED (persist)
                # await update_dependency_state(config, new_dep, "FINISHED")
                logger.info("Dependency %s set to FINISHED", getattr(new_dep, "key", "<unknown>"))
            else:
                # await update_dependency_state(config, new_dep, "FAILED")
                logger.error(
                    "Migration failed for id=%s (dep=%s)",
                    reg_id,
                    getattr(new_dep, "key", "<unknown>"),
                )


def create_parser() -> argparse.ArgumentParser:
    """Define a parser for all the command line parameters."""
    parser = argparse.ArgumentParser(prog="dlm_configdb_watcher")

    parser.add_argument(
        "--include-existing",
        action="store_true",
        help=("If set, first yield existing dataproduct keys with matching " "status."),
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

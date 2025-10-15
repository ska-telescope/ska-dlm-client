"""Main entry-point for Configuration Database watcher."""

import argparse, logging
import asyncio

from ska_sdp_config import Config

from ska_dlm_client.configdb_watcher import (
    create_sdp_migration_dependency,
    watch_dataproduct_status,
)

logger = logging.getLogger("ska_dlm_client.sdp_ingest")


async def sdp_to_dlm_ingest_and_migrate(*, include_existing: bool) -> None:
    """Ingests and migrates SDP dataproduct using DLM."""
    # watch sdp config database for finished data products
    # and for each finished dataproduct:
    # * register a dlm dependency with state WORKING
    # * invoke dlm-ingest and dlm-migration
    # * move dependency state to FINISHED
    #
    # If any DLM call fails, reliably transition state to FAILED
    config = Config()  # Share one handle between writer & watcher
    logger.info("Starting watcher (include_existing=%s)...", include_existing)

    async with watch_dataproduct_status(
        config, status="FINISHED", include_existing=include_existing
    ) as producer:
        logger.info("Watcher READY and listening for events.")
        async for dataproduct_key, _ in producer:
            # register a dlm dependency with state WORKING
            new_dep = await create_sdp_migration_dependency(config, dataproduct_key)
            # TODO: invoke dlm-ingest and dlm-migration
            # TODO: move dependency state to FINISHED/FAILED
    if new_dep:
        print("New dependency: ", new_dep)


def main():
    """Control the main execution of the program."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--include-existing",
        action="store_true",
        help="If set, first yield existing dataproduct keys with matching status.",
    )
    args = parser.parse_args()
    asyncio.run(sdp_to_dlm_ingest_and_migrate(include_existing=args.include_existing))


if __name__ == "__main__":
    main()

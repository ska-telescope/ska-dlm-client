"""Main entry-point for Configuration Database watcher."""

import argparse
import asyncio
import logging

from ska_sdp_config import Config
from ska_sdp_config.entity.flow import Flow

from ska_dlm_client.directory_watcher.registration_processor import _measurement_set_directory_in
from ska_dlm_client.sdp_ingest.configdb_utils import (
    create_sdp_migration_dependency,
    get_data_product_dir,
)
from ska_dlm_client.sdp_ingest.configdb_watcher import watch_dataproduct_status

logger = logging.getLogger("ska_dlm_client.sdp_ingest")


async def _process_completed_flow(config: Config, dataproduct_key: Flow.Key) -> None:
    """Process a single COMPLETED data-product Flow.

    - Resolve the data-product directory from Flow.sink.data_dir.
    - Identify the .ms file in that directory.
    - Create a DLM migration dependency (no state yet).
    """
    # Resolve the source directory from the Flow sink
    src_dir = get_data_product_dir(config, dataproduct_key)
    logger.info(
        "New COMPLETED data-product identified: key=%s, src_path=%s",
        dataproduct_key,
        src_dir,
    )

    # Identify the .ms file (may raise if path does not exist / no .ms)
    ms_file_name = _measurement_set_directory_in(src_dir)
    logger.info("ms_file: %s", ms_file_name)

    # Register a DLM dependency (no state)
    new_dep = await create_sdp_migration_dependency(config, dataproduct_key)
    if new_dep:
        logger.info("New dependency: %s", new_dep)

    # TODO: invoke dlm-ingest and dlm-migration
    # TODO: move dependency state to WORKING/FINISHED/FAILED


async def sdp_to_dlm_ingest_and_migrate(*, include_existing: bool) -> None:
    """Ingests and migrates SDP dataproduct using DLM."""
    # watch sdp config database for 'COMPLETED' Flow states
    # and for each 'COMPLETED' data-product:
    # * create a dlm dependency (no state)
    # * invoke dlm-ingest and dlm-migration (TODO)
    # * update dependency state to WORKING
    # * depending on outcome, move dependency state to FINISHED/FAILED (TODO)
    config = Config()  # Share one handle between writer & watcher
    logger.info("Starting SDP Config watcher (include_existing=%s)...", include_existing)

    async with watch_dataproduct_status(
        config, status="COMPLETED", include_existing=include_existing
    ) as producer:  # make the desired status configurable?
        logger.info("Watcher READY and looking for events.")

        async for dataproduct_key, _ in producer:
            try:
                await _process_completed_flow(config, dataproduct_key)
            except Exception:  # pylint: disable=broad-exception-caught  # pragma: no cover
                # Log traceback but keep watching
                logger.exception("Failed to process Flow %s", dataproduct_key)
                logger.info("Continuing to look for new Flows")


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

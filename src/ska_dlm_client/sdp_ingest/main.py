"""Main entry-point for Configuration Database watcher."""

import asyncio

from ska_sdp_config import Config

from ska_dlm_client.configdb_watcher import (
    create_sdp_migration_dependency,
    watch_dataproduct_status,
)


async def sdp_to_dlm_ingest_and_migrate():
    """Ingests and migrates SDP dataproduct to DLM."""
    # watch sdp config database for finished data products
    # and for each finished dataproduct:
    # * register a dlm dependency with state WORKING
    # * invoke dlm-ingest and dlm-migration
    # * move dependency state to FINISHED
    #
    # If any DLM call fails, reliably transition state to FAILED
    config = Config()
    async with watch_dataproduct_status(
        Config(), status="FINISHED", include_existing=True
    ) as producer:
        async for dataproduct_key, _ in producer:
            # register a dlm dependency with state WORKING
            new_dep = await create_sdp_migration_dependency(config, dataproduct_key)
            # invoke dlm-ingest and dlm-migration
            # move dependency state to FINISHED
    if new_dep:
        print("New dependency: ", new_dep)


def main():
    """Control the main execution of the program."""
    asyncio.run(sdp_to_dlm_ingest_and_migrate())


if __name__ == "__main__":
    main()

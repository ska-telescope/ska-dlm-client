"""Main entry-point for Configuration Database watcher."""

import argparse
import asyncio
import logging
import os
from pathlib import Path

import athreading
import ska_ser_logging
from ska_sdp_config import Config
from ska_sdp_config.entity.flow import Dependency, Flow

from ska_dlm_client.config import DIRECTORY_IS_MEASUREMENT_SET_SUFFIX
from ska_dlm_client.configdb_watcher.configdb_utils import (
    create_sdp_migration_dependency,
    get_pvc_subpath,
    update_dependency_state,
)
from ska_dlm_client.configdb_watcher.configdb_watcher import watch_dataproduct_status
from ska_dlm_client.openapi.configuration import Configuration
from ska_dlm_client.register_storage_location.main import RCLONE_CONFIG_SOURCE, setup_volume
from ska_dlm_client.registration_processor import (
    RegistrationProcessor,
    directory_contains_metadata_file,
)
from ska_dlm_client.configdb_watcher.config import WatcherArgs, SdpWatcherConfig

logger = logging.getLogger("ska_dlm_client.configdb_watcher")
# TODO: add a proper option for LOG_LEVEL=DEBUG


def process_args(args: argparse.Namespace) -> SdpWatcherConfig:
    """Collect all command line parameters and create an SdpWatcherConfig object."""
    ingest_configuration = Configuration(host=args.ingest_url)

    # Only configure migration if the user supplied a migration server URL
    if args.migration_url is not None:
        migration_configuration = Configuration(host=args.migration_url)
    else:
        migration_configuration = None
        logger.warning("No migration server specified. Unable to perform migrations.")

    if args.source_name:
        RCLONE_CONFIG_SOURCE["name"] = args.source_name

    return SdpWatcherConfig(
        ingest_url=args.ingest_url,
        storage_url=args.storage_url,
        target_name=args.target_name,
    )


def _register_and_migrate_path(
    processor: RegistrationProcessor,
    src_dir: str,
    root_dir: str,
    dataproduct_key: Flow.Key,
    new_dep: str,
) -> str | None:
    """Register and migrate a whole path.

    Args:
        processor: The RegistrationProcessor instance to use.
        src_dir: The source directory to register and migrate.
        root_dir: The root directory of the source storage.
        dataproduct_key: The Flow.Key of the data product being processed.
        new_dep: The dependency created for this data product.

    Returns:
        The dependency status.
    """
    dlm_source_uuid = processor.add_path(
        absolute_path=src_dir,
        path_rel_to_watch_dir=os.path.relpath(src_dir, start=root_dir),
    )
    logger.debug("dlm_source_uuid: %s", dlm_source_uuid)

    if dlm_source_uuid is None:  # Registration failed
        logger.warning(
            "DLM registration failed for %s; marking dependency %s as FAILED.",
            dataproduct_key,
            new_dep,
        )
        dep_status = "FAILED"
    else:
        migration_result = processor.last_migration_result  # TODO: DMAN-213
        logger.debug("migration_result: %s", migration_result)

        if migration_result is None:
            logger.warning(
                "Migration failed or was skipped for %s; marking dependency %s as FAILED.",
                dataproduct_key,
                new_dep,
            )
            dep_status = "FAILED"
        else:
            logger.debug(
                "Registration and migration succeeded for %s; "
                "marking dependency %s as FINISHED.",
                dataproduct_key,
                new_dep,
            )
            dep_status = "FINISHED"
    return dep_status


async def _process_completed_flow(  # noqa: C901
    # pylint: disable=too-many-locals
    configdb: Config,
    dataproduct_key: Flow.Key,
    config: SdpWatcherConfig,
) -> None:
    """Process a single COMPLETED data product.

    - Resolve the directory from DataProduct Flow.sink.data_dir.
    - Identify the .ms file(s) in that directory (or one level deeper).
    - Create a DLM migration Dependency.
    - Register data product(s) in DLM.
    - Migrate the data product(s) to the configured destination storage.
    - Set Dependency state to WORKING/FINISHED/FAILED depending on outcome.

    Args:
        configdb: Shared SDP ConfigDB client.
        dataproduct_key: Flow.Key from the related DataProduct Flow.
        ingest_config: Runtime ingest and migration configuration.

    Notes:
        This implementation processes each derived work directory sequentially.
        If later we want faster throughput, could add bounded concurrency (e.g. 2–4 in-flight).
    """
    new_dep: Dependency | None = None

    @athreading.call
    def _aupdate_dependency_state(status: str) -> None:
        """Async wrapper for updating Dependency state."""
        for txn in configdb.txn():
            update_dependency_state(txn, new_dep, status=status)
            state = txn.dependency.state(new_dep).get()
            logger.info("Dependency status set to %s.", state.get("status"))

    # Resolve the source directory from the Flow sink
    source_root = SdpWatcherConfig.directory_to_watch
    source_subpath = get_pvc_subpath(configdb, dataproduct_key)
    source_path_full = Path(source_root / source_subpath)

    logger.info(
        "New COMPLETED data-product identified via data-product-persist: DataProduct uri=%s, "
        "source_root=%s, source_subpath=%s, source_path_full=%s",
        dataproduct_key,
        source_root,
        source_subpath,
        source_path_full,
    )

    if not source_path_full.exists() or not source_path_full.is_dir():
        logger.error(
            "Data product source directory does not exist or is not a directory: %s",
            source_path_full,
        )
        return

    processor = RegistrationProcessor(config)
    processor.last_migration_result = None  # Clear any stale migration result

    # ---- Find MS directories (directly or one level deeper) ----
    def iter_ms_dirs_one_level(path: Path):
        for entry in os.listdir(path):
            full_entry = path / entry
            logger.info("Checking: %s", full_entry)
            if full_entry.is_dir() and full_entry.name.lower().endswith(
                DIRECTORY_IS_MEASUREMENT_SET_SUFFIX
            ):
                yield full_entry

    ms_dirs = list(iter_ms_dirs_one_level(source_path_full))

    if not ms_dirs:
        logger.info("No MS found in %s — searching one level deeper.", source_path_full)
        for subdir in os.listdir(source_path_full):
            subdir_full = source_path_full / subdir
            if subdir_full.is_dir():
                ms_dirs.extend(list(iter_ms_dirs_one_level(subdir_full)))

    if not ms_dirs:
        logger.error("No Measurement Set(s) found.")
        return

    logger.info("Found %s Measurement Set(s)", len(ms_dirs))

    # Derive parent work directories from MS paths.
    # Deduplicate to avoid processing the same directory multiple times.
    work_dirs = sorted({ms_dir.parent for ms_dir in ms_dirs})
    logger.info("Found %s work dir(s) to process: %s", len(work_dirs), work_dirs)

    # ---- Create a DLM dependency + set state to WORKING once ----
    new_dep = await create_sdp_migration_dependency(configdb, dataproduct_key)
    if not new_dep:
        logger.error("Failed to create dependency for data product %s", dataproduct_key)
        return
    logger.debug("New dependency created: %s", new_dep)

    await _aupdate_dependency_state("WORKING")

    # ---- Process each work directory ----
    any_failed = False
    for work_dir in work_dirs:  # Could add parallelism in the future
        if not directory_contains_metadata_file(work_dir):
            logger.warning("No metadata file found in %s — proceeding anyway.", work_dir)
        else:
            logger.info("Found the metadata file in %s!", work_dir)

        dep_status = _register_and_migrate_path(
            processor,
            str(work_dir),
            dataproduct_key,
            new_dep,
        )
        if dep_status == "FAILED":
            any_failed = True

    # ---- Set final dependency state once all MS in the Flow have been attempted ----
    final_status = "FAILED" if any_failed else "FINISHED"
    await _aupdate_dependency_state(final_status)


async def sdp_to_dlm_ingest_and_migrate(
    config: SdpWatcherConfig
) -> None:
    """Ingest and migrate SDP data-products using DLM."""
    configdb = Config()  # Share one handle between writer & watcher
    _ = setup_volume(
        watcher_config=config,
        api_configuration=config.ingest_configuration,
        rclone_config=RCLONE_CONFIG_SOURCE,
        storage_url=config.storage_url,
    )
    logger.info(
        "Starting ConfigDB watcher (include_existing=%s, source name=%s, target name=%s)",
        config.include_existing,
        config.source_name,
        config.target_name,
    )

    async with watch_dataproduct_status(
        configdb,
        status="COMPLETED",
        include_existing=config.include_existing,
    ) as producer:  # make the desired status configurable?
        logger.info("Watcher READY and looking for events.")

        async for dataproduct_key, _ in producer:
            try:
                await _process_completed_flow(
                    configdb,
                    dataproduct_key,
                    config,
                )
                logger.info("Done processing %s", dataproduct_key)
            except Exception:  # pylint: disable=broad-exception-caught  # pragma: no cover
                logger.exception("Failed to process Flow %s", dataproduct_key)
            finally:
                logger.info(
                    "Continuing to watch for data products referenced by "
                    "data-product-persist Flows."
                )


def main() -> None:
    """Control the main execution of the program."""
    ska_ser_logging.configure_logging(logging.INFO)

    cmd_line_parameters = WatcherArgs()
    args = cmd_line_parameters.parser.parse_args()
    cmd_line_parameters.parse_arguments(args)
    config = process_args(args)

    asyncio.run(sdp_to_dlm_ingest_and_migrate(config))


if __name__ == "__main__":
    main()

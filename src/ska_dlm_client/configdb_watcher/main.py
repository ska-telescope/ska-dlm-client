"""Main entry-point for Configuration Database watcher."""

import argparse
import asyncio
import logging
import os
from dataclasses import dataclass
from pathlib import Path

import athreading
from ska_sdp_config import Config
from ska_sdp_config.entity.flow import Flow

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

logger = logging.getLogger("ska_dlm_client.configdb_watcher")


# pylint: disable=too-many-instance-attributes
@dataclass
class SDPIngestConfig:
    """Runtime configuration for the SDP→DLM ConfigDB Watcher."""

    include_existing: bool
    ingest_url: str
    ingest_configuration: Configuration
    storage_url: str
    storage_name: str
    storage_root_directory: str
    migration_destination_storage_name: str | None = None
    migration_configuration: Configuration | None = None


def process_args(args: argparse.Namespace) -> SDPIngestConfig:
    """Collect all command line parameters and create an SDPIngestConfig object."""
    ingest_configuration = Configuration(host=args.ingest_url)

    # Only configure migration if the user supplied a migration server URL
    if args.migration_url is not None:
        migration_configuration = Configuration(host=args.migration_url)
    else:
        migration_configuration = None
        logger.warning("No migration server specified. Unable to perform migrations.")

    if args.source_name:
        RCLONE_CONFIG_SOURCE["name"] = args.source_name

    return SDPIngestConfig(
        include_existing=args.include_existing,
        ingest_url=args.ingest_url,
        ingest_configuration=ingest_configuration,
        storage_url=args.storage_url,
        storage_name=args.source_name,
        storage_root_directory=args.source_root,
        migration_destination_storage_name=args.target_name,
        migration_configuration=migration_configuration,
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
        rooot_dir: The root directory of the source storage.
        dataproduct_key: The Flow.Key of the data-product being processed.
        new_dep: The dependency created for this data-product.

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
            logger.info(
                "Registration and migration succeeded for %s; "
                "marking dependency %s as FINISHED.",
                dataproduct_key,
                new_dep,
            )
            dep_status = "FINISHED"
    return dep_status


async def _process_completed_flow(  # noqa: C901
    configdb: Config,
    dataproduct_key: Flow.Key,
    ingest_config: SDPIngestConfig,
) -> None:
    """Process a single COMPLETED data-product Flow.

    - Resolve the data-product directory from Flow.sink.data_dir.
    - Identify the .ms file in that directory.
    - Create a DLM migration dependency
    - Register data-product in DLM
    - Migrate the data-product (if configured)
    - Set dependency state to WORKING/FINISHED/FAILED depending on outcome.
    """
    new_dep: str | None = None
    dep_status: str | None = None

    @athreading.call
    def _aupdate_dependency_state(status: str) -> None:
        """Async wrapper for updating Dependency state."""
        for txn in configdb.txn():
            update_dependency_state(txn, new_dep, status=status)
            state = txn.dependency.state(new_dep).get()
            logger.info("Dependency %s status set to %s.", new_dep, state.get("status"))

    # Resolve the source directory from the Flow sink
    source_subpath = get_pvc_subpath(configdb, dataproduct_key)
    source_root = Path(ingest_config.storage_root_directory)
    source_path_full = source_root / source_subpath

    logger.info(
        "New COMPLETED data-product identified: key=%s, source_root=%s, source_subpath=%s, "
        "source_path_full=%s",
        dataproduct_key,
        source_root,
        source_subpath,
        source_path_full,
    )

    if not source_path_full.exists() or not source_path_full.is_dir():
        logger.error(
            "Data-product source directory does not exist or is not a directory: %s",
            source_path_full,
        )
        return

    # Are there any MS here?
    ms_sets = 0
    for entry in os.listdir(source_path_full):
        entry = os.path.join(source_path_full, entry)
        logger.info("Checking: %s", entry)
        if os.path.isdir(entry) and entry.lower().endswith(DIRECTORY_IS_MEASUREMENT_SET_SUFFIX):
            ms_sets += 1

    if ms_sets == 0:
        logger.error("No Measurement Set found in directory %s", source_path_full)
        return
    logger.info("Found %s MS directories", ms_sets)

    # Create a DLM dependency (no state yet)
    new_dep = await create_sdp_migration_dependency(configdb, dataproduct_key)
    if not new_dep:
        logger.error(
            "Failed to create dependency for data-product %s ",
            dataproduct_key,
        )
    else:
        logger.info("New dependency created: %s", new_dep)

    # Look for the metadata file
    if not directory_contains_metadata_file(source_path_full):
        logger.error("No metadata file found!")
    else:
        logger.info("Found the metadata file!")

    # If we have a dependency, mark it WORKING before we start register+migrate
    if new_dep:
        await _aupdate_dependency_state("WORKING")
        logger.info("Setting Dependency %s state as WORKING", new_dep)

    # Handle each of the found MSs
    processor = RegistrationProcessor(ingest_config)
    processor.last_migration_result = None  # Clear any stale migration result
    dep_status = _register_and_migrate_path(
        processor, source_path_full, ingest_config.storage_root_directory, dataproduct_key, new_dep
    )  # register+migrate everything in src_dir

    # Update the dependency state to FAILED/FINISHED
    if new_dep and dep_status:
        await _aupdate_dependency_state(dep_status)


async def sdp_to_dlm_ingest_and_migrate(
    ingest_config: SDPIngestConfig, dev_test_mode=False
) -> None:
    """Ingest and migrate SDP data-products using DLM."""
    configdb = Config()  # Share one handle between writer & watcher
    if not dev_test_mode:
        # setup the source volume
        _ = setup_volume(
            watcher_config=ingest_config,
            api_configuration=ingest_config.ingest_configuration,
            rclone_config=RCLONE_CONFIG_SOURCE,
            storage_url=ingest_config.storage_url,
        )
    logger.info(
        "Starting SDP Config watcher (include_existing=%s, source storage=%s, target storage=%s)",
        ingest_config.include_existing,
        ingest_config.storage_name,
        ingest_config.migration_destination_storage_name,
    )

    async with watch_dataproduct_status(
        configdb,
        status="COMPLETED",
        include_existing=ingest_config.include_existing,
    ) as producer:  # make the desired status configurable?
        logger.info("Watcher READY and looking for events.")

        async for dataproduct_key, _ in producer:
            try:
                await _process_completed_flow(
                    configdb,
                    dataproduct_key,
                    ingest_config,
                )
                logger.info(
                    "Done processing %s; continuing to watch for COMPLETED data-product Flows.",
                    dataproduct_key,
                )
            except Exception:  # pylint: disable=broad-exception-caught  # pragma: no cover
                logger.exception("Failed to process Flow %s", dataproduct_key)
                logger.info("Continuing to watch for COMPLETED data-product Flows.")


def main() -> None:
    """Control the main execution of the program."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--include-existing",
        action="store_true",
        help="If set, first yield existing dataproduct keys with matching status.",
    )
    parser.add_argument(
        "-i",
        "--ingest-url",
        type=str,
        default="http://dlm_ingest:8001",
        help=(
            "Ingest server URL including the service port. " "Default 'http://dlm_ingest:8001'."
        ),
    )
    parser.add_argument(
        "--source-name",
        type=str,
        required=True,
        help="Source storage name (e.g., 'SDPBuffer').",
    )
    parser.add_argument(
        "--storage-url",
        type=str,
        default="http://dlm_storage:8003",
        help=(
            "Storage server URL including the service port. " "Default 'http://dlm_storage:8003'."
        ),
    )
    parser.add_argument(
        "-r",
        "--source-root",
        type=str,
        default="/dlm/product_dir",
        help=("Local mount directory of the shared PVC inside the configdb-watcher pod."),
    )
    parser.add_argument(
        "--target-name",
        type=str,
        default=None,
        help=(
            "Destination storage name used for migration. "
            "If omitted, migration will be skipped."
        ),
    )
    parser.add_argument(
        "-m",
        "--migration-url",
        type=str,
        default=None,
        help=(
            "Migration server URL including the service port. "
            "If omitted, migration will be skipped."
        ),
    )
    args = parser.parse_args()
    ingest_config = process_args(args)

    asyncio.run(sdp_to_dlm_ingest_and_migrate(ingest_config))


if __name__ == "__main__":
    main()

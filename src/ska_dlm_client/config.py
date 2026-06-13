# pylint: disable=invalid-name
"""Module-level constants used by the DLM client."""
import argparse
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

from ska_dlm_client.openapi.configuration import Configuration

logger = logging.getLogger(__name__)

STATUS_FILE_FILENAME = ".directory_watcher_status.run"
DIRECTORY_IS_MEASUREMENT_SET_SUFFIX = ".ms"
# Based on
# https://confluence.skatelescope.org/display/SWSI/ADR-55+Definition+of+metadata+for+data+management+at+AA0.5
METADATA_FILENAME = "ska-data-product.yaml"  # TODO: import from from ska_sdp_dataproduct_metadata
METADATA_EXECUTION_BLOCK_KEY = "execution_block"

# pylint: disable=too-many-instance-attributes
"""Class to hold the configuration used by the directory_watcher package."""


@dataclass
class ClientConfig:
    """General configuration class of the SKA DLM clients.

    This class holds all configuration parameters needed for the DLM clients.
    Specific configurations for the individual clients are expanding this class.
    """

    source_name: str = None
    target_name: str = "dlm-archive"
    ingest_url: str = "http://dlm_ingest:8001"
    storage_url: str = "http://dlm_storage:8003"
    migration_url: str = "http://dlm_migration:8004"
    reload_status_file: bool = True
    ingest_configuration: Configuration = field(init=False)
    migration_configuration: Configuration = field(init=False)
    include_existing: bool = False
    rclone_access_check_on_register: bool = False
    METADATA_FILENAME: str = METADATA_FILENAME
    METADATA_EXECUTION_BLOCK_KEY: str = METADATA_EXECUTION_BLOCK_KEY
    status_file_filename: str = STATUS_FILE_FILENAME
    DIRECTORY_IS_MEASUREMENT_SET_SUFFIX: str = DIRECTORY_IS_MEASUREMENT_SET_SUFFIX


@dataclass
class CmdLineParameters:  # pylint: disable=too-many-instance-attributes
    """Class for common/required command line parameters and helper methods."""

    source_name: str = ""
    directory_to_watch: str = ""
    target_name: str = ""
    storage_url: str = ""
    ingest_url: str = ""
    request_url: str = ""
    migration_url: str = ""
    readiness_probe_file: str = ""
    use_status_file: bool = False
    reload_status_file: bool = True
    parser: argparse.ArgumentParser = field(default_factory=argparse.ArgumentParser)

    def __default_args__(self):
        """Initialise parameters to include on the command line."""
        self.parser.add_argument(
            "-s",
            "--source-name",
            type=str,
            help="Source storage name (e.g., 'SDPBuffer').",
        )
        self.parser.add_argument(
            "-d",
            "--directory-to-watch",
            type=str,
            required=True,
            default="/dlm/watch_dir",
            help="The directory to watch (def /dlm/watch_dir).",
        )
        self.parser.add_argument(
            "-t",
            "--target-name",
            type=str,
            default="dlm-archive",
            help=("Destination storage name used for migration. "),
        )
        self.parser.add_argument(
            "--include-existing",
            action="store_true",
            help="If set, first yield existing dataproduct keys with matching status.",
        )
        self.parser.add_argument(
            "--ingest-url",
            type=str,
            default="http://dlm_ingest:8001",
            help=(
                "Ingest server URL including the service port. "
                "Default 'http://dlm_ingest:8001'."
            ),
        )
        self.parser.add_argument(
            "--request-url",
            type=str,
            default="http://dlm_request:8002",
            help=("Request server URL including the service port."),
        )
        self.parser.add_argument(
            "--storage-url",
            type=str,
            default="http://dlm_storage:8003",
            help=(
                "Storage server URL including the service port. "
                "Default 'http://dlm_storage:8003'."
            ),
        )
        self.parser.add_argument(
            "--migration-url",
            type=str,
            default="http://dlm_migration:8004",
            help=(
                "Migration server URL including the service port. "
                "If omitted, migration will be skipped."
            ),
        )
        self.parser.add_argument(
            "--uid-expiration-days",
            type=int,
            default=os.getenv("UID_EXPIRATION_DAYS"),
            help="UID expiration in days.",
        )
        self.parser.add_argument(
            "--oid-expiration-days",
            type=int,
            default=os.getenv("OID_EXPIRATION_DAYS"),
            help="OID expiration in days.",
        )
        self.parser.add_argument(
            "--readiness-probe-file",
            type=str,
            default="/tmp/dlm_client_ready",
            help="Indicator file to probe readiness",
        )
        self.parser.add_argument(
            "--use_status-file",
            type=bool,
            default=False,
            help="Use a status file (def False)",
        )

    def parse_arguments(self, args: argparse.Namespace = None):
        """Parse command line arguments and assign to class parameters."""
        if args is None:
            args = self.parser.parse_args()
        self.source_name = args.source_name
        self.directory_to_watch = args.directory_to_watch
        self.target_name = args.target_name
        self.ingest_url = args.ingest_url
        self.storage_url = args.storage_url
        self.migration_url = args.migration_url
        self.request_url = args.request_url
        self.use_status_file = args.use_status_file

    def set_application_ready(self):
        """Create the required file to indicate the application is ready."""
        if self.readiness_probe_file:
            Path(self.readiness_probe_file).touch()
            logger.info("The readiness probe file has been created %s.", self.readiness_probe_file)

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Delete the readiness file on deletion of the instance."""
        if self.readiness_probe_file:
            os.remove(self.readiness_probe_file)
            logger.info("The readiness probe file has been deleted %s.", self.readiness_probe_file)


# Backwards-compat alias for any existing imports of Config
Config = ClientConfig

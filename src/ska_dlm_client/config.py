"""Module-level constants used by the DLM client."""

STATUS_FILE_FILENAME = ".directory_watcher_status.run"
DIRECTORY_IS_MEASUREMENT_SET_SUFFIX = ".ms"
# Based on
# https://confluence.skatelescope.org/display/SWSI/ADR-55+Definition+of+metadata+for+data+management+at+AA0.5
METADATA_FILENAME = "ska-data-product.yaml"  # TODO: import from from ska_sdp_dataproduct_metadata
METADATA_EXECUTION_BLOCK_KEY = "execution_block"


class WatcherConstants:  # pylint: disable=too-few-public-methods
    """Constants shared by Directory- and ConfigDB-watchers."""

    STATUS_FILE_FILENAME = STATUS_FILE_FILENAME
    DIRECTORY_IS_MEASUREMENT_SET_SUFFIX = DIRECTORY_IS_MEASUREMENT_SET_SUFFIX
    METADATA_FILENAME = METADATA_FILENAME
    METADATA_EXECUTION_BLOCK_KEY = METADATA_EXECUTION_BLOCK_KEY


# Backwards-compat alias for any existing imports of Config
Config = WatcherConstants

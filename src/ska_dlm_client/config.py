"""Class to hold the configuration used by the directory_watcher package."""

import dataclasses

STATUS_FILE_FILENAME = ".directory_watcher_status.run"
DIRECTORY_IS_MEASUREMENT_SET_SUFFIX = ".ms"
# Based on
# https://confluence.skatelescope.org/display/SWSI/ADR-55+Definition+of+metadata+for+data+management+at+AA0.5
METADATA_FILENAME = "ska-data-product.yaml"
METADATA_EXECUTION_BLOCK_KEY = "execution_block"


@dataclasses.dataclass
class Config:
    """Module level configuration constants."""

    STATUS_FILE_FILENAME = ".directory_watcher_status.run"
    DIRECTORY_IS_MEASUREMENT_SET_SUFFIX = ".ms"
    # Based on
    # https://confluence.skatelescope.org/display/SWSI/ADR-55+Definition+of+metadata+for+data+management+at+AA0.5
    METADATA_FILENAME = "ska-data-product.yaml"
    METADATA_EXECUTION_BLOCK_KEY = "execution_block"

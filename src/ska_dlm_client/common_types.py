"""Constants used throughout the DLM package."""

# Refer to https://confluence.skatelescope.org/pages/viewpage.action?pageId=330648807
# for additional details.
from enum import Enum

# This is currently a copy of the required enums only from
# https://gitlab.com/ska-telescope/ska-data-lifecycle/-/blob/main/src/ska_dlm/common_types.py?ref_type=heads


class LocationType(str, Enum):
    """Location type."""

    LOCAL_DEV = "local-dev"
    LOW_INTEGRATION = "low-integration"
    MID_INTEGRATION = "mid-integration"
    LOW_OPERATIONS = "low-operations"
    MID_OPERATIONS = "mid-operations"


class LocationCountry(str, Enum):
    """Location country."""

    AU = "AU"
    ZA = "ZA"
    UK = "UK"


class StorageType(str, Enum):
    """Storage type."""

    FILESYSTEM = "filesystem"
    OBJECTSTORE = "objectstore"
    TAPE = "tape"


class StorageInterface(str, Enum):
    """Storage interface."""

    POSIX = "posix"
    S3 = "s3"
    SFTP = "sftp"
    HTTPS = "https"


class ItemType(str, Enum):
    """Data Item on the filesystem."""

    # Undetermined type
    UNKNOWN = "unknown"
    # A single file
    FILE = "file"
    # A directory superset with parents
    CONTAINER = "container"

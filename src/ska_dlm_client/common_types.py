"""DLM Storage API module."""

# Refer to https://confluence.skatelescope.org/pages/viewpage.action?pageId=330648807
# for additional details.
from enum import Enum

# This is currently a copy of the required enums only from
# https://gitlab.com/ska-telescope/ska-data-lifecycle/-/blob/main/src/ska_dlm/common_types.py?ref_type=heads


class ItemType(str, Enum):
    """Data Item on the filesystem."""

    UNKNOWN = "unknown"
    FILE = "file"
    CONTAINER = "container"


class ItemState(str, Enum):
    """Item state."""

    INITIALISED = "INITIALISED"
    READY = "READY"
    CORRUPTED = "CORRUPTED"
    EXPIRED = "EXPIRED"
    DELETED = "DELETED"

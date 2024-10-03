"""dlm_ingest REST client"""

from typing import Any, Dict, List, Union

INGEST_URL = ""
SESSION = None

JsonType = Union[Dict[str, Any], List[Any], str, int, float, bool, None]


# pylint: disable=unused-argument
def init_data_item(item_name: str = "", phase: str = "GAS", json_data: str = "") -> str:
    """
    Intialize a new data_item by at least specifying an item_name.

    Parameters:
    -----------
    item_name, the item_name, can be empty, but then json_data has to be specified.
    phase, the phase this item is set to (usually inherited from the storage)
    json_data, provides the ability to specify all values.

    Returns:
    --------
    uid,
    """
    params = {k: v for k, v in locals().items() if v}
    response = SESSION.post(f"{INGEST_URL}/ingest/init_data_item", params=params, timeout=60)
    if response.status_code in [401, 403]:
        response.raise_for_status()
    return response.json()


# pylint: disable=unused-argument, too-many-arguments
def register_data_item(
    item_name: str,
    uri: str = "",
    storage_name: str = "",
    storage_id: str = "",
    metadata: dict = None,
    item_format: str | None = "unknown",
    eb_id: str | None = None,
) -> str:
    """Ingest a data_item (register function is an alias).

    This high level function is a combination of init_data_item, set_uri and set_state(READY).
    It also checks whether a data_item is already registered on the requested storage.

    (1) check whether requested storage is known and accessible
    (2) check whether item is accessible/exists on that storage
    (3) check whether item is already registered on that storage
    (4) initialize the new item with the same OID on the new storage
    (5) set state to READY
    (6) generate metadata
    (7) notify the data dashboard

    Parameters
    ----------
    item_name: str
        could be empty, in which case the first 1000 items are returned
    uri: str
        the access path to the payload.
    storage_name: str
        the name of the configured storage volume (name or ID required)
    storage_id: str, optional
        the ID of the configured storage.
    metadata: dict, optional
        metadata provided by the client
    eb_id: str, optional
        execution block ID provided by the client

    Returns
    -------
    str
        data_item UID

    Raises
    ------
    UnmetPreconditionForOperation
    """
    params = {k: v for k, v in locals().items() if v}
    response = SESSION.post(f"{INGEST_URL}/ingest/register_data_item", params=params, timeout=60)
    if response.status_code in [401, 403]:
        response.raise_for_status()
    return response.json()

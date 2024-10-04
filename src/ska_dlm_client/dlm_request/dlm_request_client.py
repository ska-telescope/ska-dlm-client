"""dlm_request REST client."""

from datetime import timedelta

REQUEST_URL = ""
SESSION = None


# pylint: disable=unused-argument
def query_data_item(
    item_name: str = "", oid: str = "", uid: str = "", params: str | None = None
) -> list:
    """
    Query a new data_item by at least specifying an item_name.

    Parameters:
    -----------
    item_name: could be empty, in which case the first 1000 items are returned
    oid:    Return data_items referred to by the OID provided.
    uid:    Return data_item referred to by the UID provided.
    params: specify the query parameters

    Returns:
    --------
    list
    """
    params = {k: v for k, v in locals().items() if v}
    response = SESSION.get(f"{REQUEST_URL}/request/query_data_item", params=params, timeout=60)
    if response.status_code in [401, 403]:
        response.raise_for_status()
    return response.json()


# pylint: disable=unused-argument
def query_expired(offset: timedelta | None = None):
    """
    Query for all expired data_items using the uid_expiration timestamp.

    Parameters:
    -----------
    offset: optional offset for the query
    """
    params = {k: v for k, v in locals().items() if v}
    response = SESSION.get(f"{REQUEST_URL}/request/query_expired", params=params, timeout=60)
    if response.status_code in [401, 403]:
        response.raise_for_status()
    return response.json()


# pylint: disable=unused-argument
def query_deleted(uid: str = "") -> list:
    """Query for all deleted data_items using the deleted state.

    Parameters:
    -----------
    uid: The UID to be checked, optional.

    RETURNS:
    --------
    list of dictionaries with UIDs of deleted items.
    """
    params = {k: v for k, v in locals().items() if v}
    response = SESSION.get(f"{REQUEST_URL}/request/query_deleted", params=params, timeout=60)
    if response.status_code in [401, 403]:
        response.raise_for_status()
    return response.json()


# pylint: disable=unused-argument
def query_new(check_date: str, uid: str = "") -> list:
    """Query for all data_items newer than the date provided.

    Parameters:
    -----------
    check_date: str, the UTC starting date (exclusive)
    uid: The UID to be checked, optional.

    RETURNS:
    --------
    list of dictionaries with UID, UID_creation and storage_id of new items.
    """
    params = {k: v for k, v in locals().items() if v}
    response = SESSION.get(f"{REQUEST_URL}/request/query_new", params=params, timeout=60)
    if response.status_code in [401, 403]:
        response.raise_for_status()
    return response.json()


def query_exists(item_name: str = "", oid: str = "", uid: str = "", ready: bool = False) -> bool:
    """
    Query to check for existence of a data_item.

    Parameters:
    -----------
    item_name: optional item_name
    oid: optional, the oid to be searched for
    uid: optional, this returns only one storage_id
    """
    params = {k: v for k, v in locals().items() if v}
    response = SESSION.get(f"{REQUEST_URL}/request/query_exists", params=params, timeout=60)
    if response.status_code in [401, 403]:
        response.raise_for_status()
    return response.json()


# pylint: disable=unused-argument
def query_exists_and_ready(item_name: str = "", oid: str = "", uid: str = "") -> bool:
    """
    Check whether a data_item exists and is in ready state.

    Parameters:
    -----------
    item_name: optional item_name
    oid: optional, the oid to be searched for
    uid: optional, this returns only one storage_id

    Returns:
    boolean
    """
    params = {k: v for k, v in locals().items() if v}
    response = SESSION.get(
        f"{REQUEST_URL}/request/query_exist_and_ready", params=params, timeout=60
    )
    if response.status_code in [401, 403]:
        response.raise_for_status()
    return response.json()


# pylint: disable=unused-argument
def query_item_storage(item_name: str = "", oid: str = "", uid: str = "") -> str:
    """
    Query for the storage_ids of all backends holding a copy of a data_item.

    Either an item_name or a OID have to be provided.

    Parameters:
    -----------
    item_name: optional item_name
    oid: optional, the oid to be searched for
    uid: optional, this returns only one storage_id
    """
    params = {k: v for k, v in locals().items() if v}
    response = SESSION.get(f"{REQUEST_URL}/request/query_item_storage", params=params, timeout=60)
    if response.status_code in [401, 403]:
        response.raise_for_status()
    return response.json()

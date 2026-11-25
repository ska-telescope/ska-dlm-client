"""Bulk deletion runs last so its queue does not delay other integration tests."""

import logging
import subprocess
from datetime import datetime, timezone
from time import sleep

import pytest

from ska_dlm_client.openapi import api_client
from ska_dlm_client.openapi.dlm_api import storage_api
from tests.integration.test_configdb_watcher import EB_ID, PB_ID, SRC_HOST, WATCHER_SOURCE_DIR_ROOT

log = logging.getLogger(__name__)


def _get_id(item, key: str) -> str:
    """Return a string ID from a dict or generated API model."""
    value = item[key] if isinstance(item, dict) else getattr(item, key)
    assert isinstance(value, str)
    return value


@pytest.mark.xfail(reason="running extremely slow on CI")
@pytest.mark.integration
def test_automatic_deletion(
    dlm_request_api, storage_configuration, _configdb_watcher_ready, _common_dlm_endpoints
):
    """Expire all data_items and let the heuristics delete the payloads."""
    now = datetime.now(timezone.utc).isoformat()

    with api_client.ApiClient(storage_configuration) as the_api_client:
        api_storage = storage_api.StorageApi(the_api_client)
        source_storage = api_storage.query_storage(storage_name="configdb-watcher")

    assert source_storage
    source_storage_id = _get_id(source_storage[0], "storage_id")

    items = dlm_request_api.query_data_item(storage_id=source_storage_id)
    log.info("Found %d data items on source storage %s.", len(items), source_storage)
    log.info("Setting uid expirations to now...")

    for item in items:
        if PB_ID in item["item_name"]:
            dlm_request_api.set_uid_expiration(uid=item["uid"], expiration=now)

    test_dir = f"{WATCHER_SOURCE_DIR_ROOT}/product/{EB_ID}/ska-sdp/{PB_ID}"
    counter = 0
    while counter < 3:
        sleep_s = 20
        log.info("Sleeping %s seconds to give heuristics some time to do its thing...", sleep_s)
        sleep(sleep_s)
        result = subprocess.run(["docker", "exec", SRC_HOST, "test", "-d", test_dir], check=False)
        logs = subprocess.run(
            ["docker", "logs", "dlm-client-integration-dlm_heuristics"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            break
        log.info("Logs from heuristics container: %s", logs.stdout)
        counter += 1
    assert result.returncode != 0, f"Directory {test_dir} still exists: {result.stdout}"

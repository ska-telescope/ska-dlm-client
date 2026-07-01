"""Directory Watcher integration tests."""

import logging
import subprocess
from datetime import datetime, timezone
from time import sleep, time
from typing import Any

import pytest

from ska_dlm_client.openapi import api_client
from ska_dlm_client.openapi.configuration import Configuration
from ska_dlm_client.openapi.dlm_api import request_api, storage_api

log = logging.getLogger(__name__)


def _get_id(item: Any, key: str) -> Any:
    return item[key] if isinstance(item, dict) else getattr(item, key)


@pytest.mark.skip(reason="WIP: DMAN-200")
@pytest.mark.integration
def test_auto_migration(
    request_configuration: Configuration,
    storage_configuration: Configuration,
):
    """Test auto migration using directory watcher."""
    testfilename = f"group.{str(time())}"
    dst = f"/dlm/watch_dir/{testfilename}"

    cmd = f"docker exec dlm_directory_watcher cp /etc/group {dst}"
    log.info("Migration initialization copy command: %s", cmd)

    p = subprocess.run(cmd, capture_output=True, shell=True, check=True, text=True)
    if p.stdout:
        log.info("[copy file STDOUT]: %s\n", p.stdout)
    if p.stderr:
        log.error("[copy file STDERR]: %s\n", p.stderr)
    assert p.returncode == 0

    with api_client.ApiClient(storage_configuration) as the_api_client:
        api_storage = storage_api.StorageApi(the_api_client)
        source_storage = api_storage.query_storage(storage_name="dir-watcher")

    assert source_storage
    source_storage_id = _get_id(source_storage[0], "storage_id")

    with api_client.ApiClient(request_configuration) as the_api_client:
        api_request = request_api.RequestApi(the_api_client)
        sleep(2)  # TODO: DMAN-193

        items = api_request.query_data_item(item_name=testfilename)
        assert len(items) == 2
        assert items and _get_id(items[0], "item_name") == testfilename
        assert items and _get_id(items[1], "item_name") == testfilename

        source_items = api_request.query_data_item(
            item_name=testfilename,
            storage_id=source_storage_id,
        )
        assert len(source_items) == 1
        assert _get_id(source_items[0], "item_name") == testfilename
        assert _get_id(source_items[0], "storage_id") == source_storage_id

        # Update expirations of source items to now.
        log.info("Setting uid expirations on source storage %s to now...", source_storage)
        now = datetime.now(timezone.utc).isoformat()
        for item in source_items:
            api_request.set_uid_expiration(uid=item["uid"], expiration=now)

        log.info("Sleep to give heuristics some time to do its thing.")
        sleep(20)  # Default poll interval of the heuristics is 10 seconds.

        result = subprocess.run(
            f"docker exec dlm_directory_watcher test -f {dst}",
            shell=True,
            check=False,
        )
        assert result.returncode != 0, f"File {dst} still exists. Automatic deletion failed."

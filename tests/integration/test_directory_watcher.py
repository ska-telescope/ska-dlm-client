"""Directory Watcher integration tests."""

import logging
import os
import subprocess
from time import sleep

import pytest

from ska_dlm_client.openapi import api_client
from ska_dlm_client.openapi.configuration import Configuration
from ska_dlm_client.openapi.dlm_api import request_api
from ska_dlm_client.register_storage_location.main import setup_testing

log = logging.getLogger(__name__)


def _get_id(item, key: str):
    return item[key] if isinstance(item, dict) else getattr(item, key)


@pytest.mark.integration
def test_auto_migration(request_configuration: Configuration):
    """Test auto migration using directory watcher."""
    host = "dlm_storage" if os.getenv("DEFAULT_HOST") else "dlm_storage"
    api_configuration = Configuration(host=f"http://{host}:8003")
    setup_testing(api_configuration)
    sleep(2)
    cmd = "docker exec dlm_directory_watcher cp /etc/group /dlm/watch_dir/."
    log.info("Migration initialization copy command: %s", cmd)
    p = subprocess.run(cmd, capture_output=True, shell=True, check=True)
    if p.returncode != 0:
        log.info("[copy file STDOUT]: %s\n", p.stdout)
        log.error("[copy file STDERR]: %s\n", p.stderr)
    assert p.returncode == 0
    with api_client.ApiClient(request_configuration) as the_api_client:
        api_request = request_api.RequestApi(the_api_client)
        sleep(2)
        resp2 = api_request.query_data_item(item_name="group")
        assert len(resp2) == 2
        assert resp2 and _get_id(resp2[0], "item_name") == "group"
        assert resp2 and _get_id(resp2[1], "item_name") == "group"

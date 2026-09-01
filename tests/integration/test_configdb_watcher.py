# pylint: disable=subprocess-run-check
"""ConfigDB Watcher integration tests."""

import logging
import os
import subprocess
import time
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from time import sleep

import pytest
from ska_sdp_config import Config
from ska_sdp_config.entity import ProcessingBlock, Script
from ska_sdp_config.entity.common import PVCPath
from ska_sdp_config.entity.flow import (
    DataProduct,
    DataProductPersist,
    Dependency,
    Flow,
    FlowSource,
)

from ska_dlm_client.common_types import LocationCountry, LocationName, LocationType
from ska_dlm_client.openapi import api_client
from ska_dlm_client.openapi.configuration import Configuration
from ska_dlm_client.openapi.dlm_api import request_api, storage_api

log = logging.getLogger(__name__)
dir_path = os.path.dirname(os.path.realpath(__file__))

EB_ID = "eb-00000000"
PB_ID = "pb-test-20260126-24294"
ARB_MS = "scan90-99/output.scan-99.beam-vis0.ms"  # random MS file in pb-test-20260126-24294
PVC_SUBPATH = f"product/{EB_ID}/ska-sdp/{PB_ID}"
PVC_SUBPATH_DIRECT = f"product/{EB_ID}/ska-sdp/{PB_ID}/scan90-99"
DATA_PATH_LOCAL = f"{dir_path}/../registration_processor/product_dir"
SCRIPT = Script.Key(kind="batch", name="test", version="0.0.0")
STORAGE_URL = os.getenv("STORAGE_URL", "http://dlm_storage:8003")
ETCD_URL = os.getenv("ETCD_URL", "http://etcd:2379")

LOCATION_NAME = LocationName.LOCAL_DEV.value
LOCATION_TYPE = LocationType.LOCAL_DEV.value
LOCATION_COUNTRY = LocationCountry.AU.value
LOCATION_CITY = "Marksville"
LOCATION_FACILITY = "local"  # TODO: query location_facility lookup table

SRC_HOST = "dlm_configdb_watcher"
WATCHER_SOURCE_DIR_ROOT = "/dlm/product_dir"


def _get_cfg() -> Config:
    """Return a Config using the same env-based backend settings as the watcher."""
    etcd_host = urllib.parse.urlparse(ETCD_URL).hostname
    etcd_port = urllib.parse.urlparse(ETCD_URL).port
    return Config(host=etcd_host, port=etcd_port)


def _ensure_processing_block() -> None:
    """Create the ProcessingBlock if it doesn't already exist (idempotent)."""
    cfg = _get_cfg()
    for txn in cfg.txn():
        if txn.processing_block.get(PB_ID) is None:
            txn.processing_block.create(
                ProcessingBlock(
                    key=PB_ID,
                    eb_id=None,
                    script=SCRIPT,
                    parameters={"test": "test"},
                    dependencies=[],
                )
            )
            print(f"Created ProcessingBlock {PB_ID}")
        else:
            print(f"ProcessingBlock {PB_ID} already exists")


def _create_completed_flows(subpath: str, flow_name_arg: str, persist_flow_name_arg: str) -> None:
    """Create a DataProduct Flow and a DataProductPersist Flow. Set their states to COMPLETED."""
    cfg = _get_cfg()
    dataproduct_flow = Flow(
        key=Flow.Key(pb_id=PB_ID, kind="data-product", name=flow_name_arg),
        sink=DataProduct(
            data_dir=PVCPath(
                k8s_namespaces=["dp-shared", "dp-shared-p"],
                k8s_pvc_name="shared-storage",
                pvc_mount_path=Path("/dlm/product_dir"),
                pvc_subpath=Path(subpath),
            ),
            paths=[],
        ),
        sources=[],
        data_model="Visibility",
    )

    for txn in cfg.txn():
        txn.flow.create(dataproduct_flow)
        ops = txn.flow.state(dataproduct_flow.key)
        ops.create({"status": "COMPLETED"})

    dataproductpersist_flow = Flow(
        key=Flow.Key(pb_id=PB_ID, kind="data-product-persist", name=persist_flow_name_arg),
        sink=DataProductPersist(phase="SOLID", expires_at=None),
        sources=[FlowSource(uri=dataproduct_flow.key, function="ska-dlm-client:ingest")],
        data_model="Visibility",
    )

    for txn in cfg.txn():
        txn.flow.create(dataproductpersist_flow)
        ops = txn.flow.state(dataproductpersist_flow.key)
        ops.create({"status": "COMPLETED"})


def trigger_completed_flows(flow_name: str, persist_flow_name: str, subpath: str) -> None:
    """Ensure PB + Flow exist and mark Flow as COMPLETED."""
    _ensure_processing_block()
    _create_completed_flows(
        subpath=subpath,
        persist_flow_name_arg=persist_flow_name,
        flow_name_arg=flow_name,
    )


def _get_id(item, key: str) -> str:
    """Return a string ID from a dict or generated API model."""
    value = item[key] if isinstance(item, dict) else getattr(item, key)
    assert isinstance(value, str)
    return value


def _get_dependency_statuses_for_product(pb_id: str, name: str) -> list[str]:
    """Return all dependency statuses for a given pb_id/name."""
    cfg = _get_cfg()
    statuses: list[str] = []
    for txn in cfg.txn():
        dkeys = txn.dependency.list_keys(pb_id=pb_id, name=name)
        log.info("Found dependencies for %s/%s: %s", pb_id, name, dkeys)
        for dkey in dkeys:
            dep_obj = Dependency(
                key=dkey, expiry_time=-1, description="DLM: lock data product for copy"
            )
            state = txn.dependency.state(dep_obj).get() or {}
            log.info("Found state %s for dependency %s", state, dep_obj)
            status = state.get("status")
            if status is not None:
                statuses.append(status)
    return statuses


def _wait_for_dependency_status(
    pb_id: str,
    flow_name: str,
    expected_status: str = "FINISHED",
    timeout_s: int = 60,
    poll_interval_s: int = 2,
) -> list[str]:
    """Poll dependency statuses until the expected status appears or time out."""
    deadline = time.time() + timeout_s
    statuses: list[str] = []

    while time.time() < deadline:
        statuses = _get_dependency_statuses_for_product(pb_id, flow_name)
        if expected_status in statuses:
            return statuses

        sleep(poll_interval_s)

    return statuses


@pytest.mark.integration
def test_data_was_copied_correctly(_configdb_watcher_ready, _common_dlm_endpoints):
    """Verify that the test data is visible inside the watcher container."""
    expected_file = f"{WATCHER_SOURCE_DIR_ROOT}/product/{EB_ID}/ska-sdp/{PB_ID}/{ARB_MS}/table.dat"

    result = subprocess.run(
        f"docker exec {SRC_HOST} sh -lc 'test -f {expected_file}'", shell=True, check=False
    )
    if result.returncode != 0:
        log.error("docker exec failed")
        log.error("stdout:\n%s", result.stdout)
        log.error("stderr:\n%s", result.stderr)

        subprocess.run(["docker", "ps", "-a"], check=False)
        subprocess.run(["docker", "logs", "dlm_configdb_watcher"], check=False)
        subprocess.run(["docker", "logs", "dlm_directory_watcher"], check=False)
        subprocess.run(["docker", "logs", "dlm_storage"], check=False)
    assert result.returncode == 0, f"Could not find expected file: {expected_file}"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_configdb_watcher(
    request_configuration: Configuration, _configdb_watcher_ready, _common_dlm_endpoints
):
    """Flow points to subfolder scan90-99, containing 10 MS files."""
    # Trigger COMPLETED Flow pointing directly at scan90-99
    flow_name = "test-flow"
    persist_flow_name = "persist-flow"
    trigger_completed_flows(flow_name, persist_flow_name, subpath=PVC_SUBPATH_DIRECT)

    # Poll for FINISHED dependency status
    statuses = _wait_for_dependency_status(PB_ID, flow_name, timeout_s=60)

    assert "FINISHED" in statuses, f"Expected FINISHED, got {statuses}"

    expected_items = [
        f"product/{EB_ID}/ska-sdp/{PB_ID}/scan90-99/output.scan-{i}.beam-vis0.ms"
        for i in range(90, 100)
    ]

    with api_client.ApiClient(request_configuration) as the_api_client:
        api_request = request_api.RequestApi(the_api_client)

        for item_name in expected_items:
            resp = api_request.query_data_item(item_name=item_name)
            # assert each data_item is in source and destination:
            assert len(resp) == 2, f"Expected 2 entries for {item_name}, got {len(resp)}"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_configdb_watcher_higher_dir(
    request_configuration: Configuration, _configdb_watcher_ready, _common_dlm_endpoints
):
    """
    Flow points at pb-test-20260126-24294 (one level higher).

    Watcher must search one level deeper to find all ms files.
    """
    # Trigger COMPLETED Flow pointing at pb-test-20260126-24294 directory
    flow_name = "test-flow-higher-dir"
    persist_flow_name = "persist-flow2"
    trigger_completed_flows(flow_name, persist_flow_name, subpath=PVC_SUBPATH)

    # This test migrates the full parent directory; registration, migration, RabbitMQ
    # processing, and dependency update can take approximately 85-90 seconds in total.
    statuses = _wait_for_dependency_status(PB_ID, flow_name, timeout_s=120)
    assert "FINISHED" in statuses, f"Expected FINISHED, got {statuses}"

    representative_items = [
        f"product/{EB_ID}/ska-sdp/{PB_ID}/ancillary/file2.png",
        f"product/{EB_ID}/ska-sdp/{PB_ID}/broken.ms",
        f"product/{EB_ID}/ska-sdp/{PB_ID}/output.scan-5.beam-vis0.ms",
        f"product/{EB_ID}/ska-sdp/{PB_ID}/scan10-19/output.scan-15.beam-vis0.ms",
        f"product/{EB_ID}/ska-sdp/{PB_ID}/scan40-49/output.scan-45.beam-vis0.ms",
        f"product/{EB_ID}/ska-sdp/{PB_ID}/scan80-89/output.scan-85.beam-vis0.ms",
    ]

    with api_client.ApiClient(request_configuration) as the_api_client:
        api_request = request_api.RequestApi(the_api_client)
        # assert each data_item is in source and destination:
        for item_name in representative_items:
            resp = api_request.query_data_item(item_name=item_name)
            assert len(resp) == 2, f"Expected 2 entries for {item_name}, got {len(resp)}"

    # By now there should be >200 entries in data_item:
    resp = api_request.query_data_item(item_name="")
    assert len(resp) > 200, f"Expected more than 200 data_items, got {len(resp)}"


# TODO: write logic for metadata files found without data.


@pytest.mark.asyncio
@pytest.mark.integration
async def test_watcher_logs_failed_registration(_configdb_watcher_ready, _common_dlm_endpoints):
    """Flow points to a data item that is already registered on the storage."""
    # Trigger a COMPLETED Flow with same subpath as previous test
    trigger_completed_flows("test-flow-failure", "persist-flow3", subpath=PVC_SUBPATH)

    # Poll for FAILED dependency status
    statuses = _wait_for_dependency_status(PB_ID, "test-flow-failure", "FAILED", timeout_s=60)
    assert "FAILED" in statuses, f"Expected FAILED due to duplicate registration, got {statuses}"


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

    items = dlm_request_api.query_data_item(
        storage_id=source_storage_id,
    )
    log.info("Found %d data items on source storage %s.", len(items), source_storage)
    log.info("Setting uid expirations to now...")

    # Update uid expirations of source items to now.
    for item in items:
        if "pb-test-20260126-24294" in item["item_name"]:
            dlm_request_api.set_uid_expiration(uid=item["uid"], expiration=now)

    # Potential optimisation: expose a server-side bulk update endpoint via @rest.patch to
    # avoid iterative HTTP round-trips to a single DB update, from the client-side.

    test_dir = f"{WATCHER_SOURCE_DIR_ROOT}/product/{EB_ID}/ska-sdp/{PB_ID}"
    counter = 0
    while counter < 3:
        sleep_s = 20
        log.info("Sleeping %s seconds to give heuristics some time to do its thing...", sleep_s)
        sleep(sleep_s)  # default poll interval of the heuristics is 10 seconds
        result = subprocess.run(["docker", "exec", SRC_HOST, "test", "-d", test_dir])
        logs = subprocess.run(["docker", "logs", "dlm_heuristics"], capture_output=True, text=True)
        if result.returncode != 0:
            break
        log.info("Logs from heuristics container: %s", logs.stdout)
        counter += 1
    assert result.returncode != 0, f"Directory {test_dir} still exists: {result.stdout}"

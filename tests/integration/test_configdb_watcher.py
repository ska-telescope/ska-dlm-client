"""SDP Ingest (ConfigDB Watcher) integration tests."""

import logging
import os
import subprocess
import time
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

from ska_dlm_client.common_types import (
    LocationCountry,
    LocationType,
    StorageInterface,
    StorageType,
)
from ska_dlm_client.openapi import api_client
from ska_dlm_client.openapi.api_client import ApiException
from ska_dlm_client.openapi.configuration import Configuration
from ska_dlm_client.openapi.dlm_api import request_api, storage_api
from ska_dlm_client.register_storage_location.main import setup_testing

log = logging.getLogger(__name__)
dir_path = os.path.dirname(os.path.realpath(__file__))

EB_ID = "eb-00000000"
PB_ID = "pb-test-20260126-24294"
ARB_MS = "scan90-99/output.scan-99.beam-vis0.ms"  # random MS file in pb-test-20260126-24294
PVC_SUBPATH = f"product/{EB_ID}/ska-sdp/{PB_ID}"
PVC_SUBPATH_DIRECT = f"product/{EB_ID}/ska-sdp/{PB_ID}/scan90-99"
DATA_PATH_LOCAL = f"{dir_path}/../registration_processor/product_dir"
SCRIPT = Script.Key(kind="batch", name="test", version="0.0.0")
INGEST_URL = os.getenv("INGEST_URL", "http://dlm_ingest:8001")
STORAGE_URL = os.getenv("STORAGE_URL", "http://dlm_storage:8003")
MIGRATION_URL = os.getenv("MIGRATION_URL", "http://dlm_migration:8004")

LOCATION_NAME = "ThisDLMClientLocationName"
LOCATION_TYPE = LocationType.LOCAL_DEV
LOCATION_COUNTRY = LocationCountry.AU

LOCATION_CITY = "Marksville"
LOCATION_FACILITY = "local"  # TODO: query location_facility lookup table
STORAGE = {
    "TGT": {
        "STORAGE_NAME": "dlm-archive",
        "STORAGE_TYPE": StorageType.FILESYSTEM,
        "STORAGE_INTERFACE": StorageInterface.POSIX,
        "ROOT_DIRECTORY": "/dlm-archive",
        "STORAGE_CONFIG": {
            "name": "dlm-archive",
            "type": "alias",  # type 'alias' or 'local'?
            "parameters": {"remote": "/dlm-archive"},
        },
    },
    "SRC": {
        "STORAGE_NAME": "sdp-watcher",
        "STORAGE_TYPE": StorageType.FILESYSTEM,
        "STORAGE_INTERFACE": StorageInterface.POSIX,
        "ROOT_DIRECTORY": "/dlm/product_dir",
        "STORAGE_CONFIG": {
            "name": "dlm",
            "type": "sftp",
            "parameters": {
                "host": "dlm_configdb_watcher",
                "key_file": "/root/.ssh/id_rsa",
                "shell_type": "unix",
                "type": "sftp",
                "user": "ska-dlm",
            },
        },
    },
}

SRC_HOST = STORAGE["SRC"]["STORAGE_CONFIG"]["parameters"]["host"]
WATCHER_SOURCE_DIR_ROOT = f"{STORAGE['SRC']['ROOT_DIRECTORY'].rstrip('/')}"


def _get_cfg() -> Config:
    """Return a Config using the same env-based backend settings as the watcher."""
    return Config()


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


def trigger_completed_flows(flow_name, persist_flow_name, subpath) -> None:
    """Ensure PB + Flow exist and mark Flow as COMPLETED."""
    _ensure_processing_block()
    # IMPORTANT: this must match what the watcher expects:
    #   - same `storage_root_directory`
    #   - points at a directory that actually contains the .ms + metadata
    _create_completed_flows(
        subpath=subpath,
        persist_flow_name_arg=persist_flow_name,
        flow_name_arg=flow_name,
    )


def _get_id(item, key: str):
    return item[key] if isinstance(item, dict) else getattr(item, key)


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


def _init_location_if_needed(api_storage: storage_api.StorageApi) -> str:
    try:
        resp = api_storage.query_location(location_name=LOCATION_NAME)
        assert isinstance(resp, list)
    except ApiException as e:
        log.error("Failed to query location: %s", e)
        storage_log = _get_container_log("dlm_postgrest")
        log.info("Log from storage container: %s", storage_log)
        return ""
    if resp:
        location_id = _get_id(resp[0], "location_id")
        log.info("Location already exists: %s", location_id)
    else:
        try:
            location_id = api_storage.init_location(
                location_name=LOCATION_NAME,
                location_type=LOCATION_TYPE,
                location_country=LOCATION_COUNTRY,
                location_city=LOCATION_CITY,
                location_facility=LOCATION_FACILITY,
            )
            assert isinstance(location_id, str) and location_id
        except ApiException as e:
            log.error("Failed to create location: %s", e)
            storage_log = _get_container_log("dlm_storage")
            log.info("Log from storage container: %s", storage_log)
            return ""
        log.info("Location created: %s", location_id)
    return location_id


def _init_storage_if_needed(
    api_storage: storage_api.StorageApi, location_id: str, storage: dict = None
) -> str:
    resp = api_storage.query_storage(storage_name=storage["STORAGE_NAME"])
    assert isinstance(resp, list)
    if resp:
        storage_id = _get_id(resp[0], "storage_id")
        log.info("Storage already exists: %s", storage_id)
    else:
        storage_id = api_storage.init_storage(
            storage_name=storage["STORAGE_NAME"],
            storage_type=storage["STORAGE_TYPE"],
            storage_interface=storage["STORAGE_INTERFACE"],
            root_directory=storage["ROOT_DIRECTORY"],
            location_id=location_id,
            location_name=LOCATION_NAME,
        )
        assert isinstance(storage_id, str) and storage_id
        log.info("Storage created: %s %s", storage["STORAGE_NAME"], storage_id)
    return storage_id


def _get_container_log(container_name: str) -> str:
    cmd = ["docker", "logs", "--since", "600s", container_name]
    p = subprocess.run(cmd, capture_output=True, text=True, check=True)
    if p.returncode != 0:
        log.error("Failed to get logs for container %s: %s", container_name, p.stderr)
        return p.stderr
    return p.stdout


@pytest.mark.integration
def test_storage_initialisation(storage_configuration: Configuration):
    """Test setting up a location, storage and storage config."""
    with api_client.ApiClient(storage_configuration) as the_api_client:
        api_storage = storage_api.StorageApi(the_api_client)

        # --- ensure location exists ---
        log.info(
            "Using storage configuration host for registering: %s", storage_configuration.host
        )
        os.environ["STORAGE_URL"] = storage_configuration.host
        storage_log = _get_container_log("dlm_storage")
        log.info("Log from storage container: %s", storage_log)
        location_id = _init_location_if_needed(api_storage)
        # --- ensure storage exists ---
        storage_id = _init_storage_if_needed(api_storage, location_id, storage=STORAGE["TGT"])

        # --- set storage config ---
        cfg_id = api_storage.create_storage_config(
            request_body=STORAGE["TGT"]["STORAGE_CONFIG"],
            storage_id=storage_id,
            storage_name=STORAGE["TGT"]["STORAGE_NAME"],
            config_type="rclone",
        )
        assert isinstance(cfg_id, str) and cfg_id
        log.info("Target storage config id: %s", cfg_id)

        # --- verify by querying again ---
        resp2 = api_storage.query_storage(storage_name=STORAGE["TGT"]["STORAGE_NAME"])
        assert resp2 and _get_id(resp2[0], "storage_id") == storage_id


def _cleanup_destination_storage() -> None:
    """Remove migrated test data from the rclone destination."""
    destination_file = f"/dlm-archive/dlm-archive/product/{EB_ID}"
    log.info("Cleaning up %s, destination_file")
    subprocess.run(
        (f"docker exec dlm_rclone sh -lc 'rm -rf {destination_file}'"),
        shell=True,
        check=False,
    )


_cleanup_destination_storage()  # remove – DMAN-200


@pytest.mark.integration
def test_data_was_copied_correctly():
    """Verify that the test data is visible inside the watcher container."""
    expected_file = f"{WATCHER_SOURCE_DIR_ROOT}/product/{EB_ID}/ska-sdp/{PB_ID}/{ARB_MS}/table.dat"

    result = subprocess.run(
        f"docker exec {SRC_HOST} sh -lc 'test -f {expected_file}'", shell=True, check=False
    )
    assert result.returncode == 0, f"Could not find expected file: {expected_file}"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_configdb_watcher(request_configuration: Configuration):
    """Flow points to subfolder scan90-99, containing 10 MS files."""
    host = os.getenv("STORAGE_URL", "http://dlm_storage:8003")
    api_configuration = Configuration(host=host)
    setup_testing(api_configuration)
    sleep(2)  # TODO: DMAN-193

    # Trigger COMPLETED Flow pointing directly at scan90-99
    flow_name = "test-flow"
    persist_flow_name = "persist-flow"
    trigger_completed_flows(flow_name, persist_flow_name, subpath=PVC_SUBPATH_DIRECT)

    # Poll for FINISHED dependency status
    deadline = time.time() + 10
    statuses = []
    while time.time() < deadline:
        statuses = _get_dependency_statuses_for_product(PB_ID, flow_name)
        if "FINISHED" in statuses:
            break
        sleep(1)

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
async def test_configdb_watcher_higher_dir(request_configuration: Configuration):
    """
    Flow points at pb-test-20260126-24294 (one level higher).

    Watcher must search one level deeper to find all ms files.
    """
    host = os.getenv("STORAGE_URL", "http://dlm_storage:8003")
    api_configuration = Configuration(host=host)
    setup_testing(api_configuration)
    sleep(2)  # TODO: DMAN-193

    # Trigger COMPLETED Flow pointing at pb-test-20260126-24294 directory
    flow_name = "test-flow-higher-dir"
    persist_flow_name = "persist-flow2"
    trigger_completed_flows(flow_name, persist_flow_name, subpath=PVC_SUBPATH)

    def _wait_for_dependency_status(
        pb_id: str,
        flow_name: str,
        expected_status: str = "FINISHED",
        timeout_s: int = 60,
        poll_interval_s: int = 2,
    ) -> list[str]:
        """Poll dependency statuses until expected_status appears, or time out."""
        deadline = time.time() + timeout_s
        statuses: list[str] = []

        while time.time() < deadline:
            statuses = _get_dependency_statuses_for_product(pb_id, flow_name)
            if expected_status in statuses:
                return statuses

            sleep(poll_interval_s)

        return statuses

    statuses = _wait_for_dependency_status(PB_ID, flow_name, timeout_s=60)
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
async def test_watcher_logs_failed_registration():
    """Flow points to a data item that is already registered on the storage."""
    host = os.getenv("STORAGE_URL", "http://dlm_storage:8003")
    api_configuration = Configuration(host=host)
    setup_testing(api_configuration)
    sleep(2)  # TODO: DMAN-193

    # Trigger a COMPLETED Flow with same subpath as previous test
    trigger_completed_flows("test-flow-failure", "persist-flow3", subpath=PVC_SUBPATH)

    # Poll for FAILED dependency status
    deadline = time.time() + 10
    statuses = []
    while time.time() < deadline:
        statuses = _get_dependency_statuses_for_product(PB_ID, "test-flow-failure")
        if "FAILED" in statuses:
            break
        sleep(1)

    assert "FAILED" in statuses, f"Expected FAILED due to duplicate registration, got {statuses}"

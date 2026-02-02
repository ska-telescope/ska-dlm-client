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
from ska_sdp_config.entity.flow import DataProduct, Dependency, Flow

from ska_dlm_client.common_types import (
    LocationCountry,
    LocationType,
    StorageInterface,
    StorageType,
)
from ska_dlm_client.openapi import api_client
from ska_dlm_client.openapi.api_client import ApiException
from ska_dlm_client.openapi.configuration import Configuration
from ska_dlm_client.openapi.dlm_api import storage_api
from ska_dlm_client.register_storage_location.main import setup_testing

log = logging.getLogger(__name__)
dir_path = os.path.dirname(os.path.realpath(__file__))

EB_ID = "eb-00000000"
PB_ID = "pb-test-00000000-a"
MS_PATH = f"{dir_path}/../directory_watcher/test_registration_processor/product_dir"
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

PVC_SUBPATH = f"product/{EB_ID}/ska-sdp/{PB_ID}"
WATCHER_SOURCE_DIR = f"{STORAGE['SRC']['ROOT_DIRECTORY'].rstrip('/')}/{PVC_SUBPATH}"


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
                )
            )
            print(f"Created ProcessingBlock {PB_ID}")
        else:
            print(f"ProcessingBlock {PB_ID} already exists")


def _create_completed_flow(subpath: str, flow_name_arg: str) -> None:
    """Create a Flow and set its state to COMPLETED."""
    cfg = _get_cfg()
    test_dataproduct = Flow(
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
        txn.flow.create(test_dataproduct)
        ops = txn.flow.state(test_dataproduct.key)
        ops.create({"status": "COMPLETED"})


def trigger_completed_flow(flow_name) -> None:
    """Ensure PB + Flow exist and mark Flow as COMPLETED."""
    _ensure_processing_block()
    # IMPORTANT: this must match what the watcher expects:
    #   - same `storage_root_directory`
    #   - points at a directory that actually contains the .ms + metadata
    _create_completed_flow(
        subpath=PVC_SUBPATH,
        flow_name_arg=flow_name,
    )


def _get_id(item, key: str):
    return item[key] if isinstance(item, dict) else getattr(item, key)


def _get_dependency_statuses_for_product(pb_id: str, name: str) -> list[str]:
    """Return all dependency statuses for a given data-product (by pb_id/name)."""
    cfg = _get_cfg()
    statuses: list[str] = []
    for txn in cfg.txn():
        dkeys = txn.dependency.list_keys(pb_id=pb_id, name=name)
        log.info("Found dependencies for %s/%s: %s", pb_id, name, dkeys)
        for dkey in dkeys:
            dep_obj = Dependency(
                key=dkey, expiry_time=-1, description="DLM: lock data-product for copy"
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


@pytest.mark.asyncio
@pytest.mark.integration
async def test_watcher_registers_and_migrates():
    """
    Run the real watcher, wait for success logs, then cancel it cleanly.

    Test auto migration using configdb watcher.
    """
    host = os.getenv("STORAGE_URL", "http://dlm_storage:8003")
    api_configuration = Configuration(host=host)
    setup_testing(api_configuration)
    sleep(2)  # TODO: DMAN-193

    src_host = STORAGE["SRC"]["STORAGE_CONFIG"]["parameters"]["host"]

    # 1) Ensure watcher source dir exists
    cmd = f"docker exec {src_host} sh -lc 'mkdir -p {WATCHER_SOURCE_DIR}'"
    log.info("Ensure watcher source dir exists: %s", cmd)
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    assert p.returncode == 0, p.stderr

    # 2) Copy MS_PATH contents into that directory
    cmd = f"docker container cp {MS_PATH}/. {src_host}:{WATCHER_SOURCE_DIR}/"
    log.info("Copy MS into watcher container: %s", cmd)
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    assert p.returncode == 0, p.stderr

    # 3) Wait until the directory is visible (avoid race with watcher)
    deadline = time.time() + 20
    while time.time() < deadline:
        check_dir = f"ls -la {WATCHER_SOURCE_DIR} | head"
        cmd = f"docker exec {src_host} sh -lc '{check_dir}'"
        p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if p.returncode == 0:
            log.info("dir check stdout: %s", p.stdout)
            break
        sleep(1)

    assert (
        p.returncode == 0
    ), f"Source dir not visible in watcher container: {WATCHER_SOURCE_DIR}\n{p.stderr}"

    # 4) Trigger a COMPLETED Flow
    trigger_completed_flow("test-flow")

    # 5) Poll for FINISHED
    deadline = time.time() + 30
    statuses = []
    while time.time() < deadline:
        statuses = _get_dependency_statuses_for_product(PB_ID, "test-flow")
        if "FINISHED" in statuses:
            break
        sleep(1)

    assert "FINISHED" in statuses, f"Expected FINISHED, got {statuses}"

    log.info("Cleaning up copied MS file(s) from watcher container.")
    cmd = f"docker exec {src_host} sh -lc 'rm -rf {WATCHER_SOURCE_DIR}'"
    log.info("Cleanup cmd: %s", cmd)
    subprocess.run(cmd, shell=True, check=False)


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.skip(reason="We need to trigger a failed registration on the container")
# The current implementation runs a new configdb_watcher locally.
async def test_watcher_logs_failed_registration():
    """Run the watcher, trigger a Flow, and check failed registration is logged."""
    # We can now use the env-variables to start a new client with a
    # deliberately bad source_name to trigger DLM registration failure

    # 1) Trigger a COMPLETED Flow
    trigger_completed_flow("test-flow-failure")

    # 2) Wait for the registration failure log
    sleep(1)
    statuses = _get_dependency_statuses_for_product(PB_ID, "test-flow-failure")
    if "FAILED" not in statuses:
        pytest.fail("Watcher did not log failed registration within timeout")

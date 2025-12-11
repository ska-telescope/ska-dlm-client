"""SDP Ingest (ConfigDB Watcher) integration tests."""

import asyncio
import logging
import os
import subprocess
from time import sleep

import pytest
from ska_sdp_config import Config
from ska_sdp_config.entity import ProcessingBlock, Script
from ska_sdp_config.entity.flow import DataProduct, Dependency, Flow

from ska_dlm_client.openapi import api_client
from ska_dlm_client.openapi.configuration import Configuration
from ska_dlm_client.openapi.dlm_api import request_api, storage_api
from ska_dlm_client.register_storage_location.main import setup_testing

from ska_dlm_client.configdb_watcher import main as configdb_watcher_main

from ska_dlm_client.common_types import (
    LocationCountry,
    LocationType,
    StorageInterface,
    StorageType,
)

log = logging.getLogger(__name__)
dir_path = os.path.dirname(os.path.realpath(__file__))

PB_ID = "pb-test-00000000-a"
DEMO_MS_PATH = f"{dir_path}/../directory_watcher/test_registration_processor/testing1"
SCRIPT = Script.Key(kind="batch", name="test", version="0.0.0")
INGEST_SERVER_URL = os.getenv("INGEST_SERVER_URL", "http://localhost:8001")
STORAGE_SERVER_URL = os.getenv("INGEST_SERVER_URL", "http://localhost:8003")
MIGRATION_SERVER_URL = os.getenv("MIGRATION_SERVER_URL", "http://localhost:8004")

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
        "ROOT_DIRECTORY": "/data",
        "STORAGE_CONFIG": {"name": "dlm-archive", "type": "local", "parameters": {}},
    },
    "SRC": {
        "STORAGE_NAME": "sdp-watcher",
        "STORAGE_TYPE": StorageType.FILESYSTEM,
        "STORAGE_INTERFACE": StorageInterface.POSIX,
        "ROOT_DIRECTORY": "/dlm",
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


def _create_completed_flow(data_dir: str, flow_name_arg: str) -> None:
    """Create a Flow and set its state to COMPLETED."""
    cfg = _get_cfg()
    test_dataproduct = Flow(
        key=Flow.Key(pb_id=PB_ID, kind="data-product", name=flow_name_arg),
        sink=DataProduct(data_dir=data_dir, paths=[]),
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
        data_dir="/dlm/testing1",
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
        for dkey in dkeys:
            dep_obj = Dependency(key=dkey, expiry_time=-1, description=None)
            state = txn.dependency.state(dep_obj).get() or {}
            status = state.get("status")
            if status is not None:
                statuses.append(status)
    return statuses

def _init_location_if_needed(api_storage: storage_api.StorageApi) -> str:
    resp = api_storage.query_location(location_name=LOCATION_NAME)
    assert isinstance(resp, list)
    if resp:
        location_id = _get_id(resp[0], "location_id")
        log.info("Location already exists: %s", location_id)
    else:
        location_id = api_storage.init_location(
            location_name=LOCATION_NAME,
            location_type=LOCATION_TYPE,
            location_country=LOCATION_COUNTRY,
            location_city=LOCATION_CITY,
            location_facility=LOCATION_FACILITY,
        )
        assert isinstance(location_id, str) and location_id
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



@pytest.mark.integration
def test_storage_initialisation(storage_configuration: Configuration):
    """Test setting up a location, storage and storage config."""
    with api_client.ApiClient(storage_configuration) as the_api_client:
        api_storage = storage_api.StorageApi(the_api_client)

        # --- ensure location exists ---
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
# TODO: This does not work at all since it is running the client locally and not in
# a container.
async def test_watcher_registers_and_migrates(caplog, storage_configuration: Configuration):
    """Run the real watcher, wait for success logs, then cancel it cleanly."""
    """Test auto migration using configdb watcher."""
    api_configuration = Configuration(host="http://localhost")
    setup_testing(api_configuration)
    caplog.set_level(logging.INFO, logger="ska_dlm_client.configdb_watcher")
        # --- copying demo.ps ---
    sleep(2)
    cmd = f"docker container cp {DEMO_MS_PATH} dlm_configdb_watcher:/dlm/."
    log.info("Move MS into container: %s", cmd)
    p = subprocess.run(cmd, capture_output=True, shell=True, check=True)
    if p.returncode != 0:
        log.info("[copy file STDOUT]: %s\n", p.stdout)
        log.error("[copy file STDERR]: %s\n", p.stderr)
    assert p.returncode == 0
    if p.returncode != 0:
        log.error("Failed to copy MS to watcher container.")
        return

    # configdb_watcher_config = configdb_watcher_main.SDPIngestConfig(
    #     include_existing=False,
    #     ingest_server_url=INGEST_SERVER_URL,
    #     ingest_configuration=Configuration(host=INGEST_SERVER_URL),
    #     storage_server_url=STORAGE_SERVER_URL,
    #     storage_name=STORAGE["SRC"]["STORAGE_NAME"],  # <- registered by previous tests
    #     storage_root_directory=STORAGE["SRC"]["ROOT_DIRECTORY"],
    #     migration_destination_storage_name=STORAGE["TGT"]["STORAGE_NAME"],  # use a second storage end-point
    #     migration_configuration=Configuration(host=MIGRATION_SERVER_URL),
    # )

    # task = asyncio.create_task(configdb_watcher_main.sdp_to_dlm_ingest_and_migrate(configdb_watcher_config))

    try:

        # 1) Trigger a COMPLETED Flow
        trigger_completed_flow(flow_name="test-flow")

        # 2) Wait for the "status set to FINISHED" log
        finished_msg = "status set to FINISHED"
        for _ in range(100):
            if finished_msg in caplog.text:
                break
            await asyncio.sleep(0.1)
        else:
            pytest.fail("Dependency was not marked FINISHED within timeout")

    finally:
        # task.cancel()
        # with pytest.raises(asyncio.CancelledError):
        #     await task
        pass

    statuses = _get_dependency_statuses_for_product(PB_ID, "test-flow")
    assert "FINISHED" in statuses


@pytest.mark.asyncio
@pytest.mark.integration
async def test_watcher_logs_failed_registration(caplog):
    """Run the watcher, trigger a Flow, and check failed registration is logged."""
    caplog.set_level(logging.INFO, logger="ska_dlm_client.configdb_watcher")

    # Deliberately use a bad storage name to trigger DLM registration failure
    configdb_watcher_config = configdb_watcher_main.SDPIngestConfig(
        include_existing=False,
        ingest_server_url=INGEST_SERVER_URL,
        ingest_configuration=Configuration(host=INGEST_SERVER_URL),
        storage_server_url=STORAGE_SERVER_URL,
        storage_name="NonExistentStorage",  # <- not registered on DLM side
        storage_root_directory=STORAGE["SRC"]["ROOT_DIRECTORY"],
        migration_destination_storage_name=STORAGE["TGT"]["STORAGE_NAME"],
        migration_configuration=Configuration(host=MIGRATION_SERVER_URL),
    )

    task = asyncio.create_task(configdb_watcher_main.sdp_to_dlm_ingest_and_migrate(configdb_watcher_config))

    try:
        # 1) Wait for watcher to be READY
        ready_msg = "Watcher READY and looking for events."
        for _ in range(50):
            if ready_msg in caplog.text:
                break
            await asyncio.sleep(0.1)
        else:
            pytest.fail("Watcher did not log readiness within timeout")

        # 2) Trigger a COMPLETED Flow
        trigger_completed_flow("test-flow-failure")

        # 3) Wait for the registration failure log
        failure_msg = "DLM registration failed"
        for _ in range(100):  # give it enough time for end-to-end path
            if failure_msg in caplog.text:
                break
            await asyncio.sleep(0.1)
        else:
            pytest.fail("Watcher did not log failed registration within timeout")

        assert "status set to FAILED" in caplog.text

    finally:
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    statuses = _get_dependency_statuses_for_product(PB_ID, "test-flow-failure")
    assert "FAILED" in statuses

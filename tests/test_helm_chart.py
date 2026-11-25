"""Checks for Helm watcher configuration and the test hook."""

import importlib.util
import shutil
import subprocess
from pathlib import Path
from unittest import mock

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(shutil.which("helm") is None, reason="Helm is not installed")


def render_chart(chart: str, *options: str) -> list[dict]:
    """Render a chart without installing it."""
    output = subprocess.check_output(
        ["helm", "template", "client-test", str(ROOT / chart), *options], text=True
    )
    return [document for document in yaml.safe_load_all(output) if document]


@pytest.mark.parametrize("enabled", [False, True])
def test_watchers_receive_request_url_and_migration_mode(enabled):
    """Both watcher deployments receive the configured server options."""
    manifests = render_chart(
        "charts/ska-dlm-client",
        "--set",
        f"configdb_watcher.server_manages_child_migrations={str(enabled).lower()}",
        "--set",
        f"directory_watcher.server_manages_child_migrations={str(enabled).lower()}",
        "--set",
        "configdb_watcher.request_url=http://request-configdb",
        "--set",
        "directory_watcher.request_url=http://request-directory",
    )
    deployments = {
        obj["spec"]["template"]["spec"]["containers"][0]["name"]: obj
        for obj in manifests
        if obj["kind"] == "Deployment"
    }
    for watcher, request_url in (
        ("configdb-watcher", "http://request-configdb"),
        ("directory-watcher", "http://request-directory"),
    ):
        env = {
            entry["name"]: entry["value"]
            for entry in deployments[watcher]["spec"]["template"]["spec"]["containers"][0]["env"]
        }
        assert env["REQUEST_URL"] == request_url
        assert ("SERVER_MANAGES_CHILD_MIGRATIONS" in env) is enabled
        if enabled:
            assert env["SERVER_MANAGES_CHILD_MIGRATIONS"] == "true"


def test_helm_test_hook_uses_script_arguments():
    """The test hook invokes the packaged script with its supported options."""
    chart = "tests/charts/test-ska-dlm-client"
    manifests = render_chart(chart, "-f", str(ROOT / "resources/dp-proj-user.yaml"))
    pod = next(obj for obj in manifests if obj["kind"] == "Pod")
    container = pod["spec"]["containers"][0]
    command = container["command"]
    assert command[:2] == ["/app/.venv/bin/python", "/dlm/setup_dlm.py"]
    assert container["image"].startswith("registry.gitlab.com/ska-telescope/ska-dlm-client/")

    script = ROOT / chart / "scripts/setup_dlm.py"
    spec = importlib.util.spec_from_file_location("helm_setup_dlm", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    args = module.create_parser().parse_args(command[2:])
    assert args.storage_url == "http://ska-dlm-storage.dp-dm"
    assert args.storage_root_directory == "/dlm/watch_dir"

    storage = mock.create_autospec(module.storage_api.StorageApi, instance=True)
    storage.query_storage.return_value = [{"storage_id": "storage-id"}]
    with mock.patch.object(module.api_client, "ApiClient"), mock.patch.object(
        module.storage_api, "StorageApi", return_value=storage
    ):
        module.init_storage_for_testing(
            args.storage_name,
            module.Configuration(host=args.storage_url),
            args.storage_root_directory,
            "location-id",
        )
    storage.create_storage_config.assert_called_once_with(
        request_body={**module.STORAGE_CONFIG, "name": args.storage_name},
        storage_id="storage-id",
        storage_name=args.storage_name,
        config_type="rclone",
    )

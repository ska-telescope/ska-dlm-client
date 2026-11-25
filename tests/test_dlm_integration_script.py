"""Tests for selecting the server revision used by the integration stack."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.fixture(name="integration_workspace")
def make_integration_workspace(tmp_path: Path) -> tuple[Path, Path, str]:
    """Create a small server repository and a client workspace with fake Docker."""
    server = tmp_path / "server"
    server.mkdir()
    subprocess.run(["git", "init", "-q", str(server)], check=True)
    (server / "tests").mkdir()
    compose = server / "tests/dlm.docker-compose.yaml"
    compose.write_text("services: {}\n", encoding="utf-8")

    def commit(message: str) -> str:
        subprocess.run(["git", "-C", str(server), "add", "."], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(server),
                "-c",
                "user.name=Test",
                "-c",
                "user.email=test@example.invalid",
                "commit",
                "-qm",
                message,
            ],
            check=True,
        )
        return subprocess.check_output(
            ["git", "-C", str(server), "rev-parse", "HEAD"], text=True
        ).strip()

    commit("first")
    subprocess.run(["git", "-C", str(server), "tag", "test-release"], check=True)
    compose.write_text("services: {}\n# second revision\n", encoding="utf-8")
    second_commit = commit("second")

    client = tmp_path / "client"
    (client / "scripts").mkdir(parents=True)
    (client / "Makefile").write_text(
        "extract-test-data:\n\t@echo extracted test data\n", encoding="utf-8"
    )
    shutil.copy(
        Path(__file__).parents[1] / "scripts/dlm-integration.sh",
        client / "scripts/dlm-integration.sh",
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    docker = bin_dir / "docker"
    docker.write_text(
        "#!/bin/sh\n"
        'case "$1" in\n'
        '  ps) [ "${FAKE_DOCKER_RUNNING:-0}" = 1 ] && echo running; exit 0 ;;\n'
        '  exec) echo "checking fixture $*"; case "$*" in\n'
        '    *"${FAKE_DOCKER_MISSING_FIXTURE:-no-missing-fixture}"*) exit 1 ;;\n'
        "    *) exit 0 ;; esac ;;\n"
        '  inspect) echo "unhealthy: health probe timed out"; exit 0 ;;\n'
        "  network|volume) exit 1 ;;\n"
        '  compose) case "$*" in *"config --services"*)\n'
        '    printf "%s\\n" dlm_storage dlm_ingest dlm_request dlm_migration '
        "dlm_outbox dlm_rclone_worker rclone-key-init dlm_heuristics ;;\n"
        '    *"config --volumes"*) echo "${FAKE_DOCKER_VOLUME:-shared-tmpfs}" ;;\n'
        '    *" up "*) echo "data volume: $DLM_DATA_VOLUME"; '
        '[ "${FAKE_DOCKER_UP_FAIL:-0}" = 1 ] && exit 17 ;;\n'
        '    *" ps --all -q"*) echo fake-container ;;\n'
        '    *" run "*) echo "running tests" ;;\n'
        "    esac; exit 0 ;;\n"
        "  *) exit 1 ;;\n"
        "esac\n",
        encoding="utf-8",
    )
    docker.chmod(0o755)
    return client, server, second_commit


def run_up(client: Path, server: Path, ref: str | None) -> subprocess.CompletedProcess:
    """Run checkout and startup with Docker commands stubbed out."""
    env = os.environ.copy()
    env["PATH"] = f"{client.parent / 'bin'}{os.pathsep}{env['PATH']}"
    env["DLM_SERVER_REPOSITORY"] = str(server)
    env.pop("DLM_SERVER_REF", None)
    if ref is not None:
        env["DLM_SERVER_REF"] = ref
    return subprocess.run(
        ["bash", str(client / "scripts/dlm-integration.sh"), "up"],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_failed_start_reports_health_diagnostics(
    integration_workspace: tuple[Path, Path, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Startup failures include health output and retain the original exit status."""
    client, server, commit = integration_workspace
    monkeypatch.setenv("FAKE_DOCKER_UP_FAIL", "1")
    result = run_up(client, server, commit)
    assert result.returncode == 17
    assert "unhealthy: health probe timed out" in result.stdout


def test_select_tag_then_commit(integration_workspace: tuple[Path, Path, str]) -> None:
    """Switching revisions checks out the selected commit rather than a stale stack."""
    client, server, second_commit = integration_workspace
    first_commit = subprocess.check_output(
        ["git", "-C", str(server), "rev-parse", "test-release"], text=True
    ).strip()
    first = run_up(client, server, "test-release")
    assert first.returncode == 0, first.stderr
    assert first_commit in first.stdout
    assert "extracted test data" in first.stdout
    second = run_up(client, server, second_commit)
    assert second.returncode == 0, second.stderr
    assert second_commit in second.stdout
    checked_out = subprocess.check_output(
        ["git", "-C", str(client / "build/dlm-server"), "rev-parse", "HEAD"], text=True
    ).strip()
    assert checked_out == second_commit


@pytest.mark.parametrize("volume", ["shared-tmpfs", "data"])
def test_select_server_data_volume(
    integration_workspace: tuple[Path, Path, str], monkeypatch: pytest.MonkeyPatch, volume: str
) -> None:
    """The client mounts the data volume used by the selected server revision."""
    client, server, second_commit = integration_workspace
    monkeypatch.setenv("FAKE_DOCKER_VOLUME", volume)
    result = run_up(client, server, second_commit)
    assert result.returncode == 0, result.stderr
    assert f"data volume: {volume}" in result.stdout


def test_ref_change_preserves_checkout_edits(
    integration_workspace: tuple[Path, Path, str]
) -> None:
    """A ref change must not overwrite edits in the cached server checkout."""
    client, server, second_commit = integration_workspace
    result = run_up(client, server, "test-release")
    assert result.returncode == 0, result.stderr
    compose = client / "build/dlm-server/tests/dlm.docker-compose.yaml"
    compose.write_text("local edits\n", encoding="utf-8")

    result = run_up(client, server, second_commit)
    assert result.returncode != 0
    assert "has local changes" in result.stderr
    assert compose.read_text(encoding="utf-8") == "local edits\n"


def test_run_rejects_mismatched_ref(integration_workspace: tuple[Path, Path, str]) -> None:
    """A running stack must not silently use a different requested revision."""
    client, server, second_commit = integration_workspace
    result = run_up(client, server, "test-release")
    assert result.returncode == 0, result.stderr
    env = os.environ.copy()
    env["PATH"] = f"{client.parent / 'bin'}{os.pathsep}{env['PATH']}"
    env["DLM_SERVER_REF"] = second_commit
    env["FAKE_DOCKER_RUNNING"] = "1"
    result = subprocess.run(
        ["bash", str(client / "scripts/dlm-integration.sh"), "run-integration-test"],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "does not match the running checkout" in result.stderr


@pytest.mark.parametrize("missing_pb", ["24294", "24295"])
def test_run_rejects_missing_fixture(
    integration_workspace: tuple[Path, Path, str], missing_pb: str
) -> None:
    """Missing watcher fixtures fail before pytest creates ConfigDB flows."""
    client, server, second_commit = integration_workspace
    result = run_up(client, server, second_commit)
    assert result.returncode == 0, result.stderr
    env = os.environ.copy()
    env["PATH"] = f"{client.parent / 'bin'}{os.pathsep}{env['PATH']}"
    env["FAKE_DOCKER_RUNNING"] = "1"
    env["FAKE_DOCKER_MISSING_FIXTURE"] = missing_pb
    result = subprocess.run(
        ["bash", str(client / "scripts/dlm-integration.sh"), "run-integration-test"],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "integration fixture missing from the watcher" in result.stderr
    assert "make extract-test-data and restart the stack" in result.stderr
    assert "running tests" not in result.stdout


def test_run_starts_tests_when_fixtures_exist(
    integration_workspace: tuple[Path, Path, str]
) -> None:
    """The running watcher is checked for both fixtures before starting pytest."""
    client, server, second_commit = integration_workspace
    result = run_up(client, server, second_commit)
    assert result.returncode == 0, result.stderr
    env = os.environ.copy()
    env["PATH"] = f"{client.parent / 'bin'}{os.pathsep}{env['PATH']}"
    env["FAKE_DOCKER_RUNNING"] = "1"
    result = subprocess.run(
        ["bash", str(client / "scripts/dlm-integration.sh"), "run-integration-test"],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "pb-test-20260126-24294" in result.stdout
    assert "pb-test-20260126-24295" in result.stdout
    assert "running tests" in result.stdout


@pytest.mark.parametrize("ref", [None, "not-a-tag"])
def test_missing_or_invalid_ref_is_rejected(
    integration_workspace: tuple[Path, Path, str], ref: str | None
) -> None:
    """An unspecified or invalid version never starts a different server."""
    client, server, _ = integration_workspace
    result = run_up(client, server, ref)
    assert result.returncode != 0
    assert "DLM integration:" in result.stderr

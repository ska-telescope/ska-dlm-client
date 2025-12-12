#!/usr/bin/env python
"""Unit tests for the CmdLineParameters class in the startup_verification.utils module."""

import argparse

import pytest

from ska_dlm_client.utils import CmdLineParameters


@pytest.fixture(name="parser")
def parser_fixture() -> argparse.ArgumentParser:
    """Create an ArgumentParser instance for testing.

    :returns: ArgumentParser instance
    """
    return argparse.ArgumentParser(description="Test CmdLineParameters")


def test_cmdline_parameters_initialization(parser: argparse.ArgumentParser) -> None:
    """Test that the CmdLineParameters class can be instantiated with all parameters enabled.

    This test verifies that:
    - The CmdLineParameters class can be instantiated with all parameters set to True
    - All attributes are correctly set to True after initialization

    :param parser: ArgumentParser fixture
    """
    # Test with all parameters enabled
    cmd_params = CmdLineParameters(
        parser=parser,
        add_directory_to_watch=True,
        add_storage_name=True,
        add_ingest_server_url=True,
        add_request_server_url=True,
        add_readiness_probe_file=True,
        add_do_not_perform_actual_ingest_and_migration=True,
        add_dir_updates_wait_time=True,
    )

    # Test that all attributes are set correctly
    assert cmd_params.add_directory_to_watch is True
    assert cmd_params.add_storage_name is True
    assert cmd_params.add_ingest_server_url is True
    assert cmd_params.add_request_server_url is True
    assert cmd_params.add_readiness_probe_file is True
    assert cmd_params.add_dev_test_mode is True
    assert cmd_params.add_do_not_perform_actual_ingest_and_migration is True
    assert cmd_params.add_dir_updates_wait_time is True


def test_cmdline_parameters_default_values(parser: argparse.ArgumentParser) -> None:
    """Test that the CmdLineParameters class initializes with correct default values.

    This test verifies that:
    - The CmdLineParameters class can be instantiated with default parameters
    - All attributes are correctly set to their default values (False)

    :param parser: ArgumentParser fixture
    """
    # Initialize with default values (all False)
    cmd_params = CmdLineParameters(parser=parser)

    # Test that all attributes are set to their default values
    assert cmd_params.add_directory_to_watch is False
    assert cmd_params.add_storage_name is False
    assert cmd_params.add_ingest_server_url is False
    assert cmd_params.add_request_server_url is False
    assert cmd_params.add_readiness_probe_file is False

    # Check if attributes exist, if not, they're expected to be False by default
    # when initialized with their respective parameters set to False
    assert getattr(cmd_params, "add_dev_test_mode", False) is False
    assert getattr(cmd_params, "add_do_not_perform_actual_ingest_and_migration", False) is False


@pytest.fixture(name="cmd_params_all_enabled")
def cmd_params_all_enabled_fixture(parser: argparse.ArgumentParser) -> CmdLineParameters:
    """Create a CmdLineParameters instance with all parameters enabled.

    :param parser: ArgumentParser fixture
    :returns: CmdLineParameters instance with all parameters enabled
    """
    return CmdLineParameters(
        parser=parser,
        add_directory_to_watch=True,
        add_storage_name=True,
        add_ingest_server_url=True,
        add_request_server_url=True,
        add_readiness_probe_file=True,
        add_do_not_perform_actual_ingest_and_migration=True,
        add_dir_updates_wait_time=True,
    )


@pytest.fixture(name="test_args")
def test_args_fixture() -> argparse.Namespace:
    """Create a test Namespace with sample argument values.

    :returns: Namespace with test argument values
    """
    return argparse.Namespace(
        directory_to_watch="/test/dir",
        storage_name="test-storage",
        ingest_server_url="http://ingest-server:8080",
        migration_server_url="http://migration-server:8080",
        request_server_url="http://request-server:8080",
        readiness_probe_file="/tmp/ready",
        migration_destination_storage_name="dest-storage",
        dev_test_mode=True,
        do_not_perform_actual_ingest_and_migration=True,
        dir_updates_wait_time=30,
    )


def test_parse_arguments(
    cmd_params_all_enabled: CmdLineParameters, test_args: argparse.Namespace
) -> None:
    """Test that arguments are correctly parsed and assigned to class attributes.

    This test verifies that:
    - The parse_arguments method correctly processes the provided arguments
    - All class attributes are set to the expected values after parsing

    :param cmd_params_all_enabled: CmdLineParameters fixture with all parameters enabled
    :param test_args: Namespace fixture with test argument values
    """
    # Parse the arguments
    cmd_params_all_enabled.parse_arguments(test_args)

    # Verify the parsed values
    assert cmd_params_all_enabled.directory_to_watch == "/test/dir"
    assert cmd_params_all_enabled.storage_name == "test-storage"
    assert cmd_params_all_enabled.ingest_server_url == "http://ingest-server:8080"
    assert cmd_params_all_enabled.request_server_url == "http://request-server:8080"
    assert cmd_params_all_enabled.readiness_probe_file == "/tmp/ready"
    assert cmd_params_all_enabled.dev_test_mode is True
    assert cmd_params_all_enabled.do_not_perform_actual_ingest_and_migration is True
    assert cmd_params_all_enabled.dir_updates_wait_time == 30
    # Verify that perform_actual_ingest_and_migration is set correctly
    assert cmd_params_all_enabled.perform_actual_ingest_and_migration is False


def test_do_not_perform_requires_dev_test_mode(cmd_params_all_enabled: CmdLineParameters) -> None:
    """Test that do_not_perform_actual_ingest_and_migration requires dev_test_mode to be True.

    This test verifies that a ValueError is raised when do_not_perform_actual_ingest_and_migration
    is True and dev_test_mode is False.

    :param cmd_params_all_enabled: CmdLineParameters fixture with all parameters enabled
    """
    # Create args with dev_test_mode=False and do_not_perform_actual_ingest_and_migration=True
    args = argparse.Namespace(
        directory_to_watch="/test/dir",
        storage_name="test-storage",
        ingest_server_url="http://ingest-server:8080",
        migration_server_url="http://migration-server:8080",
        request_server_url="http://request-server:8080",
        readiness_probe_file="/tmp/ready",
        migration_destination_storage_name="dest-storage",
        dev_test_mode=False,
        do_not_perform_actual_ingest_and_migration=True,
        dir_updates_wait_time=30,
    )

    # Verify that a ValueError is raised
    with pytest.raises(
        ValueError,
        match=(
            "do_not_perform_actual_ingest_and_migration can only be used when "
            "dev_test_mode is True"
        ),
    ):
        cmd_params_all_enabled.parse_arguments(args)

def test_perform_actual_ingest_and_migration_setting(
    cmd_params_all_enabled: CmdLineParameters,
) -> None:
    """Test that perform_actual_ingest_and_migration is set correctly.

    This test verifies that perform_actual_ingest_and_migration is set to False when
    do_not_perform_actual_ingest_and_migration is True, and set to True when
    do_not_perform_actual_ingest_and_migration is False.

    :param cmd_params_all_enabled: CmdLineParameters fixture with all parameters enabled
    """
    # Test when do_not_perform_actual_ingest_and_migration is True
    args_true = argparse.Namespace(
        directory_to_watch="/test/dir",
        storage_name="test-storage",
        ingest_server_url="http://ingest-server:8080",
        request_server_url="http://request-server:8080",
        readiness_probe_file="/tmp/ready",
        migration_destination_storage_name="dest-storage",
        migration_server_url="http://migration-server:8080",
        dev_test_mode=True,
        do_not_perform_actual_ingest_and_migration=True,
        dir_updates_wait_time=30,
    )
    cmd_params_all_enabled.parse_arguments(args_true)
    assert cmd_params_all_enabled.do_not_perform_actual_ingest_and_migration is True
    assert cmd_params_all_enabled.perform_actual_ingest_and_migration is False

    # Test when do_not_perform_actual_ingest_and_migration is False
    args_false = argparse.Namespace(
        directory_to_watch="/test/dir",
        storage_name="test-storage",
        ingest_server_url="http://ingest-server:8080",
        request_server_url="http://request-server:8080",
        readiness_probe_file="/tmp/ready",
        migration_destination_storage_name="dest-storage",
        migration_server_url="http://migration-server:8080",
        dev_test_mode=True,
        do_not_perform_actual_ingest_and_migration=False,
        dir_updates_wait_time=30,
    )
    cmd_params_all_enabled.parse_arguments(args_false)
    assert cmd_params_all_enabled.do_not_perform_actual_ingest_and_migration is False
    assert cmd_params_all_enabled.perform_actual_ingest_and_migration is True

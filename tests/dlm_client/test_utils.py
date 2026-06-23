#!/usr/bin/env python
"""Unit tests for the CmdLineParameters class in the startup_verification.utils module."""

import argparse

import pytest


@pytest.fixture(name="parser")
def parser_fixture() -> argparse.ArgumentParser:
    """Create an ArgumentParser instance for testing.

    :returns: ArgumentParser instance
    """
    return argparse.ArgumentParser(description="Test CmdLineParameters")


@pytest.fixture(name="test_args")
def test_args_fixture() -> argparse.Namespace:
    """Create a test Namespace with sample argument values.

    :returns: Namespace with test argument values
    """
    return argparse.Namespace(
        directory_to_watch="/test/dir",
        storage_name="test-storage",
        ingest_url="http://ingest-server:8080",
        migration_url="http://migration-server:8080",
        request_url="http://request-server:8080",
        readiness_probe_file="/tmp/ready",
        target_name="dest-storage",
        dir_updates_wait_time=30,
    )

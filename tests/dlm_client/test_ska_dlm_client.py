#!/usr/bin/env python

"""Tests for `ska_dlm_client` package."""

import pytest

import ska_dlm_client


# This is a sample pytest test fixture
# See more at: http://doc.pytest.org/en/latest/fixture.html
@pytest.fixture(name="version")
def version_fixture() -> str:
    """Return the package's version string.

    :returns: package version string
    """
    return ska_dlm_client.__version__


# This is a sample pytest test function with the pytest fixture as an argument.
def test_content(version: str) -> None:
    """
    Check that the package version is as expected.

    :param version: the version fixture
    """
    assert version == "1.1.0"

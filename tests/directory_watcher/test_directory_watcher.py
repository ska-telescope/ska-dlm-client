"""Tests for directory watcher."""

import unittest

import pytest_asyncio


@pytest_asyncio.fixture(name="producer")
async def producer_fixture():
    """Fixture to set up and tear down a Kafka producer."""
    # p = "a"
    # await p.start()
    # yield p
    # await p.stop()


class TestIngestApi(unittest.TestCase):
    """IngestApi unit test stubs."""

    # def setUp(self) -> None:
    #    self.api = IngestApi()

    def tearDown(self) -> None:
        """Tear down this setup."""

    def test_init_data_item_ingest_init_data_item_post(self) -> None:
        """Test case for init_data_item_ingest_init_data_item_post.

        Init Data Item
        """

    def test_register_data_item_ingest_register_data_item_post(self) -> None:
        """Test case for register_data_item_ingest_register_data_item_post.

        Register Data Item
        """


if __name__ == "__main__":
    unittest.main()

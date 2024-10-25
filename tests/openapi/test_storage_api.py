# coding: utf-8

"""merged spec

merged spec

The version of the OpenAPI document: 1.0.0
Generated by OpenAPI Generator (https://openapi-generator.tech)

Do not edit the class manually.
"""
# noqa: E501


import unittest

from ska_dlm_client.openapi.dlm_api.storage_api import StorageApi


class TestStorageApi(unittest.TestCase):
    """StorageApi unit test stubs"""

    def setUp(self) -> None:
        self.api = StorageApi()

    def tearDown(self) -> None:
        pass

    def test_create_storage_config_storage_create_storage_config_post(self) -> None:
        """Test case for create_storage_config_storage_create_storage_config_post

        Create Storage Config
        """
        pass

    def test_get_storage_config_storage_get_storage_config_get(self) -> None:
        """Test case for get_storage_config_storage_get_storage_config_get

        Get Storage Config
        """
        pass

    def test_init_location_storage_init_location_post(self) -> None:
        """Test case for init_location_storage_init_location_post

        Init Location
        """
        pass

    def test_init_storage_storage_init_storage_post(self) -> None:
        """Test case for init_storage_storage_init_storage_post

        Init Storage
        """
        pass

    def test_query_location_storage_query_location_get(self) -> None:
        """Test case for query_location_storage_query_location_get

        Query Location
        """
        pass

    def test_query_storage_storage_query_storage_get(self) -> None:
        """Test case for query_storage_storage_query_storage_get

        Query Storage
        """
        pass

    def test_rclone_config_storage_rclone_config_post(self) -> None:
        """Test case for rclone_config_storage_rclone_config_post

        Rclone Config
        """
        pass


if __name__ == "__main__":
    unittest.main()

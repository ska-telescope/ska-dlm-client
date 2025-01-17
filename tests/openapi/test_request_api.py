# coding: utf-8

"""merged spec

merged spec

The version of the OpenAPI document: 1.0.0
Generated by OpenAPI Generator (https://openapi-generator.tech)

Do not edit the class manually.
"""
# noqa: E501


import unittest

from ska_dlm_client.openapi.dlm_api.request_api import RequestApi


class TestRequestApi(unittest.TestCase):
    """RequestApi unit test stubs"""

    def setUp(self) -> None:
        self.api = RequestApi()

    def tearDown(self) -> None:
        pass

    def test_query_data_item_request_query_data_item_get(self) -> None:
        """Test case for query_data_item_request_query_data_item_get

        Query Data Item
        """
        pass

    def test_query_deleted_request_query_deleted_get(self) -> None:
        """Test case for query_deleted_request_query_deleted_get

        Query Deleted
        """
        pass

    def test_query_exists_and_ready_request_query_exist_and_ready_get(self) -> None:
        """Test case for query_exists_and_ready_request_query_exist_and_ready_get

        Query Exists And Ready
        """
        pass

    def test_query_exists_request_query_exists_get(self) -> None:
        """Test case for query_exists_request_query_exists_get

        Query Exists
        """
        pass

    def test_query_expired_request_query_expired_get(self) -> None:
        """Test case for query_expired_request_query_expired_get

        Query Expired
        """
        pass

    def test_query_item_storage_request_query_item_storage_get(self) -> None:
        """Test case for query_item_storage_request_query_item_storage_get

        Query Item Storage
        """
        pass

    def test_query_new_request_query_new_get(self) -> None:
        """Test case for query_new_request_query_new_get

        Query New
        """
        pass


if __name__ == "__main__":
    unittest.main()

# coding: utf-8

"""
    merged spec

    merged spec

    The version of the OpenAPI document: 1.0.0
    Generated by OpenAPI Generator (https://openapi-generator.tech)

    Do not edit the class manually.
"""  # noqa: E501


import unittest

from ska_dlm_client.openapi.dlm_api.gateway_api import GatewayApi


class TestGatewayApi(unittest.TestCase):
    """GatewayApi unit test stubs"""

    def setUp(self) -> None:
        self.api = GatewayApi()

    def tearDown(self) -> None:
        pass

    def test_auth_callback_auth_callback_get(self) -> None:
        """Test case for auth_callback_auth_callback_get

        Auth Callback
        """
        pass

    def test_end_session_end_session_post(self) -> None:
        """Test case for end_session_end_session_post

        End Session
        """
        pass

    def test_has_scope_scope_get(self) -> None:
        """Test case for has_scope_scope_get

        Has Scope
        """
        pass

    def test_heartbeat_heartbeat_get(self) -> None:
        """Test case for heartbeat_heartbeat_get

        Heartbeat
        """
        pass

    def test_session_start_session_post(self) -> None:
        """Test case for session_start_session_post

        Session
        """
        pass

    def test_token_by_auth_flow_token_by_auth_flow_get(self) -> None:
        """Test case for token_by_auth_flow_token_by_auth_flow_get

        Token By Auth Flow
        """
        pass

    def test_token_by_username_password_token_by_username_password_get(self) -> None:
        """Test case for token_by_username_password_token_by_username_password_get

        Token By Username Password
        """
        pass


if __name__ == "__main__":
    unittest.main()

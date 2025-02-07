# coding: utf-8

"""merged spec

merged spec

The version of the OpenAPI document: 1.0.0
Generated by OpenAPI Generator (https://openapi-generator.tech)

Do not edit the class manually.
"""
# noqa: E501

import warnings
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import Field, StrictFloat, StrictInt, StrictStr, validate_call
from typing_extensions import Annotated

from ska_dlm_client.openapi.api_client import ApiClient, RequestSerialized
from ska_dlm_client.openapi.api_response import ApiResponse
from ska_dlm_client.openapi.rest import RESTResponseType


class MigrationApi:
    """NOTE: This class is auto generated by OpenAPI Generator
    Ref: https://openapi-generator.tech

    Do not edit the class manually.
    """

    def __init__(self, api_client=None) -> None:
        if api_client is None:
            api_client = ApiClient.get_default()
        self.api_client = api_client

    @validate_call
    def copy_data_item(
        self,
        item_name: Annotated[
            Optional[StrictStr],
            Field(
                description='data item name, when empty the first 1000 items are returned, by default ""'
            ),
        ] = None,
        oid: Annotated[
            Optional[StrictStr],
            Field(
                description='object id, Return data_items referred to by the OID provided, by default ""'
            ),
        ] = None,
        uid: Annotated[
            Optional[StrictStr],
            Field(description='Return data_item referred to by the UID provided, by default ""'),
        ] = None,
        destination_name: Annotated[
            Optional[StrictStr],
            Field(description='the name of the destination storage volume, by default ""'),
        ] = None,
        destination_id: Annotated[
            Optional[StrictStr], Field(description='the destination storage, by default ""')
        ] = None,
        path: Annotated[
            Optional[StrictStr],
            Field(description='the destination path relative to storage root, by default ""'),
        ] = None,
        authorization: Annotated[
            Optional[StrictStr], Field(description="Validated Bearer token with UserInfo")
        ] = None,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[Annotated[StrictFloat, Field(gt=0)], Annotated[StrictFloat, Field(gt=0)]],
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> object:
        """Copy Data Item

        Copy a data_item from source to destination.  Steps (1) get the current storage_id(s) of the item (2) convert one (first) storage_id to a configured rclone backend (3) initialize the new item with the same OID on the new storage (4) use the rclone copy command to copy it to the new location (5) make sure the copy was successful

        Parameters
        ----------
        item_name : str
            data item name, when empty the first 1000 items are
            returned, by default \"\"
        oid : str
            object id, Return data_items referred to by the OID
            provided, by default \"\"
        uid : str
            Return data_item referred to by the UID provided, by default
            \"\"
        destination_name : str
            the name of the destination storage volume, by default \"\"
        destination_id : str
            the destination storage, by default \"\"
        path : str
            the destination path relative to storage root, by default
            \"\"
        authorization : str
            Validated Bearer token with UserInfo
        _request_timeout : int, tuple(int, int), optional
            timeout setting for this request. If one number provided, it
            will be total request timeout. It can also be a pair (tuple)
            of (connection, read) timeouts.
        _request_auth : dict, optional
            set to override the auth_settings for an a single request;
            this effectively ignores the authentication in the spec for
            a single request.
        _content_type : str, Optional
            force content-type for the request.
        _headers : dict, optional
            set to override the headers for a single request; this
            effectively ignores the headers in the spec for a single
            request.
        _host_index : int, optional
            set to override the host_index for a single request; this
            effectively ignores the host_index in the spec for a single
            request.

        Returns
        -------
        unknown
            Returns the result object.
        """
        # noqa: E501

        _param = self._copy_data_item_serialize(
            item_name=item_name,
            oid=oid,
            uid=uid,
            destination_name=destination_name,
            destination_id=destination_id,
            path=path,
            authorization=authorization,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index,
        )

        _response_types_map: Dict[str, Optional[str]] = {
            "200": "object",
            "422": "HTTPValidationError",
        }
        response_data = self.api_client.call_api(*_param, _request_timeout=_request_timeout)
        response_data.read()
        return self.api_client.response_deserialize(
            response_data=response_data,
            response_types_map=_response_types_map,
        ).data

    @validate_call
    def copy_data_item_with_http_info(
        self,
        item_name: Annotated[
            Optional[StrictStr],
            Field(
                description='data item name, when empty the first 1000 items are returned, by default ""'
            ),
        ] = None,
        oid: Annotated[
            Optional[StrictStr],
            Field(
                description='object id, Return data_items referred to by the OID provided, by default ""'
            ),
        ] = None,
        uid: Annotated[
            Optional[StrictStr],
            Field(description='Return data_item referred to by the UID provided, by default ""'),
        ] = None,
        destination_name: Annotated[
            Optional[StrictStr],
            Field(description='the name of the destination storage volume, by default ""'),
        ] = None,
        destination_id: Annotated[
            Optional[StrictStr], Field(description='the destination storage, by default ""')
        ] = None,
        path: Annotated[
            Optional[StrictStr],
            Field(description='the destination path relative to storage root, by default ""'),
        ] = None,
        authorization: Annotated[
            Optional[StrictStr], Field(description="Validated Bearer token with UserInfo")
        ] = None,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[Annotated[StrictFloat, Field(gt=0)], Annotated[StrictFloat, Field(gt=0)]],
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> ApiResponse[object]:
        """Copy Data Item

        Copy a data_item from source to destination.  Steps (1) get the current storage_id(s) of the item (2) convert one (first) storage_id to a configured rclone backend (3) initialize the new item with the same OID on the new storage (4) use the rclone copy command to copy it to the new location (5) make sure the copy was successful

        Parameters
        ----------
        item_name : str
            data item name, when empty the first 1000 items are
            returned, by default \"\"
        oid : str
            object id, Return data_items referred to by the OID
            provided, by default \"\"
        uid : str
            Return data_item referred to by the UID provided, by default
            \"\"
        destination_name : str
            the name of the destination storage volume, by default \"\"
        destination_id : str
            the destination storage, by default \"\"
        path : str
            the destination path relative to storage root, by default
            \"\"
        authorization : str
            Validated Bearer token with UserInfo
        _request_timeout : int, tuple(int, int), optional
            timeout setting for this request. If one number provided, it
            will be total request timeout. It can also be a pair (tuple)
            of (connection, read) timeouts.
        _request_auth : dict, optional
            set to override the auth_settings for an a single request;
            this effectively ignores the authentication in the spec for
            a single request.
        _content_type : str, Optional
            force content-type for the request.
        _headers : dict, optional
            set to override the headers for a single request; this
            effectively ignores the headers in the spec for a single
            request.
        _host_index : int, optional
            set to override the host_index for a single request; this
            effectively ignores the host_index in the spec for a single
            request.

        Returns
        -------
        unknown
            Returns the result object.
        """
        # noqa: E501

        _param = self._copy_data_item_serialize(
            item_name=item_name,
            oid=oid,
            uid=uid,
            destination_name=destination_name,
            destination_id=destination_id,
            path=path,
            authorization=authorization,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index,
        )

        _response_types_map: Dict[str, Optional[str]] = {
            "200": "object",
            "422": "HTTPValidationError",
        }
        response_data = self.api_client.call_api(*_param, _request_timeout=_request_timeout)
        response_data.read()
        return self.api_client.response_deserialize(
            response_data=response_data,
            response_types_map=_response_types_map,
        )

    @validate_call
    def copy_data_item_without_preload_content(
        self,
        item_name: Annotated[
            Optional[StrictStr],
            Field(
                description='data item name, when empty the first 1000 items are returned, by default ""'
            ),
        ] = None,
        oid: Annotated[
            Optional[StrictStr],
            Field(
                description='object id, Return data_items referred to by the OID provided, by default ""'
            ),
        ] = None,
        uid: Annotated[
            Optional[StrictStr],
            Field(description='Return data_item referred to by the UID provided, by default ""'),
        ] = None,
        destination_name: Annotated[
            Optional[StrictStr],
            Field(description='the name of the destination storage volume, by default ""'),
        ] = None,
        destination_id: Annotated[
            Optional[StrictStr], Field(description='the destination storage, by default ""')
        ] = None,
        path: Annotated[
            Optional[StrictStr],
            Field(description='the destination path relative to storage root, by default ""'),
        ] = None,
        authorization: Annotated[
            Optional[StrictStr], Field(description="Validated Bearer token with UserInfo")
        ] = None,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[Annotated[StrictFloat, Field(gt=0)], Annotated[StrictFloat, Field(gt=0)]],
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> RESTResponseType:
        """Copy Data Item

        Copy a data_item from source to destination.  Steps (1) get the current storage_id(s) of the item (2) convert one (first) storage_id to a configured rclone backend (3) initialize the new item with the same OID on the new storage (4) use the rclone copy command to copy it to the new location (5) make sure the copy was successful

        Parameters
        ----------
        item_name : str
            data item name, when empty the first 1000 items are
            returned, by default \"\"
        oid : str
            object id, Return data_items referred to by the OID
            provided, by default \"\"
        uid : str
            Return data_item referred to by the UID provided, by default
            \"\"
        destination_name : str
            the name of the destination storage volume, by default \"\"
        destination_id : str
            the destination storage, by default \"\"
        path : str
            the destination path relative to storage root, by default
            \"\"
        authorization : str
            Validated Bearer token with UserInfo
        _request_timeout : int, tuple(int, int), optional
            timeout setting for this request. If one number provided, it
            will be total request timeout. It can also be a pair (tuple)
            of (connection, read) timeouts.
        _request_auth : dict, optional
            set to override the auth_settings for an a single request;
            this effectively ignores the authentication in the spec for
            a single request.
        _content_type : str, Optional
            force content-type for the request.
        _headers : dict, optional
            set to override the headers for a single request; this
            effectively ignores the headers in the spec for a single
            request.
        _host_index : int, optional
            set to override the host_index for a single request; this
            effectively ignores the host_index in the spec for a single
            request.

        Returns
        -------
        unknown
            Returns the result object.
        """
        # noqa: E501

        _param = self._copy_data_item_serialize(
            item_name=item_name,
            oid=oid,
            uid=uid,
            destination_name=destination_name,
            destination_id=destination_id,
            path=path,
            authorization=authorization,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index,
        )

        _response_types_map: Dict[str, Optional[str]] = {
            "200": "object",
            "422": "HTTPValidationError",
        }
        response_data = self.api_client.call_api(*_param, _request_timeout=_request_timeout)
        return response_data.response

    def _copy_data_item_serialize(
        self,
        item_name,
        oid,
        uid,
        destination_name,
        destination_id,
        path,
        authorization,
        _request_auth,
        _content_type,
        _headers,
        _host_index,
    ) -> RequestSerialized:

        _host = None

        _collection_formats: Dict[str, str] = {}

        _path_params: Dict[str, str] = {}
        _query_params: List[Tuple[str, str]] = []
        _header_params: Dict[str, Optional[str]] = _headers or {}
        _form_params: List[Tuple[str, str]] = []
        _files: Dict[str, Union[str, bytes, List[str], List[bytes], List[Tuple[str, bytes]]]] = {}
        _body_params: Optional[bytes] = None

        # process the path parameters
        # process the query parameters
        if item_name is not None:

            _query_params.append(("item_name", item_name))

        if oid is not None:

            _query_params.append(("oid", oid))

        if uid is not None:

            _query_params.append(("uid", uid))

        if destination_name is not None:

            _query_params.append(("destination_name", destination_name))

        if destination_id is not None:

            _query_params.append(("destination_id", destination_id))

        if path is not None:

            _query_params.append(("path", path))

        # process the header parameters
        if authorization is not None:
            _header_params["authorization"] = authorization
        # process the form parameters
        # process the body parameter

        # set the HTTP header `Accept`
        if "Accept" not in _header_params:
            _header_params["Accept"] = self.api_client.select_header_accept(["application/json"])

        # authentication setting
        _auth_settings: List[str] = []

        return self.api_client.param_serialize(
            method="POST",
            resource_path="/migration/copy_data_item",
            path_params=_path_params,
            query_params=_query_params,
            header_params=_header_params,
            body=_body_params,
            post_params=_form_params,
            files=_files,
            auth_settings=_auth_settings,
            collection_formats=_collection_formats,
            _host=_host,
            _request_auth=_request_auth,
        )

    @validate_call
    def query_migrations(
        self,
        authorization: Annotated[
            Optional[StrictStr], Field(description="Validated Bearer token with UserInfo")
        ] = None,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[Annotated[StrictFloat, Field(gt=0)], Annotated[StrictFloat, Field(gt=0)]],
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> List[Optional[object]]:
        """Query Migrations

        Query for all migrations by a given user.

        Parameters
        ----------
        authorization : str
            Validated Bearer token with UserInfo
        _request_timeout : int, tuple(int, int), optional
            timeout setting for this request. If one number provided, it
            will be total request timeout. It can also be a pair (tuple)
            of (connection, read) timeouts.
        _request_auth : dict, optional
            set to override the auth_settings for an a single request;
            this effectively ignores the authentication in the spec for
            a single request.
        _content_type : str, Optional
            force content-type for the request.
        _headers : dict, optional
            set to override the headers for a single request; this
            effectively ignores the headers in the spec for a single
            request.
        _host_index : int, optional
            set to override the host_index for a single request; this
            effectively ignores the host_index in the spec for a single
            request.

        Returns
        -------
        unknown
            Returns the result object.
        """
        # noqa: E501

        _param = self._query_migrations_serialize(
            authorization=authorization,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index,
        )

        _response_types_map: Dict[str, Optional[str]] = {
            "200": "List[Optional[object]]",
            "422": "HTTPValidationError",
        }
        response_data = self.api_client.call_api(*_param, _request_timeout=_request_timeout)
        response_data.read()
        return self.api_client.response_deserialize(
            response_data=response_data,
            response_types_map=_response_types_map,
        ).data

    @validate_call
    def query_migrations_with_http_info(
        self,
        authorization: Annotated[
            Optional[StrictStr], Field(description="Validated Bearer token with UserInfo")
        ] = None,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[Annotated[StrictFloat, Field(gt=0)], Annotated[StrictFloat, Field(gt=0)]],
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> ApiResponse[List[Optional[object]]]:
        """Query Migrations

        Query for all migrations by a given user.

        Parameters
        ----------
        authorization : str
            Validated Bearer token with UserInfo
        _request_timeout : int, tuple(int, int), optional
            timeout setting for this request. If one number provided, it
            will be total request timeout. It can also be a pair (tuple)
            of (connection, read) timeouts.
        _request_auth : dict, optional
            set to override the auth_settings for an a single request;
            this effectively ignores the authentication in the spec for
            a single request.
        _content_type : str, Optional
            force content-type for the request.
        _headers : dict, optional
            set to override the headers for a single request; this
            effectively ignores the headers in the spec for a single
            request.
        _host_index : int, optional
            set to override the host_index for a single request; this
            effectively ignores the host_index in the spec for a single
            request.

        Returns
        -------
        unknown
            Returns the result object.
        """
        # noqa: E501

        _param = self._query_migrations_serialize(
            authorization=authorization,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index,
        )

        _response_types_map: Dict[str, Optional[str]] = {
            "200": "List[Optional[object]]",
            "422": "HTTPValidationError",
        }
        response_data = self.api_client.call_api(*_param, _request_timeout=_request_timeout)
        response_data.read()
        return self.api_client.response_deserialize(
            response_data=response_data,
            response_types_map=_response_types_map,
        )

    @validate_call
    def query_migrations_without_preload_content(
        self,
        authorization: Annotated[
            Optional[StrictStr], Field(description="Validated Bearer token with UserInfo")
        ] = None,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[Annotated[StrictFloat, Field(gt=0)], Annotated[StrictFloat, Field(gt=0)]],
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> RESTResponseType:
        """Query Migrations

        Query for all migrations by a given user.

        Parameters
        ----------
        authorization : str
            Validated Bearer token with UserInfo
        _request_timeout : int, tuple(int, int), optional
            timeout setting for this request. If one number provided, it
            will be total request timeout. It can also be a pair (tuple)
            of (connection, read) timeouts.
        _request_auth : dict, optional
            set to override the auth_settings for an a single request;
            this effectively ignores the authentication in the spec for
            a single request.
        _content_type : str, Optional
            force content-type for the request.
        _headers : dict, optional
            set to override the headers for a single request; this
            effectively ignores the headers in the spec for a single
            request.
        _host_index : int, optional
            set to override the host_index for a single request; this
            effectively ignores the host_index in the spec for a single
            request.

        Returns
        -------
        unknown
            Returns the result object.
        """
        # noqa: E501

        _param = self._query_migrations_serialize(
            authorization=authorization,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index,
        )

        _response_types_map: Dict[str, Optional[str]] = {
            "200": "List[Optional[object]]",
            "422": "HTTPValidationError",
        }
        response_data = self.api_client.call_api(*_param, _request_timeout=_request_timeout)
        return response_data.response

    def _query_migrations_serialize(
        self,
        authorization,
        _request_auth,
        _content_type,
        _headers,
        _host_index,
    ) -> RequestSerialized:

        _host = None

        _collection_formats: Dict[str, str] = {}

        _path_params: Dict[str, str] = {}
        _query_params: List[Tuple[str, str]] = []
        _header_params: Dict[str, Optional[str]] = _headers or {}
        _form_params: List[Tuple[str, str]] = []
        _files: Dict[str, Union[str, bytes, List[str], List[bytes], List[Tuple[str, bytes]]]] = {}
        _body_params: Optional[bytes] = None

        # process the path parameters
        # process the query parameters
        # process the header parameters
        if authorization is not None:
            _header_params["authorization"] = authorization
        # process the form parameters
        # process the body parameter

        # set the HTTP header `Accept`
        if "Accept" not in _header_params:
            _header_params["Accept"] = self.api_client.select_header_accept(["application/json"])

        # authentication setting
        _auth_settings: List[str] = []

        return self.api_client.param_serialize(
            method="GET",
            resource_path="/migration/query_migrations",
            path_params=_path_params,
            query_params=_query_params,
            header_params=_header_params,
            body=_body_params,
            post_params=_form_params,
            files=_files,
            auth_settings=_auth_settings,
            collection_formats=_collection_formats,
            _host=_host,
            _request_auth=_request_auth,
        )

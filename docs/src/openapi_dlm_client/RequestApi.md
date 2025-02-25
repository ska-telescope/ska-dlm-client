# ska_dlm_client.openapi.RequestApi

All URIs are relative to *http://localhost:8080*

Method | HTTP request | Description
------------- | ------------- | -------------
[**query_data_item**](RequestApi.md#query_data_item) | **GET** /request/query_data_item | Query Data Item
[**query_deleted**](RequestApi.md#query_deleted) | **GET** /request/query_deleted | Query Deleted
[**query_exists**](RequestApi.md#query_exists) | **GET** /request/query_exists | Query Exists
[**query_exists_and_ready**](RequestApi.md#query_exists_and_ready) | **GET** /request/query_exist_and_ready | Query Exists And Ready
[**query_expired**](RequestApi.md#query_expired) | **GET** /request/query_expired | Query Expired
[**query_item_storage**](RequestApi.md#query_item_storage) | **GET** /request/query_item_storage | Query Item Storage
[**query_new**](RequestApi.md#query_new) | **GET** /request/query_new | Query New
[**set_acl**](RequestApi.md#set_acl) | **PATCH** /request/set_acl | Set Acl
[**set_group**](RequestApi.md#set_group) | **PATCH** /request/set_group | Set Group
[**set_metadata**](RequestApi.md#set_metadata) | **PATCH** /request/set_metadata | Set Metadata
[**set_oid_expiration**](RequestApi.md#set_oid_expiration) | **PATCH** /request/set_oid_expiration | Set Oid Expiration
[**set_phase**](RequestApi.md#set_phase) | **PATCH** /request/set_phase | Set Phase
[**set_state**](RequestApi.md#set_state) | **PATCH** /request/set_state | Set State
[**set_uid_expiration**](RequestApi.md#set_uid_expiration) | **PATCH** /request/set_uid_expiration | Set Uid Expiration
[**set_uri**](RequestApi.md#set_uri) | **PATCH** /request/set_uri | Set Uri
[**set_user**](RequestApi.md#set_user) | **PATCH** /request/set_user | Set User
[**update_data_item**](RequestApi.md#update_data_item) | **PATCH** /request/update_data_item | Update Data Item
[**update_item_tags**](RequestApi.md#update_item_tags) | **PATCH** /request/update_item_tags | Update Item Tags


# **query_data_item**
> List[Optional[object]] query_data_item(item_name=item_name, oid=oid, uid=uid, storage_id=storage_id, params=params)

Query Data Item

Query a data_item.  At least one of item_name, oid, uid, or params is required.

### Example


```python
import ska_dlm_client.openapi
from ska_dlm_client.openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost:8080
# See configuration.py for a list of all supported configuration parameters.
configuration = ska_dlm_client.openapi.Configuration(
    host = "http://localhost:8080"
)


# Enter a context with an instance of the API client
with ska_dlm_client.openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = ska_dlm_client.openapi.RequestApi(api_client)
    item_name = '' # str | could be empty, in which case the first 1000 items are returned. (optional) (default to '')
    oid = '' # str | Return data_items referred to by the OID provided. (optional) (default to '')
    uid = '' # str | Return data_item referred to by the UID provided. (optional) (default to '')
    storage_id = '' # str | Return data_item referred to by a given storage_id. (optional) (default to '')
    params = 'params_example' # str | specify the query parameters (optional)

    try:
        # Query Data Item
        api_response = api_instance.query_data_item(item_name=item_name, oid=oid, uid=uid, storage_id=storage_id, params=params)
        print("The response of RequestApi->query_data_item:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling RequestApi->query_data_item: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **item_name** | **str**| could be empty, in which case the first 1000 items are returned. | [optional] [default to &#39;&#39;]
 **oid** | **str**| Return data_items referred to by the OID provided. | [optional] [default to &#39;&#39;]
 **uid** | **str**| Return data_item referred to by the UID provided. | [optional] [default to &#39;&#39;]
 **storage_id** | **str**| Return data_item referred to by a given storage_id. | [optional] [default to &#39;&#39;]
 **params** | **str**| specify the query parameters | [optional] 

### Return type

**List[Optional[object]]**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **query_deleted**
> List[Optional[object]] query_deleted(uid=uid)

Query Deleted

Query for all deleted data_items using the deleted state.

### Example


```python
import ska_dlm_client.openapi
from ska_dlm_client.openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost:8080
# See configuration.py for a list of all supported configuration parameters.
configuration = ska_dlm_client.openapi.Configuration(
    host = "http://localhost:8080"
)


# Enter a context with an instance of the API client
with ska_dlm_client.openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = ska_dlm_client.openapi.RequestApi(api_client)
    uid = '' # str | The UID to be checked, optional. (optional) (default to '')

    try:
        # Query Deleted
        api_response = api_instance.query_deleted(uid=uid)
        print("The response of RequestApi->query_deleted:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling RequestApi->query_deleted: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **uid** | **str**| The UID to be checked, optional. | [optional] [default to &#39;&#39;]

### Return type

**List[Optional[object]]**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **query_exists**
> bool query_exists(item_name=item_name, oid=oid, uid=uid, ready=ready)

Query Exists

Query to check for existence of a data_item.

### Example


```python
import ska_dlm_client.openapi
from ska_dlm_client.openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost:8080
# See configuration.py for a list of all supported configuration parameters.
configuration = ska_dlm_client.openapi.Configuration(
    host = "http://localhost:8080"
)


# Enter a context with an instance of the API client
with ska_dlm_client.openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = ska_dlm_client.openapi.RequestApi(api_client)
    item_name = '' # str | optional item_name (optional) (default to '')
    oid = '' # str | the oid to be searched for (optional) (default to '')
    uid = '' # str | this returns only one storage_id (optional) (default to '')
    ready = False # bool | whether the item must be in ready state. (optional) (default to False)

    try:
        # Query Exists
        api_response = api_instance.query_exists(item_name=item_name, oid=oid, uid=uid, ready=ready)
        print("The response of RequestApi->query_exists:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling RequestApi->query_exists: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **item_name** | **str**| optional item_name | [optional] [default to &#39;&#39;]
 **oid** | **str**| the oid to be searched for | [optional] [default to &#39;&#39;]
 **uid** | **str**| this returns only one storage_id | [optional] [default to &#39;&#39;]
 **ready** | **bool**| whether the item must be in ready state. | [optional] [default to False]

### Return type

**bool**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **query_exists_and_ready**
> bool query_exists_and_ready(item_name=item_name, oid=oid, uid=uid)

Query Exists And Ready

Check whether a data_item exists and is in ready state.

### Example


```python
import ska_dlm_client.openapi
from ska_dlm_client.openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost:8080
# See configuration.py for a list of all supported configuration parameters.
configuration = ska_dlm_client.openapi.Configuration(
    host = "http://localhost:8080"
)


# Enter a context with an instance of the API client
with ska_dlm_client.openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = ska_dlm_client.openapi.RequestApi(api_client)
    item_name = '' # str | optional item_name (optional) (default to '')
    oid = '' # str | the oid to be searched for (optional) (default to '')
    uid = '' # str | this returns only one storage_id (optional) (default to '')

    try:
        # Query Exists And Ready
        api_response = api_instance.query_exists_and_ready(item_name=item_name, oid=oid, uid=uid)
        print("The response of RequestApi->query_exists_and_ready:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling RequestApi->query_exists_and_ready: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **item_name** | **str**| optional item_name | [optional] [default to &#39;&#39;]
 **oid** | **str**| the oid to be searched for | [optional] [default to &#39;&#39;]
 **uid** | **str**| this returns only one storage_id | [optional] [default to &#39;&#39;]

### Return type

**bool**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **query_expired**
> List[Optional[object]] query_expired(offset=offset)

Query Expired

Query for all expired data_items using the uid_expiration timestamp.

### Example


```python
import ska_dlm_client.openapi
from ska_dlm_client.openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost:8080
# See configuration.py for a list of all supported configuration parameters.
configuration = ska_dlm_client.openapi.Configuration(
    host = "http://localhost:8080"
)


# Enter a context with an instance of the API client
with ska_dlm_client.openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = ska_dlm_client.openapi.RequestApi(api_client)
    offset = 'offset_example' # str | optional offset for the query (optional)

    try:
        # Query Expired
        api_response = api_instance.query_expired(offset=offset)
        print("The response of RequestApi->query_expired:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling RequestApi->query_expired: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **offset** | **str**| optional offset for the query | [optional] 

### Return type

**List[Optional[object]]**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **query_item_storage**
> List[Optional[object]] query_item_storage(item_name=item_name, oid=oid, uid=uid)

Query Item Storage

Query for the storage_ids of all backends holding a copy of a data_item.  Either an item_name or a OID have to be provided.

### Example


```python
import ska_dlm_client.openapi
from ska_dlm_client.openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost:8080
# See configuration.py for a list of all supported configuration parameters.
configuration = ska_dlm_client.openapi.Configuration(
    host = "http://localhost:8080"
)


# Enter a context with an instance of the API client
with ska_dlm_client.openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = ska_dlm_client.openapi.RequestApi(api_client)
    item_name = '' # str | optional item_name (optional) (default to '')
    oid = '' # str | the oid to be searched for (optional) (default to '')
    uid = '' # str | this returns only one storage_id (optional) (default to '')

    try:
        # Query Item Storage
        api_response = api_instance.query_item_storage(item_name=item_name, oid=oid, uid=uid)
        print("The response of RequestApi->query_item_storage:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling RequestApi->query_item_storage: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **item_name** | **str**| optional item_name | [optional] [default to &#39;&#39;]
 **oid** | **str**| the oid to be searched for | [optional] [default to &#39;&#39;]
 **uid** | **str**| this returns only one storage_id | [optional] [default to &#39;&#39;]

### Return type

**List[Optional[object]]**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **query_new**
> List[object] query_new(check_date, uid=uid)

Query New

Query for all data_items newer than the date provided.

### Example


```python
import ska_dlm_client.openapi
from ska_dlm_client.openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost:8080
# See configuration.py for a list of all supported configuration parameters.
configuration = ska_dlm_client.openapi.Configuration(
    host = "http://localhost:8080"
)


# Enter a context with an instance of the API client
with ska_dlm_client.openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = ska_dlm_client.openapi.RequestApi(api_client)
    check_date = 'check_date_example' # str | the UTC starting date (exclusive)
    uid = '' # str | The UID to be checked, optional. (optional) (default to '')

    try:
        # Query New
        api_response = api_instance.query_new(check_date, uid=uid)
        print("The response of RequestApi->query_new:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling RequestApi->query_new: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **check_date** | **str**| the UTC starting date (exclusive) | 
 **uid** | **str**| The UID to be checked, optional. | [optional] [default to &#39;&#39;]

### Return type

**List[object]**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **set_acl**
> object set_acl(oid=oid, uid=uid, acl=acl)

Set Acl

Set the user field of the data_item(s) with the given OID or UID.

### Example


```python
import ska_dlm_client.openapi
from ska_dlm_client.openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost:8080
# See configuration.py for a list of all supported configuration parameters.
configuration = ska_dlm_client.openapi.Configuration(
    host = "http://localhost:8080"
)


# Enter a context with an instance of the API client
with ska_dlm_client.openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = ska_dlm_client.openapi.RequestApi(api_client)
    oid = '' # str | the OID of the data_item to be updated (optional) (default to '')
    uid = '' # str | the UID of the data_item to be updated (optional) (default to '')
    acl = '{}' # str | the acl dict for the data_item (optional) (default to '{}')

    try:
        # Set Acl
        api_response = api_instance.set_acl(oid=oid, uid=uid, acl=acl)
        print("The response of RequestApi->set_acl:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling RequestApi->set_acl: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **oid** | **str**| the OID of the data_item to be updated | [optional] [default to &#39;&#39;]
 **uid** | **str**| the UID of the data_item to be updated | [optional] [default to &#39;&#39;]
 **acl** | **str**| the acl dict for the data_item | [optional] [default to &#39;{}&#39;]

### Return type

**object**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **set_group**
> object set_group(oid=oid, uid=uid, group=group)

Set Group

Set the user field of the data_item(s) with the given OID or UID.

### Example


```python
import ska_dlm_client.openapi
from ska_dlm_client.openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost:8080
# See configuration.py for a list of all supported configuration parameters.
configuration = ska_dlm_client.openapi.Configuration(
    host = "http://localhost:8080"
)


# Enter a context with an instance of the API client
with ska_dlm_client.openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = ska_dlm_client.openapi.RequestApi(api_client)
    oid = '' # str | the OID of the data_item to be updated (optional) (default to '')
    uid = '' # str | the UID of the data_item to be updated (optional) (default to '')
    group = 'SKA' # str | the group for the data_item (optional) (default to 'SKA')

    try:
        # Set Group
        api_response = api_instance.set_group(oid=oid, uid=uid, group=group)
        print("The response of RequestApi->set_group:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling RequestApi->set_group: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **oid** | **str**| the OID of the data_item to be updated | [optional] [default to &#39;&#39;]
 **uid** | **str**| the UID of the data_item to be updated | [optional] [default to &#39;&#39;]
 **group** | **str**| the group for the data_item | [optional] [default to &#39;SKA&#39;]

### Return type

**object**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **set_metadata**
> object set_metadata(uid, body=body)

Set Metadata

Populate the metadata column for a data_item with the metadata.

### Example


```python
import ska_dlm_client.openapi
from ska_dlm_client.openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost:8080
# See configuration.py for a list of all supported configuration parameters.
configuration = ska_dlm_client.openapi.Configuration(
    host = "http://localhost:8080"
)


# Enter a context with an instance of the API client
with ska_dlm_client.openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = ska_dlm_client.openapi.RequestApi(api_client)
    uid = 'uid_example' # str | the UID of the data_item to be updated
    body = None # object |  (optional)

    try:
        # Set Metadata
        api_response = api_instance.set_metadata(uid, body=body)
        print("The response of RequestApi->set_metadata:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling RequestApi->set_metadata: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **uid** | **str**| the UID of the data_item to be updated | 
 **body** | **object**|  | [optional] 

### Return type

**object**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **set_oid_expiration**
> object set_oid_expiration(oid, expiration)

Set Oid Expiration

Set the oid_expiration field of the data_items with the given OID.

### Example


```python
import ska_dlm_client.openapi
from ska_dlm_client.openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost:8080
# See configuration.py for a list of all supported configuration parameters.
configuration = ska_dlm_client.openapi.Configuration(
    host = "http://localhost:8080"
)


# Enter a context with an instance of the API client
with ska_dlm_client.openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = ska_dlm_client.openapi.RequestApi(api_client)
    oid = 'oid_example' # str | the oid of the data_item to be updated
    expiration = 'expiration_example' # str | the expiration date for the data_item

    try:
        # Set Oid Expiration
        api_response = api_instance.set_oid_expiration(oid, expiration)
        print("The response of RequestApi->set_oid_expiration:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling RequestApi->set_oid_expiration: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **oid** | **str**| the oid of the data_item to be updated | 
 **expiration** | **str**| the expiration date for the data_item | 

### Return type

**object**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **set_phase**
> object set_phase(uid, phase)

Set Phase

Set the phase field of the data_item(s) with given UID.

### Example


```python
import ska_dlm_client.openapi
from ska_dlm_client.openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost:8080
# See configuration.py for a list of all supported configuration parameters.
configuration = ska_dlm_client.openapi.Configuration(
    host = "http://localhost:8080"
)


# Enter a context with an instance of the API client
with ska_dlm_client.openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = ska_dlm_client.openapi.RequestApi(api_client)
    uid = 'uid_example' # str | the UID of the data_item to be updated
    phase = 'phase_example' # str | the phase for the data_item

    try:
        # Set Phase
        api_response = api_instance.set_phase(uid, phase)
        print("The response of RequestApi->set_phase:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling RequestApi->set_phase: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **uid** | **str**| the UID of the data_item to be updated | 
 **phase** | **str**| the phase for the data_item | 

### Return type

**object**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **set_state**
> object set_state(uid, state)

Set State

Set the state field of the uid data_item.

### Example


```python
import ska_dlm_client.openapi
from ska_dlm_client.openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost:8080
# See configuration.py for a list of all supported configuration parameters.
configuration = ska_dlm_client.openapi.Configuration(
    host = "http://localhost:8080"
)


# Enter a context with an instance of the API client
with ska_dlm_client.openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = ska_dlm_client.openapi.RequestApi(api_client)
    uid = 'uid_example' # str | the uid of the data_item to be updated
    state = 'state_example' # str | the new state for the data_item

    try:
        # Set State
        api_response = api_instance.set_state(uid, state)
        print("The response of RequestApi->set_state:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling RequestApi->set_state: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **uid** | **str**| the uid of the data_item to be updated | 
 **state** | **str**| the new state for the data_item | 

### Return type

**object**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **set_uid_expiration**
> object set_uid_expiration(uid, expiration)

Set Uid Expiration

Set the uid_expiration field of the data_item with the given UID.

### Example


```python
import ska_dlm_client.openapi
from ska_dlm_client.openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost:8080
# See configuration.py for a list of all supported configuration parameters.
configuration = ska_dlm_client.openapi.Configuration(
    host = "http://localhost:8080"
)


# Enter a context with an instance of the API client
with ska_dlm_client.openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = ska_dlm_client.openapi.RequestApi(api_client)
    uid = 'uid_example' # str | the UID of the data_item to be updated
    expiration = 'expiration_example' # str | the expiration date for the data_item

    try:
        # Set Uid Expiration
        api_response = api_instance.set_uid_expiration(uid, expiration)
        print("The response of RequestApi->set_uid_expiration:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling RequestApi->set_uid_expiration: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **uid** | **str**| the UID of the data_item to be updated | 
 **expiration** | **str**| the expiration date for the data_item | 

### Return type

**object**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **set_uri**
> object set_uri(uid, uri, storage_id)

Set Uri

Set the URI field of the uid data_item.

### Example


```python
import ska_dlm_client.openapi
from ska_dlm_client.openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost:8080
# See configuration.py for a list of all supported configuration parameters.
configuration = ska_dlm_client.openapi.Configuration(
    host = "http://localhost:8080"
)


# Enter a context with an instance of the API client
with ska_dlm_client.openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = ska_dlm_client.openapi.RequestApi(api_client)
    uid = 'uid_example' # str | the uid of the data_item to be updated
    uri = 'uri_example' # str | the access URI for the data_item
    storage_id = 'storage_id_example' # str | the storage_id associated with the URI

    try:
        # Set Uri
        api_response = api_instance.set_uri(uid, uri, storage_id)
        print("The response of RequestApi->set_uri:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling RequestApi->set_uri: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **uid** | **str**| the uid of the data_item to be updated | 
 **uri** | **str**| the access URI for the data_item | 
 **storage_id** | **str**| the storage_id associated with the URI | 

### Return type

**object**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **set_user**
> object set_user(oid=oid, uid=uid, user=user)

Set User

Set the user field of the data_item(s) with the given OID or UID.

### Example


```python
import ska_dlm_client.openapi
from ska_dlm_client.openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost:8080
# See configuration.py for a list of all supported configuration parameters.
configuration = ska_dlm_client.openapi.Configuration(
    host = "http://localhost:8080"
)


# Enter a context with an instance of the API client
with ska_dlm_client.openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = ska_dlm_client.openapi.RequestApi(api_client)
    oid = '' # str | the OID of the data_item to be updated (optional) (default to '')
    uid = '' # str | the UID of the data_item to be updated (optional) (default to '')
    user = 'SKA' # str | the user for the data_item (optional) (default to 'SKA')

    try:
        # Set User
        api_response = api_instance.set_user(oid=oid, uid=uid, user=user)
        print("The response of RequestApi->set_user:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling RequestApi->set_user: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **oid** | **str**| the OID of the data_item to be updated | [optional] [default to &#39;&#39;]
 **uid** | **str**| the UID of the data_item to be updated | [optional] [default to &#39;&#39;]
 **user** | **str**| the user for the data_item | [optional] [default to &#39;SKA&#39;]

### Return type

**object**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **update_data_item**
> object update_data_item(item_name=item_name, oid=oid, uid=uid, body=body)

Update Data Item

Update fields of an existing data_item.  This is mostly used by the other convenience functions. In general when specifying an OID or an item_name, multiple entries will be updated at the same time.

### Example


```python
import ska_dlm_client.openapi
from ska_dlm_client.openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost:8080
# See configuration.py for a list of all supported configuration parameters.
configuration = ska_dlm_client.openapi.Configuration(
    host = "http://localhost:8080"
)


# Enter a context with an instance of the API client
with ska_dlm_client.openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = ska_dlm_client.openapi.RequestApi(api_client)
    item_name = '' # str | the name of the data_items to be updated (optional) (default to '')
    oid = '' # str | the OID of the data_items to be updated (optional) (default to '')
    uid = '' # str | the UID of the data_item to be updated (optional) (default to '')
    body = None # object |  (optional)

    try:
        # Update Data Item
        api_response = api_instance.update_data_item(item_name=item_name, oid=oid, uid=uid, body=body)
        print("The response of RequestApi->update_data_item:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling RequestApi->update_data_item: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **item_name** | **str**| the name of the data_items to be updated | [optional] [default to &#39;&#39;]
 **oid** | **str**| the OID of the data_items to be updated | [optional] [default to &#39;&#39;]
 **uid** | **str**| the UID of the data_item to be updated | [optional] [default to &#39;&#39;]
 **body** | **object**|  | [optional] 

### Return type

**object**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **update_item_tags**
> object update_item_tags(item_name=item_name, oid=oid, body=body)

Update Item Tags

Update/set the item_tags field of a data_item with given item_name/OID.  This will update all records for a data_item at the same time. Updating a single UID does not make sense.

### Example


```python
import ska_dlm_client.openapi
from ska_dlm_client.openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost:8080
# See configuration.py for a list of all supported configuration parameters.
configuration = ska_dlm_client.openapi.Configuration(
    host = "http://localhost:8080"
)


# Enter a context with an instance of the API client
with ska_dlm_client.openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = ska_dlm_client.openapi.RequestApi(api_client)
    item_name = '' # str | the name of the data_item (optional) (default to '')
    oid = '' # str | the OID of the data_item to be updated (optional) (default to '')
    body = None # object |  (optional)

    try:
        # Update Item Tags
        api_response = api_instance.update_item_tags(item_name=item_name, oid=oid, body=body)
        print("The response of RequestApi->update_item_tags:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling RequestApi->update_item_tags: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **item_name** | **str**| the name of the data_item | [optional] [default to &#39;&#39;]
 **oid** | **str**| the OID of the data_item to be updated | [optional] [default to &#39;&#39;]
 **body** | **object**|  | [optional] 

### Return type

**object**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)


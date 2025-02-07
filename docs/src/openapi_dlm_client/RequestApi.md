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


# **query_data_item**
> List[Optional[object]] query_data_item(item_name=item_name, oid=oid, uid=uid, params=params)

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
    params = 'params_example' # str | specify the query parameters (optional)

    try:
        # Query Data Item
        api_response = api_instance.query_data_item(item_name=item_name, oid=oid, uid=uid, params=params)
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
> List[Optional[object]] query_new(check_date, uid=uid)

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


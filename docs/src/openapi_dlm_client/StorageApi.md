# ska_dlm_client.openapi.StorageApi

All URIs are relative to *http://localhost:8080*

Method | HTTP request | Description
------------- | ------------- | -------------
[**create_storage_config_storage_create_storage_config_post**](StorageApi.md#create_storage_config_storage_create_storage_config_post) | **POST** /storage/create_storage_config | Create Storage Config
[**get_storage_config_storage_get_storage_config_get**](StorageApi.md#get_storage_config_storage_get_storage_config_get) | **GET** /storage/get_storage_config | Get Storage Config
[**init_location_storage_init_location_post**](StorageApi.md#init_location_storage_init_location_post) | **POST** /storage/init_location | Init Location
[**init_storage_storage_init_storage_post**](StorageApi.md#init_storage_storage_init_storage_post) | **POST** /storage/init_storage | Init Storage
[**query_location_storage_query_location_get**](StorageApi.md#query_location_storage_query_location_get) | **GET** /storage/query_location | Query Location
[**query_storage_storage_query_storage_get**](StorageApi.md#query_storage_storage_query_storage_get) | **GET** /storage/query_storage | Query Storage
[**rclone_config_storage_rclone_config_post**](StorageApi.md#rclone_config_storage_rclone_config_post) | **POST** /storage/rclone_config | Rclone Config


# **create_storage_config_storage_create_storage_config_post**
> object create_storage_config_storage_create_storage_config_post(body, storage_id=storage_id, storage_name=storage_name, config_type=config_type)

Create Storage Config

Create a new record in the storage_config table for a storage with the given id.

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
    api_instance = ska_dlm_client.openapi.StorageApi(api_client)
    body = None # object | 
    storage_id = '' # str | the storage_id for which to create the entry. (optional) (default to '')
    storage_name = '' # str | the name of the storage for which the config is provided. (optional) (default to '')
    config_type = 'rclone' # str | default is rclone, but could be something else in the future. (optional) (default to 'rclone')

    try:
        # Create Storage Config
        api_response = api_instance.create_storage_config_storage_create_storage_config_post(body, storage_id=storage_id, storage_name=storage_name, config_type=config_type)
        print("The response of StorageApi->create_storage_config_storage_create_storage_config_post:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling StorageApi->create_storage_config_storage_create_storage_config_post: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **body** | **object**|  | 
 **storage_id** | **str**| the storage_id for which to create the entry. | [optional] [default to &#39;&#39;]
 **storage_name** | **str**| the name of the storage for which the config is provided. | [optional] [default to &#39;&#39;]
 **config_type** | **str**| default is rclone, but could be something else in the future. | [optional] [default to &#39;rclone&#39;]

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

# **get_storage_config_storage_get_storage_config_get**
> object get_storage_config_storage_get_storage_config_get(storage_id=storage_id, storage_name=storage_name, config_type=config_type)

Get Storage Config

Get the storage configuration entry for a particular storage backend.

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
    api_instance = ska_dlm_client.openapi.StorageApi(api_client)
    storage_id = '' # str | the storage id, by default \"\" (optional) (default to '')
    storage_name = '' # str | the name of the storage volume, by default \"\" (optional) (default to '')
    config_type = 'rclone' # str | query only the specified type, by default \"rclone\" (optional) (default to 'rclone')

    try:
        # Get Storage Config
        api_response = api_instance.get_storage_config_storage_get_storage_config_get(storage_id=storage_id, storage_name=storage_name, config_type=config_type)
        print("The response of StorageApi->get_storage_config_storage_get_storage_config_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling StorageApi->get_storage_config_storage_get_storage_config_get: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **storage_id** | **str**| the storage id, by default \&quot;\&quot; | [optional] [default to &#39;&#39;]
 **storage_name** | **str**| the name of the storage volume, by default \&quot;\&quot; | [optional] [default to &#39;&#39;]
 **config_type** | **str**| query only the specified type, by default \&quot;rclone\&quot; | [optional] [default to &#39;rclone&#39;]

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

# **init_location_storage_init_location_post**
> object init_location_storage_init_location_post(location_name, location_type, location_country=location_country, location_city=location_city, location_facility=location_facility)

Init Location

Initialize a new storage location.

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
    api_instance = ska_dlm_client.openapi.StorageApi(api_client)
    location_name = 'location_name_example' # str | the orgization or owner's name managing the storage location.
    location_type = 'location_type_example' # str | the location type, e.g. \"server\"
    location_country = '' # str | the location country name (optional) (default to '')
    location_city = '' # str | the location city name (optional) (default to '')
    location_facility = '' # str | the location facility name (optional) (default to '')

    try:
        # Init Location
        api_response = api_instance.init_location_storage_init_location_post(location_name, location_type, location_country=location_country, location_city=location_city, location_facility=location_facility)
        print("The response of StorageApi->init_location_storage_init_location_post:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling StorageApi->init_location_storage_init_location_post: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **location_name** | **str**| the orgization or owner&#39;s name managing the storage location. | 
 **location_type** | **str**| the location type, e.g. \&quot;server\&quot; | 
 **location_country** | **str**| the location country name | [optional] [default to &#39;&#39;]
 **location_city** | **str**| the location city name | [optional] [default to &#39;&#39;]
 **location_facility** | **str**| the location facility name | [optional] [default to &#39;&#39;]

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

# **init_storage_storage_init_storage_post**
> object init_storage_storage_init_storage_post(storage_name, storage_type, storage_interface, location_id=location_id, location_name=location_name, storage_capacity=storage_capacity, storage_phase_level=storage_phase_level, body=body)

Init Storage

Intialize a new storage by at least specifying a storage_name.

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
    api_instance = ska_dlm_client.openapi.StorageApi(api_client)
    storage_name = 'storage_name_example' # str | An organisation or owner name for the storage.
    storage_type = 'storage_type_example' # str | high level type of the storage, e.g. \"disk\", \"s3\"
    storage_interface = 'storage_interface_example' # str | storage interface for rclone access, e.g. \"posix\", \"s3\"
    location_id = '' # str | a dlm registered location id (optional) (default to '')
    location_name = '' # str | a dlm registered location name (optional) (default to '')
    storage_capacity = -1 # int | reserved storage capacity in bytes (optional) (default to -1)
    storage_phase_level = 'GAS' # str | one of \"GAS\", \"LIQUID\", \"SOLID\" (optional) (default to 'GAS')
    body = None # object |  (optional)

    try:
        # Init Storage
        api_response = api_instance.init_storage_storage_init_storage_post(storage_name, storage_type, storage_interface, location_id=location_id, location_name=location_name, storage_capacity=storage_capacity, storage_phase_level=storage_phase_level, body=body)
        print("The response of StorageApi->init_storage_storage_init_storage_post:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling StorageApi->init_storage_storage_init_storage_post: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **storage_name** | **str**| An organisation or owner name for the storage. | 
 **storage_type** | **str**| high level type of the storage, e.g. \&quot;disk\&quot;, \&quot;s3\&quot; | 
 **storage_interface** | **str**| storage interface for rclone access, e.g. \&quot;posix\&quot;, \&quot;s3\&quot; | 
 **location_id** | **str**| a dlm registered location id | [optional] [default to &#39;&#39;]
 **location_name** | **str**| a dlm registered location name | [optional] [default to &#39;&#39;]
 **storage_capacity** | **int**| reserved storage capacity in bytes | [optional] [default to -1]
 **storage_phase_level** | **str**| one of \&quot;GAS\&quot;, \&quot;LIQUID\&quot;, \&quot;SOLID\&quot; | [optional] [default to &#39;GAS&#39;]
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

# **query_location_storage_query_location_get**
> object query_location_storage_query_location_get(location_name=location_name, location_id=location_id)

Query Location

Query a location by at least specifying a location_name.

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
    api_instance = ska_dlm_client.openapi.StorageApi(api_client)
    location_name = '' # str | could be empty, in which case the first 1000 items are returned (optional) (default to '')
    location_id = '' # str | Return locations referred to by the location_id provided. (optional) (default to '')

    try:
        # Query Location
        api_response = api_instance.query_location_storage_query_location_get(location_name=location_name, location_id=location_id)
        print("The response of StorageApi->query_location_storage_query_location_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling StorageApi->query_location_storage_query_location_get: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **location_name** | **str**| could be empty, in which case the first 1000 items are returned | [optional] [default to &#39;&#39;]
 **location_id** | **str**| Return locations referred to by the location_id provided. | [optional] [default to &#39;&#39;]

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

# **query_storage_storage_query_storage_get**
> object query_storage_storage_query_storage_get(storage_name=storage_name, storage_id=storage_id)

Query Storage

Query a storage by at least specifying a storage_name.

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
    api_instance = ska_dlm_client.openapi.StorageApi(api_client)
    storage_name = '' # str | could be empty, in which case the first 1000 items are returned (optional) (default to '')
    storage_id = '' # str | Return locations referred to by the location_id provided. (optional) (default to '')

    try:
        # Query Storage
        api_response = api_instance.query_storage_storage_query_storage_get(storage_name=storage_name, storage_id=storage_id)
        print("The response of StorageApi->query_storage_storage_query_storage_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling StorageApi->query_storage_storage_query_storage_get: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **storage_name** | **str**| could be empty, in which case the first 1000 items are returned | [optional] [default to &#39;&#39;]
 **storage_id** | **str**| Return locations referred to by the location_id provided. | [optional] [default to &#39;&#39;]

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

# **rclone_config_storage_rclone_config_post**
> object rclone_config_storage_rclone_config_post(body)

Rclone Config

Create a new rclone backend configuration entry on the rclone server.

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
    api_instance = ska_dlm_client.openapi.StorageApi(api_client)
    body = None # object | 

    try:
        # Rclone Config
        api_response = api_instance.rclone_config_storage_rclone_config_post(body)
        print("The response of StorageApi->rclone_config_storage_rclone_config_post:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling StorageApi->rclone_config_storage_rclone_config_post: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **body** | **object**|  | 

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


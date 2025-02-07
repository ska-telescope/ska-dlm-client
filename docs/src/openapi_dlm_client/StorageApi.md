# ska_dlm_client.openapi.StorageApi

All URIs are relative to *http://localhost:8080*

Method | HTTP request | Description
------------- | ------------- | -------------
[**create_rclone_config**](StorageApi.md#create_rclone_config) | **POST** /storage/rclone_config | Create Rclone Config
[**create_storage_config**](StorageApi.md#create_storage_config) | **POST** /storage/create_storage_config | Create Storage Config
[**get_storage_config**](StorageApi.md#get_storage_config) | **GET** /storage/get_storage_config | Get Storage Config
[**init_location**](StorageApi.md#init_location) | **POST** /storage/init_location | Init Location
[**init_storage**](StorageApi.md#init_storage) | **POST** /storage/init_storage | Init Storage
[**query_location**](StorageApi.md#query_location) | **GET** /storage/query_location | Query Location
[**query_storage**](StorageApi.md#query_storage) | **GET** /storage/query_storage | Query Storage


# **create_rclone_config**
> bool create_rclone_config(body)

Create Rclone Config

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
        # Create Rclone Config
        api_response = api_instance.create_rclone_config(body)
        print("The response of StorageApi->create_rclone_config:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling StorageApi->create_rclone_config: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **body** | **object**|  | 

### Return type

**bool**

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

# **create_storage_config**
> str create_storage_config(body, storage_id=storage_id, storage_name=storage_name, config_type=config_type)

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
        api_response = api_instance.create_storage_config(body, storage_id=storage_id, storage_name=storage_name, config_type=config_type)
        print("The response of StorageApi->create_storage_config:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling StorageApi->create_storage_config: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **body** | **object**|  | 
 **storage_id** | **str**| the storage_id for which to create the entry. | [optional] [default to &#39;&#39;]
 **storage_name** | **str**| the name of the storage for which the config is provided. | [optional] [default to &#39;&#39;]
 **config_type** | **str**| default is rclone, but could be something else in the future. | [optional] [default to &#39;rclone&#39;]

### Return type

**str**

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

# **get_storage_config**
> List[Optional[str]] get_storage_config(storage_id=storage_id, storage_name=storage_name, config_type=config_type)

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
        api_response = api_instance.get_storage_config(storage_id=storage_id, storage_name=storage_name, config_type=config_type)
        print("The response of StorageApi->get_storage_config:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling StorageApi->get_storage_config: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **storage_id** | **str**| the storage id, by default \&quot;\&quot; | [optional] [default to &#39;&#39;]
 **storage_name** | **str**| the name of the storage volume, by default \&quot;\&quot; | [optional] [default to &#39;&#39;]
 **config_type** | **str**| query only the specified type, by default \&quot;rclone\&quot; | [optional] [default to &#39;rclone&#39;]

### Return type

**List[Optional[str]]**

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

# **init_location**
> str init_location(location_name, location_type, location_country=location_country, location_city=location_city, location_facility=location_facility)

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
        api_response = api_instance.init_location(location_name, location_type, location_country=location_country, location_city=location_city, location_facility=location_facility)
        print("The response of StorageApi->init_location:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling StorageApi->init_location: %s\n" % e)
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

**str**

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

# **init_storage**
> str init_storage(storage_name, storage_type, storage_interface, root_directory, location_id=location_id, location_name=location_name, storage_capacity=storage_capacity, storage_phase_level=storage_phase_level, body=body)

Init Storage

Initialize a new storage.  location_name or location_id is required.

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
    root_directory = 'root_directory_example' # str | data directory as an absolute path on the remote storage endpoint
    location_id = 'location_id_example' # str | a dlm registered location id (optional)
    location_name = 'location_name_example' # str | a dlm registered location name (optional)
    storage_capacity = -1 # int | reserved storage capacity in bytes (optional) (default to -1)
    storage_phase_level = 'GAS' # str | one of \"GAS\", \"LIQUID\", \"SOLID\" (optional) (default to 'GAS')
    body = None # object |  (optional)

    try:
        # Init Storage
        api_response = api_instance.init_storage(storage_name, storage_type, storage_interface, root_directory, location_id=location_id, location_name=location_name, storage_capacity=storage_capacity, storage_phase_level=storage_phase_level, body=body)
        print("The response of StorageApi->init_storage:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling StorageApi->init_storage: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **storage_name** | **str**| An organisation or owner name for the storage. | 
 **storage_type** | **str**| high level type of the storage, e.g. \&quot;disk\&quot;, \&quot;s3\&quot; | 
 **storage_interface** | **str**| storage interface for rclone access, e.g. \&quot;posix\&quot;, \&quot;s3\&quot; | 
 **root_directory** | **str**| data directory as an absolute path on the remote storage endpoint | 
 **location_id** | **str**| a dlm registered location id | [optional] 
 **location_name** | **str**| a dlm registered location name | [optional] 
 **storage_capacity** | **int**| reserved storage capacity in bytes | [optional] [default to -1]
 **storage_phase_level** | **str**| one of \&quot;GAS\&quot;, \&quot;LIQUID\&quot;, \&quot;SOLID\&quot; | [optional] [default to &#39;GAS&#39;]
 **body** | **object**|  | [optional] 

### Return type

**str**

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

# **query_location**
> List[Optional[object]] query_location(location_name=location_name, location_id=location_id)

Query Location

Query a location.

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
        api_response = api_instance.query_location(location_name=location_name, location_id=location_id)
        print("The response of StorageApi->query_location:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling StorageApi->query_location: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **location_name** | **str**| could be empty, in which case the first 1000 items are returned | [optional] [default to &#39;&#39;]
 **location_id** | **str**| Return locations referred to by the location_id provided. | [optional] [default to &#39;&#39;]

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

# **query_storage**
> List[Optional[object]] query_storage(storage_name=storage_name, storage_id=storage_id)

Query Storage

Query a storage.

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
        api_response = api_instance.query_storage(storage_name=storage_name, storage_id=storage_id)
        print("The response of StorageApi->query_storage:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling StorageApi->query_storage: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **storage_name** | **str**| could be empty, in which case the first 1000 items are returned | [optional] [default to &#39;&#39;]
 **storage_id** | **str**| Return locations referred to by the location_id provided. | [optional] [default to &#39;&#39;]

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


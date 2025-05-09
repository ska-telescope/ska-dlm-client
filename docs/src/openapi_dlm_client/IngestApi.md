# ska_dlm_client.openapi.IngestApi

All URIs are relative to *http://localhost:8080*

Method | HTTP request | Description
------------- | ------------- | -------------
[**init_data_item**](IngestApi.md#init_data_item) | **POST** /ingest/init_data_item | Init Data Item
[**register_data_item**](IngestApi.md#register_data_item) | **POST** /ingest/register_data_item | Register Data Item


# **init_data_item**
> str init_data_item(item_name=item_name, phase=phase, authorization=authorization, body=body)

Init Data Item

Initialize a new data_item.  item_name or json_data is required.

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
    api_instance = ska_dlm_client.openapi.IngestApi(api_client)
    item_name = 'item_name_example' # str | the item_name, can be empty, but then json_data has to be specified. (optional)
    phase = 'GAS' # str | the phase this item is set to (usually inherited from the storage) (optional) (default to 'GAS')
    authorization = 'authorization_example' # str | Validated Bearer token with UserInfo (optional)
    body = None # object |  (optional)

    try:
        # Init Data Item
        api_response = api_instance.init_data_item(item_name=item_name, phase=phase, authorization=authorization, body=body)
        print("The response of IngestApi->init_data_item:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling IngestApi->init_data_item: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **item_name** | **str**| the item_name, can be empty, but then json_data has to be specified. | [optional] 
 **phase** | **str**| the phase this item is set to (usually inherited from the storage) | [optional] [default to &#39;GAS&#39;]
 **authorization** | **str**| Validated Bearer token with UserInfo | [optional] 
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

# **register_data_item**
> str register_data_item(item_name, uri, item_type=item_type, storage_name=storage_name, storage_id=storage_id, parents=parents, do_storage_access_check=do_storage_access_check, authorization=authorization, body=body)

Register Data Item

Ingest a data_item (register function is an alias).  This high level function is a combination of init_data_item, set_uri and set_state(READY). It also checks whether a data_item is already registered on the requested storage.  (1) check whether requested storage is known and accessible (2) check, if required, whether item is accessible/exists on that storage (3) check whether item is already registered on that storage (4) initialize the item on the storage (5) set the access path to the payload (6) set state to READY (7) save metadata in the data_item table

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
    api_instance = ska_dlm_client.openapi.IngestApi(api_client)
    item_name = 'item_name_example' # str | item name to register with. Does not need to be unique.
    uri = 'uri_example' # str | the relative access path to the payload.
    item_type = file # str |  (optional) (default to file)
    storage_name = '' # str | the name of the configured storage volume (name or ID required) (optional) (default to '')
    storage_id = '' # str | the ID of the configured storage. (optional) (default to '')
    parents = 'parents_example' # str | uuid of parent item (optional)
    do_storage_access_check = True # bool | perform check_storage_access() against provided storage and uri (optional) (default to True)
    authorization = 'authorization_example' # str | Validated Bearer token with UserInfo (optional)
    body = None # object |  (optional)

    try:
        # Register Data Item
        api_response = api_instance.register_data_item(item_name, uri, item_type=item_type, storage_name=storage_name, storage_id=storage_id, parents=parents, do_storage_access_check=do_storage_access_check, authorization=authorization, body=body)
        print("The response of IngestApi->register_data_item:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling IngestApi->register_data_item: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **item_name** | **str**| item name to register with. Does not need to be unique. | 
 **uri** | **str**| the relative access path to the payload. | 
 **item_type** | **str**|  | [optional] [default to file]
 **storage_name** | **str**| the name of the configured storage volume (name or ID required) | [optional] [default to &#39;&#39;]
 **storage_id** | **str**| the ID of the configured storage. | [optional] [default to &#39;&#39;]
 **parents** | **str**| uuid of parent item | [optional] 
 **do_storage_access_check** | **bool**| perform check_storage_access() against provided storage and uri | [optional] [default to True]
 **authorization** | **str**| Validated Bearer token with UserInfo | [optional] 
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


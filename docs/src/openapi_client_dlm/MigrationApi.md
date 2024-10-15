# ska_dlm_client.openapi.MigrationApi

All URIs are relative to *http://localhost:8080*

Method | HTTP request | Description
------------- | ------------- | -------------
[**copy_data_item_migration_copy_data_item_get**](MigrationApi.md#copy_data_item_migration_copy_data_item_get) | **GET** /migration/copy_data_item | Copy Data Item


# **copy_data_item_migration_copy_data_item_get**
> object copy_data_item_migration_copy_data_item_get(item_name=item_name, oid=oid, uid=uid, destination_name=destination_name, destination_id=destination_id, path=path)

Copy Data Item

Copy a data_item from source to destination.  Steps (1) get the current storage_id(s) of the item (2) convert one(first) storage_id to a configured rclone backend (3) check whether item already exists on destination (4) initialize the new item with the same OID on the new storage (5) use the rclone copy command to copy it to the new location (6) make sure the copy was successful

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
    api_instance = ska_dlm_client.openapi.MigrationApi(api_client)
    item_name = '' # str | data item name, when empty the first 1000 items are returned, by default \"\" (optional) (default to '')
    oid = '' # str | object id, Return data_items referred to by the OID provided, by default \"\" (optional) (default to '')
    uid = '' # str | Return data_item referred to by the UID provided, by default \"\" (optional) (default to '')
    destination_name = '' # str | the name of the destination storage volume, by default \"\" (optional) (default to '')
    destination_id = '' # str | the destination storage, by default \"\" (optional) (default to '')
    path = '' # str | the destination path, by default \"\" (optional) (default to '')

    try:
        # Copy Data Item
        api_response = api_instance.copy_data_item_migration_copy_data_item_get(item_name=item_name, oid=oid, uid=uid, destination_name=destination_name, destination_id=destination_id, path=path)
        print("The response of MigrationApi->copy_data_item_migration_copy_data_item_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling MigrationApi->copy_data_item_migration_copy_data_item_get: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **item_name** | **str**| data item name, when empty the first 1000 items are returned, by default \&quot;\&quot; | [optional] [default to &#39;&#39;]
 **oid** | **str**| object id, Return data_items referred to by the OID provided, by default \&quot;\&quot; | [optional] [default to &#39;&#39;]
 **uid** | **str**| Return data_item referred to by the UID provided, by default \&quot;\&quot; | [optional] [default to &#39;&#39;]
 **destination_name** | **str**| the name of the destination storage volume, by default \&quot;\&quot; | [optional] [default to &#39;&#39;]
 **destination_id** | **str**| the destination storage, by default \&quot;\&quot; | [optional] [default to &#39;&#39;]
 **path** | **str**| the destination path, by default \&quot;\&quot; | [optional] [default to &#39;&#39;]

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


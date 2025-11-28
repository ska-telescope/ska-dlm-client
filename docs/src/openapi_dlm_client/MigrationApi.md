# ska_dlm_client.openapi.MigrationApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**copy_data_item**](MigrationApi.md#copy_data_item) | **POST** /migration/copy_data_item | Copy Data Item
[**get_migration_record**](MigrationApi.md#get_migration_record) | **GET** /migration/get_migration | Get Migration Record
[**query_migrations**](MigrationApi.md#query_migrations) | **GET** /migration/query_migrations | Query Migrations


# **copy_data_item**
> Dict[str, object] copy_data_item(item_name=item_name, oid=oid, uid=uid, destination_name=destination_name, destination_id=destination_id, path=path, authorization=authorization)

Copy Data Item

Copy a data_item from source to destination.

Steps
(1) get the current storage_id(s) of the item
(2) convert one (first) storage_id to a configured rclone backend
(3) initialise the new item with the same OID on the new storage
(4) use the rclone copy command to copy it to the new location
(5) set the access path to the payload
(6) set state to READY
(7) save metadata in the data_item table

### Example


```python
import ska_dlm_client.openapi
from ska_dlm_client.openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = ska_dlm_client.openapi.Configuration(
    host = "http://localhost"
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
    path = '' # str | the destination path relative to storage root, by default \"\" (optional) (default to '')
    authorization = 'authorization_example' # str | Validated Bearer token with UserInfo (optional)

    try:
        # Copy Data Item
        api_response = api_instance.copy_data_item(item_name=item_name, oid=oid, uid=uid, destination_name=destination_name, destination_id=destination_id, path=path, authorization=authorization)
        print("The response of MigrationApi->copy_data_item:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling MigrationApi->copy_data_item: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **item_name** | **str**| data item name, when empty the first 1000 items are returned, by default \&quot;\&quot; | [optional] [default to &#39;&#39;]
 **oid** | **str**| object id, Return data_items referred to by the OID provided, by default \&quot;\&quot; | [optional] [default to &#39;&#39;]
 **uid** | **str**| Return data_item referred to by the UID provided, by default \&quot;\&quot; | [optional] [default to &#39;&#39;]
 **destination_name** | **str**| the name of the destination storage volume, by default \&quot;\&quot; | [optional] [default to &#39;&#39;]
 **destination_id** | **str**| the destination storage, by default \&quot;\&quot; | [optional] [default to &#39;&#39;]
 **path** | **str**| the destination path relative to storage root, by default \&quot;\&quot; | [optional] [default to &#39;&#39;]
 **authorization** | **str**| Validated Bearer token with UserInfo | [optional] 

### Return type

**Dict[str, object]**

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

# **get_migration_record**
> object get_migration_record(migration_id)

Get Migration Record

Query for a specific migration.

### Example


```python
import ska_dlm_client.openapi
from ska_dlm_client.openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = ska_dlm_client.openapi.Configuration(
    host = "http://localhost"
)


# Enter a context with an instance of the API client
with ska_dlm_client.openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = ska_dlm_client.openapi.MigrationApi(api_client)
    migration_id = 56 # int | Migration id of migration

    try:
        # Get Migration Record
        api_response = api_instance.get_migration_record(migration_id)
        print("The response of MigrationApi->get_migration_record:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling MigrationApi->get_migration_record: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **migration_id** | **int**| Migration id of migration | 

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

# **query_migrations**
> List[Optional[Dict[str, object]]] query_migrations(start_date=start_date, end_date=end_date, storage_id=storage_id, authorization=authorization)

Query Migrations

Query for all migrations by a given user, with optional filters.

### Example


```python
import ska_dlm_client.openapi
from ska_dlm_client.openapi.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = ska_dlm_client.openapi.Configuration(
    host = "http://localhost"
)


# Enter a context with an instance of the API client
with ska_dlm_client.openapi.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = ska_dlm_client.openapi.MigrationApi(api_client)
    start_date = 'start_date_example' # str | Filter migrations that started after this date (YYYY-MM-DD or YYYYMMDD) (optional)
    end_date = 'end_date_example' # str | Filter migrations that ended before this date (YYYY-MM-DD or YYYYMMDD) (optional)
    storage_id = 'storage_id_example' # str | Filter migrations by a specific storage location (optional)
    authorization = 'authorization_example' # str | Validated Bearer token with UserInfo (optional)

    try:
        # Query Migrations
        api_response = api_instance.query_migrations(start_date=start_date, end_date=end_date, storage_id=storage_id, authorization=authorization)
        print("The response of MigrationApi->query_migrations:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling MigrationApi->query_migrations: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **start_date** | **str**| Filter migrations that started after this date (YYYY-MM-DD or YYYYMMDD) | [optional] 
 **end_date** | **str**| Filter migrations that ended before this date (YYYY-MM-DD or YYYYMMDD) | [optional] 
 **storage_id** | **str**| Filter migrations by a specific storage location | [optional] 
 **authorization** | **str**| Validated Bearer token with UserInfo | [optional] 

### Return type

**List[Optional[Dict[str, object]]]**

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


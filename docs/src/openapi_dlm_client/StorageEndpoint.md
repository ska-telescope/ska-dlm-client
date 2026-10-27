# StorageEndpoint

Storage endpoint fields exposed by the storage API.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**storage_id** | **str** |  | 
**storage_name** | **str** |  | 

## Example

```python
from ska_dlm_client.openapi.models.storage_endpoint import StorageEndpoint

# TODO update the JSON string below
json = "{}"
# create an instance of StorageEndpoint from a JSON string
storage_endpoint_instance = StorageEndpoint.from_json(json)
# print the JSON string representation of the object
print(StorageEndpoint.to_json())

# convert the object into a dict
storage_endpoint_dict = storage_endpoint_instance.to_dict()
# create an instance of StorageEndpoint from a dict
storage_endpoint_from_dict = StorageEndpoint.from_dict(storage_endpoint_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



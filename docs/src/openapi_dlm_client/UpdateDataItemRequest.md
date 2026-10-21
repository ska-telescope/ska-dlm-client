# UpdateDataItemRequest

Request body for associating child items with a data item.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**parent_data_item_uid** | **UUID** |  | 
**children** | **List[UUID]** |  | 

## Example

```python
from ska_dlm_client.openapi.models.update_data_item_request import UpdateDataItemRequest

# TODO update the JSON string below
json = "{}"
# create an instance of UpdateDataItemRequest from a JSON string
update_data_item_request_instance = UpdateDataItemRequest.from_json(json)
# print the JSON string representation of the object
print(UpdateDataItemRequest.to_json())

# convert the object into a dict
update_data_item_request_dict = update_data_item_request_instance.to_dict()
# create an instance of UpdateDataItemRequest from a dict
update_data_item_request_from_dict = UpdateDataItemRequest.from_dict(update_data_item_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



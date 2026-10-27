# UpdateDataItemResponse

Response containing the number of newly inserted child associations.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**inserted_count** | **int** |  | 

## Example

```python
from ska_dlm_client.openapi.models.update_data_item_response import UpdateDataItemResponse

# TODO update the JSON string below
json = "{}"
# create an instance of UpdateDataItemResponse from a JSON string
update_data_item_response_instance = UpdateDataItemResponse.from_json(json)
# print the JSON string representation of the object
print(UpdateDataItemResponse.to_json())

# convert the object into a dict
update_data_item_response_dict = update_data_item_response_instance.to_dict()
# create an instance of UpdateDataItemResponse from a dict
update_data_item_response_from_dict = UpdateDataItemResponse.from_dict(update_data_item_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



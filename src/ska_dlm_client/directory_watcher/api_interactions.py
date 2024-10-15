#
# Example/test code for OpenAPI integration
#
from ska_dlm_client.openapi import configuration, api_client
from ska_dlm_client.openapi.dlm_api import request_api, storage_api

gateway_configuration = configuration.Configuration(host='http://localhost:8000')
ingest_configuration = configuration.Configuration(host='http://localhost:8001')
request_configuration = configuration.Configuration(host='http://localhost:8002')
storage_configuration = configuration.Configuration(host='http://localhost:8003')
migration_configuration = configuration.Configuration(host='http://localhost:8004')

with api_client.ApiClient(storage_configuration) as api_client:
    #api_request = request_api.RequestApi(api_client)
    api_storage = storage_api.StorageApi(api_client)
#    default = api_default.register_data_item_ingest_register_data_item_post(item_name="mark_test1")
#    print()
#    print(default)

    #default = api_default.query_new_request_query_new_get(check_date='Wed, 25 Sep 2024 00:39:31 GMT')
    storage = api_storage.query_location_storage_query_location_get()
    print()
    print(storage)

#with api_client.ApiClient(configuration) as api_client:
#    api_storage = storage_api.StorageApi(api_client)
#    storage = api_storage.storage_get()
#    print()
#    print(storage)
#    api_data_item = data_item_api.DataItemApi(api_client)
#    data_item = api_data_item.data_item_get()
#    print()
#    print(data_item)
#    api_storage_config = storage_config_api.StorageConfigApi(api_client)
#    storage_config = api_storage_config.storage_config_get()
#    print()
#    print(storage_config)

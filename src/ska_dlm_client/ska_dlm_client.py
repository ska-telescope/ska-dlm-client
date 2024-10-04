"""Main module."""

from dlm_gateway import dlm_gateway_client
from dlm_ingest import dlm_ingest_client
from dlm_storage import dlm_storage_client

from ska_dlm_client import CONFIG

# exchange the token for a cookie
session = dlm_gateway_client.start_session(CONFIG.auth_token, CONFIG.DLM.gateway_url)

# check if the location is known to DLM
locations = dlm_storage_client.query_location(CONFIG.location.name)

# init location
location = dlm_storage_client.init_location(
    CONFIG.location.name,
    CONFIG.location.type,
    CONFIG.location.country,
    CONFIG.location.city,
    CONFIG.location.facility,
)

location_id = location[0]["location_id"]

# init storage
storage = dlm_storage_client.init_storage(
    CONFIG.storage.name,
    CONFIG.location.name,
    location_id,
    CONFIG.storage.type,
    CONFIG.storage.interface,
    CONFIG.storage.capacity,
    CONFIG.storage.phase_level,
)

storage_id = storage[0]["storage_id"]

# create storage config
config = '{"name":"MyDisk","type":"local", "parameters":{}}'
config_id = dlm_storage_client.create_storage_config(storage_id, config=config)

# some path here
path = ""

# then begin adding data items
uid = dlm_ingest_client.register_data_item(
    "/my/ingest/item", path, CONFIG.storage.name, metadata=None
)

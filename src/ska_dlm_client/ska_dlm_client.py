"""Main module."""

from dlm_gateway import dlm_gateway_client
from dlm_storage import dlm_storage_client

from ska_dlm_client import CONFIG

# exchange the token for a cookie
session = dlm_gateway_client.start_session(CONFIG.auth_token, CONFIG.DLM.gateway_url)

# check if the location is known to DLM
locations = dlm_storage_client.query_location(CONFIG.location_name)

# init location
dlm_storage_client.init_location(
    CONFIG.location_name,
    CONFIG.location_type,
    CONFIG.location_country,
    CONFIG.location_city,
    CONFIG.location_facility,
)

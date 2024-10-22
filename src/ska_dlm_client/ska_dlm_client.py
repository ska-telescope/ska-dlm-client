"""Main module."""

import logging

from requests import Session

from . import CONFIG

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


async def init_dlm_session():
    """Initialise a session with the DLM."""
    # setup configuration
    # gateway_configuration = configuration.Configuration(host='http://localhost:8000')

    # start session
    # with api_client.ApiClient(gateway_configuration) as api_client:
    #    api_gateway = gateway_api.GatewayApi(api_client)
    #    api_gateway.session_start_session_post()
    session = Session()
    bearer = {"Authorization": f"Bearer {CONFIG.auth_token}"}
    response = session.post(f"{CONFIG.DLM.url}/start_session", headers=bearer, timeout=60)
    response.raise_for_status()

    # check if this location is already known to DLM
    params = {"location_name": CONFIG.location.name}
    location = session.get(f"{CONFIG.DLM.url}/storage/query_location", params=params, timeout=60)
    logger.info("Query Location: %s", location.json())

    # otherwise, register this location:
    if location is None:
        params = {
            "location_name": CONFIG.location.name,
            "location_facility": CONFIG.location.facility,
        }
        location = session.post(
            f"{CONFIG.DLM.url}/storage/init_location", params=params, timeout=60
        )
        logger.info("Init Location: %s", location.json())

    # get the location id
    location_id = location.json()[0]["location_id"]

    # check if this storage is already known to DLM
    params = {"storage_name": CONFIG.storage.name}
    storage = session.get(f"{CONFIG.DLM.url}/storage/query_storage", params=params, timeout=60)
    logger.info("Query Storage: %s", storage.json())

    # initialise a storage, if it doesn’t already exist:
    if storage is None:
        params = {
            "storage_name": CONFIG.storage.name,
            "location_id": location_id,
            "storage_type": CONFIG.storage.type,
            "storage_interface": CONFIG.storage.interface,
            "storage_capacity": CONFIG.storage.capacity,
        }
        storage = session.post(f"{CONFIG.DLM.url}/storage/init_storage", params=params, timeout=60)
        logger.info("Init Storage: %s", storage.json())

    # get the storage id
    storage_id = storage.json()[0]["storage_id"]

    # TODO: check if a storage config is already known to DLM
    # params = {"storage_id": storage_id}

    # supply a rclone config for this storage, if it doesn’t already exist
    params = {
        "config": {
            "name": CONFIG.storage.name,
            "type": CONFIG.storage.type,
            "parameters": CONFIG.storage.parameters,
        }
    }
    config = session.post(
        f"{CONFIG.DLM.url}/storage/create_storage_config", params=params, timeout=60
    )
    logger.info("Create Storage Config: %s", config.json())

    return session, storage_id


async def post_dlm_data_item(session: Session, storage_id, data):
    """Register Data Item with DLM."""
    params = {
        "item_name": "/my/ingest/item",
        "uri": "/some/path/to/the/file",
        "storage_name": CONFIG.storage.name,
        "storage_id": storage_id,
        "metadata": data,
        "item_format": None,
        "eb_id": None,
    }
    response = session.post(
        f"{CONFIG.DLM.url}/ingest/register_data_item", params=params, timeout=60
    )
    logger.info("Register Data Item: %s", response.json())

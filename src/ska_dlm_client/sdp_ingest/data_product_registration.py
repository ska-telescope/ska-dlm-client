"""Register SDP data-products with DLM."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional

# from ska_dlm_client.openapi import api_client
# from ska_dlm_client.openapi.dlm_api import ingest_api
# from ska_dlm_client.openapi.exceptions import OpenApiException
# from ska_dlm_client.openapi import ApiException

logger = logging.getLogger(__name__)


# pylint: disable=broad-exception-caught
def _resolve_path(p: Path) -> Path:
    """Return absolute, symlink-resolved path; tolerate missing targets."""
    try:
        return p.expanduser().resolve(strict=False)
    except Exception:  # pragma: no cover
        logger.exception("Failed to resolve path %s; using as-is", p)
        return p


def register_data_product(
    data_product_path: str | Path,  # or derive from the SDP key?
    destination_storage: str,  # also accept storage_id?
    metadata: Optional[Dict[str, Any]] = None,
    do_storage_access_check: bool = False,
) -> Optional[str]:
    """Call the DLM server to register an SDP data-product.

    Returns:
        Registration UUID on success, else None.
    """
    src_path = _resolve_path(Path(data_product_path))
    if not src_path.name:
        logger.error("Refusing to register an empty path: %s", data_product_path)
        return None

    product_name = src_path.name
    storage_name = destination_storage  # storage name only (for now)
    # uri = str(src_path)  # TODO: convert to DLM-relative URI if required

    logger.info(
        "Registering data product '%s' -> storage(name)=%s; access_check=%s",
        product_name,
        storage_name,
        do_storage_access_check,
    )
    if metadata is None:
        logger.debug("No metadata provided for '%s'", product_name)
    else:
        logger.debug("Metadata keys for '%s': %s", product_name, list(metadata))

    # --- TODO: Wire in OpenAPI call and return the real UUID --------------
    # try:
    #     with api_client.ApiClient(<ingest_configuration>) as client:
    #         api = ingest_api.IngestApi(client)
    #         resp = api.register_data_product(
    #             product_name=product_name,
    #             uri=uri,
    #             storage_name=storage_name,
    #             do_storage_access_check=do_storage_access_check,
    #             request_body=metadata,
    #         )
    #         return str(resp)
    # except OpenApiException as err:
    #     logger.error(
    #         "OpenApiException caught during register_data_product"
    #     )
    #     if isinstance(err, ApiException):
    #         logger.error("ApiException: %s", err.body)
    #     logger.error("%s", err)
    #     logger.error("Ignoring and continuing.....")
    #     return None
    # ----------------------------------------------------------------------

    logger.warning("register_data_product is currently a stub (no API call).")
    return None

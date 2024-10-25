"""Application to watch a directory for changes and send to DLM."""

import asyncio
import logging
import os

from watchfiles import Change, awatch

from ska_dlm_client.directory_watcher.configuration_details import get_config
from ska_dlm_client.directory_watcher.registration_processor import init
from ska_dlm_client.directory_watcher.testing import (
    init_location_for_testing,
    init_storage_for_testing,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def process_directory_entry_change(entry: tuple[Change, str]):
    """TODO: Test function currently."""
    logger.info("in do process_directory_entry_change %s", entry)
    change_type = entry[0]
    full_path = entry[1]
    relative_path = full_path.replace(f"{config.directory_to_watch}/", "")
    if config.status_file_full_filename == full_path:
        return
    if change_type is Change.added:
        registration_processor.add_path(full_path=full_path, relative_path=relative_path)
    # TODO: Change.deleted Change.modified mayh need support


async def main():
    """Start watching the given directory."""
    async for changes in awatch(config.directory_to_watch):  # type: Set[tuple[Change, str]]
        for change in changes:
            logger.info("in main %s", change)
            process_directory_entry_change(change)


config = get_config()

# TODO: It would be expected that the following config would already be
# completed in prod but leaving in place for now.
location_id = init_location_for_testing(config.storage_configuration)
storage_id = init_storage_for_testing(
    storage_name=config.storage_name,
    storage_configuration=config.storage_configuration,
    the_location_id=location_id,
)
config.storage_id = storage_id
registration_processor = init(config)
for root, dirs, files in os.walk(
    top="/Users/00077990/yanda/pi24/ska-dlm-client/docs/src", topdown=True
):
    print(f"root: {root}, dirs: {dirs}, files: {files}")
# test_ingest_item()

if __name__ == "__main__":
    asyncio.run(main(), debug=None)

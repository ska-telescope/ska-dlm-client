"""Application to verify the state of the DLM client, intended for startup."""

import argparse
import datetime
import logging
import os
import tempfile
import time
from datetime import datetime

import ska_dlm_client.startup_verification.utils as utils
from ska_dlm_client.openapi import ApiException, api_client, configuration
from ska_dlm_client.openapi.dlm_api import request_api
from ska_dlm_client.openapi.exceptions import OpenApiException

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class StartupVerification:
    """Class to perform the startup verification."""

    _dir_to_watch: str
    _request_server_url: str
    _storage_name: str
    data_item_name: str = None

    def __init__(self, directory_to_watch: str, storage_name: str, request_server_url: str):
        """Initialize the StartupVerification class."""
        TEST_FILE_NAME = "testfile"
        self._dir_to_watch = directory_to_watch
        self._request_server_url = request_server_url
        self._storage_name = storage_name
        now = datetime.now()
        timestamp: int = int(now.timestamp())
        with tempfile.TemporaryDirectory(dir=directory_to_watch, prefix=".") as temp_dir:
            logger.info("Created temp dir %s", temp_dir)
            test_file = os.path.join(temp_dir, TEST_FILE_NAME)
            logger.info("testfile name is %s", test_file)
            with open(test_file, "w", encoding="utf-8") as the_file:
                the_file.write(f"Test data item for dlm.startup_verification, {now}")
            logger.info("before setting new_dir")
            new_dir = temp_dir.replace("/.", f"/{timestamp}_dlm_startup_verification-")
            logger.info("Renamed to new dir %s", new_dir)
            os.rename(src=temp_dir, dst=new_dir)
            # wait enough time for
            time.sleep(5)
            # TODO: put back
            # self.data_item_name = os.path.join(new_dir, TEST_FILE_NAME).replace(f"{directory_to_watch}/", "")
            self.data_item_name = os.path.join(new_dir, TEST_FILE_NAME).replace(
                f"{directory_to_watch}/", ""
            )
            os.rename(src=new_dir, dst=temp_dir)
        logger.info("watch directory after cleanup: %s", os.listdir(directory_to_watch))
        logger.info("data item to look for has name %s", self.data_item_name)

    def verify_registration(self) -> bool:
        """Verify the data item was adding by querying the DLM."""
        request_configuration = configuration.Configuration(host=self._request_server_url)
        with api_client.ApiClient(request_configuration) as request_api_client:
            api_request = request_api.RequestApi(request_api_client)
            try:
                logger.info("Verifying startup verification for %s", self.data_item_name)
                data_item_exists = api_request.query_exists(item_name=self.data_item_name)
                return data_item_exists
            except OpenApiException as err:
                logger.error("OpenApiException caught during request.query_data_item: %s", err)
                if isinstance(err, ApiException):
                    logger.error("ApiException: %s", err.body)
                logger.error("%s", err)
                return False


def main():
    """Run main in its own function."""
    verification_passed: bool = False
    try:
        parser = argparse.ArgumentParser(prog="dlm_startup_verification")
        cmd_line_parameters = utils.CmdLineParameters(
            parser, add_directory_to_watch=True, add_storage_name=True, add_request_server_url=True
        )
        cmd_line_parameters.parse_arguments()

        startup_verification = StartupVerification(
            directory_to_watch=cmd_line_parameters.directory_to_watch,
            storage_name=cmd_line_parameters.storage_name,
            request_server_url=cmd_line_parameters.request_server_url,
        )
        verification_passed = startup_verification.verify_registration()
    except Exception as err:
        logger.error(err)
    if verification_passed:
        logger.info("\n\nPASSED startup tests\n")
    else:
        logger.error("\n\nFAILED startup tests\n")
    logger.info("Startup verification completed.")


if __name__ == "__main__":
    main()

# pylint: disable=too-many-instance-attributes
"""Class to hold the configuration used by the directory_watcher package."""
from dataclasses import dataclass
import os
from ska_dlm_client.config import ClientConfig
from ska_dlm_client.config import CmdLineParameters
from ska_dlm_client.openapi.configuration import Configuration

@dataclass
class SdpWatcherConfig(ClientConfig):
    """Running configuration of the SKA DLM client directory watcher.

    This class holds all configuration parameters needed for the ConfigDB watcher
    to monitor flows and register data items with the DLM.
    """
    source_name:str = "configdb-watcher"
    directory_to_watch:str = "/dlm/product_dir"
    reload_status_file: bool = True
    use_status_file: bool = False
    register_contents_of_watch_directory: bool = False

    def __post_init__(self):
        self.status_file_absolute_path = f"{self.directory_to_watch}/{self.STATUS_FILE_FILENAME}"
        self.ingest_configuration = Configuration(host=self.ingest_url)
        self.ingest_register_path_to_add = os.path.relpath(
            path=self.directory_to_watch
        )
        # Migration related options
        self.migration_configuration = Configuration(host=self.migration_url)

@dataclass
class WatcherArgs(CmdLineParameters):
    """
    Adding the additional specific command line arguments for the configdb_watcher
    """
    def __post_init__(self):
        self.__default_args__()

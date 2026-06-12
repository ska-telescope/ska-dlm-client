# pylint: disable=too-many-instance-attributes
"""Class to hold the configuration used by the directory_watcher package."""
import os
from dataclasses import dataclass, field
from ska_dlm_client.config import ClientConfig
from ska_dlm_client.config import CmdLineParameters

from ska_dlm_client.directory_watcher.directory_watcher_entries import DirectoryWatcherEntries
from ska_dlm_client.openapi.configuration import Configuration

@dataclass
class WatcherConfig(ClientConfig):
    """Running configuration of the SKA DLM client directory watcher.

    This class holds all configuration parameters needed for the directory watcher
    to monitor directories and register data items with the DLM.
    """
    source_name: str = "dir-watcher"
    directory_to_watch:str = "/dlm/watch_dir"
    reload_status_file: bool = True
    use_status_file: bool = False
    register_contents_of_watch_directory: bool = False
    directory_watcher_entries: DirectoryWatcherEntries = field(init=False)

    def __post_init__(self):
        self.status_file_absolute_path = f"{self.directory_to_watch}/{self.STATUS_FILE_FILENAME}"
        self.ingest_configuration = Configuration(host=self.ingest_url)
        self.ingest_register_path_to_add = os.path.relpath(
            path=self.directory_to_watch
        )
        # Migration related options
        self.migration_configuration = Configuration(host=self.migration_url)
        self.directory_watcher_entries = DirectoryWatcherEntries()

@dataclass
class WatcherArgs(CmdLineParameters):
    """
    Adding the additional specific command line arguments for the directory_watcher
    """
    def __post_init__(self):
        self.__default_args__()
        self.parser.add_argument(
            "-p",
            "--readiness-probe-file",
            type=str,
            required=True,
            help="The path to the readiness probe file.",
        )
        self.parser.add_argument(
            "--reload_status_file",
            type=bool,
            required=False,
            default=True,
            help="Reload the status file on startup (def: True)",
        )
        self.parser.add_argument(
            "--skip_rclone_access_check_on_register",
            type=bool,
            required=False,
            default=False,
            help="Reload the status file on startup (def: True)",
        )
        self.parser.add_argument(
            "--status_file_absolute_path",
            type=str,
            required=False,
            default="/dlm/watch_dir/.dlm_status",
            help="Path of status file",
        )
        self.parser.add_argument(
            "--register_contents_of_watch_directory",
            type=bool,
            required=False,
            default=False,
            help="Register existing contents (def: False)",
        )
        self.parser.add_argument(
            "--use_polling_watcher",
            type=bool,
            required=False,
            default=False,
            help="Use a polling watcher (def: False)",
        )

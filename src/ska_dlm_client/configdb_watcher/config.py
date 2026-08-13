# pylint: disable=too-many-instance-attributes
"""Class to hold the configuration used by the configdb_watcher package."""
import urllib.parse
from dataclasses import dataclass

from ska_dlm_client.config import ClientConfig, CmdLineParameters
from ska_dlm_client.openapi.configuration import Configuration


@dataclass
class SdpWatcherConfig(ClientConfig):
    """Configuration for the ConfigDB watcher."""

    source_name: str = "configdb-watcher"
    directory_to_watch: str = "/dlm/product_dir"
    reload_status_file: bool = True
    use_status_file: bool = False
    include_existing: bool = False
    etcd_url: str = "http://etcd:2379"
    queue_connection_string: str = "amqp://guest:guest@rabbitmq/"
    queue_exchange_name: str = "dlm.outbox"

    def __post_init__(self):
        """Create derived/processed attributes."""
        self.status_file_absolute_path = f"{self.directory_to_watch}/{self.status_file_filename}"
        self.ingest_configuration = Configuration(host=self.ingest_url)
        self.storage_configuration = Configuration(host=self.storage_url)
        # Migration related options
        self.migration_configuration = Configuration(host=self.migration_url)
        self.request_configuration = Configuration(host=self.request_url)
        self.etcd_host = urllib.parse.urlparse(self.etcd_url).hostname
        self.etcd_port = urllib.parse.urlparse(self.etcd_url).port


@dataclass
class WatcherArgs(CmdLineParameters):
    """Adding the additional specific command line arguments for the configdb_watcher."""

    def __post_init__(self):
        self.__default_args__()
        self.parser.add_argument(
            "--etcd-url",
            type=str,
            required=False,
            help="etcd service URL (def: http://etcd:2379).",
        )
        self.parser.add_argument(
            "--queue-connection-string",
            type=str,
            required=False,
            help="RabbitMQ connection url",
        )
        self.parser.add_argument(
            "--queue-exchange-name",
            type=str,
            required=False,
            help="RabbitMQ exchange.",
        )

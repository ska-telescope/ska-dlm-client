Kafka Watcher
--------------

The Kafka watcher subscribes to a specified Kafka topic and triggers an ingestion when a compliant message is received.

**Calling the Kafka watcher CLI:**

.. code-block:: sh

    $ dlm-kafka-watcher
    usage: dlm-kafka-watcher [-h] [--kafka-topic [KAFKA_TOPIC ...]] --kafka-broker-url KAFKA_BROKER_URL [KAFKA_BROKER_URL ...] --storage-name STORAGE_NAME --ingest-server-url INGEST_URL [--check-rclone-access]
    dlm-kafka-watcher: error: the following arguments are required: --kafka-broker-url, --storage-name, --ingest-server-url


**Required parameters:**

- Kafka broker URL: A URL pointing to the Kafka broker. (``--kafka-broker-url``)
- Kafka topic: The Kafka topic to watch. (``--kafka-topic``)
- Storage name: The storage name to use for registering the files. (``--storage-name``)
- DLM server URL: The URL to the DLM server (``--ingest-server-url``).

**Optional parameters:**

- Prefix to add to the URI of data items being registered. (``--register-dir-prefix``)
- Check rclone access before starting the watcher. (``--check-rclone-access``)
- Use a polling watcher instead of the iNotify event-based watcher. (``--use-polling-watcher``)
- Whether to use the status file. (``--use-status-file``)
- Reload the status file. (``--reload-status-file``)
- An alternative name for the status file. (``--status-file-filename``)

.. note::
   As part of the Kafka message a directory is given to the data product needing to be added. This path must accessible to DLM services to perform the eventual file transfer.

**Module Documentation:**

.. automodule:: ska_dlm_client.kafka_watcher.main
    :members:
    :special-members:

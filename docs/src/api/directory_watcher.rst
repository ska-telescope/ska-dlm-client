Directory Watcher
-------------------

The directory_watcher will watch a given directory and add the file or directory to the DLM.

The directory_watcher requires the following parameters:

* A directory to watch
* The storage name to use for registering the files
* The URL to the DLM server

Optional parameters include:

* Prefix to add to uri of data items being registered
* Use a polling watcher instead of the iNotify event based watcher
* Whether to use the status file
* Reload the status file
* An alternative name for the status file

CLI call example::


    $ dlm_directory_watcher
    usage: dlm_directory_watcher [-h] -d DIRECTORY_TO_WATCH -i INGEST_SERVER_URL
                                 -n STORAGE_NAME [-p REGISTER_DIR_PREFIX]
                                 [--use-polling-watcher | --no-use-polling-watcher]
                                 [--use-status-file | --no-use-status-file]
                                 [--reload-status-file | --no-reload-status-file]
                                 [--status-file-filename STATUS_FILE_FILENAME]
    dlm_directory_watcher: error: the following arguments are required: -d/--directory-to-watch, -i/--ingest-server-url, -n/--storage-name


The additional parameters allow for greater flexibility.

Package level documentation
'''''''''''''''''''''''''''

.. automodule:: ska_dlm_client.directory_watcher.main
    :members:

.. automodule:: ska_dlm_client.directory_watcher.data_product_metadata
    :members:

.. automodule:: ska_dlm_client.directory_watcher.directory_watcher_entries
    :members:

.. automodule:: ska_dlm_client.directory_watcher.minimal_metadata_generator
    :members:

.. automodule:: ska_dlm_client.directory_watcher.registration_processor
    :members:

.. automodule:: ska_dlm_client.directory_watcher.watcher_event_handler
    :members:

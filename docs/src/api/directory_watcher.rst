Directory Watcher
-------------------

.. Move this section somewhere else
The directory_watcher will watch a given directory and add any files or directories that are created after startup to the DLM.

CLI call example::


    $ dlm_directory_watcher
    usage: dlm_directory_watcher [-h] -d DIRECTORY_TO_WATCH -i INGEST_URL
                                 -n STORAGE_NAME [-p REGISTER_DIR_PREFIX]
                                 [--use-polling-watcher | --no-use-polling-watcher]
                                 [--use-status-file | --no-use-status-file]
                                 [--reload-status-file | --no-reload-status-file]
                                 [--status-file-filename STATUS_FILE_FILENAME]
    dlm_directory_watcher: error: the following arguments are required: -d/--directory-to-watch, -i/--ingest-server-url, -n/--storage-name


The directory_watcher requires the following parameters:

* A directory to watch (``-d``)
* The storage name to use for registering the files (``-n``)
* The URL to the DLM server (``-i``)

Optional parameters include:

* Prefix to add to uri of data items being registered (``-p``)
* Use a polling watcher instead of the iNotify event based watcher (``--use-polling-watcher``)
* Whether to use the status file (``--use-status-file``)
* Reload the status file (``--reload-status-file``)
* An alternative name for the status file (``--status-file-filename``)

Module documentation
''''''''''''''''''''

.. automodule:: ska_dlm_client.directory_watcher.main
    :members:

.. automodule:: ska_dlm_client.directory_watcher.directory_watcher
    :members:

.. automodule:: ska_dlm_client.directory_watcher.directory_utils
    :members:

.. automodule:: ska_dlm_client.directory_watcher.directory_watcher_entries
    :members:

.. automodule:: ska_dlm_client.directory_watcher.watcher_event_handler
    :members:

.. automodule:: ska_dlm_client.directory_watcher.config
    :members:

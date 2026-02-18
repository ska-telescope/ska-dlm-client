Deployment
==========

The standard deployment of the ska-dlm-client within the SKA Kubernetes environment uses a set of Helm charts and an associated configuration file. A `sample Deployment <https://gitlab.com/ska-telescope/ska-dlm-client/-/blob/main/resources/sample-deployment.yaml>`_ is provided in the resources directory of the repository. A full guide is also given below.


Clone the repository
------------------

.. code-block:: bash

    git clone --recurse-submodules https://gitlab.com/ska-dlm-client/ska-data-lifecycle.git

Retrieve the available release tags and check out the desired release:

.. code-block:: bash

    cd ska-dlm-client
    git fetch --tags
    git tag --list
    git checkout <release-tag>


Example Deployment
------------------

An example deployment of the ska-dlm-client:

.. code-block:: shell

   helm install -f resources/dp-proj-user.yaml [-n <namespace>] ska-dlm-client charts/ska-dlm-client

This will deploy to the currently configured cluster and namespace.


Values
-------

- ``global.dataProduct.pvc.name``: Name of the location of the data products or the directory to be watched.
- ``global.dataProduct.pvc.read_only``: Should be set to ``true`` for now. This limits the scope of what directory_watcher can do.
- ``setupStorageLocation``: Set to ``true`` if a test location/storage is needed.

**Note:** There is currently overlap between ``ska_dlm_client``, ``directory_watcher``, and ``kafka_watcher``. Values like ``storage_name`` and ``storage_root_directory`` appear in multiple sections because different components may reference different storage locations.

ska_dlm_client
--------------

- ``image``: Container image to use for all watcher components (e.g., ``artefact.skao.int/ska-dlm-client``).
- ``version``: Image tag or version (e.g., ``"1.0.0"``).
- ``storage_name``: The DLM storage location name used during data registration.
- ``storage_root_directory``: Used as the root directory when generating URIs for DLM DB.
- ``securityContext``: Kubernetes context updated during deployment.
- ``ingest_url``: Full HTTP URL of the ingest server.
- ``storage_url``: Full HTTP URL of the storage server.
- ``request_url``: Full HTTP URL of the request server.

directory_watcher
-----------------

- ``enabled``: Whether to deploy the ``directory-watcher`` component.
- ``directory_to_watch``: Filesystem path to monitor for new data products. Must exist within the mounted storage (e.g., ``/dlm/watch_dir``).
- ``storage_root_directory``: Root directory used to generate URIs for the DLM database. Should match ``ska_dlm_client.storage_root_directory``.
- ``skip_rclone_access_check_on_register``: If ``true``, skips verifying rclone access before attempting to register the file.
- ``register_contents_of_watch_directory``: If ``true``, registers all contents of the watch directory at startup, not just newly detected files.

configdb_watcher
-----------------

- TODO

kafka_watcher
---------------

The Kafka watcher is now deprecated. If you are working on an older release of the dlm-client, please set ``enabled: false``.

ssh-storage-access Related Values
----------------------------------

- ``ssh_storage_access``:
  - ``ssh_user_name``: Username to be used for remote SSH connections.
  - ``ssh_uid``: User ID for remote SSH connection.
  - ``ssh_gid``: Group ID for remote SSH connection.
  - ``xxx``: This needs to be one of ``daq``, ``pst`` or ``sdp``. All three can exist.
    - ``enabled``: Value is either ``true`` or ``false``.
    - ``deployment_name``: Name to be used for the Kubernetes deployment.
    - ``service_name``: Name to be used for the Kubernetes service.
    - ``pvc``:
      - ``name``: Name of the PVC to mount.
      - ``mount_path``: Path to mount PVC inside the pod.
      - ``read_only``: Should it be mounted read only.
    - ``secret``:
      - ``pub_name``: Name of the "ssh public key" Kubernetes secret.

startup-verification Related Values
-----------------------------------

- ``startup_verification``:
  - ``enabled``: Enable startup verification.
- ``kubectl``: Values related to the kubectl image used for k8s readiness testing.

Testing
-------

A Helm chart has been created for testing: ``tests/charts/test-ska-dlm-client``.

The test chart is used to configure an existing DLM instance running in the same cluster namespace.

Usage:

.. code-block:: shell

   helm install -f resources/dp-proj-user.yaml test-ska-dlm-client tests/charts/test-ska-dlm-client/
   helm test test-ska-dlm-client
   helm uninstall test-ska-dlm-client

.. note::

   It is expected that the same values file can be used between this test and the ska-dlm-client.

Configuration
--------------

Use the ``src/ska_dlm_client/config.yaml`` file to specify the configuration of the ska-dlm-client. For example:

- The URLs of the DLM (Data Lifecycle Management) service and DPD (Data Product Dashboard) service.
- The Authentication Token used to access the DLM and DPD services.
- The name (and additional details) of the location and storage on which the ska-dlm-client will be run.

Here is an example of the config YAML (refer to the repository for the latest format):

.. code-block:: yaml

   auth_token: "Replace this with the authorization token"

   location:
     name: "MyLocationName"
     type: "MyLocationType"
     country: "MyLocationCountry"
     city: "MyLocationCity"
     facility: "MyLocationFacility"

   storage:
     name: "MyStorageName"
     type: "disk"
     interface: "posix"
     capacity: 100000000
     phase_level: "GAS"

   DLM:
     url: "http://dlm/api"

Startup Verification
---------------------

A ``startup verification`` can be enabled during the deployment of the watcher Helm chart. This will exercise the ``directory watcher`` by:

- Adding a data item to the watch directory.
- Giving the directory watcher a short amount of time to detect and register the data item.
- Querying the DLM request service for the data item name.
- Reporting a ``PASSED`` or ``FAILED`` response (based on the result) to the logs and exiting.

To check the logs of the startup verification pod:

.. code-block:: shell

   kubectl logs <ska dlm client startup-verification pod name>

Sample output:

.. code-block:: none

   2025-04-21 13:08:33,187 - INFO -

   PASSED startup tests

   2025-04-21 13:08:33,187 - INFO - Startup verification completed.

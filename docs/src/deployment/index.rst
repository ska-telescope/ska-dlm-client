Deployment
==========

The standard deployment of the ska-dlm-client within the SKA Kubernetes environment uses a set of Helm charts and an associated configuration file (`values.yaml <https://gitlab.com/ska-telescope/ska-dlm-client/-/blob/main/charts/ska-dlm-client/values.yaml>`_). A full guide is given below.


Clone the ska-dlm-client repository
---------------------------------------

Begin by cloning the GitLab repository:

.. code-block:: bash

  git clone --recurse-submodules https://gitlab.com/ska-telescope/ska-dlm-client.git

Retrieve the available release tags and check out the desired release:

.. code-block:: bash

  cd ska-dlm-client
  git fetch --tags
  git tag --list
  git checkout <release-tag>


.. note::

   Before continuing, confirm that the DLM **server** service pods are running.
   See the `installation guide for DLM server <https://developer.skao.int/projects/ska-data-lifecycle/en/latest/guides/installation/helm_install.html>`_ (*WIP*).


Before deploying, verify that the running DLM server version is compatible with the dlm-client release you intend to deploy.

Next, modify the ``values.yaml`` file as required. The sections below describe the configuration options most likely to require adjustment in typical deployments. Other values should generally be left at their defaults unless you have a specific reason to change them.


Global values
-------------

The global section contains cluster- and deployment-wide settings shared by all components deployed by this chart.

- ``global.dataProduct.pvc.name``: Name of the volume to mount into watcher pods
- ``global.dataProduct.pvc.read_only``: Should be set to ``true`` for now. This limits the scope of what the watchers can do.

.. Mention enums somewhere

Chart feature flags
-------------------

- ``setupStorageLocation``: keep ``false``. Will be removed (DMAN-222), because this functionality is now inside the watcher components themselves.


Shared ska-dlm-client values
----------------------------

- ``image``: Container image to use for all watcher components (e.g., ``artefact.skao.int/ska-dlm-client``).
- ``version``: Image tag or version (e.g., ``"1.0.0"``).
- ``storage_name``: The DLM storage name used during data registration.
- ``storage_root_directory``: Used as the root directory by the startup_verification component.
- ``securityContext``: Kubernetes context updated during deployment.
- ``ingest_url``: Full HTTP URL of the ingest server.
- ``storage_url``: Full HTTP URL of the storage server.
- ``request_server_url``: Full HTTP URL of the request server.


Directory Watcher component
---------------------------

- ``enabled``: Whether to deploy the ``directory-watcher`` component.
- ``directory_to_watch``: Filesystem path to monitor for new data products. Must exist within the mounted storage (e.g., ``/dlm/watch_dir``).
- ``source_storage``: Storage to monitor for new data.
- ``storage_root_directory``: Root directory used to generate URIs for the DLM database.
- ``directory_to_watch``: Directory to monitor for new data.
- ``target_name``: Target storage (where new data will be migrated to)
- ``target_root``: Target storage rot directory.
- ``skip_rclone_access_check_on_register``: If ``true``, skips verifying rclone access before attempting to register the file.
- ``register_contents_of_watch_directory``: If ``true``, registers all contents of the watch directory at startup, not just newly detected files.
- ``migration_url``: Full HTTP URL of the migration server.


Startup Verification
---------------------

- ``startup_verification``: Whether to enable startup verification. Keep ``false`` atm because this code is out of date.

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


ConfigDB Watcher component
--------------------------

- ``enabled``: Whether to deploy the ``configdb-watcher`` component.
- ``ingest_server_url``: Full HTTP URL of the ingest server.
- ``storage_server_url``: Full HTTP URL of the storage server.
- ``source_storage``: Storage where the new data appears.
- ``storage_root_directory``: Root directory used to generate URIs for the DLM database.
- ``migration_destination_storage_name``: Target storage (where new data will be migrated to).
- ``migration_url``: Full HTTP URL of the migration server.
- ``sdp_config.host``: Kubernetes DNS hostname of the external ConfigDB (etcd) service. Leave empty to deploy a local etcd instance.
- ``sdp_config.etcd.enabled``: Optionally enable a local etcd instance (for testing purposes).


Kafka Watcher component (deprecated)
------------------------------------

The Kafka watcher is now **deprecated** (superseded by the ConfigDB Watcher). If you are working on an older release of the dlm-client, please set ``enabled: false``.


.. _deploy-dlm-client:

Deploy dlm-client
-----------------

Once you have customised your ``values.yaml`` file, deploy dlm-client to a Kubernetes cluster (or a local Kubernetes environment) using:

.. code-block:: shell

   helm upgrade --install ska-dlm-client [-n <namespace>] charts/ska-dlm-client

If no namespace is specified, the default namespace associated with your current Kubernetes context will be used.

Example Deployment
------------------

A `sample deployment configuration <https://gitlab.com/ska-telescope/ska-dlm-client/-/blob/main/resources/dp-proj-user.yaml>`_ is provided in the ``resources`` directory of the repository. This example is configured for deployment to the DP cluster.

To deploy using this configuration:

.. code-block:: shell

   helm install -f resources/dp-proj-user.yaml [-n <namespace>] ska-dlm-client charts/ska-dlm-client


.. _uninstall-dlm-client:

Uninstall the chart
-------------------

To remove the dlm-client chart from the cluster:

.. code-block:: shell

   helm uninstall [-n <namespace>] ska-dlm-client


Troubleshooting (*WIP*)
-----------------------

The following are common issues encountered during deployment and suggested resolutions.

**Pods not starting or not syncing after configuration changes**

If pods are not behaving as expected after modifying configuration values, it can help to uninstall and redeploy the chart to ensure all resources are recreated cleanly (see :ref:`uninstall-dlm-client`). After uninstalling, redeploy as described in :ref:`deploy-dlm-client`.

**Helm dependency errors**

If you see an error such as:

::

  Error: INSTALLATION FAILED: An error occurred while checking for chart dependencies.
  You may need to run `helm dependency build` to fetch missing dependencies.

From the chart directory, run ``helm dependency build charts/ska-dlm-client``.

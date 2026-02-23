Deployment
==========

*WIP*

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

  Before continuing, ensure that the DLM **server** service pods are up and running.
  See the `installation guide for DLM server <https://developer.skao.int/projects/ska-data-lifecycle/en/latest/guides/installation/helm_install.html>`_ (*WIP*)


Before deploying, modify the ``values.yaml`` file to suit your needs. The configuration options that are most likely to require modification in typical deployments are described below. The values not mentioned below should generally be left at their default values, unless you have a specific reason to modify them.

Global values
-------------

The global section contains cluster- and deployment-wide settings shared by all components deployed by this chart.

- ``global.dataProduct.pvc.name``: Name of the volume to mount into watcher pods
- ``global.dataProduct.pvc.read_only``: Should be set to ``true`` for now. This limits the scope of what the watchers can do.

.. Mention enums somewhere

Chart feature flags
-------------------

- ``setupStorageLocation``: # keep ``false``. Will be removed (DMAN-222), because this functionality is now inside the watcher components themselves.


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


Kafka Watcher component
-----------------------

The Kafka watcher is now **deprecated** (superseded by the ConfigDB Watcher). If you are working on an older release of the dlm-client, please set ``enabled: false``.


ssh-storage-access
-------------------

- ``ssh_user_name``: Username to be used for remote SSH connections.
- ``ssh_uid``: User ID for remote SSH connection.
- ``ssh_gid``: Group ID for remote SSH connection.
- ``xxx``: This needs to be one of ``daq``, ``pst`` or ``sdp``. If more than one is required, make multiple sections.
- ``xxx.enabled``: Either ``true`` or ``false``.
- ``xxx.deployment_name``: Name to be used for the Kubernetes deployment.
- ``xxx.service_name``: Name to be used for the Kubernetes service.
- ``xxx.pvc.name``: Name of the PVC to mount.
- ``xxx.pvc.mount_path``: Path to mount PVC inside the pod.
- ``xxx.pvc.read_only``: Either ``true`` or ``false``.
- ``xxx.secret.pub_name``: Name of the "ssh public key" Kubernetes secret.


Deploy dlm-client
------------------

Once you have customised your ``values.yaml`` file, deploy dlm-client to a Kubernetes cluster (or a local Kubernetes environment) using:

.. code-block:: shell

  helm upgrade --install ska-dlm-client [-n <namespace>] charts/ska-dlm-client

If no namespace is specified, the default namespace associated with your current Kubernetes context will be used.

Example Deployment
------------------

A `sample deployment configuration <https://gitlab.com/ska-telescope/ska-dlm-client/-/blob/main/resources/dp-proj-user.yaml>`_
is provided in the ``resources`` directory of the repository. This example is configured for deployment to the DP cluster.

To deploy using this configuration:

.. code-block:: shell

  helm install -f resources/dp-proj-user.yaml [-n <namespace>] ska-dlm-client charts/ska-dlm-client


Uninstall the chart
-------------------

.. code-block:: shell

  helm uninstall [-n <namespace>] ska-dlm-client


.. Errors you could come across:
.. Error: INSTALLATION FAILED: An error occurred while checking for chart dependencies. You may need to run `helm dependency build` to fetch missing dependencies...
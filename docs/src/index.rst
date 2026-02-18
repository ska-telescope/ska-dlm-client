Introduction
=============


**Work In Progress**


Welcome to ska-dlm-client's documentation! The ``ska_dlm_client`` package provides client tools for interacting with the
`SKA Data Lifecycle Management (DLM) system <https://developer.skao.int/projects/ska-data-lifecycle/en/latest/overview/index.html>`_,
supporting the ingestion of data products along with their associated metadata.

Two clients are available:

- **Directory Watcher Client**: A general-purpose tool that monitors a specified directory
  and ingests new data products as they appear.

- **ConfigDB Watcher Client**: A tool that monitors the Configuration Database for data-product Flows with a COMPLETED status,
  and ingests new data products under the given pvc_path.

- Note the **Kafka Client** is now deprecated.



.. toctree::
   :maxdepth: 2
   :caption: Contents

   self
   deployment/index

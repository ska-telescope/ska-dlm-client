Welcome to ska-dlm-client's documentation!
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The ska_dlm_client package provides clients for the SKA Data Lifecycle Managment system (DLM) service, enabling ingestion of data products and their metadata. There are three interfaces available, the Kafka Watcher, Directory Watcher, and a lower level interface through the REST API exposed by the DLM. The Kafka client is being used in operations to ingest visibility data products created by the SDP receive pipeline, the Directory Watcher client is used in a more generic way to watch a directory_watcher and ingest new products as soon as they appear there. These two clients are making use of the auto-generated openAPI REST interface, directly interfacing with the REST openAPI is not recommended, but is described here for advanced use cases.


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   api/index
   openapi_readme.md


Indices and tables
^^^^^^^^^^^^^^^^^^

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


Sample Deployment
^^^^^^^^^^^^^^^^^
The clients are being deployed in a Kubernetes cluster, for example, to ingest data products from the SDP receive pipeline. A sample deployment is provided in the resources directory of the repository. For more information on how to deploy the clients in such an environment, view the

`sample deployment <https://gitlab.com/ska-telescope/ska-dlm-client/-/blob/main/resources/sample-deployment.yaml>`_

However, the clients can also be used in a standalone environment, using a CLI interface, for example, to ingest data products from a local directory.
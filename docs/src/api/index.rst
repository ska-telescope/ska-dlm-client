ska_dlm_client Package
======================
The ska_dlm_client package provides two clients for the SKA Data Lifecycle Managment system (DLM) service, enabling ingestion of data products and their metadata.
The Kafka client is being used in operations to ingest visibility data products created by the SDP receive pipeline, the Directory Watcher client is used in a more generic way to watch a configured directory
and ingest new products as soon as they appear there. These two clients are using the openAPI REST interface, directly interfacing with the REST openAPI is not recommended, but is described here for advanced use cases.


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   package
   directory_watcher
   kafka_watcher
   register_storage_location
   startup_verification

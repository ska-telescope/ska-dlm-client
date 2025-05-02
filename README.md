# ska-dlm-client

Client(s) for the SKA Data Lifecycle Manager


## Documentation

[![Documentation Status](https://readthedocs.org/projects/ska-telescope-ska-dlm-client/badge/?version=latest)](https://developer.skao.int/projects/ska-dlm-client/en/latest/?badge=latest)

Additional documentation for this project, particularly the OpenAPI libraries, can be found in the `docs` folder, or browsed in the SKA development portal:

* [ska-dlm-client documentation](https://developer.skatelescope.org/projects/ska-dlm-client/en/latest/index.html "SKA Developer Portal: ska-dlm-client documentation")

## Directory Watcher

The directory_watcher will watch a given directory and add the file or directory to the DLM.

As parameters the directory_watcher requires
- A directory to watch
- The storage name to use for registering the files
- The URL to the DLM server

Optional parameters include
- Prefix to add to uri of data items being registered
- Use a polling watcher instead of the iNotify event based watcher
- Whether to use the status file
- Reload the status file
- An alternative name for the status file

```sh
$ dlm_directory_watcher
usage: dlm_directory_watcher [-h] -d DIRECTORY_TO_WATCH -i INGEST_SERVER_URL
                             -n STORAGE_NAME [-p REGISTER_DIR_PREFIX]
                             [--use-polling-watcher | --no-use-polling-watcher]
                             [--use-status-file | --no-use-status-file]
                             [--reload-status-file | --no-reload-status-file]
                             [--status-file-filename STATUS_FILE_FILENAME]
dlm_directory_watcher: error: the following arguments are required: -d/--directory-to-watch, -i/--ingest-server-url, -n/--storage-name
```

The additional parameters can be given for greater configuration.

### Metadata Handling

Code has been added to generate a "minimal set of metadata" for any dataproduct found without
an identifiable associated metadata file (expecting a file called ska-data-product.yaml). The
exact rules for this are a WIP.

## Execution Modes

The SKA DLM client can run in two modes:

* Kafka Watcher: where the client is triggered by incoming kafka messages on a specified topic
* File System Watcher: where the client is triggered by the creation of a file in a specified directory

In both cases, once triggered, the SKA DLM client proceeds to ingest (register) the new data product
into a DLM service.

## Startup Verification

A `startup verification` can be enabled during the deployment of the watcher helm chart. This will exercise
the `directory watcher` by
* adding a `data item` to the `watch directory`
* give the `directory watcher` a short amount of time to detect and register the `data item`
* query the DLM `request` service for the `data item` name
* report a `PASSED` or `FAILED` response (based on the response) to the logs and exit

It is then possible for anyone to check the logs of the `startup verication` pod to see the status reported, ie

```sh
kubectl logs <ska dlm client startup-verification pod name>
```

With sample output

```
2025-04-21 13:08:33,187 - INFO -

PASSED startup tests

2025-04-21 13:08:33,187 - INFO - Startup verification completed.
```

## Configuration

*Work in progress*

Use the ```src/ska_dlm_client/config.yaml``` file to specify the configuration of the ska-dlm-client. For example:

* the URLs of the DLM (Data Lifecycle Management) service and DPD (Data Product Dashboard) service
* the Authentication Token used to access the DLM and DPD services
* the name (and additional details) of the location and storage on which the ska-dlm-client will be run

Here is an example of the config YAML, but defer to the version in the repository for the latest format and attributes:

```yaml
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
  capacity: 100000000,
  phase_level: "GAS"

DLM:
  url: "http://dlm/api"
```


# Testing

To run automated tests

```sh
make python-test
```

# Data Product Metadata

Metadata can now be loaded and the "execution block" attribute extracted.

This is based on [ADR-55 Definition of metadata for data management at AA0.5](https://confluence.skatelescope.org/display/SWSI/ADR-55+Definition+of+metadata+for+data+management+at+AA0.5).


# Helm Charts

## Deployment

An example deployment of the ska-dlm-client would look like:

```sh
helm install -f resources/dp-proj-user.yaml -n <namespace> ska-dlm-client charts/ska-dlm-client
```

This will deploy to the currently configured cluster and namespace.

NOTE: More production specific values (values files) will be added in a future release.

### Values

* global.dataProduct.pvc.name is the name of the location of the data products or the location of the directory to be watched.
* global.dataProduct.pvc.read_only should be set to `true` for now. This limits the scope of what directory_watcher can do.
* `setupStorageLocation`: Set to `true` if a test location/storage is needed.

**Note:** There is currently overlap between `ska_dlm_client`, `directory_watcher`, and `kafka_watcher`.
Values like `storage_name` and `storage_root_directory` must be defined in multiple sections where needed.

#### ska_dlm_client

  * `image`: Container image to use for all watcher components (e.g., `artefact.skao.int/ska-dlm-client`).
  * `version`: Image tag or version (e.g., `"1.0.0"`).
  * `storage_name`: The DLM storage location name used during data registration.
  * `storage_root_directory`: used as the root directory when generating URIs for DLM DB.
  * `securityContext`: Kubernetes context updated during deployment.
  * `ingest_server_url`: Full HTTP URL of the ingest server.
  * `storage_server_url`: Full HTTP URL of the storage server.
  * `request_server_url`: Full HTTP URL of the request server.

#### directory_watcher

  * `enabled`: Whether to deploy the `directory-watcher` component.
  * `directory_to_watch`: Filesystem path to monitor for new data products. Must exist within the mounted storage (e.g., `/data/dlm/watch_dir`).
  * `storage_root_directory`: Root directory used to generate URIs for the DLM database. Should match `ska_dlm_client.storage_root_directory`.
  * `skip_rclone_access_check_on_register`: If `true`, skips verifying rclone access before attempting to register the file.
  * `register_contents_of_watch_directory`: If `true`, registers all contents of the watch directory at startup, not just newly detected files.

#### kafka_watcher

  * `enabled`: Whether to deploy the `kafka-watcher` component.
  * `kafka_topic`: Kafka topic(s) to subscribe to for ingest event messages.
  * `storage_name`: The DLM storage location name to use when registering data items.
  * `check_rclone_access`: If true, verifies rclone access before attempting registration. Optional.
  - **In production:**
    - Keep `kafka_server_local` as `false`
    - Keep `ingest_server_local` as `false`
    - Provide the following explicitly:
      - `kafka_broker_url` (e.g. `ska-sdp-kafka.dp-shared:9092`)
      - `ska_dlm_client.ingest_server_url` (e.g. `http://ska-dlm-dev-ingest.dp-shared`)
  - **In local development:**
    - Set `kafka_server_local: true`
    - Set `ingest_server_local: true`
    - `kafka_server_local_port`: Port to use for the local Kafka broker. Default is 9092.
    - `ingest_server_local_port`: Port to use for the local ingest server. Default is 80.
    - The Helm chart will automatically construct internal URLs using Kubernetes DNS:
      - Kafka broker URL: `<service>.<namespace>:<port>`
      - Ingest URL: `http://<service>.<namespace>:<port>`


#### ssh-storage-access Related Values

 * `ssh_storage_access`:
    * `ssh_user_name`: the username to be used for remote ssh connections
    * `ssh_uid`: the user ID of the user to be used for remote ssh connection
    * `ssh_gid`: the group ID of the user to be used for remote ssh connection
    * `xxx`: this needs to be one of `daq`, `pst` or `sdp`. All three can exist.
        * `enabled`: value is either `true` or `false`
        * `deployment_name`: the name to be used for the Kubernetes deployment
        * `service_name`: the name to be used for the Kubernetes service
        * `pvc`:
            * `name`: the name of the pvc to mounted
            * `mount_path`: the path to mount pvc inside the pod
            * `read_only`: should it be mounted read only
        * `secret`:
            * `pub_name`: the name of the "ssh public key" Kubernetes secret.

#### startup-verifcation Related Values

 * `startup_verification`:
    * `enabled`: the username to be used for remote ssh connections

 * `kubectl`: values related to the kubectl image used for k8s readiness testing

## Testing

A helm chart has been created for testing ```tests/charts/test-ska-dlm-client.```

The test chart is used to configure an existing DLM instance running in the same cluster
namespace. Additional tests are planned to be developed and ticket YAN-1910 has been created
to track this.

The usage expected is
```sh
helm install -f resources/dp-proj-user.yaml test-ska-dlm-client tests/charts/test-ska-dlm-client/
helm test test-ska-dlm-client
helm uninstall test-ska-dlm-client
```

NOTE: it is expected that the same values file can be used between this test and the ska-dlm-client.


# OpenAPI Generated Client

```ska_dlm_client.openapi``` is an OpenAPI generated RESTful python client for accessing DLM services.

See [OpenAPI README.md](src/ska_dlm_client/openapi/README.md) for further information.

## Version

As openapi-generator was not installed via poetry the version used is shown here.

installation via brew with package details
```sh
$ openapi-generator --version
openapi-generator-cli 7.9.0
  commit : 4145000
  built  : -999999999-01-01T00:00:00+18:00
  source : https://github.com/openapitools/openapi-generator
  docs   : https://openapi-generator.tech/
```

## Contributing

The OpenAPI generated client can be regenerated using exported OpenAPI specs from [ska-data-lifecycle](https://gitlab.com/ska-telescope/ska-data-lifecycle):

* Start the DLM services such that they can be accessed from `http://localhost`
* run `make openapi-code-from-local-dlm`

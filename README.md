# ska-dlm-client

Client(s) for the SKA Data Lifecycle Manager


## Documentation

[![Documentation Status](https://readthedocs.org/projects/ska-telescope-ska-dlm-client/badge/?version=latest)](https://developer.skao.int/projects/ska-dlm-client/en/latest/?badge=latest)

The documentation for this project, including how to get started with it, can be found in the `docs` folder, or browsed in the SKA development portal:

* [ska-dlm-client documentation](https://developer.skatelescope.org/projects/ska-dlm-client/en/latest/index.html "SKA Developer Portal: ska-dlm-client documentation")

## Directory Watcher

The directory_watcher will watch a given directory and add the file or directory to the DLM.

As parameters the directory_watcher requires
- A directory to watch
- The storage name to use for registering the files
- The URL to the DLM server
- The execution block id to use for registering the files

```sh
$ directory_watcher
usage: directory_watcher [-h] -d DIRECTORY_TO_WATCH -n STORAGE_NAME -s SERVER_URL -e EXECUTION_BLOCK_ID
[--reload_status_file RELOAD_STATUS_FILE]
[--ingest_service_port INGEST_SERVICE_PORT]
[--storage_service_port STORAGE_SERVICE_PORT]
[--status_file_filename STATUS_FILE_FILENAME]
```

The additional parameters can be given for greater configuration.

## Execution Modes

The SKA DLM client can run in two modes:

* Kafka Watcher: where the client is triggered by incoming kafka messages on a specified topic
* File System Monitor: where the client is triggered by the creation of a file in a specified directory

In both cases, once triggered, the SKA DLM client proceeds to ingest the new data product into a DLM service.

## Configuration

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


## OpenAPI Generated Client

```ska_dlm_client.openapi``` is an OpenAPI generated RESTful python client for accessing DLM services.

See [OpenAPI README.md](src/ska_dlm_client/openapi/README.md) for further information.

### Version

As openapi-generator was not installed via poetry the version used is shown here.

installation via brew with package details
```sh
$ openapi-generator --version
openapi-generator-cli 7.8.0
  commit : 6bdc452
  built  : -999999999-01-01T00:00:00+18:00
  source : https://github.com/openapitools/openapi-generator
  docs   : https://openapi-generator.tech/
```

### Contributing

The OpenAPI generated client can be regenerated using exported OpenAPI specs from [ska-data-lifecycle](https://gitlab.com/ska-telescope/ska-data-lifecycle):

* Start the DLM services such that they can be accessed from `http://localhost`
* run `make openapi-code-from-local-dlm`

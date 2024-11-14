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
usage: directory_watcher [-h] -d DIRECTORY_TO_WATCH -i INGEST_SERVER_URL -n STORAGE_NAME
                         [--reload-status-file RELOAD_STATUS_FILE]
                         [--status-file-filename STATUS_FILE_FILENAME]
                         [--use-status-file USE_STATUS_FILE]
```

The additional parameters can be given for greater configuration.

NOTE: --test_init and --test_init_storage_url are ONLY used to configure a predefined
location and storage config plus create the given storage name.

## Execution Modes

The SKA DLM client can run in two modes:

* Kafka Watcher: where the client is triggered by incoming kafka messages on a specified topic
* File System Watcher: where the client is triggered by the creation of a file in a specified directory

In both cases, once triggered, the SKA DLM client proceeds to ingest (register) the new data product
into a DLM service.

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

Metadata can now be loaded and execution block id extracted.

This is based on [ADR-55 Definition of metadata for data management at AA0.5](https://confluence.skatelescope.org/display/SWSI/ADR-55+Definition+of+metadata+for+data+management+at+AA0.5).


# Helm Charts

## Deployment

An example deployment of the ska-dlm-client directory watcher would look like

```sh
helm install -f resources/dp-proj-user.yaml ska-dlm-client charts/ska-dlm-client
```

This will deploy to the currently configured cluster and namespace.

NOTE: More production specific values (values files) will be added in a future release.


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

# ska-dlm-client

Client(s) for the SKA Data Lifecycle Manager


## Documentation

[![Documentation Status](https://readthedocs.org/projects/ska-telescope-ska-dlm-client/badge/?version=latest)](https://developer.skao.int/projects/ska-dlm-client/en/latest/?badge=latest)

The documentation for this project, including how to get started with it, can be found in the `docs` folder, or browsed in the SKA development portal:

* [ska-dlm-client documentation](https://developer.skatelescope.org/projects/ska-dlm-client/en/latest/index.html "SKA Developer Portal: ska-dlm-client documentation")

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

### Contributing

The OpenAPI generated client can be regenerated using exported OpenAPI specs from [ska-data-lifecycle](https://gitlab.com/ska-telescope/ska-data-lifecycle):

* Start the DLM services such that they can be accessed from `http://localhost`
* run `make openapi-code-from-local-dlm`

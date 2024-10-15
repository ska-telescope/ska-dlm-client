# ska-dlm-client

Client(s) for the SKA Data Lifecycle Manager


## Documentation

[![Documentation Status](https://readthedocs.org/projects/ska-telescope-ska-dlm-client/badge/?version=latest)](https://developer.skao.int/projects/ska-dlm-client/en/latest/?badge=latest)

The documentation for this project, including how to get started with it, can be found in the `docs` folder, or browsed in the SKA development portal:

* [ska-dlm-client documentation](https://developer.skatelescope.org/projects/ska-dlm-client/en/latest/index.html "SKA Developer Portal: ska-dlm-client documentation")

## Features

* TODO


## OpenAPI Generated Client

```ska_dlm_client.openapi``` is an OpenAPI generated RESTful python client for accessing DLM services.

See [README-OPENAPI.md](README-OPENAPI.md) for further information.

### Contributing

The OpenAPI generated client can be regenerated using exported OpenAPI specs from [ska-data-lifecycle](https://gitlab.com/ska-telescope/ska-data-lifecycle):

* Start the DLM services such that they can be accessed from `http://localhost`
* run `make openapi-code-from-local-dlm`

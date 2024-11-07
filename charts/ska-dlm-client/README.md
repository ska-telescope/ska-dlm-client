# SKA DLM Client Chart

*This is a work in progress*

## Test Deployment

### Minikube Setup

* Start minikube (this is what was used during development but have confirmed other smaller values work)
  ```sh
  minikube start --disk-size 64g --cpus=6 --memory=16384
  ```

* Download the helm dependencies and initialise the database from the root directory of this repository
  ```sh
  make k8s-dep-build
  ```

Refer to
[ska-data-lifecycle documentation](https://gitlab.com/ska-telescope/ska-data-lifecycle/-/blob/main/charts/ska-dlm/README.md)
for more information on starting/running the DLM services.

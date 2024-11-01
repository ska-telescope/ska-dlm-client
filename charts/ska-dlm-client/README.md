# SKA DLM Client Chart

*This is a work in progress*

## Test Deployment

### Minikube Setup

* Start minikube (this is what was used during development but have confirmed other smaller values work)
  ```sh
  minikube start --disk-size 64g --cpus=6 --memory=16384
  ```

* If not already done, you will need to enable the ingress plugin:
  ```sh
  minikube addons enable ingress
  ```

* Download the helm dependencies and initialise the database from the root directory of this repository
  ```sh
  make k8s-dep-build
  ```

  * The chart lock can be regenerated using `make k8s-dep-update`

- Depending on you system you may also need to run `minikube tunnel` in a separate terminal(notably [M1 Macs](https://github.com/kubernetes/minikube/issues/13510)). In this case, you can access ingress services via `localhost` instead of `minikube ip`.


### Running Helm Chart Tests

#### k8s tests

Run the following to test against the running test deployment:
```sh
make k8s-install-chart
make k8s-test
```

Alternatively, installing, testing and uninstalling can be performed manually by running the following respective commands:

```sh
make k8s-install-chart
make k8s-do-test
make k8s-uninstall-chart
```

## Cluster Deployment

To deploy in a cluster k8s environment, DevOps can:

* Select the Kubernetes environment via `export KUBECONFIG="path to kubeconfig"`
* Modify the `resources/initialized-dlm.yaml` file to override helm values
* Install the release using the following commands:

```bash
make k8s-dep-build

KUBE_NAMESPACE=<prod-namespace> HELM_RELEASE=<prod-release-name> HELM_VALUES=resources/<values_file> K8S_SKIP_NAMESPACE=1 make k8s-install-chart
```

* Uninstall a previously deployed release using the following commands:

```bash
KUBE_NAMESPACE=<prod-namespace> HELM_RELEASE=<prod-release-name> HELM_VALUES=resources/<values_file> K8S_SKIP_NAMESPACE=1 make k8s-uninstall-chart
```

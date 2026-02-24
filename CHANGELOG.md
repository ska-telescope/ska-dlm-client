# Version History

## Development

### Updated

* Updated ReadTheDocs documentation.
* Reorganized the values.yaml file.

### Removed

* Unused config files.

## 1.2.3

### Updated

* The ConfigDB Watcher now searches recursively (one level deeper) than the given pvc_subpath.
* Measurement Set paths are always treated as opaque containers.

## 1.2.2

### Updated

* Improved the Directory Watcher readiness behaviour.

### Fixed

* Added support for overriding the rclone remote hostname via an env variable to ensure correct resolution when running in Kubernetes.

## 1.2.1

### Fixed

* ConfigDB Watcher derives the data-product path from the sink’s PVCPath.pvc_subpath.

### Updated

* Extensive re-factoring of the scanning and registration logic, and the migration calls.

## 1.2.0

### Updated

* Updated the readme file.

### Fixed

* Directory Watcher now correctly accepts a configurable storage URL (via --storage-url).
* Various small bug fixes.

### Added

* When deploying a local etcd service, the ConfigDB Watcher pod waits for the etcd pod.
* ConfigDB watcher calls the DLM server to register data-products at the source destination and creates a DLM Dependency.
* Added Helm chart configuration for the ConfigDB Watcher.
* ConfigDB watcher calls the DLM server to register and migrate data-products, and creates a DLM Dependency.
* ska-sdp-configDB watcher that yields matching data-product Flow status events.
* Integration test harness to start DLM services (via Docker Compose).
* Start of integration tests for directory-watcher and kafka-watcher.

### Changed

* DLM Client tests now run against OCI images of DLM server (instead of building the DLM server).
* Refactored the directory-watcher and configdb-watcher helm templates to set arguments using environment variables (instead of CLI args).
* Docker tests now also use environment variables.
* Moved the etcd configuration from a top-level values.yaml section to configdb_watcher.sdp_config.etcd.
* The SSH key is always installed, to allow for re-starts of the container.
* Testing against the new server image (1.3.0).
* Various changes to variable names, e.g. storage_name --> source_storage.
* Kafka Docker image switched from bitnami/kafka to apache/kafka
* kubectl image switched from bitnami/kubectl to artefact.skao.int/ska-ser-utils
* Renamed client CLI arguments and aligned the corresponding Helm values.
* Changed the tests to use a 'testrunner' container, rather than directly running pytest on the host machine.
* Tests now run against OCI images of DLM server, instead of building the DLM server from the GitLab repo.
* Client and server containers in the tests now consistently use the same network.

## 1.1.0

### Added

* Added optional Kafka service to the Helm chart for local development support.
* Added setting of kafka-watcher's command line parameter kafka-base-dir in the helm chart.

### Updated

* Updated OpenAPI spec to match DLM Server Services 1.2.0 release. Minor fixes associated with this.

## 1.0.2

### Fixed

* kafka-watcher now passes item_type of container on register_data_item call.

## 1.0.1

### Fixed

* kafka-watcher now uses path of file to help ensure unique data_item.

## 1.0.0

### Added

* Added rclone access check cmd line arg to kafka watcher.
* Added a startup verification automated process for directory watcher.

### Changed

* Continued to consolidate the helm values.

## 0.1.0

### Added

* Added Kafka server
* Bootstrap repo with ska-cookiecutter-pypackage
* Added directory watcher
* Added command line option and implementation to skip rclone access check on data item register.
* Added support for storage root directory.
* Added support for skip rclone access check.
* Added helm chart gitlab-ci support.
* Added option to register the contents of the watch directory at startup.
* Added ssh storage access pods for each of DAQ, PST and SDP. These are end points for rclone to migrate data.

### Changed

* Registering of data items will now work for files, directories and symlinks created in
the watch directory.
* crc32c is now used during metadata generation to improve performance.
* Updated OpenAPI spec and code for DLM 1.0.0.
no production version released yet.
* Includes return types although the generator doesn't add return type doc strings.
* Metadata is sent in the body of the API request to DLM.
* Updated register process to cater for more metadata location options.

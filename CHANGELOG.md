# Version History

## Development

### Notes

* Still aimed at integration with 1.1.x of DLM server services.

### Added

* Added optional Kafka service to the Helm chart for local development support.
* Documentation updates, particularly around class/method docstrings.
* An offline test mode is added to allow dev testing without full DLM server deployment.
* Added migration ability to directory-watcher that will call copy_data after an ingest.
* Added old documentation related to DLM Client demo in PI26.

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

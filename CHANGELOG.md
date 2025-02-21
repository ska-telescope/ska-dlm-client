# Version History

## Development

### Added

* Added command line option and implementation to skip rclone access check on data item register.

### Changed

* Registering of data items will now work for files, directories and symlinks created in
the watch directory.
* crc32c is now used during metadata generation to improve performance.
* Updated OpenAPI spec and code for DLM server 1.0.0. No change in DLM client version as
no production version released yet.
* Includes return types although the generator doesn't add return type doc strings.
* Metadata is sent in the body of the API request to DLM.

## 0.1.0

### Added

* Added Kafka server
* Bootstrap repo with ska-cookiecutter-pypackage
* Added directory watcher

include .make/base.mk
include .make/python.mk
include .make/oci.mk
include .make/k8s.mk
include .make/helm.mk

DOCKER_COMPOSE = docker compose
# NOTE: removed the -W option from SPHINXOPTS due to warnings from code generated docs.
DOCS_SPHINXOPTS = -n --keep-going
PYTHON_LINE_LENGTH = 99
PYTHON_VARS_AFTER_PYTEST = --ignore=tests/integration -m integration

# The DLM server image to use in integration tests is currently not a released version
DLM_SERVER_IMAGE = registry.gitlab.com/ska-telescope/ska-data-lifecycle/ska-data-lifecycle:81d01d51
# GitlabCI services used in CI

python-test: python-pre-test python-do-test docker-compose-down

python-pre-test:
	$(DOCKER_COMPOSE) --file tests/test_services.docker-compose.yaml up -d

python-do-test:
	$(DOCKER_COMPOSE) --file tests/integration/testrunner.docker-compose.yaml run --entrypoint="pytest --ignore tests/integration" dlm_client_testrunner

integration-test: docker-compose-up run-integration-test docker-compose-down

run-integration-test:
	$(DOCKER_COMPOSE) --file tests/integration/testrunner.docker-compose.yaml up dlm_client_testrunner

docs-pre-build:
	poetry config virtualenvs.create false
	poetry install --no-root --only docs

.PHONY: docs-pre-build openapi-code-from-local-dlm

docker-compose-up: ## Bring up test services in docker
	export SERVER_IMAGE=$(DLM_SERVER_IMAGE) && $(DOCKER_COMPOSE) --file tests/integration/dlm_servers.docker-compose.yaml up -d --wait
	$(DOCKER_COMPOSE) --file tests/test_services.docker-compose.yaml up -d
	$(DOCKER_COMPOSE) --file tests/dlm_clients.docker-compose.yaml up -d

docker-compose-down: ## Shut down test services in docker previously started with docker-compose-up
	$(DOCKER_COMPOSE) --file tests/integration/testrunner.docker-compose.yaml down --volumes --remove-orphans
	export SERVER_IMAGE=$(DLM_SERVER_IMAGE) && $(DOCKER_COMPOSE) --file tests/integration/dlm_servers.docker-compose.yaml down --volumes
	$(DOCKER_COMPOSE) --file tests/dlm_clients.docker-compose.yaml down --volumes
	$(DOCKER_COMPOSE) --file tests/test_services.docker-compose.yaml down --volumes --remove-orphans

oci-build-dlm_directory_watcher:
	make oci-build OCI_IMAGE=ska-dlm-directory_watcher \
	OCI_IMAGE_FILE_PATH=Dockerfile

oci-build-dlm_configdb_watcher:
	make oci-build OCI_IMAGE=ska-dlm-configdb_watcher \
	OCI_IMAGE_FILE_PATH=Dockerfile

openapi-code-from-local-dlm: ## Use the connection to DLM services to retrieve and generate OpenAPI code
	@echo "Using the connection to DLM services to retrieve and generate OpenAPI code"
	cd openapi_client_dlm_specs && sh generate_code.sh

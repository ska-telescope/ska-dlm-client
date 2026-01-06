include .make/base.mk
include .make/python.mk
include .make/oci.mk
include .make/k8s.mk
include .make/helm.mk

DOCKER_COMPOSE = docker compose
# NOTE: removed the -W option from SPHINXOPTS due to warnings from code generated docs.
DOCS_SPHINXOPTS = -n --keep-going
PYTHON_LINE_LENGTH = 99
# GitlabCI services used in CI

python-pre-test: ${SERVICES_UP}

python-post-test: ${SERVICES_DOWN}

integration-tests: docker-compose-up run-integration-tests docker-compose-down

run-integration-tests: 
	pytest -m "integration"

docs-pre-build:
	poetry config virtualenvs.create false
	poetry install --no-root --only docs

.PHONY: docs-pre-build openapi-code-from-local-dlm

docker-compose-up: ## Bring up test services in docker
	$(DOCKER_COMPOSE) --file tests/test-services.docker-compose.yml up --detach --wait

docker-compose-down: ## Shut down test services in docker previously started with docker-compose-up
	$(DOCKER_COMPOSE) --file tests/test-services.docker-compose.yml down

oci-build-dlm_directory_watcher:
	make oci-build OCI_IMAGE=ska-dlm-directory_watcher \
	OCI_IMAGE_FILE_PATH=Dockerfile

oci-build-dlm_configdb_watcher:
	make oci-build OCI_IMAGE=ska-dlm-configdb_watcher \
	OCI_IMAGE_FILE_PATH=Dockerfile

openapi-code-from-local-dlm: ## Use the connection to DLM services to retrieve and generate OpenAPI code
	@echo "Using the connection to DLM services to retrieve and generate OpenAPI code"
	cd openapi_client_dlm_specs && sh generate_code.sh

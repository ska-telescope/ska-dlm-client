include .make/base.mk
include .make/python.mk
include .make/oci.mk
include .make/k8s.mk
include .make/helm.mk

DOCKER_COMPOSE = docker compose
UNIT_COMPOSE = $(DOCKER_COMPOSE) --project-name dlm-client-unit \
	--file tests/testrunner.docker-compose.yaml --file tests/unit-compose.override.yaml
# NOTE: removed the -W option from SPHINXOPTS due to warnings from code generated docs.
DOCS_SPHINXOPTS = -n --keep-going
PYTHON_LINE_LENGTH = 99
PYTHON_VARS_AFTER_PYTEST = --ignore=tests/integration -m integration

export DLM_SERVER_REF

test-cleanup:
	@test -n "$$CI" || (echo "Cleaning up generated test files..." && rm -rf \
		tests/registration_processor/product_dir/product/eb-00000000/ska-sdp/pb-test-20260126-24294 \
		tests/registration_processor/product_dir/product/eb-00000000/ska-sdp/pb-test-20260126-24295)

python-test: python-pre-test python-do-test python-post-test

python-pre-test:
	$(UNIT_COMPOSE) build

python-do-test:
	$(UNIT_COMPOSE) run --rm --entrypoint="pytest --ignore tests/integration $(PYTHON_TEST_FILE)" dlm_client_testrunner

python-post-test:
	$(UNIT_COMPOSE) down --volumes --remove-orphans

# extract all compressed files in `data` directory
extract-test-data:
	./extract_data.sh

integration-test:
	bash ./scripts/dlm-integration.sh test

integration-test-keep:
	bash ./scripts/dlm-integration.sh test-keep

run-integration-test:
	bash ./scripts/dlm-integration.sh run-integration-test

all-tests:
	bash ./scripts/dlm-integration.sh all-tests

run-all-tests:
	bash ./scripts/dlm-integration.sh run-all-tests

docs-pre-build:
	poetry config virtualenvs.create false
	poetry install --no-root --only docs

.PHONY: docs-pre-build openapi-code-from-local-dlm

docker-compose-up: ## Bring up test services in docker
	bash ./scripts/dlm-integration.sh up

docker-compose-down: ## Shut down test services in docker previously started with docker-compose-up
	bash ./scripts/dlm-integration.sh down

oci-build-dlm-client:
	make oci-build OCI_IMAGE=ska-dlm-client \
	OCI_IMAGE_FILE_PATH=Dockerfile

openapi-code-from-local-dlm: ## Use the connection to DLM services to retrieve and generate OpenAPI code
	bash ./scripts/dlm-integration.sh openapi

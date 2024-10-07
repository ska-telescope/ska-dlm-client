include .make/base.mk
include .make/python.mk
include .make/oci.mk

DOCKER_COMPOSE = docker compose
DOCS_SPHINXOPTS = -n -W --keep-going
PYTHON_LINE_LENGTH = 99

# GitlabCI services used in CI, docker compose for local testing only
ifndef GITLAB_CI
SERVICES_UP=docker-compose-up
SERVICES_DOWN=docker-compose-down
endif

python-pre-test: ${SERVICES_UP}

python-post-test: ${SERVICES_DOWN}

docs-pre-build:
	poetry config virtualenvs.create false
	poetry install --no-root --only docs

.PHONY: docs-pre-build

docker-compose-up:
	$(DOCKER_COMPOSE) --file tests/test-services.docker-compose.yml up --detach

docker-compose-down:
	$(DOCKER_COMPOSE) --file tests/test-services.docker-compose.yml down


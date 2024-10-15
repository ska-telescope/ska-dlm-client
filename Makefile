include .make/base.mk
include .make/python.mk

DOCS_SPHINXOPTS = -n -W --keep-going

docs-pre-build:
	poetry config virtualenvs.create false
	poetry install --no-root --only docs

.PHONY: docs-pre-build openapi-code-from-local-dlm

PYTHON_LINE_LENGTH = 99

openapi-code-from-local-dlm: ## Use the connection to DLM services to retrieve and generate OpenAPI code
	@echo "Using the connection to DLM services to retrieve and generate OpenAPI code"
	cd openapi_client_dlm_specs && sh generate_code.sh

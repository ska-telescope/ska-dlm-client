#!/bin/bash
echo removing old directories
rm -rf specs openapi_client_dlm_project

echo running the python script to generate the OpenAPI specs
python3 generate_openapi_specs.py specs

echo running openapi-generatoe to create an OpenAPI project from the spec files
openapi-generator generate --generator-name python --api-package ska_dlm_client.openapi.dlm_api -o openapi_client_dlm_project --package-name ska_dlm_client.openapi --input-spec-root-directory specs/

echo fixing package location of dlm_api
mv openapi_client_dlm_project/ska_dlm_client/openapi/ska_dlm_client/openapi/dlm_api openapi_client_dlm_project/ska_dlm_client/openapi/
rm -rf openapi_client_dlm_project/ska_dlm_client/openapi/ska_dlm_client

echo cleaning up src, tests and docs area of ska_dlm_client for new version of openapi generated code
rm -rf ../src/ska_dlm_client/openapi/ ../tests/openapi/ ../docs/openapi/
mkdir ../docs/openapi ../tests/openapi

echo moving over code to ska_dlm_client project
mv openapi_client_dlm_project/ska_dlm_client/openapi ../src/ska_dlm_client/
mv openapi_client_dlm_project/docs/* ../docs/openapi/
mv openapi_client_dlm_project/test/* ../tests/openapi/
cd ..

echo now running isort and black to fix code \(to some extent\!\) for linting
isort --profile black --line-length 99 src/ska_dlm_client/openapi/ tests/openapi/
black --exclude .+\.ipynb --line-length 99  src/ska_dlm_client/openapi/ tests/openapi/

echo REMEMBER TO UPDATE README.md MANUALLY

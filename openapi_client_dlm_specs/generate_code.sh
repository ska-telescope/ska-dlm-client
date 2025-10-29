#!/bin/bash
#
# fail the script if a command fails
set -e

handle_error() {
    echo "An error occurred on line $1"
    exit 1
}
trap 'handle_error $LINENO' ERR

echo "\nremoving old directories"
rm -rf specs openapi_client_dlm_project

echo "\nrunning the python script to generate the OpenAPI specs"
python3 generate_openapi_specs.py specs

echo "\nrunning openapi-generate to create an OpenAPI project from the spec files"
openapi-generator-cli generate --generator-name python --api-package ska_dlm_client.openapi.dlm_api -o openapi_client_dlm_project --package-name ska_dlm_client.openapi --input-spec-root-directory specs/

echo "\nfixing package location of dlm_api"
mv openapi_client_dlm_project/ska_dlm_client/openapi/ska_dlm_client/openapi/dlm_api openapi_client_dlm_project/ska_dlm_client/openapi/
rm -rf openapi_client_dlm_project/ska_dlm_client/openapi/ska_dlm_client

echo "\nfixing docstrings"
docconvert --in-place -i rest -o numpy openapi_client_dlm_project/ska_dlm_client/openapi/
docconvert --in-place -i rest -o numpy openapi_client_dlm_project/test/

echo "\ncleaning up src, tests and docs area of ska_dlm_client for new version of openapi generated code"
rm -rf ../src/ska_dlm_client/openapi/ ../tests/openapi/ ../docs/src/openapi_dlm_client/
mkdir ../docs/src/openapi_dlm_client ../tests/openapi

echo "\nReplace line in README.md"
sed -i.bak "s|pip install git+https://github.com/GIT_USER_ID/GIT_REPO_ID.git|pip install git+https://gitlab.com/ska-telescope/ska-dlm-client.git|g" openapi_client_dlm_project/README.md
sed -i.bak "s|## Documentation [fF]or|##|g" openapi_client_dlm_project/README.md
# The following fixes the path to the linked service API docs.
sed -i.bak "s|docs/|openapi_dlm_client/|g" openapi_client_dlm_project/README.md

echo "\nmoving over code to ska_dlm_client project"
mv openapi_client_dlm_project/README.md ../docs/src/openapi_readme.md
mv openapi_client_dlm_project/ska_dlm_client/openapi ../src/ska_dlm_client/
mv openapi_client_dlm_project/docs/* ../docs/src/openapi_dlm_client/
mv openapi_client_dlm_project/test/* ../tests/openapi/
cd ..

echo "\nnow running isort and black to fix code \(to some extent\!\) for linting"
isort --profile black --line-length 99 src/ska_dlm_client/openapi/ tests/openapi/
black --exclude .+\.ipynb --line-length 99  src/ska_dlm_client/openapi/ tests/openapi/

#!/bin/bash
#
# Fail the script if a command fails
set -e

REQUIRED_OPENAPI_GENERATOR_VERSION="7.25"
# The generated code is known to have been produced with 7.25.0.
# If intentionally moving to a new minor/major version, account for any changes
# in generator behaviour, update this script as necessary, and bump this version.

handle_error() {
    echo "An error occurred on line $1"
    exit 1
}
trap 'handle_error $LINENO' ERR

# Find available OpenAPI Generator executable
if command -v openapi-generator-cli >/dev/null 2>&1; then
    OPENAPI_GENERATOR="openapi-generator-cli"
elif command -v openapi-generator >/dev/null 2>&1; then
    OPENAPI_GENERATOR="openapi-generator"
else
    echo "Error: OpenAPI Generator executable not found. Check if it needs isntalling."
    exit 1
fi

OPENAPI_GENERATOR_VERSION=$("$OPENAPI_GENERATOR" version)

if [[ "$OPENAPI_GENERATOR_VERSION" != "$REQUIRED_OPENAPI_GENERATOR_VERSION".* ]]; then
    echo "Error: OpenAPI Generator ${REQUIRED_OPENAPI_GENERATOR_VERSION}.x is required."
    echo "Found: $OPENAPI_GENERATOR_VERSION"
    exit 1
fi

printf "\nremoving old directories\n"
rm -rf specs openapi_client_dlm_project

printf "\nrunning the python script to generate the OpenAPI specs\n"
python3 generate_openapi_specs.py specs

printf "\nrunning openapi-generate to create an OpenAPI project from the spec files\n"
"$OPENAPI_GENERATOR" generate \
    --generator-name python \
    --api-package ska_dlm_client.openapi.dlm_api \
    -o openapi_client_dlm_project \
    --package-name ska_dlm_client.openapi \
    --input-spec-root-directory specs/

printf "\nfixing package location of dlm_api\n"
mv openapi_client_dlm_project/ska_dlm_client/openapi/ska_dlm_client/openapi/dlm_api \
    openapi_client_dlm_project/ska_dlm_client/openapi/
rm -rf openapi_client_dlm_project/ska_dlm_client/openapi/ska_dlm_client

printf "\nfixing imports for dlm_api package\n"
grep -rl "ska_dlm_client.openapi.ska_dlm_client.openapi.dlm_api" openapi_client_dlm_project \
    | xargs sed -i.bak \
        's/ska_dlm_client\.openapi\.ska_dlm_client\.openapi\.dlm_api/ska_dlm_client.openapi.dlm_api/g'
find openapi_client_dlm_project -name "*.bak" -delete

printf "\nfixing missing Optional type support in api_client.py\n"
git apply --reject --whitespace=fix < api_client.patch

printf "\nfixing docstrings\n"
docconvert --in-place -i rest -o numpy openapi_client_dlm_project/ska_dlm_client/openapi/
docconvert --in-place -i rest -o numpy openapi_client_dlm_project/test/

printf "\ncleaning up src, tests and docs area of ska_dlm_client for new version of openapi generated code\n"
rm -rf ../src/ska_dlm_client/openapi/ ../tests/openapi/ ../docs/src/openapi_dlm_client/
mkdir ../docs/src/openapi_dlm_client ../tests/openapi

printf "\nreplacing lines in README.md\n"
sed -i.bak \
    "s|pip install git+https://github.com/GIT_USER_ID/GIT_REPO_ID.git|pip install git+https://gitlab.com/ska-telescope/ska-dlm-client.git|g" \
    openapi_client_dlm_project/README.md
sed -i.bak \
    "s|## Documentation [fF]or|##|g" \
    openapi_client_dlm_project/README.md

# The following fixes the path to the linked service API docs.
sed -i.bak \
    "s|docs/|openapi_dlm_client/|g" \
    openapi_client_dlm_project/README.md

printf "\nmoving over code to ska_dlm_client project\n"
mv openapi_client_dlm_project/README.md ../docs/src/openapi_readme.md
mv openapi_client_dlm_project/ska_dlm_client/openapi ../src/ska_dlm_client/
mv openapi_client_dlm_project/docs/* ../docs/src/openapi_dlm_client/
mv openapi_client_dlm_project/test/* ../tests/openapi/
cd ..

printf "\nnow running isort and black to fix code (to some extent!) for linting\n"
isort --profile black --line-length 99 src/ska_dlm_client/openapi/ tests/openapi/
black --exclude .+\.ipynb --line-length 99 src/ska_dlm_client/openapi/ tests/openapi/

printf "\nDone. Now run the tests to make sure nothing broke.\n"
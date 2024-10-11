
To generate openapi-client code first ensure DLM services are running and accessible locally.

Next copy the json spec files.

```sh
curl -H "Accept: application/json" -X GET http://localhost:8000/openapi.json -o specs/gateway_spec.json
curl -H "Accept: application/json" -X GET http://localhost:8001/openapi.json -o specs/ingest_spec.json
curl -H "Accept: application/json" -X GET http://localhost:8002/openapi.json -o specs/request_spec.json
curl -H "Accept: application/json" -X GET http://localhost:8003/openapi.json -o specs/storage_spec.json
curl -H "Accept: application/json" -X GET http://localhost:8004/openapi.json -o specs/migration_spec.json
```

and copy into "specs" directory for passing to openapi-generator

Use your favourite code formatter to "pretty up" the one line version of these json files into something more human friendly.

If required use diff.sh to see what has changed. As a minimum the tags should be different.

If desired use the edit_tags.sh to manually update tags.

Add tag field to all paths

```json
"tags": [
  "gateway|ingest|storage|request|migration"
],
```

```sh
openapi-generator generate --generator-name python --api-package dlm_api -o openapi_client_dlm_project --package-name openapi_client_dlm --input-spec-root-directory specs
```

Copy the generated src, docs, tests and README.md to this project.

Run the following to fix isort complaining during lint

```sh
isort --profile black --line-length 99 src/openapi_client_dlm tests/openapi_client_dlm
black --exclude .+\.ipynb --line-length 99  src/openapi_client_dlm tests/openapi_client_dlm/
```

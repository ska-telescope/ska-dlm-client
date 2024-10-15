#!/bin/bash
echo Do diff on gateway_spec
diff gateway_spec.json specs/gateway_spec.json
echo \\nDo diff on ingest_spec
diff ingest_spec.json specs/ingest_spec.json
echo \\nDo diff on request_spec
diff request_spec.json specs/request_spec.json
echo \\nDo diff on storage_spec
diff storage_spec.json specs/storage_spec.json
echo \\nDo diff on migration_spec
diff migration_spec.json specs/migration_spec.json

#!/bin/bash
mkdir -p /dlm/watch_dir
chown -R ska-dlm:ska-dlm /dlm/watch_dir
chmod g+w /dlm/watch_dir
/etc/init.d/ssh start

case "$1" in
    "directory-watcher")
        CMD="dlm-directory-watcher --directory-to-watch ${SOURCE_ROOT:-/dlm/watch_dir} --source-name ${SOURCE_NAME:-dir-watcher} --source-root ${SOURCE_ROOT:-/dlm/watch_dir} --target-name ${TARGET_NAME:-dlm-archive} --migration-url ${MIGRATION_URL:-http://dlm_migration:8004} --ingest-url ${INGEST_URL:-http://dlm_ingest:8001} --readiness-probe-file /tmp/dlm-client-ready --skip-rclone-access-check-on-register --use-polling-watcher "
        ;;
    "configdb-watcher")

        CMD="SDP_CONFIG_HOST='etcd' dlm-configdb-watcher --source-name ${SOURCE_NAME:-sdp-watcher} --source-root ${SOURCE_ROOT:-/dlm/testing1} --target-name ${TARGET_NAME:-dlm-archive} --storage-url ${STORAGE_URL:-http://dlm_storage:8003} --migration-url ${MIGRATION_URL:-http://dlm_migration:8004} --ingest-url ${INGEST_URL:-http://dlm_ingest:8001}"
        ;;
    *)
        echo "Usage: entrypoint.sh <directory-watcher|configdb-watcher>"
        exit 0;;
esac
source /app/.venv/bin/activate
echo "Executing command: $CMD"
eval $CMD

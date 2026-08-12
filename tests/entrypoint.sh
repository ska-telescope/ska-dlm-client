#!/bin/bash
watcher_mode=${MODE:-$1}
/etc/init.d/ssh start

case "$watcher_mode" in
    "directory-watcher")
        mkdir -p /dlm/watch_dir
        chown -R ska-dlm:ska-dlm /dlm/watch_dir
        chmod g+w /dlm/watch_dir

        CMD="dlm-directory-watcher \
          --location ${LOCATION_NAME:-SKA-DEV} \
          --source-name ${SOURCE_NAME:-dir-watcher} \
          --directory-to-watch ${DIRECTORY_TO_WATCH:-/dlm/watch_dir} \
          --target-name ${TARGET_NAME:-dlm-archive} \
          --migration-url ${MIGRATION_URL:-http://dlm_migration:8004} \
          --storage-url ${STORAGE_URL:-http://dlm_storage:8003} \
          --ingest-url ${INGEST_URL:-http://dlm_ingest:8001} \
          --watcher-hostname ${WATCHER_HOSTNAME:-$(hostname)} \
          --readiness-probe-file "${READINESS_PROBE_FILE:-/tmp/dlm-client-ready}" \
          ${UID_EXPIRATION_DAYS:+--uid-expiration-days ${UID_EXPIRATION_DAYS}} \
          ${OID_EXPIRATION_DAYS:+--oid-expiration-days ${OID_EXPIRATION_DAYS}} \
          ${SKIP_RCLONE_ACCESS_CHECK_ON_REGISTER:+--skip-rclone-access-check-on-register} \
          ${USE_POLLING_WATCHER:+--use-polling-watcher}"
        ;;
    "configdb-watcher")
        CMD="dlm-configdb-watcher \
          --location ${LOCATION_NAME:-SKA-DEV} \
          --source-name ${SOURCE_NAME:-configdb-watcher} \
          --directory-to-watch ${DIRECTORY_TO_WATCH:-/dlm/product_dir} \
          --target-name ${TARGET_NAME:-dlm-archive} \
          --storage-url ${STORAGE_URL:-http://dlm_storage:8003} \
          --migration-url ${MIGRATION_URL:-http://dlm_migration:8004} \
          --ingest-url ${INGEST_URL:-http://dlm_ingest:8001} \
          --etcd-url ${ETCD_URL:-http://etcd:2379} \
          --watcher-hostname ${WATCHER_HOSTNAME:-$(hostname)} \
          ${UID_EXPIRATION_DAYS:+--uid-expiration-days ${UID_EXPIRATION_DAYS}} \
          ${OID_EXPIRATION_DAYS:+--oid-expiration-days ${OID_EXPIRATION_DAYS}} \
          --queue-connection-string ${QUEUE_CONNECTION_STRING} \
          --queue-exchange-name ${QUEUE_EXCHANGE_NAME} "
        ;;
    *)
        echo "Usage: entrypoint.sh <directory-watcher|configdb-watcher>"
        exit 0;;
esac

source /app/.venv/bin/activate
echo "Executing command: $CMD"
eval $CMD

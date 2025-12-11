#!/bin/bash
case "$1" in
    "directory-watcher")
        CMD="dlm-directory-watcher --directory-to-watch /dlm/watch_dir --storage-name dir-watcher --storage-root-directory /dlm/watch_dir --use-polling-watcher --ingest-server-url "http://dlm_ingest:8001" --migration-server-url http://dlm_migration:8004 --migration-destination-storage-name dlm-archive --readiness-probe-file "/tmp/dlm-client-ready" --skip-rclone-access-check-on-register"
        ;;
    "configdb-watcher")
        CMD="SDP_CONFIG_HOST='etcd' dlm-configdb-watcher --source-storage sdp-watcher -r /dlm"
        ;;
    *)
        echo "Usage: entrypoint.sh <directory-watcher|configdb-watcher>"
        exit 0;;
esac
chown -R ska-dlm:ska-dlm /dlm/watch_dir
chmod g+w /dlm/watch_dir
/etc/init.d/ssh start
source /app/.venv/bin/activate
echo "Executing command: $CMD"
eval $CMD

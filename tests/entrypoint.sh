#!/bin/bash
chown -R ska-dlm:ska-dlm /dlm/watch_dir
chmod g+w /dlm/watch_dir
cp /data/.ssh/authorized_keys /home/ska-dlm/.ssh/authorized_keys
chown ska-dlm:root /home/ska-dlm/.ssh/authorized_keys
chmod 600 /home/ska-dlm/.ssh/authorized_keys
/etc/init.d/ssh start
source /dlm/.venv/bin/activate
python3 -m ska_dlm_client.directory_watcher.main --directory-to-watch /dlm/watch_dir --storage-name dlm-watcher --storage-root-directory /dlm --use-polling-watcher --ingest-server-url "http://dlm_ingest:8001" --migration-server-url http://dlm_migration:8004 --migration-destination-storage-name data --readiness-probe-file "/tmp/dlm-client-ready" --skip-rclone-access-check-on-register

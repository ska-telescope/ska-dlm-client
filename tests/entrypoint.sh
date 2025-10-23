#!/bin/bash
cat /data/.ssh/authorized_keys > /home/ska-dlm/.ssh/authorized_keys
chown -R ska-dlm:ska-dlm /home/ska-dlm/.ssh
chown -R ska-dlm:ska-dlm /data/watch_dir
chmod g+w /data/watch_dir
/etc/init.d/ssh start
source /data/.venv/bin/activate
python3 -m ska_dlm_client.directory_watcher.main --directory-to-watch /data/watch_dir --storage-name dlm-watcher --storage-root-directory /data --use-polling-watcher --ingest-server-url "http://dlm_ingest:8001" --migration-server-url http://dlm_migration:8004 --migration-destination-storage-name data --readiness-probe-file "/tmp/dlm-client-ready" --skip-rclone-access-check-on-register

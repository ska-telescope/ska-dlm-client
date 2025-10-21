#!/bin/sh
cat /data/.ssh/authorized_keys > /home/ska-dlm/.ssh/authorized_keys
chown -R ska-dlm:ska-dlm /home/ska-dlm/.ssh
/etc/init.d/ssh start
su ska-dlm -c 'python3 -m ska_dlm_client.directory_watcher.main --directory-to-watch /data/watch_dir --storage-name data --storage-root-directory /data --use-polling-watcher --ingest-server-url "http://dlm_ingest:8001"  --readiness-probe-file "/tmp/dlm-client-ready" --skip-rclone-access-check-on-register'
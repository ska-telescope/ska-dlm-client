#!/bin/bash
set -euo pipefail
# -e  → exit immediately on errors
# -u  → treat unset variables as errors
# -o pipefail → fail if any part of a pipeline fails


############################################
# 1. Ensure the source + destination folders
#    exist AND are readable by the 'ska-dlm'
#    user (the SFTP user for rclone).
############################################

# Make sure /data/SDPBuffer exists (user must bind-mount it)
mkdir -p /data/SDPBuffer
# Change ownership so rclone (running as user ska-dlm) can read it
chown -R ska-dlm:ska-dlm /data/SDPBuffer || true
# Allow read/write/execute for user+group
chmod -R ug+rwX /data/SDPBuffer || true

# Make sure the destination storage folder exists
mkdir -p /data/dest_storage
# Give rclone write access
chown -R ska-dlm:ska-dlm /data/dest_storage
chmod -R ug+rwX /data/dest_storage


############################################
# 2. Start SSH server
#    This is required because rclone connects
#    via SFTP into THIS container.
############################################

/etc/init.d/ssh start
# rclone config has:
#   type = sftp
#   user = ska-dlm
# which means SSH/SFTP must be running.


############################################
# 3. Activate Python virtual environment
#    that was created and baked into /app/.venv
############################################

source /app/.venv/bin/activate
# This ensures python3 -m ... uses the installed
# ska-dlm-client code inside the container.


############################################
# 4. Run the ConfigDB watcher using your CLI
#    and pass in the mandatory arguments.
#
#    The watcher will:
#       - connect to etcd (tests-etcd-1)
#       - listen for FINISHED data-products
#       - ingest + migrate
############################################

python3 -m ska_dlm_client.sdp_ingest.main \
  --src-path /data/SDPBuffer \
  --dest-storage dest_storage

# --src-path tells the watcher where raw MS files are. In reality I'll get the source path from data_dir in the Flow
# --dest-storage tells the watcher which DLM storage name to migrate to

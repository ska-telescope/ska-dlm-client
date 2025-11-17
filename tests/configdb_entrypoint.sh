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
chown -R ska-dlm:ska-dlm /data/SDPBuffer || true
chmod -R 777 /data/SDPBuffer || true

# Ensure SFTP sees paths that DLM/rclone might use
mkdir -p /home/ska-dlm
mkdir -p /home/ska-dlm/data

# Clean up any old symlinks / dirs
rm -rf /home/ska-dlm/SDPBuffer 2>/dev/null || true
rm -rf /home/ska-dlm/data/SDPBuffer 2>/dev/null || true

# Two symlinks pointing at the real source dir
ln -s /data/SDPBuffer /home/ska-dlm/SDPBuffer
ln -s /data/SDPBuffer /home/ska-dlm/data/SDPBuffer

chown -h ska-dlm:ska-dlm /home/ska-dlm/SDPBuffer
chown -h ska-dlm:ska-dlm /home/ska-dlm/data/SDPBuffer


############################################
# 2. Start SSH server
#    This is required because rclone connects
#    via SFTP into THIS container.
############################################

/etc/init.d/ssh start
/usr/sbin/sshd
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

python3 -m ska_dlm_client.register_storage_location.main \
  --storage-server-url "http://dlm_storage:8003"

python3 -m ska_dlm_client.sdp_ingest.main \
  --src-path /data/SDPBuffer \
  --dest-storage dest_storage

# --src-path tells the watcher where raw MS files are. In reality I'll get the source path from data_dir in the Flow
# --dest-storage tells the watcher which DLM storage name to migrate to

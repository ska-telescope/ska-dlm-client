#!/usr/bin/env bash
#
# For dev testing this script will create the daq, pst and sdp SSH public and private keys.
# It writes files named <name>-priv and <name>-pub in the specified directory.
#
# Usage: ./generate_dev_test_keys.sh <directory-to-store-ssh-keys>
#
set -euo pipefail

usage() {
  echo "Usage: $0 <directory-to-store-ssh-keys>"
}

if [ $# -ne 1 ]; then
  echo "Generate the daq, pst and sdp public/private key pairs"
  usage
  exit 1
fi

DIR="$1"

# Create target directory if it doesn't exist
mkdir -p "$DIR"

for system in daq pst sdp; do
  priv="$DIR/${system}-priv"
  pub="$DIR/${system}-pub"

  # Remove any pre-existing files to avoid ssh-keygen prompts
  rm -f "$priv" "$pub" "${priv}.pub"

  # Generate ed25519 keypair with no passphrase
  ssh-keygen -t ed25519 -q -N "" -f "$priv"

  # Rename the public key to the expected "-pub" suffix
  mv -f "${priv}.pub" "$pub"

echo "Created: $(basename "$priv") and $(basename "$pub")"
done

echo "All keys generated in: $DIR"

#!/bin/bash
# Run a command inside the QEMU guest (live system) via rig -> hostfwd :2222.
# Requires: guest booted from qemu-drive.py (hostfwd on rig 127.0.0.1:2222)
# and the operator pubkey in the guest user's authorized_keys.
: "${RIG_HOST:?set RIG_HOST}"
exec ssh -i ~/.ssh/id_ed25519 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
  -o "ProxyCommand=ssh -i $HOME/.ssh/id_ed25519 -o ProxyCommand=none -o StrictHostKeyChecking=no rig@${RIG_HOST} -W %h:%p" \
  -p 2222 user@127.0.0.1 "$@"

#!/bin/bash
# Guest SSH for slice-2 QEMU guests (port 2223 on the rig, chained
# through the rig so the operator private key never leaves this box).
: "${RIG_HOST:?set RIG_HOST}"
exec ssh -i $HOME/.ssh/id_ed25519 \
  -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
  -o ConnectTimeout=8 \
  -o ProxyCommand="ssh -i $HOME/.ssh/id_ed25519 -o ProxyCommand=none -o StrictHostKeyChecking=no -W %h:%p rig@${RIG_HOST}" \
  -p 2223 user@127.0.0.1 "$@"

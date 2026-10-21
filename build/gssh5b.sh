#!/bin/bash
# Guest SSH for slice-5B battery guests, chained through the rig.
# Usage: gssh5b.sh <guest-ssh-port> [ssh args / command...]
# The guest user is the live/install user "user" with the operator
# pubkey (test flavour live session; installed guests get the key
# planted by the 9p bootstrap).
PORT="$1"; shift
GUSER="${GUSER:-user}"
: "${RIG_HOST:?set RIG_HOST}"
exec ssh -i $HOME/.ssh/id_ed25519 \
  -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
  -o ConnectTimeout=10 \
  -o ProxyCommand="ssh -i $HOME/.ssh/id_ed25519 -o ProxyCommand=none -o StrictHostKeyChecking=no -o UserKnownHostsFile=/tmp/rig_kh -W %h:%p rig@${RIG_HOST}" \
  -p "$PORT" "$GUSER"@127.0.0.1 "$@"

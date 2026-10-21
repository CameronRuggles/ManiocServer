#!/bin/bash
# Slice-5B throwaway-guest bootstrap. Runs as root INSIDE a battery
# guest (installed system), invoked from a desktop terminal via one
# monitor-typed sudo line. Gives the operator an SSH+xdotool channel
# into the throwaway guest ONLY (test installs are deleted after
# the battery; production images never see this).
#   usage: bootstrap.sh <guest-tag> <owner-user>
set -x
TAG="${1:-guest}"
OWNER="${2:-user}"
export DEBIAN_FRONTEND=noninteractive
apt-get -o Acquire::Check-Valid-Until=false update -qq
apt-get -o Acquire::Check-Valid-Until=false install -y -qq \
  openssh-server xdotool
systemctl unmask ssh.service 2>/dev/null
systemctl enable --now ssh.service
install -d -m 700 -o "$OWNER" -g "$OWNER" "/home/$OWNER/.ssh"
cat > "/home/$OWNER/.ssh/authorized_keys" <<'PUBKEY'
__OPERATOR_PUBKEY__
PUBKEY
chown "$OWNER:$OWNER" "/home/$OWNER/.ssh/authorized_keys"
chmod 600 "/home/$OWNER/.ssh/authorized_keys"
# The guest nftables base policy blocks the operator's inbound SSH
# (slice-5A operator note); the battery guests are throwaway, so
# flush for the session. The slice-3 gate will notice the drift -
# that is expected in the battery and was recorded in slice 5A too.
nft flush ruleset
echo "bootstrap done tag=$TAG owner=$OWNER ip=$(hostname -I)" \
  > "/mnt/hostshare/bootstrap-$TAG.done" 2>/dev/null || \
  echo "bootstrap done tag=$TAG" > "/tmp/bootstrap-$TAG.done"

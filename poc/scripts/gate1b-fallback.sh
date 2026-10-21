#!/bin/bash
# Gate 1b fallback: single HiddenServicePort line rewrite + SIGHUP (A8 fallback),
# plus A restart-to-reachable measurement (host-tor substitution).
set -u
POC=$HOME/workspace/onion-host-os/poc
SHARED=$POC/shared-rotation
RUNSC="/usr/local/bin/runsc --root /tmp/onionhost-t2-runsc"
ONION=$(cat "$POC/tor-data-host/hs/hostname")
SOCKS=127.0.0.1:19050
exec > >(tee "$POC/logs/gate1b-fallback.txt") 2>&1
echo "=== Gate 1b fallback + restart measure $(date -u +%FT%TZ)"

echo "--- restart B2 (idle, b2.sock)"
$RUNSC state web-b2 >/dev/null 2>&1 && { $RUNSC kill web-b2 9 2>/dev/null; $RUNSC delete web-b2 2>/dev/null; }
$RUNSC --ignore-cgroups --network=none --host-uds=create run --detach --bundle "$POC/bundle-web-b2" web-b2
for i in $(seq 1 30); do
  out=$(curl -sS --max-time 3 --unix-socket "$SHARED/b2.sock" http://localhost/version.txt 2>/dev/null) && break
  sleep 0.5
done
echo "b2_health=$out"

echo "--- stop current A; start A with DIRECT target b1.sock (torrc.fallback)"
[ -f /tmp/onionhost-a.pid ] && kill "$(cat /tmp/onionhost-a.pid)" 2>/dev/null
sleep 2
sed 's#shared-rotation/http.sock#shared-rotation/b1.sock#' "$POC/configs/torrc.rotation" > "$POC/configs/torrc.fallback"
grep HiddenServicePort "$POC/configs/torrc.fallback"
t0=$(date +%s)
tor -f "$POC/configs/torrc.fallback" --Log "notice file $POC/logs/gate1b-a-fallback.log" --PidFile /tmp/onionhost-a-fb.pid &
APID=$!
reach=""
for i in $(seq 1 60); do
  v=$(curl -sS --max-time 15 --socks5-hostname $SOCKS "http://$ONION/version.txt" 2>/dev/null) && { reach=$(( $(date +%s) - t0 )); echo "reachable after ${reach}s version=$v"; break; }
  sleep 10
done
[ -z "$reach" ] && echo "A NOT REACHABLE within ~10 min"

echo "--- rewrite target to b2.sock + SIGHUP"
sed -i 's#shared-rotation/b1.sock#shared-rotation/b2.sock#' "$POC/configs/torrc.fallback"
grep HiddenServicePort "$POC/configs/torrc.fallback"
th=$(date +%s)
kill -HUP "$(cat /tmp/onionhost-a-fb.pid)"
got=""
for i in $(seq 1 30); do
  v=$(curl -sS --max-time 15 --socks5-hostname $SOCKS "http://$ONION/version.txt" 2>/dev/null)
  if [ "$v" = "B2" ]; then got=$(( $(date +%s) - th )); echo "after SIGHUP: version=B2 after ${got}s"; break; fi
  sleep 5
done
[ -z "$got" ] && echo "SIGHUP fallback did NOT switch to B2 (last version=${v:-none})"
grep -i 'reload\|hup' "$POC/logs/gate1b-a-fallback.log" | tail -3
echo "hostname still: $(cat "$POC/tor-data-host/hs/hostname")"
echo "=== fallback end $(date -u +%FT%TZ)"

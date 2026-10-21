#!/bin/bash
# Gate 1b symlink-swap test (DESIGN-v3 A8/A9).
# Preconditions: web-b1 running; host tor (A, substituted) targeting
# shared-rotation/http.sock and published; client tor on 127.0.0.1:19050.
# The download client is rate-limited to 1 MiB/s purely to keep the 200 MiB
# download in flight across the swap + 60 s drain window (deterministic test
# condition; not a server limit).
set -u
POC=$HOME/workspace/onion-host-os/poc
SHARED=$POC/shared-rotation
RUNSC="/usr/local/bin/runsc --root /tmp/onionhost-t2-runsc"
ONION=$(cat "$POC/tor-data-host/hs/hostname")
SOCKS=127.0.0.1:19050
LOG=$POC/logs/gate1b-swap.txt
DL=$POC/tmpwork/big.dl
mkdir -p "$POC/tmpwork"
exec > >(tee "$LOG") 2>&1

echo "=== Gate 1b swap test $(date -u +%FT%TZ) onion=$ONION"
echo "--- start B2 on idle socket b2.sock"
$RUNSC --ignore-cgroups --network=none --host-uds=create \
  run --detach --bundle "$POC/bundle-web-b2" web-b2
echo "b2_start_rc=$?"
for i in $(seq 1 30); do
  out=$(curl -sS --max-time 3 --unix-socket "$SHARED/b2.sock" http://localhost/version.txt 2>/dev/null) && break
  sleep 0.5
done
echo "b2_health=$out"

echo "--- pre-swap version via Tor (expect B1)"
curl -sS --max-time 30 --socks5-hostname $SOCKS "http://$ONION/version.txt" || echo "PRE-SWAP FETCH FAILED rc=$?"

echo "--- begin looping big download via Tor (limit-rate 1M)"
rm -f "$DL"
curl -sS --limit-rate 1M --socks5-hostname $SOCKS -o "$DL" "http://$ONION/big.bin" &
DLPID=$!
echo "download_pid=$DLPID"
sleep 10
sz1=$(stat -c %s "$DL" 2>/dev/null || echo 0)
echo "download_bytes_after_10s=$sz1"

echo "--- atomic symlink swap http.sock -> b2.sock"
python3 - "$SHARED" <<'PY'
import os, sys
shared = sys.argv[1]
tmp = os.path.join(shared, "http.sock.new")
try:
    os.unlink(tmp)
except FileNotFoundError:
    pass
os.symlink("b2.sock", tmp)
os.replace(tmp, os.path.join(shared, "http.sock"))  # atomic rename over
print("symlink_now=", os.readlink(os.path.join(shared, "http.sock")))
PY

fails=0; total=0; declare -A seen=()
for i in $(seq 1 6); do
  total=$((total+1))
  v=$(curl -sS --max-time 20 --socks5-hostname $SOCKS "http://$ONION/version.txt" 2>/dev/null)
  rc=$?
  echo "post-swap req#$i rc=$rc version=${v:-NONE}"
  if [ $rc -ne 0 ] || [ -z "$v" ]; then fails=$((fails+1)); else seen[$v]=1; fi
  sleep 2
done
echo "post-swap small requests: total=$total failed=$fails versions=${!seen[*]}"
sz2=$(stat -c %s "$DL" 2>/dev/null || echo 0)
echo "download_bytes_after_swap=$sz2 (was $sz1) alive=$(kill -0 $DLPID 2>/dev/null && echo yes || echo no)"

echo "--- SIGQUIT old B1 (graceful drain, cap 60 s)"
tq=$(date +%s)
$RUNSC kill web-b1 3 || $RUNSC kill web-b1 SIGQUIT || echo "kill_quit_failed rc=$?"
for i in $(seq 1 6); do
  total=$((total+1))
  v=$(curl -sS --max-time 20 --socks5-hostname $SOCKS "http://$ONION/version.txt" 2>/dev/null)
  rc=$?
  echo "drain req#$i rc=$rc version=${v:-NONE}"
  if [ $rc -ne 0 ] || [ -z "$v" ]; then fails=$((fails+1)); fi
  sleep 2
done
sz3=$(stat -c %s "$DL" 2>/dev/null || echo 0)
echo "download_bytes_during_drain=$sz3 alive=$(kill -0 $DLPID 2>/dev/null && echo yes || echo no)"

echo "--- enforce 60 s drain cap"
while [ $(( $(date +%s) - tq )) -lt 60 ]; do sleep 3; done
st=$($RUNSC state web-b1 2>/dev/null | python3 -c 'import json,sys; print(json.load(sys.stdin).get("status"))' 2>/dev/null || echo gone)
echo "b1_status_at_cap=$st download_alive=$(kill -0 $DLPID 2>/dev/null && echo yes || echo no) bytes=$(stat -c %s "$DL" 2>/dev/null || echo 0)"
if [ "$st" = "running" ]; then
  $RUNSC kill web-b1 9 || true
  sleep 2
  $RUNSC delete web-b1 || true
  echo "b1 force-stopped at cap"
fi
sleep 5
if kill -0 $DLPID 2>/dev/null; then
  kill $DLPID 2>/dev/null; wait $DLPID 2>/dev/null; dlrc="killed-by-harness-after-cut"
else
  wait $DLPID; dlrc=$?
fi
echo "download_final_rc=$dlrc final_bytes=$(stat -c %s "$DL" 2>/dev/null || echo 0) of 209715200"

echo "--- final version via Tor (expect B2)"
curl -sS --max-time 30 --socks5-hostname $SOCKS "http://$ONION/version.txt" || echo "FINAL FETCH FAILED rc=$?"
echo "small_request_totals: total=$total failed=$fails"
echo "=== swap test end $(date -u +%FT%TZ)"

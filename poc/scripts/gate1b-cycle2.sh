#!/bin/bash
# Gate 1b cycle 2: B2 -> B1 swap with an UNLIMITED in-flight Tor download of
# a 30 MiB file (~60 s at the ~0.5 MB/s this sandbox's Tor path sustains),
# to observe nginx graceful drain honestly. Cycle 1's rate-limited client
# stalled at exactly 262144 bytes (harness artifact; unlimited flows fine).
set -u
POC=$HOME/workspace/onion-host-os/poc
SHARED=$POC/shared-rotation
RUNSC="/usr/local/bin/runsc --root /tmp/onionhost-t2-runsc"
ONION=$(cat "$POC/tor-data-host/hs/hostname")
SOCKS=127.0.0.1:19050
DL=$POC/tmpwork/big30.dl
exec > >(tee "$POC/logs/gate1b-cycle2.txt") 2>&1
echo "=== Gate 1b cycle 2 $(date -u +%FT%TZ)"

for B in bundle-web-b1 bundle-web-b2; do
  truncate -s 30M "$POC/$B/rootfs/var/www/html/big30.bin"
done

echo "--- ensure B1 idle-running on b1.sock (symlink currently -> b2)"
$RUNSC state web-b1 >/dev/null 2>&1 && $RUNSC kill web-b1 9 2>/dev/null; $RUNSC delete web-b1 2>/dev/null
$RUNSC --ignore-cgroups --network=none --host-uds=create run --detach --bundle "$POC/bundle-web-b1" web-b1
for i in $(seq 1 30); do
  out=$(curl -sS --max-time 3 --unix-socket "$SHARED/b1.sock" http://localhost/version.txt 2>/dev/null) && break
  sleep 0.5
done
echo "b1_health=$out symlink=$(readlink "$SHARED/http.sock")"

echo "--- start unlimited Tor download of big30.bin (served by B2)"
rm -f "$DL"
curl -sS --socks5-hostname $SOCKS -o "$DL" "http://$ONION/big30.bin" &
DLPID=$!
sleep 12
echo "bytes_after_12s=$(stat -c %s "$DL" 2>/dev/null || echo 0) alive=$(kill -0 $DLPID 2>/dev/null && echo yes || echo no)"

echo "--- swap symlink -> b1.sock"
python3 - "$SHARED" <<'PY'
import os, sys
shared = sys.argv[1]
tmp = os.path.join(shared, "http.sock.new")
try: os.unlink(tmp)
except FileNotFoundError: pass
os.symlink("b1.sock", tmp)
os.replace(tmp, os.path.join(shared, "http.sock"))
print("symlink_now=", os.readlink(os.path.join(shared, "http.sock")))
PY
fails=0
for i in 1 2 3; do
  v=$(curl -sS --max-time 20 --socks5-hostname $SOCKS "http://$ONION/version.txt" 2>/dev/null); rc=$?
  echo "post-swap req#$i rc=$rc version=${v:-NONE}"
  [ $rc -ne 0 ] && fails=$((fails+1))
  sleep 1
done
echo "bytes_at_quit=$(stat -c %s "$DL" 2>/dev/null || echo 0)"

echo "--- SIGQUIT B2 (drain)"
tq=$(date +%s)
$RUNSC kill web-b2 3 || $RUNSC kill web-b2 SIGQUIT || echo quit_failed
completed=no
for i in $(seq 1 9); do
  sleep 10
  b=$(stat -c %s "$DL" 2>/dev/null || echo 0)
  alive=$(kill -0 $DLPID 2>/dev/null && echo yes || echo no)
  st=$($RUNSC state web-b2 2>/dev/null | python3 -c 'import json,sys; print(json.load(sys.stdin).get("status"))' 2>/dev/null || echo gone)
  echo "t+$(( $(date +%s) - tq ))s bytes=$b download_alive=$alive b2_status=$st"
  if [ "$alive" = no ]; then completed=yes; break; fi
  if [ $(( $(date +%s) - tq )) -ge 60 ] && [ "$st" = running ]; then
    echo "cap reached: force-stop B2"
    $RUNSC kill web-b2 9 || true; sleep 2; $RUNSC delete web-b2 || true
    break
  fi
done
sleep 3
if kill -0 $DLPID 2>/dev/null; then kill $DLPID 2>/dev/null; wait $DLPID 2>/dev/null; dlrc=cut; else wait $DLPID; dlrc=$?; fi
echo "download_completed_during_drain=$completed final_rc=$dlrc final_bytes=$(stat -c %s "$DL" 2>/dev/null || echo 0) of 31457280"
v=$(curl -sS --max-time 20 --socks5-hostname $SOCKS "http://$ONION/version.txt" 2>/dev/null)
echo "final version via Tor: ${v:-FAILED}"
echo "=== cycle 2 end $(date -u +%FT%TZ)"

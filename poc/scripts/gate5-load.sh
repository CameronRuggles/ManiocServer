#!/bin/bash
# Gate 5 bounded rendezvous-load attempt against OUR throwaway onion only.
# Usage: gate5-load.sh [seconds] [parallel]
# Counts completed fetches of /version.txt through the client tor and
# reports successes/failures and the sustained rate. Bounded and small:
# this measures what this sandbox can obtain, not a production calibration.
set -u
POC=$HOME/workspace/onion-host-os/poc
ONION=$(cat "$POC/tor-data-host/hs/hostname")
DUR=${1:-60}
PAR=${2:-16}
OUT=$POC/tmpwork/gate5
mkdir -p "$OUT"; rm -f "$OUT"/r.*
echo "gate5 load: duration=${DUR}s parallel=${PAR} onion=$ONION start=$(date -u +%FT%TZ)"
start=$(date +%s)
seq 1 "$PAR" | xargs -P "$PAR" -I{} bash -c '
  end=$(( $(date +%s) + '"$DUR"' ))
  n=0; ok=0; fail=0
  while [ $(date +%s) -lt $end ]; do
    n=$((n+1))
    if curl -sS --max-time 20 --socks5-hostname 127.0.0.1:19050 -o /dev/null "http://'"$ONION"'/version.txt" 2>/dev/null; then
      ok=$((ok+1))
    else
      fail=$((fail+1))
    fi
  done
  echo "$n $ok $fail" > "'"$OUT"'/r.{}"
'
elapsed=$(( $(date +%s) - start ))
tot=0; ok=0; fail=0
for f in "$OUT"/r.*; do read -r a b c < "$f"; tot=$((tot+a)); ok=$((ok+b)); fail=$((fail+c)); done
echo "gate5 result: elapsed=${elapsed}s attempts=$tot ok=$ok fail=$fail sustained_ok_per_sec=$(python3 -c "print(f'{$ok/max($elapsed,1):.2f}')")"

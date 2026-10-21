#!/bin/bash
# Gate 5 baseline on the Stage 1 rig: bounded rendezvous load against the
# rig-hosted throwaway onion, via a local client tor (SocksPort 19054).
set -u
cd "$(dirname "$0")/.." || exit 1
# when copied to the rig, run from ~/rig-poc instead:
[ -f onion.txt ] || cd "$HOME/rig-poc"
ONION=$(cat onion.txt)
DUR=${1:-60}
PAR=${2:-16}
mkdir -p g5out; rm -f g5out/r.*
export ONION DUR
seq 1 "$PAR" | xargs -P "$PAR" -I{} bash -c '
  end=$(( $(date +%s) + DUR )); n=0; ok=0; fail=0
  while [ $(date +%s) -lt $end ]; do
    n=$((n+1))
    if curl -s --max-time 25 --socks5-hostname 127.0.0.1:19054 -o /dev/null "http://$ONION/" 2>/dev/null; then
      ok=$((ok+1))
    else
      fail=$((fail+1))
    fi
  done
  echo "$n $ok $fail" > "g5out/r.{}"
'
awk -v d="$DUR" '{n+=$1; ok+=$2; f+=$3} END {printf "total=%d ok=%d fail=%d sustained-ok-rate=%.2f req/s\n", n, ok, f, ok/d}' g5out/r.*

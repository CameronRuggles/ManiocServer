#!/bin/bash
# Gate 3 miniature: scratch-netns (via unshare -n; named `ip netns exec` is
# setns-blocked in this sandbox) + canonical-JSON comparison (v3 A8 method).
set -u
POC=$HOME/workspace/onion-host-os/poc
GOLD=$POC/configs/nft-golden.nft
ALT=$POC/tmpwork/nft-alt.nft
mkdir -p "$POC/tmpwork"

list_from_file() { # $1=ruleset file, $2=output json
  unshare -n bash -c 'nft -f "$1" && nft -j list table inet onionhost' _ "$1" > "$2" 2>"$2.err"
  return $?
}
list_corrupted() { # golden + one inserted accept rule, then list
  unshare -n bash -c 'nft -f "$1" && nft insert rule inet onionhost output tcp dport 22 accept && nft -j list table inet onionhost' _ "$GOLD" > "$1" 2>"$1.err"
  return $?
}

# Semantically identical to golden: different whitespace/comments/layout and
# the ct-state set written in the other order. Must compare SAME.
cat > "$ALT" <<'EOF'
# alt formatting of the same table: layout, comments, and set order differ
table inet onionhost {
 chain input { type filter hook input priority 0; policy drop;
   iifname "lo" accept;
   tcp flags ack,syn accept;
 }
 chain output { type filter hook output priority 0; policy drop;
   oifname "lo" accept; tcp flags ack,syn accept;
   tcp dport { 8443, 443 } accept;
   udp dport 53 accept;
 }
}
EOF

echo "== reference (golden in scratch netns) =="
list_from_file "$GOLD" "$POC/logs/gate3-ref.json"; echo "list_rc=$?"
echo "== alt formatting (same semantics) =="
list_from_file "$ALT" "$POC/logs/gate3-alt.json"; echo "list_rc=$?"
printf 'compare golden vs alt: '
python3 "$POC/scripts/nft_compare.py" "$POC/logs/gate3-ref.json" "$POC/logs/gate3-alt.json"
echo "compare_rc=$?"
echo "== corrupted live (golden + inserted tcp/22 accept) =="
list_corrupted "$POC/logs/gate3-corrupt.json"; echo "list_rc=$?"
printf 'compare golden vs corrupted: '
python3 "$POC/scripts/nft_compare.py" "$POC/logs/gate3-ref.json" "$POC/logs/gate3-corrupt.json"
echo "compare_rc=$? (1 expected: mismatch detected)"

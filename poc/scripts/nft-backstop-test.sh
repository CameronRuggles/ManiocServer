#!/bin/bash
# Gate 2b companion: prove an nft back-stop rule actually drops traffic in a
# scratch netns (the exercisable part in this sandbox; B itself lives in a
# gVisor netns that host nft cannot see into — recorded in POC-RESULTS).
set -u
unshare -n bash -s <<'INNER'
set -u
ip link set lo up
cd /tmp
python3 -m http.server 18099 --bind 127.0.0.1 >/dev/null 2>&1 &
SRV=$!
sleep 1
code1=$(curl -s -o /dev/null -w '%{http_code}' --max-time 3 http://127.0.0.1:18099/ || echo FAIL)
echo "baseline (no nft drop): HTTP $code1"
cat > /tmp/backstop.nft <<'EOF'
table inet backstop {
    chain output {
        type filter hook output priority 0; policy accept;
        oifname "lo" tcp dport 18099 counter drop
    }
}
EOF
nft -f /tmp/backstop.nft
out=$(curl -s -o /dev/null -w '%{http_code}' --max-time 3 http://127.0.0.1:18099/ 2>&1)
rc=$?
echo "with nft drop rule: curl_rc=$rc out=$out (expect failure: dropped)"
nft -j list table inet backstop | grep -o '"counter": {"packets": [0-9]*' | head -1 || true
kill $SRV 2>/dev/null
INNER

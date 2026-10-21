#!/bin/bash
# Gate H: headers over Tor (DESIGN-v3 A8).
# Preconditions: bundle-web-headers built; host tor A stopped; this script
# starts A with configs/torrc.headers (same throwaway HS identity, target =
# shared-headers/http.sock) and the client tor on 19050 already running.
set -u
POC=$HOME/workspace/onion-host-os/poc
B=$POC/bundle-web-headers
SHARED=$POC/shared-headers
RUNSC="/usr/local/bin/runsc --root /tmp/onionhost-t2-runsc"
ONION=$(cat "$POC/tor-data-host/hs/hostname")
SOCKS=127.0.0.1:19050
exec > >(tee "$POC/logs/gateh-test.txt") 2>&1
echo "=== Gate H $(date -u +%FT%TZ) onion=$ONION"

$RUNSC state web-headers >/dev/null 2>&1 && { $RUNSC kill web-headers 9 2>/dev/null; $RUNSC delete web-headers 2>/dev/null; }
$RUNSC --ignore-cgroups --network=none --host-uds=create run --detach --bundle "$B" web-headers
for i in $(seq 1 30); do
  curl -sS --max-time 3 --unix-socket "$SHARED/http.sock" -o /dev/null http://localhost/ 2>/dev/null && break
  sleep 0.5
done
echo "local socket health: rc=$?"

echo "--- start host tor A -> shared-headers"
tor -f "$POC/configs/torrc.headers" --Log "notice file $POC/logs/gateh-host-a.log" --PidFile /tmp/onionhost-a-h.pid &
APID=$!
for i in $(seq 1 36); do
  grep -q 'Bootstrapped 100%' "$POC/logs/gateh-host-a.log" 2>/dev/null && break
  sleep 5
done
grep 'Bootstrapped 100%' "$POC/logs/gateh-host-a.log" | tail -1 || echo "A bootstrap incomplete"

fetch_headers() { curl -sS -D - -o /dev/null --max-time 30 --socks5-hostname $SOCKS "http://$ONION/" 2>/dev/null; }

echo "--- wait for service + fetch headers (v1)"
for i in $(seq 1 20); do
  H=$(fetch_headers) && [ -n "$H" ] && break
  sleep 6
done
echo "$H"
LM1=$(printf '%s' "$H" | grep -i '^Last-Modified:' | tr -d '\r' | cut -d' ' -f2-)
ET1=$(printf '%s' "$H" | grep -i '^ETag:' | tr -d '\r' | cut -d' ' -f2-)
echo "LM1=$LM1 ET1=$ET1"
printf '%s' "$H" | grep -qi '^Date:' && echo "DATE HEADER: PRESENT (bad)" || echo "DATE HEADER: ABSENT (good)"
stat -c 'file mtime epoch=%Y' "$B/rootfs/var/www/html/index.html"

echo "--- revalidation with If-None-Match (expect 304)"
curl -sS -o /dev/null -w 'status=%{http_code}\n' --max-time 30 --socks5-hostname $SOCKS -H "If-None-Match: $ET1" "http://$ONION/"
echo "--- revalidation with If-Modified-Since (expect 304)"
curl -sS -o /dev/null -w 'status=%{http_code}\n' --max-time 30 --socks5-hostname $SOCKS -H "If-Modified-Since: $LM1" "http://$ONION/"

echo "--- edit content -> publisher mtime -> conditional fetch with OLD etag (expect 200 + new LM/ETag)"
printf '<!doctype html><title>OnionHost PoC</title><h1>Gate H headers test — version 2</h1>\n' > "$B/rootfs/var/www/html/index.html"
python3 "$POC/scripts/publisher_mtime.py" "$B/rootfs/var/www/html/index.html"
stat -c 'file mtime epoch=%Y' "$B/rootfs/var/www/html/index.html"
H2=$(curl -sS -D - -o /dev/null --max-time 30 --socks5-hostname $SOCKS -H "If-None-Match: $ET1" "http://$ONION/" 2>/dev/null)
echo "$H2"
LM2=$(printf '%s' "$H2" | grep -i '^Last-Modified:' | tr -d '\r' | cut -d' ' -f2-)
ET2=$(printf '%s' "$H2" | grep -i '^ETag:' | tr -d '\r' | cut -d' ' -f2-)
echo "LM2=$LM2 ET2=$ET2"
[ "$ET2" != "$ET1" ] && echo "ETAG CHANGED WITH CONTENT: yes" || echo "ETAG CHANGED: NO"
[ "$LM2" != "$LM1" ] && echo "LAST-MODIFIED CHANGED WITH CONTENT: yes" || echo "LAST-MODIFIED CHANGED: NO"

kill $APID 2>/dev/null
echo "=== Gate H end $(date -u +%FT%TZ)"

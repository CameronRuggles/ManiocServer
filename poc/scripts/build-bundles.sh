#!/bin/bash
# Build standalone OCI bundles (web=nginx, tor) from rootfs-base2 for runsc.
set -e
POC=$HOME/workspace/onion-host-os/poc
mkdir -p $POC/shared-web && chmod 777 $POC/shared-web

for name in web tor; do
  B=$POC/bundle-$name
  rm -rf $B; mkdir -p $B/rootfs
  cp -a $POC/rootfs-base2/. $B/rootfs/
  (cd $B && /usr/local/bin/runsc spec -- /bin/true >/dev/null)
done

# --- B: nginx config ---
cat > $POC/bundle-web/rootfs/etc/nginx/poc.conf <<'EOF'
worker_processes 1;
pid /tmp/nginx.pid;
error_log /tmp/error.log notice;
events { worker_connections 64; }
http {
  types { text/html html; }
  access_log /tmp/access.log;
  client_body_temp_path /tmp/cb; proxy_temp_path /tmp/px;
  fastcgi_temp_path /tmp/fc; uwsgi_temp_path /tmp/uw; scgi_temp_path /tmp/sc;
  server {
    listen unix:/run/web/http.sock;
    root /var/www/html;
    location / { index index.html; }
  }
}
EOF

# --- A: torrc (golden options + DataDirectory inside sandbox rootfs) ---
cat > $POC/bundle-tor/rootfs/etc/tor/torrc-poc <<'EOF'
DataDirectory /var/lib/tor
SocksPort 0
Log notice stderr
HiddenServiceDir /var/lib/tor/hs
HiddenServicePort 80 unix:/run/web/http.sock
HiddenServicePoWDefensesEnabled 1
HiddenServicePoWQueueRate 250
HiddenServicePoWQueueBurst 500
HiddenServiceEnableIntroDoSDefense 1
HiddenServiceEnableIntroDoSRatePerSec 25
HiddenServiceEnableIntroDoSBurstPerSec 200
HiddenServiceNumIntroductionPoints 3
HiddenServiceMaxStreams 50
HiddenServiceMaxStreamsCloseCircuit 1
EOF
echo "bundles staged"

#!/bin/bash
# Build two Gate 1b web bundles (B1/B2) from tranche 1's bundle-web.
# Both bind-mount the same host socket directory; each listens on its own
# socket (b1.sock / b2.sock). Tor targets the host-owned symlink http.sock.
set -eu
POC=$HOME/workspace/onion-host-os/poc
SHARED=$POC/shared-rotation
mkdir -p "$SHARED"
chmod 777 "$SHARED"
rm -f "$SHARED"/b1.sock "$SHARED"/b2.sock "$SHARED"/http.sock "$SHARED"/http.sock.new

for n in 1 2; do
  B=$POC/bundle-web-b$n
  rm -rf "$B"
  cp -a "$POC/bundle-web" "$B"
  python3 - "$B/config.json" "$B" "$SHARED" <<'PY'
import json, sys
cfg_path, bundle, shared = sys.argv[1:4]
with open(cfg_path) as f:
    cfg = json.load(f)
cfg["root"]["path"] = bundle + "/rootfs"
for m in cfg.get("mounts", []):
    if m.get("destination") == "/run/web":
        m["source"] = shared
with open(cfg_path, "w") as f:
    json.dump(cfg, f, indent=1)
PY
  cat > "$B/rootfs/etc/nginx/poc.conf" <<EOF
user root;
worker_processes 1;
pid /tmp/nginx.pid;
error_log /tmp/error.log notice;
events { worker_connections 128; }
http {
  types { text/html html; text/plain txt; application/octet-stream bin; }
  access_log /tmp/access.log;
  client_body_temp_path /tmp/cb; proxy_temp_path /tmp/px;
  fastcgi_temp_path /tmp/fc; uwsgi_temp_path /tmp/uw; scgi_temp_path /tmp/sc;
  server {
    listen unix:/run/web/b$n.sock;
    root /var/www/html;
    location / { index index.html; }
  }
}
EOF
  printf 'B%s\n' "$n" > "$B/rootfs/var/www/html/version.txt"
  printf '<!doctype html><title>OnionHost PoC</title><h1>Gate 1b rotation: B%s</h1>\n' "$n" \
    > "$B/rootfs/var/www/html/index.html"
  # 200 MiB download payload (sparse zeros; Content-Length is real).
  truncate -s 200M "$B/rootfs/var/www/html/big.bin"
done

# Initial host-owned symlink: http.sock -> b1.sock (atomically replaced later).
ln -s b1.sock "$SHARED/http.sock"
echo "rotation bundles staged: bundle-web-b1 bundle-web-b2; shared=$SHARED"

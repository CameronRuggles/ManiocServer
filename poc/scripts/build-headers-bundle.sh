#!/bin/bash
# Build the Gate H web bundle: tranche-1 web bundle + Debian-packaged
# headers-more module + a test page whose mtime is publisher-derived.
set -eu
POC=$HOME/workspace/onion-host-os/poc
B=$POC/bundle-web-headers
SHARED=$POC/shared-headers
DEB=$(ls "$HOME"/libnginx-mod-http-headers-more-filter_*_amd64.deb 2>/dev/null | head -1 || true)
if [ -z "$DEB" ]; then
  (cd "$POC/debs" && apt-get download libnginx-mod-http-headers-more-filter >/dev/null)
  DEB=$(ls "$POC"/debs/libnginx-mod-http-headers-more-filter_*_amd64.deb | head -1)
fi

rm -rf "$B" "$SHARED"
cp -a "$POC/bundle-web" "$B"
mkdir -p "$SHARED" "$B/rootfs/usr/lib/nginx/modules"
chmod 777 "$SHARED"
TMPX=$(mktemp -d)
dpkg-deb -x "$DEB" "$TMPX"
cp "$TMPX/usr/lib/nginx/modules/ngx_http_headers_more_filter_module.so" \
   "$B/rootfs/usr/lib/nginx/modules/"
rm -rf "$TMPX"

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

cat > "$B/rootfs/etc/nginx/poc.conf" <<'EOF'
load_module /usr/lib/nginx/modules/ngx_http_headers_more_filter_module.so;
user root;
worker_processes 1;
pid /tmp/nginx.pid;
error_log /tmp/error.log notice;
events { worker_connections 64; }
http {
  types { text/html html; }
  access_log /tmp/access.log;
  client_body_temp_path /tmp/cb; proxy_temp_path /tmp/px;
  fastcgi_temp_path /tmp/fc; uwsgi_temp_path /tmp/uw; scgi_temp_path /tmp/sc;
  more_clear_headers Date;
  server {
    listen unix:/run/web/http.sock;
    root /var/www/html;
    location / {
      index index.html;
      more_set_headers "Cache-Control: public, max-age=60";
    }
  }
}
EOF

printf '<!doctype html><title>OnionHost PoC</title><h1>Gate H headers test — version 1</h1>\n' \
  > "$B/rootfs/var/www/html/index.html"
python3 "$POC/scripts/publisher_mtime.py" "$B/rootfs/var/www/html/index.html"
echo "headers bundle staged: $B (shared=$SHARED)"

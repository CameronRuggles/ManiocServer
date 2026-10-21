#!/bin/bash
# Assemble a minimal Ubuntu rootfs (tor + nginx-light + dep closure) from apt
# .debs via dpkg-deb extraction (no mknod available in this sandbox), then
# `podman import` it — the same no-registry approach as DESIGN-v3 A6.
set -e
POC=$HOME/workspace/onion-host-os/poc
ROOTFS=$POC/rootfs-base
mkdir -p "$ROOTFS"

apt-get install --download-only -y --no-install-recommends tor nginx-light dash coreutils iproute2 procps util-linux > $POC/logs/gate1-apt-download.log 2>&1
echo "debs downloaded: $(ls /var/cache/apt/archives/*.deb | wc -l)"

for d in /var/cache/apt/archives/*.deb; do dpkg-deb -x "$d" "$ROOTFS"; done

# Minimal handcrafted /etc (base-passwd postinst normally does this)
cat > "$ROOTFS/etc/passwd" <<'EOF'
root:x:0:0:root:/root:/bin/sh
nobody:x:65534:65534:nobody:/nonexistent:/usr/sbin/nologin
www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin
debian-tor:x:100:100::/var/lib/tor:/bin/false
EOF
cat > "$ROOTFS/etc/group" <<'EOF'
root:x:0:
nogroup:x:65534:
www-data:x:33:
debian-tor:x:100:
EOF
printf 'passwd: files\ngroup: files\nhosts: files\n' > "$ROOTFS/etc/nsswitch.conf"
printf '127.0.0.1 localhost\n' > "$ROOTFS/etc/hosts"
mkdir -p "$ROOTFS/var/lib/tor" "$ROOTFS/run/web" "$ROOTFS/var/log/nginx" "$ROOTFS/var/cache/nginx"
printf '<!doctype html><title>OnionHost PoC</title><h1>Gate 1: served from a no-network container, over Tor</h1>\n' > "$ROOTFS/var/www/html/index.html" 2>/dev/null || { mkdir -p "$ROOTFS/var/www/html"; printf '<!doctype html><title>OnionHost PoC</title><h1>Gate 1: served from a no-network container, over Tor</h1>\n' > "$ROOTFS/var/www/html/index.html"; }

tar -C "$ROOTFS" -cf - . | podman import --change 'CMD ["/bin/sh"]' - localhost/onionhost/poc-base:local
podman images | grep poc-base

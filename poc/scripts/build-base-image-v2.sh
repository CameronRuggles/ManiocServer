#!/bin/bash
# v2: full dependency closure via apt-cache depends --recurse (independent of
# host install state), `apt-get download` (fetches .debs even for packages the
# host already has), dpkg-deb extraction, usrmerge symlinks, podman import.
set -e
POC=$HOME/workspace/onion-host-os/poc
DEBS=$POC/debs; ROOTFS=$POC/rootfs-base2
rm -rf "$ROOTFS"; mkdir -p "$DEBS" "$ROOTFS"

SEED="tor nginx-light dash coreutils iproute2 procps util-linux"
PKGS=$(apt-cache depends --recurse --no-recommends --no-suggests --no-conflicts \
        --no-breaks --no-replaces --no-enhances $SEED 2>/dev/null \
       | grep -E '^[a-zA-Z0-9][a-zA-Z0-9+.-]*$' | sort -u)
echo "closure packages: $(echo "$PKGS" | wc -l)"
cd "$DEBS"
for p in $PKGS; do apt-get download "$p" >/dev/null 2>&1 || echo "download failed: $p"; done
echo "debs: $(ls *.deb | wc -l)"
for d in *.deb; do dpkg-deb -x "$d" "$ROOTFS"; done

# usrmerge compatibility links (postinst would do this in a real install)
cd "$ROOTFS"
[ -d usr/bin ] && [ ! -e bin ] && ln -s usr/bin bin
[ -d usr/lib ] && [ ! -e lib ] && ln -s usr/lib lib
[ -d usr/lib64 ] && [ ! -e lib64 ] && ln -s usr/lib64 lib64
[ -d usr/sbin ] && [ ! -e sbin ] && ln -s usr/sbin sbin
[ -e usr/bin/dash ] && ln -sf dash usr/bin/sh
mkdir -p etc var/lib/tor run/web var/log/nginx var/cache/nginx var/www/html tmp
cat > etc/passwd <<'EOF'
root:x:0:0:root:/root:/bin/sh
nobody:x:65534:65534:nobody:/nonexistent:/usr/sbin/nologin
www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin
debian-tor:x:100:100::/var/lib/tor:/bin/false
EOF
printf 'root:x:0:\nnogroup:x:65534:\nwww-data:x:33:\ndebian-tor:x:100:\n' > etc/group
printf 'passwd: files\ngroup: files\nhosts: files\n' > etc/nsswitch.conf
printf '127.0.0.1 localhost\n' > etc/hosts
printf '<!doctype html><title>OnionHost PoC</title><h1>Gate 1: served from a no-network container, over Tor</h1>\n' > var/www/html/index.html
ls -la "$ROOTFS/lib64/" | head -3; ls "$ROOTFS/usr/bin/tor" "$ROOTFS/usr/sbin/nginx" "$ROOTFS/usr/bin/dash"
tar -C "$ROOTFS" -cf - . | podman import --change 'CMD ["/bin/sh"]' - localhost/onionhost/poc-base:local
podman images | grep poc-base

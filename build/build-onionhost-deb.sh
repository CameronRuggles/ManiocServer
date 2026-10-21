#!/bin/bash
# Build the signed-channel `onionhost` package from the product tree
# (Gate 4 / DESIGN-v2 §7: the maintainer signs exactly one thing -
# this small package: golden config, wizard, dashboard, units).
#
#   build-onionhost-deb.sh VERSION OUTDIR [--floor X] [--extra-dir D]
#                          [--sabotage]
#
# Payload: rootfs-overlay's etc/ + usr/ (the runtime system), minus
# etc/calamares (installer-only) and all __pycache__. var/ is NEVER
# packaged: live owner data (site content, state) is not dpkg's
# business - the ISO plants the seed, updates never touch it.
#
# --floor X   write {"onionhost": "X"} as this release's security
#             floor (default: the tree's usr/share/onionhost/
#             floor.json). The floor travels inside the signed
#             package and drives onionhost-update's rollback /
#             fail-closed decisions (DESIGN-v3 A6/Y8).
# --extra-dir D  merge extra payload (proof harnesses only).
# --sabotage  PROOF ONLY: replace the stack launcher from the extra
#             dir with one that always fails, producing a package
#             whose install succeeds but whose stack never starts -
#             the broken-update case for health-check tests.
set -euo pipefail
SRC=${OH_OVERLAY:-$HOME/workspace/onion-host-os/onionhost/rootfs-overlay}
VERSION=${1:?usage: build-onionhost-deb.sh VERSION OUTDIR}
OUTDIR=${2:?usage: build-onionhost-deb.sh VERSION OUTDIR}
shift 2
FLOOR=""
EXTRA=""
SABOTAGE=0
while [ $# -gt 0 ]; do
  case "$1" in
    --floor) FLOOR=$2; shift 2;;
    --extra-dir) EXTRA=$2; shift 2;;
    --sabotage) SABOTAGE=1; shift;;
    *) echo "unknown arg: $1" >&2; exit 2;;
  esac
done
mkdir -p "$OUTDIR"
STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT
for top in etc usr; do
  cp -a "$SRC/$top" "$STAGE/$top"
done
rm -rf "$STAGE/etc/calamares"
find "$STAGE" -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
if [ -n "$EXTRA" ]; then cp -a "$EXTRA"/. "$STAGE"/; fi
if [ -n "$FLOOR" ]; then
  printf '{"onionhost":"%s"}\n' "$FLOOR" > "$STAGE/usr/share/onionhost/floor.json"
fi
if [ "$SABOTAGE" = 1 ]; then
  printf '#!/bin/sh\n# SABOTAGED build (Gate 4 proof): stack never starts.\nexit 1\n' \
    > "$STAGE/usr/lib/onionhost/stack-launcher"
  chmod 755 "$STAGE/usr/lib/onionhost/stack-launcher"
fi
mkdir -p "$STAGE/DEBIAN"
cat > "$STAGE/DEBIAN/control" <<EOF
Package: onionhost
Version: $VERSION
Architecture: all
Maintainer: OnionHost Project <release-signing@onionhost.invalid>
Depends: apt, dpkg, python3, tor (>= 0.4.8)
Description: OnionHost platform (golden config, wizard, dashboard, units)
 The small signed package through which an installed OnionHost
 machine updates itself over Tor (Gate 4). Carries a security
 floor (usr/share/onionhost/floor.json) used by onionhost-update
 for rollback / fail-closed decisions.
EOF
cat > "$STAGE/DEBIAN/postinst" <<'EOF'
#!/bin/sh
# onionhost package postinst: re-render golden configs so a package
# update takes configuration effect; stack restarts and health
# checks are owned by onionhost-update, not by dpkg - a bare
# maintenance dpkg -i must not bounce the site's containers.
set -e
if [ -x /usr/local/bin/onionhost-generate-configs ]; then
    /usr/local/bin/onionhost-generate-configs >/dev/null 2>&1 || true
fi
if [ -d /run/systemd/system ]; then
    systemctl daemon-reload >/dev/null 2>&1 || true
fi
exit 0
EOF
chmod 755 "$STAGE/DEBIAN/postinst"
find "$STAGE" -type d -exec chmod 755 {} +
find "$STAGE" -type f -exec chmod 644 {} +
for f in "$STAGE"/usr/local/bin/* "$STAGE"/usr/lib/apt/methods/*; do
  [ -f "$f" ] && chmod 755 "$f"
done
# Executables outside the two classic dirs must stay executable too:
# restore +x for every staged file whose source-overlay counterpart has
# any execute bit. The blanket 644 above once shipped the initramfs
# hooks (/etc/initramfs-tools/hooks/zz-onionhost-*) non-executable, and
# update-initramfs SILENTLY SKIPS non-executable hooks: an initramfs
# built after installing this package then lacked the root keyfile and
# the --disable-keyring wrapper - unbootable, and a silent loss of the
# A18 boot property. Found by the rig battery, 2026-10-14 (the package
# had only ever been installed by the updater, which never rebuilds the
# initramfs, so the defect stayed latent through Gate 4).
(cd "$SRC" && find etc usr -type f -perm /111) | while read -r rel; do
  [ -f "$STAGE/$rel" ] && chmod 755 "$STAGE/$rel"
done
# Regression guard: fail the build if any source-executable would ship
# non-executable.
GUARD_FAIL=0
(cd "$SRC" && find etc usr -type f -perm /111) | while read -r rel; do
  if [ -f "$STAGE/$rel" ] && [ ! -x "$STAGE/$rel" ]; then
    echo "MODE GUARD: $rel is executable in the source overlay but not in the package" >&2
    exit 1
  fi
done || GUARD_FAIL=1
[ "$GUARD_FAIL" = 0 ] || { echo "build-onionhost-deb: mode guard failed" >&2; exit 1; }
chmod 755 "$STAGE/DEBIAN/postinst"
OUT="$OUTDIR/onionhost_${VERSION}_all.deb"
dpkg-deb --build --root-owner-group "$STAGE" "$OUT" >/dev/null
echo "$OUT"

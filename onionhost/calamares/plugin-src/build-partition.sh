#!/bin/bash
# Build the OnionHost-patched Calamares partition viewmodule.
#
# Runs INSIDE the same pinned-snapshot chroot as build-plugins.sh
# (see build-iso.sh). The Calamares 3.3.14 source tree there is the
# sha256-verified tarball from the signed Debian .dsc; this script
# applies calamares/patches/0001-onionhost-force-encryption.patch
# to a scratch copy and builds ONLY the partition viewmodule target
# against it. The resulting .so replaces the stock module in the
# ISO rootfs (build-iso.sh, phase B0) and its sha256 is recorded in
# BUILD-INFO. Without the OnionHost GlobalStorage marker key the
# patched module behaves exactly like stock 3.3.14.
#
# The patched module must not gain runtime dependencies over the
# stock one: the NEEDED soname sets are compared here and the build
# FAILS on any addition.
set -euo pipefail

SRC=/src/calamares-3.3.14
WORK=/tmp/calasrc-patched
BLD=/build/cala
STOCK=/usr/lib/x86_64-linux-gnu/calamares/modules/partition/libcalamares_viewmodule_partition.so

rm -rf "$WORK" "$BLD"
cp -a "$SRC" "$WORK"
cd "$WORK"
patch -p1 --no-backup-if-mismatch < /src/patches/0001-onionhost-force-encryption.patch

export LC_ALL=C TZ=UTC
cmake -S "$WORK" -B "$BLD" \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX=/usr \
  -DKDE_INSTALL_USE_QT_SYS_PATHS=ON \
  -DWEBVIEW_FORCE_WEBKIT=1 \
  -DCMAKE_CXX_FLAGS="-ffile-prefix-map=$WORK=." \
  -DCMAKE_C_FLAGS="-ffile-prefix-map=$WORK=." \
  > /tmp/partition-cmake-configure.log 2>&1
cmake --build "$BLD" --target calamares_viewmodule_partition -j"$(nproc)" \
  > /tmp/partition-cmake-build.log 2>&1

OUT="$BLD/src/modules/partition/libcalamares_viewmodule_partition.so"
[ -f "$OUT" ] || { echo "FATAL: partition module target produced no .so" >&2; exit 1; }

needed() { readelf -d "$1" | sed -n 's/.*NEEDED.*\[\([^]]*\)\].*/\1/p' | sort; }
# (No process substitution: /dev/fd is not available in the bare
# build chroot.)
needed "$STOCK" > /tmp/needed-stock.txt
needed "$OUT" > /tmp/needed-patched.txt
if ! diff /tmp/needed-stock.txt /tmp/needed-patched.txt > /tmp/partition-needed.diff; then
  echo "FATAL: patched partition module NEEDED set differs from stock:" >&2
  cat /tmp/partition-needed.diff >&2
  exit 1
fi
cp "$OUT" /src/modules-out-partition.so
# Success only (set -e preserves the tree and the cmake logs on
# failure): the patched source copy and the cmake build tree are
# several GB the rig does not have to spare.
rm -rf "$WORK" "$BLD"
echo "PARTITION MODULE BUILD OK"

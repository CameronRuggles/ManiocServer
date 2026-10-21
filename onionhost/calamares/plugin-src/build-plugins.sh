#!/bin/bash
# Build the OnionHost Calamares view-module plugins.
#
# Runs INSIDE a Debian 13 (trixie) chroot built from the same pinned
# snapshot as the ISO (see ISO-BUILD-LOG, slice 2), with g++,
# qt6-base-dev and the calamares package installed. It compiles the
# two C++ view steps against the Calamares 3.3.14 source headers
# (headers are not shipped by the Debian package) and the installed
# libcalamares / libcalamaresui shared libraries, and drops the
# resulting .so files into the module directories of the OnionHost
# source tree ($OH_SRC/calamares/modules/<name>/).
#
# Usage (on the rig):
#   sudo chroot ~/calabuild/rootfs /bin/bash /build/build-plugins.sh
# with the calamares source at /src/calamares-3.3.14 and this
# plugin-src tree at /src/plugin-src inside the chroot.
set -euo pipefail

SRC=/src/calamares-3.3.14
PLUG=/src/plugin-src
OUT=/src/modules-out
mkdir -p "$OUT/onionhostphrase" "$OUT/onionhostguard"

QT_CFLAGS=$(pkg-config --cflags Qt6Widgets)
QT_LIBS=$(pkg-config --libs Qt6Widgets)
MOC=/usr/lib/qt6/libexec/moc
INCLUDES="-I$PLUG/shim -I$SRC/src/libcalamares -I$SRC/src/libcalamaresui"
LIBS="-lcalamaresui -lcalamares"

# Determinism (A14): strip the chroot's build paths out of debug info
# and __FILE__ strings; the caller exports SOURCE_DATE_EPOCH, LC_ALL=C
# and TZ=UTC so __DATE__/__TIME__ and diagnostics are stable. Two runs
# of this script over identical inputs must produce identical .so
# bytes - verified by sha256 in build-iso.sh's BUILD-INFO (slice 3).
DETFLAGS="-ffile-prefix-map=$SRC=. -ffile-prefix-map=$PLUG=."

build_one() {
    local name="$1" base="$2"
    echo "== building $name"
    $MOC $INCLUDES $QT_CFLAGS -I"$PLUG/$name" \
        "$PLUG/$name/$base.h" -o "/tmp/moc_$base.cpp"
    g++ -fPIC -shared -std=c++17 -O2 $DETFLAGS \
        $INCLUDES $QT_CFLAGS -I"$PLUG/$name" \
        "$PLUG/$name/$base.cpp" "/tmp/moc_$base.cpp" \
        -o "$OUT/$name/libcalamares_viewmodule_$name.so" \
        $LIBS $QT_LIBS
    echo "   -> $OUT/$name/libcalamares_viewmodule_$name.so"
}

build_one onionhostphrase OnionHostPhraseViewStep
build_one onionhostguard OnionHostGuardViewStep
echo "PLUGIN BUILD OK"

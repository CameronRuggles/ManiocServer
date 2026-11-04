#!/bin/bash
# Build the signed-channel `onionhost-images` package: the three
# container rootfs tarballs (Tor gateway, web, app) that the ISO
# used to be the only source of (review 2026-10-25, finding F2 -
# before this package existed, an installed box's container
# software was frozen at ISO versions for the life of the
# install while its host packages updated normally).
#
#   build-onionhost-images-deb.sh IMAGES_DIR VERSION OUTDIR
#
# IMAGES_DIR holds onionhost-tor.tar, onionhost-web.tar and
# onionhost-app.tar (the same files build-iso.sh places in the
# image). VERSION is the release/platform version being built.
#
# The package version is 1:VERSION+img.<counter>.<hash>, where
# <hash> is the first 12 hex of the sha256 over the three
# tarballs' own sha256 lines: the version CHANGES whenever any
# tarball changes, so a rebuilt image set can never hide behind
# an unchanged version string.
#
# The <counter> is the version's ORDER (full-tree audit
# 2026-11-03, Finding 1): onionhost-update judges this package
# by dpkg ordering - the repository's best version is the
# dpkg-max, and the high-water mark refuses anything below it -
# but a content hash orders lexically, not temporally, so a
# hash-only version refused legitimate same-base rebuilds about
# half the time and admitted older sets whose hash happened to
# sort higher. The counter is a plain integer the release bumps
# (build/images-build-counter, in the same commit that cuts an
# images release; never reused, never decreased), so dpkg
# orders two builds of a base version by build order and the
# hash is reached only as a tie-break between builds of the
# same counter - which, the content being identical, is no
# decision at all. The epoch "1:" marks the scheme: every
# pre-scheme version (VERSION+img.<hash>, epoch 0) sorts below
# every counter version, so the first counter release is never
# refused as a downgrade by a mark an old-format install left
# behind, whatever its hash. Rebuilding the same content with
# the same counter reproduces the same version: the version is
# a pure function of VERSION, the counter file and the content
# - no wall clock anywhere in it. (IMAGES_BUILD_COUNTER
# overrides the file for verification builds and tests; a
# release build reads the file.)
#
# The payload is the tarballs plus IMAGES-VERSION, a manifest
# carrying that same content identity (version: img-<hash>) and
# each tarball's sha256. onionhost-import-images verifies the
# tarballs against the manifest before loading them and judges
# "is there anything new?" by manifest-vs-import-record, never
# by version arithmetic. build-iso.sh writes the identical
# manifest into the ISO, so a fresh install's record starts at
# the version of the images actually on the ISO.
#
# The package has NO maintainer scripts, deliberately: apt's
# context is the wrong place to touch Podman or restart
# containers. dpkg lays the files down; onionhost-update notices
# the delivered manifest differs from the import record, runs
# the importer, and lets its health check judge the result -
# exactly the discipline the platform package follows.
set -euo pipefail
IMGDIR=$(readlink -f "${1:?usage: build-onionhost-images-deb.sh IMAGES_DIR VERSION OUTDIR}")
VERSION=${2:?usage: build-onionhost-images-deb.sh IMAGES_DIR VERSION OUTDIR}
OUTDIR=$(readlink -f "${3:?usage: build-onionhost-images-deb.sh IMAGES_DIR VERSION OUTDIR}")
TARS="onionhost-tor.tar onionhost-web.tar onionhost-app.tar"
for t in $TARS; do
  [ -s "$IMGDIR/$t" ] || {
    echo "missing or empty image tarball: $IMGDIR/$t" >&2; exit 2; }
done
mkdir -p "$OUTDIR"
STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT
PAYLOAD="$STAGE/usr/lib/onionhost/images"
mkdir -p "$PAYLOAD" "$STAGE/DEBIAN"
for t in $TARS; do
  cp -a "$IMGDIR/$t" "$PAYLOAD/$t"
done
# Manifest: one "file: sha256" line per tarball in fixed order,
# then the content identity over exactly those lines.
{
  for t in $TARS; do
    printf '%s: %s\n' "$t" "$(sha256sum "$PAYLOAD/$t" | awk '{print $1}')"
  done
} > "$STAGE/.hashlines"
COMBINED=$(sha256sum "$STAGE/.hashlines" | awk '{print $1}')
IMGVER="img-${COMBINED:0:12}"
{
  printf 'version: %s\n' "$IMGVER"
  cat "$STAGE/.hashlines"
} > "$PAYLOAD/IMAGES-VERSION"
rm -f "$STAGE/.hashlines"
COUNTER_FILE="$(dirname "$(readlink -f "$0")")/images-build-counter"
COUNTER=${IMAGES_BUILD_COUNTER:-$(cat "$COUNTER_FILE" 2>/dev/null)}
case $COUNTER in
  ''|*[!0-9]*)
    echo "bad images build counter '${COUNTER}': expected a positive integer from $COUNTER_FILE (or IMAGES_BUILD_COUNTER) - bump the counter file in the release commit" >&2
    exit 2 ;;
esac
COUNTER=$((10#$COUNTER))
[ "$COUNTER" -ge 1 ] || {
  echo "bad images build counter 0: expected a positive integer" >&2
  exit 2; }
PKGVER="1:${VERSION}+img.${COUNTER}.${COMBINED:0:12}"
cat > "$STAGE/DEBIAN/control" <<EOF
Package: onionhost-images
Version: $PKGVER
Architecture: amd64
Maintainer: OnionHost Project <release-signing@onionhost.invalid>
Depends: onionhost
Description: OnionHost container images (Tor gateway, web, app rootfs tarballs)
 The container software an OnionHost box serves from, delivered
 through the same signed repository as the platform package
 (review 2026-10-25, F2). Installing this package only lays the
 tarballs and their IMAGES-VERSION manifest on disk; the
 importer loads them under onionhost-update's health-checked
 discipline, never from a maintainer script.
EOF
find "$STAGE" -type d -exec chmod 755 {} +
find "$STAGE" -type f -exec chmod 644 {} +
OUT="$OUTDIR/onionhost-images_${PKGVER}_amd64.deb"
dpkg-deb --build --root-owner-group "$STAGE" "$OUT" >/dev/null
echo "$OUT"

#!/bin/bash
# Build + sign the OnionHost apt repository (Gate 4 / DESIGN-v3 A6).
#
#   make-onionhost-repo.sh DEBDIR OUTDIR
#
# DEBDIR: directory of onionhost_*.deb files to publish (the repo
# serves exactly what's here - rebuilding with fewer debs simulates
# a rolled-back/frozen mirror). OUTDIR: repository root to serve
# over the repo onion service.
#
# Metadata: Release with Valid-Until = now + 45 days (A6), re-signed
# monthly on the release key even if no package changed. Signing key
# comes from GNUPGHOME (the maintainer keyring - see
# ~/workspace/onionhost-maintainer/README.md; the release gate swaps
# in the hardware key). KEYID overrides the signing key id.
set -euo pipefail
DEBDIR=$(readlink -f "${1:?usage: make-onionhost-repo.sh DEBDIR OUTDIR}")
OUTDIR=$(readlink -f "${2:?usage: make-onionhost-repo.sh DEBDIR OUTDIR}")
KEYID=${KEYID:-38AA06376F68206F072939DE82610F8D4BEF9565}
: "${GNUPGHOME:?set GNUPGHOME to the maintainer keyring}"
SUITE=trixie
BIN=$OUTDIR/dists/$SUITE/main/binary-amd64
mkdir -p "$BIN" "$OUTDIR/pool/main/o/onionhost"
find "$OUTDIR/pool" -name '*.deb' -delete
cp "$DEBDIR"/onionhost_*.deb "$OUTDIR/pool/main/o/onionhost/"
# Recipe packages (A23) publish beside the platform package, one
# pool directory per package name, and ride the same signing.
for deb in "$DEBDIR"/onionhost-recipe-*_*.deb; do
  [ -e "$deb" ] || continue
  pkg=$(dpkg-deb -f "$deb" Package)
  mkdir -p "$OUTDIR/pool/main/o/$pkg"
  cp "$deb" "$OUTDIR/pool/main/o/$pkg/"
done
cd "$OUTDIR"
apt-ftparchive packages pool > "$BIN/Packages"
xz -kf "$BIN/Packages"
cat > "$OUTDIR/.release.conf" <<EOF
APT::FTPArchive::Release::Origin "OnionHost";
APT::FTPArchive::Release::Label "OnionHost";
APT::FTPArchive::Release::Suite "$SUITE";
APT::FTPArchive::Release::Codename "$SUITE";
APT::FTPArchive::Release::Architectures "amd64 all";
APT::FTPArchive::Release::Components "main";
APT::FTPArchive::Release::Description "OnionHost project packages - updates over Tor (Gate 4)";
EOF
# RELEASE_DATE (optional, RFC-2822): pin the Release Date instead of
# "now" - for reproducible builds and for test rigs whose clock is
# known to lag (apt refuses a Release dated in its future).
if [ -n "${RELEASE_DATE:-}" ]; then
  echo "APT::FTPArchive::Release::Date \"$RELEASE_DATE\";" \
    >> "$OUTDIR/.release.conf"
fi
apt-ftparchive -c "$OUTDIR/.release.conf" release "dists/$SUITE" \
  > "dists/$SUITE/Release"
rm -f "$OUTDIR/.release.conf"
# Inject Valid-Until (+45 days, A6) - a header field only; the hash
# sections apt-ftparchive computed are untouched, and both signature
# files are made AFTER this edit, over the final bytes.
python3 - "dists/$SUITE/Release" <<'EOF'
import datetime, email.utils, sys, time
p = sys.argv[1]
lines = open(p).read().splitlines()
base = time.time()
for line in lines:
    if line.startswith("Date:"):
        try:
            base = email.utils.parsedate_to_datetime(
                line[5:].strip()).timestamp()
        except (TypeError, ValueError):
            pass
        break
vu = email.utils.formatdate(base + 45 * 86400, usegmt=True)
out = []
for line in lines:
    out.append(line)
    if line.startswith("Date:"):
        out.append("Valid-Until: %s" % vu)
open(p, "w").write("\n".join(out) + "\n")
print("Valid-Until:", vu)
EOF
cd "dists/$SUITE"
gpg --batch --yes --pinentry-mode loopback --default-key "$KEYID" \
    --clearsign -o InRelease Release
gpg --batch --yes --pinentry-mode loopback --default-key "$KEYID" \
    --armor --detach-sign -o Release.gpg Release
echo "repo built + signed at $OUTDIR (suite $SUITE)"

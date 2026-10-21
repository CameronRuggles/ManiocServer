#!/bin/bash
# Build the signed-channel package for one packaged app recipe
# (A23): onionhost-recipe-<id>_<version>_all.deb.
#
#   build-recipe-deb.sh RECIPE_DIR VERSION OUTDIR [--floor X]
#                       [--sabotage]
#
# A recipe is DATA for the onionhost package channel - its own
# .deb in the same Tor-served, project-signed repository as the
# platform package (Gate 4) - so a bundled app's security fix
# ships on its own cadence, with its own anti-rollback floor, and
# the updater's install -> restart -> health-check -> rollback
# choreography covers it unchanged (the package's postinst runs
# onionhost-recipe apply when this machine selected the recipe;
# rolling back the .deb re-applies the previous payload).
#
# The payload lands in /usr/share/onionhost/recipes/<id>/:
# manifest.json (recipe.json with the version stamped in),
# archive/ (the pinned app archive - the applier verifies its
# sha256 against the manifest before every apply; NO database
# credentials are ever in here: they are per-install and are
# substituted at apply time from /etc/onionhost/app-db.env),
# overlay/, seed/, and floor.json ({"onionhost-recipe-<id>": F}).
#
# --sabotage builds a deliberately broken recipe (a core app file
# corrupted inside the archive - for a native recipe, the binary's
# own header - manifest hash updated so the package is
# self-consistent) to prove the update rollback path.
# Never ship a sabotage build anywhere but a test repo.
set -euo pipefail
RECIPEDIR=$(readlink -f "${1:?usage: build-recipe-deb.sh RECIPE_DIR VERSION OUTDIR [--floor X] [--sabotage]}")
VERSION=${2:?version required (e.g. 2.1.7+oh.1)}
OUTDIR=$(readlink -f "${3:?outdir required}")
shift 3
FLOOR=""
SABOTAGE=0
while [ $# -gt 0 ]; do
  case "$1" in
    --floor) FLOOR=$2; shift 2 ;;
    --sabotage) SABOTAGE=1; shift ;;
    *) echo "unknown flag: $1" >&2; exit 2 ;;
  esac
done
[ -f "$RECIPEDIR/recipe.json" ] || {
  echo "no recipe.json in $RECIPEDIR" >&2; exit 2; }
# --- path validation (Repo Review 4 task 11, B16) ---------------
# archive.file and every native_files src/dst are joined onto
# other directories below (the archive dir at package time, the
# app-data volume at apply time). Each must be a plain relative
# path: an absolute value or a ".." component would copy or
# place a file outside its intended directory. This runs FIRST,
# before the staging directory is created or anything is copied,
# so a hostile or corrupted recipe.json fails before any write.
python3 - "$RECIPEDIR" <<'EOF'
import json, os, sys
rdir = sys.argv[1]
d = json.load(open(os.path.join(rdir, "recipe.json")))
rid = d.get("id", "?")
def unsafe(v):
    return (not isinstance(v, str) or not v
            or v.startswith("/")
            or ".." in v.split("/"))
afile = d.get("archive", {}).get("file")
if unsafe(afile):
    sys.exit("path check: recipe %s: archive.file %r is absolute "
             "or contains a '..' path component - refusing to "
             "package" % (rid, afile))
for nf in d.get("native_files", []):
    for field in ("src", "dst"):
        v = nf.get(field) if isinstance(nf, dict) else None
        if unsafe(v):
            sys.exit("path check: recipe %s: native_files %s %r "
                     "is absolute or contains a '..' path "
                     "component - refusing to package"
                     % (rid, field, v))
print("path check OK: archive.file + native_files paths are "
      "relative and '..' free")
EOF
ID=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["id"])' \
     "$RECIPEDIR/recipe.json")
PKG="onionhost-recipe-$ID"
# A native recipe ships a machine binary: its package is
# architecture-specific. Tree recipes are data: arch all.
ARCH=$(python3 -c 'import json,sys; print("amd64" if json.load(open(sys.argv[1])).get("runtime")=="native" else "all")' \
     "$RECIPEDIR/recipe.json")
[ -n "$FLOOR" ] || FLOOR=$(tr -d '[:space:]' \
                           < "$RECIPEDIR/floor.txt")

STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT
PAYLOAD="$STAGE/usr/share/onionhost/recipes/$ID"
mkdir -p "$PAYLOAD" "$STAGE/DEBIAN" "$OUTDIR"
chmod 0755 "$STAGE" "$STAGE/DEBIAN"

# --- pin verification (Repo Review 2 tasks 9+10, B2) ------------
# The pins in recipe.json are the ONLY provenance a rebuilder can
# check. Verify BEFORE anything is packaged:
#   * the vendored archive's sha256 must equal archive.sha256;
#   * every native_files entry must carry a sha256 and the file
#     must match it.
# Before this gate the builder re-hashed whatever it found and
# signed that, so a wrong or substituted input shipped silently.
# (A --sabotage build corrupts only the STAGED copy below; the
# source inputs are verified here either way.)
python3 - "$RECIPEDIR" <<'EOF'
import hashlib, json, os, sys
rdir = sys.argv[1]
d = json.load(open(os.path.join(rdir, "recipe.json")))
def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()
arc = d["archive"]
p = os.path.join(rdir, "archive", arc["file"])
if not os.path.isfile(p):
    sys.exit("pin check: archive %s missing (fetch it with "
             "build/fetch-recipe-archives.sh)" % p)
if sha(p) != arc["sha256"]:
    sys.exit("pin check: archive %s sha256 %s != recipe.json pin %s"
             " - refusing to package an unverified archive"
             % (p, sha(p), arc["sha256"]))
for nf in d.get("native_files", []):
    if "sha256" not in nf:
        sys.exit("pin check: native_files entry %s carries no "
                 "sha256 - add one to recipe.json" % nf.get("src"))
    p = os.path.join(rdir, nf["src"])
    if not os.path.isfile(p) or sha(p) != nf["sha256"]:
        sys.exit("pin check: native file %s does not match its "
                 "recipe.json sha256 - refusing to package it" % p)
print("pin check OK: archive + %d native file(s) verified"
      % len(d.get("native_files", [])))
EOF

# --- payload -----------------------------------------------------
# archive/ is the one required component; overlay/, seed/ and
# files/ (extra payload files the applier places into the app
# tree, e.g. a must-use plugin) ride along when present.
# Repo Review 3 task 14 (B11): copy ONLY the pinned archive file,
# not the whole archive/ directory. The pin check above covers
# archive/<archive.file> alone; copying the directory shipped any
# stray file left in it unverified inside a signed package.
ARCFILE_NAME=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["archive"]["file"])' \
               "$RECIPEDIR/recipe.json")
mkdir -p "$PAYLOAD/archive"
cp -a "$RECIPEDIR/archive/$ARCFILE_NAME" "$PAYLOAD/archive/"
for d in overlay seed files; do
  if [ -d "$RECIPEDIR/$d" ]; then
    cp -a "$RECIPEDIR/$d" "$PAYLOAD/"
  fi
done
if [ "$SABOTAGE" = 1 ]; then
  ARCFILE=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["archive"]["file"])' \
            "$RECIPEDIR/recipe.json")
  ARCFMT=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["archive"].get("format",""))' \
            "$RECIPEDIR/recipe.json")
  if [ "$ARCFMT" = "file" ]; then
    # A native recipe's archive IS the application binary:
    # scramble its first bytes (the ELF header) so it can never
    # start. The manifest hash re-seal below keeps the package
    # self-consistent - the app is simply broken, as with the
    # corrupted index.php of the tree recipes.
    python3 - "$PAYLOAD/archive/$ARCFILE" <<'EOF'
import sys
path = sys.argv[1]
with open(path, "r+b") as f:
    head = f.read(64)
    f.seek(0)
    f.write(bytes(b ^ 0xFF for b in head))
EOF
    echo "SABOTAGE: scrambled the native binary's header" \
         "in the recipe archive"
  else
    TMPX=$(mktemp -d)
    case "$ARCFILE" in
      *.zip)
        ( cd "$TMPX" && unzip -qq "$PAYLOAD/archive/$ARCFILE" )
        ROOT=$(find "$TMPX" -maxdepth 2 -name index.php -printf '%h\n' \
              | head -1)
        printf '\n<?php this is not php at all {{{\n' >> "$ROOT/index.php"
        ( cd "$TMPX" && rm -f "$PAYLOAD/archive/$ARCFILE" \
          && zip -qq -r "$PAYLOAD/archive/$ARCFILE" . )
        ;;
      *.tar.gz|*.tgz)
        ( cd "$TMPX" && tar xzf "$PAYLOAD/archive/$ARCFILE" )
        ROOT=$(find "$TMPX" -maxdepth 2 -name index.php -printf '%h\n' \
              | head -1)
        printf '\n<?php this is not php at all {{{\n' >> "$ROOT/index.php"
        ( cd "$TMPX" && rm -f "$PAYLOAD/archive/$ARCFILE" \
          && tar czf "$PAYLOAD/archive/$ARCFILE" . )
        ;;
      *) echo "sabotage: unsupported archive $ARCFILE" >&2; exit 2 ;;
    esac
    rm -rf "$TMPX"
    echo "SABOTAGE: corrupted index.php inside the recipe archive"
  fi
fi
# manifest.json: the recipe source with this build's version. The
# archive hash it carries is the recipe.json PIN (verified against
# the source archive above) - never a silent re-hash of whatever
# was found. The one exception is a --sabotage build, which
# corrupts the staged copy on purpose and re-seals the manifest
# with the corrupted hash so the package stays self-consistent.
python3 - "$RECIPEDIR/recipe.json" "$PAYLOAD/manifest.json" \
          "$VERSION" "$PAYLOAD" "$SABOTAGE" <<'EOF'
import hashlib, json, sys
src, dst, version, payload, sabotage = sys.argv[1:6]
m = json.load(open(src))
m["version"] = version
arc = "%s/archive/%s" % (payload, m["archive"]["file"])
actual = hashlib.sha256(open(arc, "rb").read()).hexdigest()
if sabotage == "1":
    m["archive"]["sha256"] = actual
elif actual != m["archive"]["sha256"]:
    sys.exit("manifest: staged archive hash != pin (non-sabotage "
             "build) - this is a bug in the build, refusing")
json.dump(m, open(dst, "w"), indent=1, sort_keys=True)
open(dst, "a").write("\n")
EOF
python3 - "$PKG" "$FLOOR" "$PAYLOAD/floor.json" <<'EOF'
import json, sys
json.dump({sys.argv[1]: sys.argv[2]}, open(sys.argv[3], "w"),
          indent=1)
open(sys.argv[3], "a").write("\n")
EOF
find "$STAGE" -type d -exec chmod 0755 {} +
find "$PAYLOAD" -type f -exec chmod 0644 {} +

# --- control -----------------------------------------------------
cat > "$STAGE/DEBIAN/control" <<EOF
Package: $PKG
Version: $VERSION
Section: misc
Priority: optional
Architecture: $ARCH
Maintainer: OnionHost Project <release-signing@onionhost.invalid>
Depends: onionhost
Description: OnionHost packaged application recipe: $ID
 Data package for the onionhost platform: the pinned application
 archive, its sealed-world configuration overlay and its database
 seed. Applied by onionhost-recipe when a site chooses this
 recipe; updated through the same signed channel as the platform.
EOF
cat > "$STAGE/DEBIAN/postinst" <<EOF
#!/bin/sh
# A recipe package never restarts the stack itself: the updater
# restarts and health-checks after managed installs, and rolls
# back through the previous .deb - whose postinst re-applies the
# previous payload the same way. Machines that did not select
# this recipe (including the ISO image build) are untouched.
set -e
if [ "\${1:-}" = "configure" ]; then
    if [ -f /var/lib/onionhost/app-site ] \\
       && [ -f /etc/onionhost/recipe-selection ] \\
       && [ "\$(cat /etc/onionhost/recipe-selection)" = "$ID" ]; then
        /usr/local/bin/onionhost-recipe apply $ID
    fi
fi
exit 0
EOF
chmod 0755 "$STAGE/DEBIAN/postinst"

DEB="$OUTDIR/${PKG}_${VERSION}_${ARCH}.deb"
dpkg-deb --build --root-owner-group "$STAGE" "$DEB" >/dev/null
if [ "$SABOTAGE" = 1 ]; then
  echo "built $DEB (floor $FLOOR, SABOTAGED)"
else
  echo "built $DEB (floor $FLOOR)"
fi

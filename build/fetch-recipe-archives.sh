#!/bin/bash
# Manioc Server - fetch + verify the vendored recipe archives (A14 /
# Repo Review 2 task 3). A release build must not depend on files
# that exist only in one developer's tree: every recipe's archive is
# either re-fetchable from its documented source or, for the one
# build-from-source recipe (marketplace), verified against its pin.
#
# RECIPE SELECTION (Repo Review 3 task 10, B9): by default only the
# recipes named in the tracked ship list <recipes>/SHIPPING are
# fetched/verified. The marketplace is NOT on that list until owner
# decision 3 is met (it must first be rebuildable from a pinned
# public commit), so a release build cannot include it. A different
# set may be selected with OH_RECIPES="id,id,..." ONLY for a
# non-release build: OH_NONRELEASE_BUILD=1 must also be set, or this
# script is FATAL. A non-release run banners itself and is never the
# default. build/build-iso.sh resolves the same selection the same
# way, packages exactly the selected recipes, and stamps the
# selection and release status into BUILD-INFO.
#
# For every SELECTED recipe under RECIPES_DIR (default:
# <repo>/onionhost/recipes, resolved relative to this script):
#
#   * archive/archive.file present and sha256 == archive.sha256 pin
#       -> OK (nothing downloaded)
#   * archive/archive.file present but sha256 != pin
#       -> FAIL, untouched. A changed cached archive is a tamper /
#          corruption signal, never silently healed by re-download.
#   * archive has a downloadable archive.url
#       -> download to a temp file, place ONLY if its sha256 equals
#          the pin; on mismatch, print the mismatch (and the recipe's
#          archive.refetch_note when present) and FAIL. A substituted
#          or regenerated archive is never placed silently.
#   * archive belongs to a build-from-source recipe (source_build)
#       -> it cannot be downloaded; if missing or wrong, FAIL with
#          the build instructions from source_build.
#
# Exit 0 only if every selected recipe's archive is present and
# pin-verified. Every selected recipe is attempted and reported,
# even after a failure.
set -uo pipefail

BDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RECIPES_DIR="${1:-$(dirname "$BDIR")/onionhost/recipes}"
[ -d "$RECIPES_DIR" ] || { echo "fetch-recipe-archives: no recipes dir at $RECIPES_DIR" >&2; exit 2; }

# --- recipe selection (same semantics as build/build-iso.sh) -------
SHIPPING_FILE="$RECIPES_DIR/SHIPPING"
[ -f "$SHIPPING_FILE" ] || { echo "FATAL: recipe ship list missing at $SHIPPING_FILE - refusing to guess which recipes ship. Restore the tracked SHIPPING list (Repo Review 3 task 10)." >&2; exit 1; }
SELECTED_RECIPES=()
while IFS= read -r _line || [ -n "$_line" ]; do
  _line="${_line%%#*}"
  _line="$(printf '%s' "$_line" | tr -d ' \t\r')"
  [ -n "$_line" ] && SELECTED_RECIPES+=("$_line")
done < "$SHIPPING_FILE"
RECIPES_SOURCE="SHIPPING"
RELEASE_STATUS="release"
if [ -n "${OH_RECIPES:-}" ]; then
  if [ "${OH_NONRELEASE_BUILD:-}" != "1" ]; then
    echo "FATAL: OH_RECIPES is set ('${OH_RECIPES}') but OH_NONRELEASE_BUILD=1 is not. A recipe-selection override is allowed only for a clearly-marked NON-RELEASE build: unset OH_RECIPES for a release build, or set OH_NONRELEASE_BUILD=1 to build non-release with this selection." >&2
    exit 1
  fi
  SELECTED_RECIPES=()
  read -ra SELECTED_RECIPES <<< "$(printf '%s' "$OH_RECIPES" | tr ',' ' ')"
  RECIPES_SOURCE="OH_RECIPES override"
  RELEASE_STATUS="non-release"
elif [ "${OH_NONRELEASE_BUILD:-}" = "1" ]; then
  RELEASE_STATUS="non-release"
fi
[ "${#SELECTED_RECIPES[@]}" -gt 0 ] || { echo "FATAL: recipe selection is empty (the SHIPPING list / OH_RECIPES named no recipes) - refusing to fetch nothing and call it verified." >&2; exit 1; }
_seen=" "
for _id in "${SELECTED_RECIPES[@]}"; do
  case "$_id" in
    *[!a-z0-9-]*|"") echo "FATAL: invalid recipe id in selection: '$_id'" >&2; exit 1 ;;
  esac
  case "$_seen" in
    *" $_id "*) echo "FATAL: recipe '$_id' is selected twice - fix the SHIPPING list / OH_RECIPES." >&2; exit 1 ;;
  esac
  _seen="$_seen$_id "
  [ -f "$RECIPES_DIR/$_id/recipe.json" ] || { echo "FATAL: selected recipe '$_id' has no recipe.json at $RECIPES_DIR/$_id/recipe.json" >&2; exit 1; }
done
if [ "$RELEASE_STATUS" = "non-release" ]; then
  {
    echo "======================================================================"
    echo "*** NON-RELEASE BUILD (OH_NONRELEASE_BUILD=1) ***"
    echo "Recipe selection: ${SELECTED_RECIPES[*]} (source: $RECIPES_SOURCE)"
    echo "This is NOT a release build and must not be published as one."
    echo "======================================================================"
  } >&2
fi
echo "fetch-recipe-archives: selection ($RELEASE_STATUS, source: $RECIPES_SOURCE): ${SELECTED_RECIPES[*]}"

fail=0
for rid_sel in "${SELECTED_RECIPES[@]}"; do
  rdir="$RECIPES_DIR/$rid_sel"
  rjson="$rdir/recipe.json"
  # Recipe fields, ONE PER LINE from Python (an empty line is an
  # explicit empty field). The old whitespace-split `read` shifted
  # every field after an empty one, so a recipe with no archive.url
  # failed as a bogus download instead of naming the missing field
  # (Repo Review 3 task 13, B11). One-field-per-line preserves
  # explicit empties exactly; a tab-separated `read` would not -
  # tab is IFS whitespace in bash, so consecutive tabs collapse.
  fields_tmp="$(mktemp)"
  if ! python3 - "$rjson" > "$fields_tmp" <<'PYEOF'
import json, sys
d = json.load(open(sys.argv[1]))
a = d.get("archive", {})
for v in (d.get("id", "?"), a.get("file", ""), a.get("sha256", ""),
          a.get("url", ""), "1" if "source_build" in d else "0"):
    print(v)
PYEOF
  then
    echo "FAIL $rid_sel: cannot parse $rjson" >&2
    rm -f "$fields_tmp"; fail=1; continue
  fi
  {
    IFS= read -r rid || rid=""
    IFS= read -r afile || afile=""
    IFS= read -r apin || apin=""
    IFS= read -r aurl || aurl=""
    IFS= read -r has_sb || has_sb=""
  } < "$fields_tmp"
  rm -f "$fields_tmp"
  if [ -z "$afile" ]; then
    echo "FAIL $rid: recipe.json names no archive.file - cannot verify or fetch its archive" >&2
    fail=1; continue
  fi
  if [ -z "$apin" ]; then
    echo "FAIL $rid: recipe.json names no archive.sha256 for $afile - refusing to use an unpinned archive" >&2
    fail=1; continue
  fi
  # Path validation (Repo Review 4 task 11, B16): archive.file is
  # joined under $rdir/archive/ below, so it must be a plain
  # relative path - an absolute value or a ".." component would
  # place (or check) a file outside the recipe's archive dir.
  case "$afile" in
    /*|..|../*|*/..|*/../*)
      echo "FAIL $rid: archive.file '$afile' in recipe $rid is absolute or contains a '..' path component - refusing to use it as a path" >&2
      fail=1; continue
      ;;
  esac
  target="$rdir/archive/$afile"
  if [ -f "$target" ]; then
    got="$(sha256sum "$target" | awk '{print $1}')"
    if [ "$got" = "$apin" ]; then
      echo "OK   $rid: $afile matches pin"
    else
      echo "FAIL $rid: cached $afile sha256 $got != pin $apin - refusing to use or replace it" >&2
      fail=1
    fi
    continue
  fi
  if [ "$has_sb" = "1" ]; then
    echo "FAIL $rid: $afile is a build-from-source artifact and is missing or does not match its pin." >&2
    python3 - "$rjson" <<'EOF' >&2
import json, sys
sb = json.load(open(sys.argv[1]))["source_build"]
print("     build it from %s at commit %s:" % (sb["repo"], sb["commit"]))
print("       %s" % sb["build_command"])
print("     (%s)" % sb["toolchain"])
EOF
    fail=1
    continue
  fi
  if [ -z "$aurl" ]; then
    echo "FAIL $rid: $afile missing/mismatched and recipe.json names no archive.url" >&2
    fail=1
    continue
  fi
  echo "GET  $rid: $aurl"
  tmp="$(mktemp)"
  if ! curl -fsSL -o "$tmp" "$aurl"; then
    echo "FAIL $rid: download failed: $aurl" >&2
    rm -f "$tmp"; fail=1; continue
  fi
  got="$(sha256sum "$tmp" | awk '{print $1}')"
  if [ "$got" != "$apin" ]; then
    echo "FAIL $rid: downloaded $afile sha256 $got != pin $apin - NOT placed" >&2
    python3 - "$rjson" <<'EOF' >&2
import json, sys
note = json.load(open(sys.argv[1])).get("archive", {}).get("refetch_note")
if note:
    print("     recipe note: %s" % note)
EOF
    rm -f "$tmp"; fail=1; continue
  fi
  mkdir -p "$rdir/archive"
  if ! install -m 0644 "$tmp" "$target"; then
    echo "FAIL $rid: could not place the pin-verified download at $target" >&2
    rm -f "$tmp"; fail=1; continue
  fi
  rm -f "$tmp"
  echo "OK   $rid: fetched and pin-verified -> $target"
done
exit $fail

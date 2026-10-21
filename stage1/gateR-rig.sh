#!/bin/bash
# Gate R — LUKS2 keyring / re-key path test, Stage 1 rig version.
# Extends ../poc/scripts/gater-test.sh (Stage 0) with the steps Stage 0
# could not run (no device-mapper there) plus cleanup.
#
# THE question (DESIGN-v3 A3/A9): on a default-opened LUKS2 volume, does
# `dmsetup table --showkeys` reveal the raw volume key or only a `:logon:`
# keyring reference — and can a new passphrase be added WITHOUT the user
# re-typing the existing one? The answer decides whether the installer
# wizard may promise in-place re-key, or must use A3's pre-committed
# fallback (spare keyslot, or backup + reinstall).
#
# Safety: works only on a throwaway image file in this directory, created
# fresh each run and shredded on exit. Never point it at a real device.
set -u

HERE="$(cd "$(dirname "$0")" && pwd)"
IMG="$HERE/gater-rig.img"
NAME="gater-rig-test"
PASS1='gate-r-test-passphrase-one'
PASS2='gate-r-test-passphrase-two'

cleanup() {
  cryptsetup luksClose "$NAME" >/dev/null 2>&1 || true
  if [ -f "$IMG" ]; then shred -u "$IMG" 2>/dev/null || rm -f "$IMG"; fi
}
trap cleanup EXIT

# Fresh 64 MB throwaway image (Stage 0 used a pre-made one; create it here
# so the rig run is self-contained).
rm -f "$IMG"
dd if=/dev/zero of="$IMG" bs=1M count=64 status=none || { echo "FATAL: cannot create image"; exit 1; }

echo "### 1. luksFormat LUKS2 on regular file"
printf '%s' "$PASS1" | cryptsetup luksFormat --type luks2 --batch-mode --key-file - "$IMG" && echo "luksFormat: OK"

echo "### 2. luksDump (header sanity)"
cryptsetup luksDump "$IMG" | grep -E "Version|Keyslots|  0: luks2" | head -5

echo "### 3. test-passphrase (no activation)"
printf '%s' "$PASS1" | cryptsetup open --test-passphrase --key-file - "$IMG" && echo "test-passphrase: OK"

echo "### 4. luksOpen (ACTIVE mapping — the step Stage 0 could not run)"
printf '%s' "$PASS1" | cryptsetup luksOpen --key-file - "$IMG" "$NAME" 2>&1
echo "luksOpen exit: $?"

echo "### 5. dmsetup table --showkeys (the decisive output)"
SHOWKEYS="$(dmsetup table --showkeys "$NAME" 2>&1)"
echo "$SHOWKEYS"

echo "### 6. Verdict on what --showkeys revealed"
if echo "$SHOWKEYS" | grep -q ":logon:"; then
  echo "SHOWKEYS_VERDICT: keyring-reference — dm exposes only a :logon: keyring reference, NOT the raw volume key"
elif echo "$SHOWKEYS" | grep -qE "\b[0-9a-f]{64,}\b"; then
  echo "SHOWKEYS_VERDICT: raw-key — dm exposes the raw volume key in the table"
else
  echo "SHOWKEYS_VERDICT: inconclusive — output matched neither pattern; read the raw table above"
fi

echo "### 7. Passphrase-less luksAddKey attempt (expected to fail — the ordinary path demands an existing credential)"
printf '%s' "$PASS2" | cryptsetup luksAddKey --batch-mode "$IMG" 2>&1
echo "luksAddKey(no existing passphrase) exit: $?"

echo "### 8. Volume-key luksAddKey attempt (only if this cryptsetup supports it)"
# Flag name differs across cryptsetup versions; ask the binary, don't guess.
VKFLAG=""
for f in --volume-key-file --master-key-file; do
  if cryptsetup luksAddKey --help 2>&1 | grep -q -- "$f"; then VKFLAG="$f"; break; fi
done
if [ -z "$VKFLAG" ]; then
  echo "ADDKEY_VIA_VOLUME_KEY: not attempted — this cryptsetup lists no volume/master key file flag for luksAddKey"
elif echo "$SHOWKEYS" | grep -q ":logon:"; then
  echo "ADDKEY_VIA_VOLUME_KEY: not attempted — no raw key in the dm table to feed it (keyring-reference case); a keyring-extraction step would be needed and is a design question, not a test shortcut"
else
  KEYFILE="$(mktemp)"
  chmod 600 "$KEYFILE"
  # Extract the hex key field from the dm table into a binary keyfile.
  HEX="$(echo "$SHOWKEYS" | grep -oE '\b[0-9a-f]{64,}\b' | head -1)"
  printf '%s' "$HEX" | xxd -r -p >"$KEYFILE" 2>/dev/null || echo "WARN: hex decode failed"
  printf '%s' "$PASS2" | cryptsetup luksAddKey --batch-mode "$VKFLAG" "$KEYFILE" "$IMG" 2>&1
  echo "luksAddKey(via $VKFLAG) exit: $?"
  shred -u "$KEYFILE" 2>/dev/null || rm -f "$KEYFILE"
fi

echo "### 9. Confirm PASS2 state matches the step-8 result"
printf '%s' "$PASS2" | cryptsetup open --test-passphrase --key-file - "$IMG" 2>&1 && echo "PASS2 active: YES" || echo "PASS2 active: NO"
echo "### Gate R rig run complete — verdict lines above (SHOWKEYS_VERDICT / ADDKEY_VIA_VOLUME_KEY) are what the wizard wording waits on."

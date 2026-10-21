#!/bin/bash
# Gate R — LUKS2 keyring / re-key path test (DESIGN-v3 A9 Gate R)
# Question: on a default-opened LUKS2 volume, does dmsetup table --showkeys
# reveal the raw volume key or only a :logon: keyring reference, and can
# luksAddKey succeed without an existing passphrase?
POC=$HOME/workspace/onion-host-os/poc
IMG=$POC/gater.img
PASS1='gate-r-test-passphrase-one'
PASS2='gate-r-test-passphrase-two'

echo "### 1. luksFormat LUKS2 on regular file"
printf '%s' "$PASS1" | cryptsetup luksFormat --type luks2 --batch-mode --key-file - "$IMG" && echo "luksFormat: OK"

echo "### 2. luksDump (header sanity)"
cryptsetup luksDump "$IMG" | grep -E "Version|Keyslots|  0: luks2" | head -5

echo "### 3. test-passphrase (no activation)"
printf '%s' "$PASS1" | cryptsetup open --test-passphrase --key-file - "$IMG" && echo "test-passphrase: OK"

echo "### 4. luksOpen (ACTIVE mapping — needs device-mapper)"
printf '%s' "$PASS1" | cryptsetup luksOpen --key-file - "$IMG" gater-test 2>&1
echo "luksOpen exit: $?"

echo "### 5. dmsetup table --showkeys (only if step 4 succeeded)"
dmsetup table --showkeys gater-test 2>&1

echo "### 6. passphrase-less luksAddKey attempt (the Gate R question)"
printf '%s' "$PASS2" | cryptsetup luksAddKey --batch-mode "$IMG" 2>&1
echo "luksAddKey(no existing passphrase) exit: $?"

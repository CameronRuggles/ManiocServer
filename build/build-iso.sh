#!/bin/bash
# Manioc Server — ISO build (ISO-BUILD-PLAN steps 1-3, step-3 slice 1)
# Runs as root on any host that meets the prerequisites in the
# top-level README.md (a Debian/Ubuntu-family build host with the
# tools and network endpoints the README lists). It does NOT need
# the Stage 1 rig; the rig is simply where it was first run.
#
# FLAVOUR=prod (default): the production image. NO test access anywhere:
#   no openssh-server/xdotool packages, no authorized_keys, and the live
#   account's password is locked (autologin only; Repo Review 2 task 8).
# FLAVOUR=test: live-session test access ONLY (known live password
#   "onion", operator pubkey, sshd drop-in, xdotool) so rig automation
#   can drive installs. The operator pubkey is NOT in this source
#   tree (Repo Review 5 P-4): set OH_TEST_SSH_PUBKEY, or place the
#   key in $OH_TEST_SSH_PUBKEY_FILE (default
#   $HOME/.onionhost-test-pubkey, outside the tree). A test build
#   with neither fails loudly below. The onionhostcleanup Calamares
#   job strips the
#   live user / autologin / test access from the INSTALLED target in
#   BOTH flavours; sshd/xdotool binaries remain in a test-flavour
#   target's package set (purged by cleanup if present - see module).
# OH_PROBE=1: also insert the onionhostprobe jobmodule (diagnostics).
#
# Recipe selection: a release build fetches and packages EXACTLY the
# recipes listed in onionhost/recipes/SHIPPING (the marketplace is
# not on that list until owner decision 3 is met). OH_RECIPES may
# select a different set ONLY together with OH_NONRELEASE_BUILD=1,
# which banners the build and stamps BUILD-INFO as non-release.
# OH_SRC (the source-tree override) is held to the same rule, and
# the source commit / tree hash are stamped into BUILD-INFO.
# See README.md ("Recipe ship list and the non-release override").
#
# Pipeline: mmdebstrap (Debian 13/trixie, pinned snapshot) -> chroot
# customisation (+ onionhost overlay from this repo's onionhost/
# tree - see SRC below; OH_SRC overrides it) -> squashfs
# -> grub-mkrescue hybrid ISO. Container images are built the same way
# (mmdebstrap tarballs) and shipped for podman import (DESIGN-v3 A6).
set -euo pipefail

FLAVOUR="${FLAVOUR:-prod}"
OH_PROBE="${OH_PROBE:-0}"
# Test-flavour operator pubkey (Repo Review 5 P-4): from the
# environment or an out-of-tree file, never from tracked source -
# an operator-identifying key has no business shipping in the
# repo, and a test build must not silently lose its access path.
TEST_SSH_PUBKEY="${OH_TEST_SSH_PUBKEY:-}"
if [ -z "$TEST_SSH_PUBKEY" ]; then
  _pubkey_file="${OH_TEST_SSH_PUBKEY_FILE:-$HOME/.onionhost-test-pubkey}"
  if [ -f "$_pubkey_file" ]; then
    TEST_SSH_PUBKEY="$(head -n 1 "$_pubkey_file")"
  fi
fi
if [ "$FLAVOUR" = "test" ]; then
  case "$TEST_SSH_PUBKEY" in
    ssh-ed25519\ *|ssh-rsa\ *|ecdsa-sha2-nistp*\ *) ;;
    *)
      echo "FATAL: FLAVOUR=test needs an operator SSH public key, but none was supplied." >&2
      echo "Set OH_TEST_SSH_PUBKEY to the key, or write it to \${OH_TEST_SSH_PUBKEY_FILE:-\$HOME/.onionhost-test-pubkey} (outside the source tree)." >&2
      exit 1 ;;
  esac
fi
SNAPSHOT="20261023T142942Z"                       # snapshot.debian.org pin
MIRROR="https://snapshot.debian.org/archive/debian/${SNAPSHOT}"
export SOURCE_DATE_EPOCH=1792765782               # 2026-10-23T14:29:42Z (== snapshot)
WORK="${WORK:-$HOME/iso-build-$FLAVOUR}"
ROOTFS="$WORK/rootfs"
ISOTREE="$WORK/iso-tree"
if [ "$FLAVOUR" = "prod" ]; then OUT="$WORK/maniocserver-amd64.iso"; else OUT="$WORK/maniocserver-$FLAVOUR-amd64.iso"; fi
BDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Default source: the onionhost/ dir of the repo this script lives
# in (Repo Review 2 task 6, B4) - a plain clone builds with no
# environment variables set. OH_SRC still overrides (the rig's
# historical rsync layout).
SRC="${OH_SRC:-$(dirname "$BDIR")/onionhost}"
RUNSC_VERSION="release-20251006.0"                # pinned, Stage 0/1 verified
RUNSC_URL="https://storage.googleapis.com/gvisor/releases/release/20251006/x86_64/runsc"
# Repo Review 2 task 5 (B7): the expected sha512 of the pinned
# binary, recorded here - NOT trusted from the .sha512 served
# beside it (same origin; a substituted download would bring its
# own). Verified against the publisher's .sha512 at pin time,
# 2026-10-20, and cross-checked against the vendored release.
RUNSC_SHA512_PIN="2086280196df63be2a983e15b594bd9dfbb90a177160e3dfcbfc73bf38dcd31705e62a4ac6d2a3c17e9d2afbd6699dc9780e4cc2bb0ae877ea375d10925882cd"
# Base packages. openssh-server and xdotool are deliberately ABSENT:
# test flavour installs them in its chroot phase only.
PKGS="linux-image-amd64,initramfs-tools,live-boot,live-config,systemd-sysv,udev,dbus,sudo,locales,console-setup,keyboard-configuration,xkb-data,lightdm,xfce4,xfce4-terminal,xserver-xorg,network-manager,calamares,calamares-settings-debian,cryptsetup,cryptsetup-initramfs,parted,dosfstools,e2fsprogs,rsync,squashfs-tools,podman,tor,chrony,nftables,shim-signed,grub-efi-amd64-signed,grub-pc-bin,isolinux,syslinux-common,efibootmgr,ca-certificates,less,vim-tiny,psmisc,cracklib-runtime,wamerican,grub-efi,python3,age,python3-argon2,acl"

log(){ echo "[build-iso $FLAVOUR $(date -u +%H:%M:%S)] $*"; }

# --- recipe selection (Repo Review 3 task 10, B9) -------------------
# A release build ships EXACTLY the recipes in the tracked ship list
# $SRC/recipes/SHIPPING. The marketplace is not on that list until
# owner decision 3 is met (it must first be rebuildable from a
# pinned public commit), so a release build cannot include it
# without a change to SHIPPING. build/fetch-recipe-archives.sh resolves this same
# selection the same way; the factory-package loop below packages
# exactly SELECTED_RECIPES. OH_RECIPES="id,id,..." may select a
# different set (e.g. a local/stranger build that must leave out
# SMF, whose archive cannot be re-fetched) ONLY for a non-release
# build: without OH_NONRELEASE_BUILD=1 it is FATAL here, before any
# work; with it, the build banners itself NON-RELEASE below and
# stamps release_status=non-release into BUILD-INFO.
SHIPPING_FILE="$SRC/recipes/SHIPPING"
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

# --- source-tree provenance (doc batch 2026-10-22, item 5) --------
# OH_SRC overrides the source tree this build consumes (the rig's
# historical rsync layout). It is held to the same rule as the
# OH_RECIPES override above: allowed only for a clearly-marked
# NON-RELEASE build. Without OH_NONRELEASE_BUILD=1 it is FATAL
# here, before any image work; with it, the build is stamped
# non-release by the same machinery, so an overridden-source build
# can no longer produce release paperwork. The source commit /
# tree hash are computed here and stamped into BUILD-INFO below;
# an overridden tree that is not a git checkout records "unknown"
# — which is itself the disclosure.
if [ -n "${OH_SRC:-}" ]; then
  if [ "$RELEASE_STATUS" != "non-release" ]; then
    echo "FATAL: OH_SRC is set ('${OH_SRC}') but OH_NONRELEASE_BUILD=1 is not. A source-tree override is allowed only for a clearly-marked NON-RELEASE build: unset OH_SRC for a release build, or set OH_NONRELEASE_BUILD=1 to build non-release from this source tree." >&2
    exit 1
  fi
  SRC_SOURCE="OH_SRC override"
else
  SRC_SOURCE="tracked clone default"
fi
SRC_COMMIT="$(git -C "$SRC" rev-parse HEAD 2>/dev/null || echo unknown)"
SRC_TREE="$(git -C "$SRC" rev-parse 'HEAD^{tree}' 2>/dev/null || echo unknown)"
[ "${#SELECTED_RECIPES[@]}" -gt 0 ] || { echo "FATAL: recipe selection is empty (the SHIPPING list / OH_RECIPES named no recipes) - refusing to build an image with no factory recipes." >&2; exit 1; }
_seen=" "
for _id in "${SELECTED_RECIPES[@]}"; do
  case "$_id" in
    *[!a-z0-9-]*|"") echo "FATAL: invalid recipe id in selection: '$_id'" >&2; exit 1 ;;
  esac
  case "$_seen" in
    *" $_id "*) echo "FATAL: recipe '$_id' is selected twice - fix the SHIPPING list / OH_RECIPES." >&2; exit 1 ;;
  esac
  _seen="$_seen$_id "
  [ -f "$SRC/recipes/$_id/recipe.json" ] || { echo "FATAL: selected recipe '$_id' has no recipe.json at $SRC/recipes/$_id/recipe.json" >&2; exit 1; }
done
if [ "$RELEASE_STATUS" = "non-release" ]; then
  log "======================================================================"
  log "*** NON-RELEASE BUILD (OH_NONRELEASE_BUILD=1) ***"
  log "Recipe selection: ${SELECTED_RECIPES[*]} (source: $RECIPES_SOURCE)"
  log "This ISO is NOT a release build and must not be published as one."
  log "======================================================================"
fi
log "recipe selection ($RELEASE_STATUS, source: $RECIPES_SOURCE): ${SELECTED_RECIPES[*]}"

# --- output naming (Repo Review 4 task 9, B15) ----------------------
# A non-release ISO must not look like a release ISO: its file name
# carries "nonrelease" and its volume label carries "NONRELEASE".
# Release naming is exactly the historical naming (OUT set at the
# top of this script, volume label MANIOC_LIVE).
if [ "$RELEASE_STATUS" = "non-release" ]; then
  VOLID="MANIOC_NONRELEASE"
  case "$FLAVOUR" in
    prod) OUT="$WORK/maniocserver-nonrelease-amd64.iso" ;;
    *) OUT="$WORK/maniocserver-nonrelease-$FLAVOUR-amd64.iso" ;;
  esac
else
  VOLID="MANIOC_LIVE"
fi
log "output: $OUT (volume label $VOLID, $RELEASE_STATUS)"

[ -d "$SRC/rootfs-overlay" ] || { echo "onionhost source tree not found at $SRC" >&2; exit 1; }
mkdir -p "$WORK" "$WORK/logs" "$WORK/cache"

# --- archive keyring gate (Repo Review 2 task 4, B3) ----------------
# Every installed box verifies project updates against this PUBLIC
# keyring, baked into the image from the overlay. Missing, the build
# would ship boxes that can never verify an update; wrong, they
# would trust the wrong signer. Fail here, in plain words.
ARCHIVE_KEY_FPR="38AA06376F68206F072939DE82610F8D4BEF9565"
KEYRING="$SRC/rootfs-overlay/usr/share/keyrings/onionhost-archive-keyring.gpg"
[ -f "$KEYRING" ] || { echo "FATAL: archive keyring missing at $KEYRING - this build would ship boxes that can never verify a project update. Restore the PUBLIC project keyring (export procedure: maintainer README, outside this repo) and rebuild." >&2; exit 1; }
# Repo Review 3 task 11 (B10), as corrected by Repo Review 4
# task 8 (B13): judge the WHOLE file, not its first key. apt's
# Signed-By trusts EVERY key in this file, so require exactly one
# pub record (one primary key), require no secret material (no
# sec/ssb records) anywhere in it, and compare the pin against the
# fpr record immediately following that pub. Do NOT count fpr
# records: GnuPG prints an fpr after the primary key AND after
# every subkey, so a primary key with a signing subkey - the
# expected release shape, e.g. a hardware key - legitimately has
# more than one fpr and must pass.
KEYRING_COLONS="$(gpg --show-keys --with-colons "$KEYRING" 2>/dev/null)" \
  || { echo "FATAL: archive keyring at $KEYRING is unreadable by gpg --show-keys - refusing to ship boxes that trust an unverifiable keyring." >&2; exit 1; }
if printf '%s\n' "$KEYRING_COLONS" | awk -F: '$1=="sec" || $1=="ssb" {found=1} END{if (found) exit 0; else exit 1}'; then
  echo "FATAL: archive keyring at $KEYRING contains SECRET key material (a sec/ssb record) - a signing key must never ship in an image or a repo. Restore the PUBLIC-only project keyring and rebuild." >&2; exit 1;
fi
KEYRING_PUB_COUNT="$(printf '%s\n' "$KEYRING_COLONS" | awk -F: '$1=="pub" {c++} END{print c+0}')"
[ "$KEYRING_PUB_COUNT" = "1" ] || { echo "FATAL: archive keyring at $KEYRING holds $KEYRING_PUB_COUNT primary key(s), expected exactly 1 - apt would trust every key in the file. Restore the single-key PUBLIC project keyring and rebuild." >&2; exit 1; }
KEYRING_FPR="$(printf '%s\n' "$KEYRING_COLONS" | awk -F: '$1=="pub" {want=1; next} want && $1=="fpr" {print $10; exit} want {exit}')"
[ "$KEYRING_FPR" = "$ARCHIVE_KEY_FPR" ] || { echo "FATAL: archive keyring fingerprint is '${KEYRING_FPR:-unreadable}', pinned is $ARCHIVE_KEY_FPR - refusing to ship boxes that trust the wrong signing key." >&2; exit 1; }
log "archive keyring gate OK: $ARCHIVE_KEY_FPR"

# --- host deps -------------------------------------------------------------
for t in mmdebstrap mksquashfs xorriso grub-mkrescue; do command -v $t >/dev/null || MISSING=1; done
if [ "${MISSING:-}" = 1 ]; then
  log "installing host build deps"
  apt-get update -qq
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq mmdebstrap xorriso grub-common grub-pc-bin grub-efi-amd64-bin mtools debian-archive-keyring squashfs-tools curl >"$WORK/logs/hostdeps.log" 2>&1
fi

# --- runsc (pinned official binary, sha512-verified) ------------------------
if [ ! -f "$WORK/cache/runsc" ]; then
  log "fetching runsc $RUNSC_VERSION"
  curl -fsSL -o "$WORK/cache/runsc" "$RUNSC_URL"
  curl -fsSL -o "$WORK/cache/runsc.sha512" "${RUNSC_URL}.sha512"
  ( cd "$WORK/cache" && sha512sum -c runsc.sha512 ) || { echo "runsc sha512 MISMATCH" >&2; exit 1; }
  chmod 755 "$WORK/cache/runsc"
fi
RUNSC_SHA512=$(sha512sum "$WORK/cache/runsc" | awk '{print $1}')
# Repo Review 2 task 5 (B7): the digest must equal the constant
# pinned at the top of this script, not merely the .sha512 served
# from the same origin as the binary.
[ "$RUNSC_SHA512" = "$RUNSC_SHA512_PIN" ] || { echo "FATAL: runsc sha512 $RUNSC_SHA512 != pinned $RUNSC_SHA512_PIN - refusing to build with an unverified sandbox runtime" >&2; exit 1; }

# --- Calamares phrase plugin (slice 3: build automated) -------------------
# Slice 2 compiled the two C++ viewstep plugins by hand in a rig chroot.
# That manual step is now part of this script (A14: a release build has
# no manual steps and no binaries out of a developer's home directory).
# The compile chroot is an mmdebstrap tree from the SAME pinned snapshot;
# the Calamares source headers (not shipped by the Debian package) come
# from the snapshot pool, verified against the SHA-256 recorded in the
# signed .dsc of calamares 3.3.14-1 at this snapshot. The chroot is
# cached under $WORK (delete $WORK/calabuild to recreate it); the .so
# outputs are rebuilt on EVERY run and their hashes land in BUILD-INFO.
CALA_VER="3.3.14"
CALA_ORIG_SHA256="fa158d679bb9384beaf4a2f821be6da63500b13631ad14acec9bb446565dad4a"
CALABUILD="$WORK/calabuild"
# The calabuild chroot serves two compiles: the OnionHost viewstep
# plugins (build-plugins.sh) and, since slice 5A, the patched
# Calamares partition module (build-partition.sh), whose cmake
# build needs Calamares' own build dependencies. The include list
# is stamped into the chroot; a mismatch recreates it.
CALABUILD_INCLUDE="g++,make,qt6-base-dev,qt6-base-dev-tools,pkg-config,calamares,ca-certificates,cmake,extra-cmake-modules,gettext,patch,python3-dev,qt6-declarative-dev,libkf6config-dev,libkf6coreaddons-dev,libkf6crash-dev,libkf6i18n-dev,libkf6iconthemes-dev,libkf6kio-dev,libkf6parts-dev,libkf6service-dev,libkf6solid-dev,libkpmcore-dev,libparted-dev,libpolkit-qt6-1-dev,libpwquality-dev,libboost-python-dev,libqt6svg6-dev,libyaml-cpp-dev"
build_plugins(){
  local rootfs="$CALABUILD/rootfs"
  if [ "$(cat "$CALABUILD/.include-stamp" 2>/dev/null)" != "$CALABUILD_INCLUDE" ]; then
    log "mmdebstrap plugin-build chroot -> $rootfs"
    rm -rf "$CALABUILD"; mkdir -p "$CALABUILD"
    mmdebstrap --mode=root --variant=important --components=main \
      --aptopt='Acquire::Check-Valid-Until "false"' \
      --include="$CALABUILD_INCLUDE" \
      trixie "$rootfs" "$MIRROR" > "$WORK/logs/calabuild-mmdebstrap.log" 2>&1
    echo "$CALABUILD_INCLUDE" > "$CALABUILD/.include-stamp"
    touch "$CALABUILD/.ready"
  fi
  local srcdir="$CALABUILD/calamares-$CALA_VER"
  if [ ! -d "$srcdir" ]; then
    curl -fsSL -o "$CALABUILD/calamares_$CALA_VER.orig.tar.gz" \
      "$MIRROR/pool/main/c/calamares/calamares_$CALA_VER.orig.tar.gz"
    echo "$CALA_ORIG_SHA256  $CALABUILD/calamares_$CALA_VER.orig.tar.gz" | sha256sum -c - >/dev/null \
      || { echo "FATAL: calamares source tarball sha256 mismatch" >&2; exit 1; }
    tar -xzf "$CALABUILD/calamares_$CALA_VER.orig.tar.gz" -C "$CALABUILD"
  fi
  rm -rf "$rootfs/src" "$rootfs/build"
  mkdir -p "$rootfs/src" "$rootfs/build"
  cp -a "$srcdir" "$rootfs/src/"
  cp -a "$SRC/calamares/plugin-src" "$rootfs/src/plugin-src"
  install -m 0755 "$SRC/calamares/plugin-src/build-plugins.sh" "$rootfs/build/build-plugins.sh"
  log "compiling Calamares plugins (in chroot)"
  chroot "$rootfs" /usr/bin/env -i \
    PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
    LC_ALL=C TZ=UTC SOURCE_DATE_EPOCH="$SOURCE_DATE_EPOCH" \
    /bin/bash /build/build-plugins.sh > "$WORK/logs/plugin-build.log" 2>&1
  # Repo Review 2 task 6 (P5/B4): compiled plugins land in $WORK,
  # never in the source tree (a build from a git clone must leave
  # `git status` clean); phase B0 installs them into the rootfs.
  local m
  mkdir -p "$WORK/cache/plugins"
  for m in onionhostphrase onionhostguard; do
    mkdir -p "$WORK/cache/plugins/$m"
    install -m 0644 "$rootfs/src/modules-out/$m/libcalamares_viewmodule_$m.so" \
      "$WORK/cache/plugins/$m/libcalamares_viewmodule_$m.so"
  done
  log "plugins built OK"
}
build_plugins

# --- Calamares partition module (slice 5A: forced-encryption patch) -----
# Stock Calamares 3.3.14 cannot force encryption: its erase/replace/
# alongside layouts take the passphrase ONLY from the encrypt
# widget's text fields, and ChoicePage::onLeave overwrites
# GlobalStorage luksPassphrase with the widget state (empty when the
# box is unticked or the fields are blank) - the exact mechanism of
# Cameron's failed phone install. The pinned patch (in $SRC, applied
# to the same sha256-verified source tarball as the plugins) makes
# the generated phrase - already in GlobalStorage, set by the phrase
# view step - the only passphrase an automated install can use, and
# keeps the widget's fields hidden so nothing typed can override it.
# See calamares/patches/0001-onionhost-force-encryption.patch.
build_partition_module(){
  local rootfs="$CALABUILD/rootfs"
  rm -rf "$rootfs/src/patches"
  cp -a "$SRC/calamares/patches" "$rootfs/src/patches"
  install -m 0755 "$SRC/calamares/plugin-src/build-partition.sh" "$rootfs/build/build-partition.sh"
  log "compiling patched Calamares partition module (in chroot)"
  chroot "$rootfs" /usr/bin/env -i \
    PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
    HOME=/root \
    LC_ALL=C TZ=UTC SOURCE_DATE_EPOCH="$SOURCE_DATE_EPOCH" \
    /bin/bash /build/build-partition.sh > "$WORK/logs/partition-build.log" 2>&1
  install -m 0644 "$rootfs/src/modules-out-partition.so" \
    "$WORK/cache/libcalamares_viewmodule_partition.so"
  log "patched partition module built OK"
}
build_partition_module

# --- container image rootfs tarballs (A6: local build, podman import) ------
build_image_tar(){ # $1=name $2=packages $3=keep-zoneinfo (optional)
  local tar="$WORK/cache/onionhost-$1.tar"
  if [ ! -f "$tar" ]; then
    log "mmdebstrap container image: $1 ($2)" >&2
    # Slice-3 slimming (measured on the rig, ISO-BUILD-LOG slice 3):
    # --variant=minbase and NO --skip=cleanup/apt. The containers
    # never run apt, so the kept .deb cache (116 MB) and package
    # lists (~60 MB) the old recipe shipped in EVERY image were pure
    # dead weight; the customize-hook strips docs (keeping copyright
    # files), man pages and locale data the two daemons never read.
    # tor image 381 MB -> 88 MB, web image 375 MB -> 91 MB, with
    # tor --version / --list-modules and nginx -t verified on the
    # slimmed images before adoption. (Pre-compressing the tars was
    # also tested: podman import accepts .tar.xz, but the tars live
    # inside the xz squashfs, so it would buy ~nothing.)
    # D3 (rig battery 2026-10-14): the zoneinfo strip is NOT
    # universal. Debian's PHP is built against the system timezone
    # database (/usr/share/zoneinfo), so an app image without it
    # gives PHP an empty timezone database and every page of a PHP
    # app dies ("Timezone database is corrupt"). The app image
    # therefore ships tzdata AND keeps its zoneinfo; tor/web keep
    # the strip (neither reads it). The cached-tar check above
    # means a flag change only takes effect once the cached tar
    # is deleted - the build that adopts this must rm the app tar.
    local zoneinfo_rm=' "$1"/usr/share/zoneinfo'
    if [ "${3:-}" = "keep-zoneinfo" ]; then zoneinfo_rm=''; fi
    local hook='find "$1"/usr/share/doc -type f ! -name copyright -delete 2>/dev/null; rm -rf "$1"/usr/share/man/* "$1"/usr/share/info "$1"/usr/share/lintian "$1"/usr/share/i18n'"$zoneinfo_rm"' "$1"/var/cache/apt/archives/*.deb "$1"/var/lib/apt/lists/* 2>/dev/null; find "$1"/usr/share/locale -mindepth 1 -maxdepth 1 -type d -exec rm -rf {} + 2>/dev/null; true'
    mmdebstrap --mode=root --variant=minbase --components=main \
      --aptopt='Acquire::Check-Valid-Until "false"' \
      --customize-hook="$hook" \
      --include="$2" trixie "$tar" "$MIRROR" > "$WORK/logs/img-$1.log" 2>&1
  fi
  echo "$tar"
}
IMG_TOR=$(build_image_tar tor "tor,ca-certificates")
IMG_WEB=$(build_image_tar web "nginx-light,libnginx-mod-http-headers-more-filter,ca-certificates")
# Slice 6B: the combined app image (nginx + PHP-FPM + MariaDB in one
# sandbox; sqlite3 is for native apps' own use and host-side checks).
# The package closure is the gate round's proven set
# (poc/dynamic/scripts/build-rootfs.sh seed).
# A23 recipe 4 (Gitea) added git: a native app may hard-require it
# (Gitea shells out to git for every repository operation and
# refuses to start without it). It is part of the slot's furniture,
# like sqlite3 - inert in the sealed room (no network exists for
# it to reach), present so apps that need it can run at all.
# tzdata + keep-zoneinfo: defect D3 (see build_image_tar) - PHP
# reads the system timezone database, and without it every PHP
# page dies on an empty timezone database.
IMG_APP=$(build_image_tar app "nginx,libnginx-mod-http-headers-more-filter,php-fpm,php-mysql,php-gd,php-mbstring,php-xml,php-intl,php-zip,php-curl,mariadb-server,mariadb-client,postgresql,curl,libnettle8t64,libhogweed6t64,sqlite3,git,tzdata,ca-certificates" keep-zoneinfo)

{
  echo "snapshot=${SNAPSHOT}"
  echo "mirror=${MIRROR}"
  echo "source_date_epoch=${SOURCE_DATE_EPOCH}"
  echo "suite=trixie arch=amd64 components=main"
  echo "flavour=${FLAVOUR} oh_probe=${OH_PROBE}"
  echo "release_status=${RELEASE_STATUS}"
  echo "recipes_source=${RECIPES_SOURCE}"
  echo "recipes_selected=${SELECTED_RECIPES[*]}"
  echo "src_source=${SRC_SOURCE}"
  echo "src_commit=${SRC_COMMIT}"
  echo "src_tree=${SRC_TREE}"
  echo "runsc=${RUNSC_VERSION} sha512=${RUNSC_SHA512}"
  echo "img_tor_sha256=$(sha256sum "$IMG_TOR" | awk '{print $1}')"
  echo "img_web_sha256=$(sha256sum "$IMG_WEB" | awk '{print $1}')"
  echo "img_app_sha256=$(sha256sum "$IMG_APP" | awk '{print $1}')"
  echo "plugin_phrase_sha256=$(sha256sum "$WORK/cache/plugins/onionhostphrase/libcalamares_viewmodule_onionhostphrase.so" | awk '{print $1}')"
  echo "plugin_guard_sha256=$(sha256sum "$WORK/cache/plugins/onionhostguard/libcalamares_viewmodule_onionhostguard.so" | awk '{print $1}')"
  echo "partition_module_sha256=$(sha256sum "$WORK/cache/libcalamares_viewmodule_partition.so" | awk '{print $1}')"
  echo "partition_patch=0001-onionhost-force-encryption.patch sha256=$(sha256sum "$SRC/calamares/patches/0001-onionhost-force-encryption.patch" | awk '{print $1}')"
  echo "builder_host=$(uname -sr) mmdebstrap=$(mmdebstrap --version 2>/dev/null | head -1)"
  echo "build_started_utc=$(date -u +%FT%TZ)"
} > "$WORK/BUILD-INFO"

# --- phase A: rootfs --------------------------------------------------------
if [ ! -f "$ROOTFS/.mmdebstrap-done" ]; then
  log "mmdebstrap trixie from pinned snapshot -> $ROOTFS"
  rm -rf "$ROOTFS"
  # variant=important (not standard): standard pulls systemd-timesyncd, which
  # conflicts with chrony over the time-daemon virtual package.
  # --skip=cleanup/apt keeps /var/lib/apt/lists: Calamares' bootloader-config
  # helper apt-installs grub-efi INSIDE the target, which needs candidates.
  mmdebstrap --mode=root --variant=important --components=main --skip=cleanup/apt \
    --aptopt='Acquire::Check-Valid-Until "false"' \
    --include="$PKGS" \
    trixie "$ROOTFS" "$MIRROR" > "$WORK/logs/mmdebstrap.log" 2>&1
  touch "$ROOTFS/.mmdebstrap-done"
  log "mmdebstrap done: $(du -sh "$ROOTFS" | cut -f1)"
else
  log "rootfs exists, skipping mmdebstrap (rm -rf $ROOTFS to redo)"
fi

# --- phase B0: onionhost overlay + assets -----------------------------------
log "applying onionhost overlay from $SRC"
# __pycache__ is never image content (review 2026-10-25, F5): the
# .deb builder already strips it, but this rsync did not - a build
# tree in which anyone had imported the overlay's Python (the poc
# harnesses do exactly that) would ship stale bytecode, including
# compiled test-vector constants that read as secrets to scanners.
rsync -a --exclude '__pycache__' "$SRC/rootfs-overlay/" "$ROOTFS/"
mkdir -p "$ROOTFS/usr/lib/onionhost/images"
cp "$IMG_TOR" "$ROOTFS/usr/lib/onionhost/images/onionhost-tor.tar"
cp "$IMG_WEB" "$ROOTFS/usr/lib/onionhost/images/onionhost-web.tar"
cp "$IMG_APP" "$ROOTFS/usr/lib/onionhost/images/onionhost-app.tar"
# The images manifest (review 2026-10-25, F2): the identical
# IMAGES-VERSION the onionhost-images package delivers (same
# format, same content identity - see build-onionhost-images-deb.sh),
# so a fresh install's import record starts at the version of the
# images actually on this ISO and a later package delivery is
# judged as the change it is, not as a first import.
{
  for t in onionhost-tor.tar onionhost-web.tar onionhost-app.tar; do
    printf '%s: %s\n' "$t" \
      "$(sha256sum "$ROOTFS/usr/lib/onionhost/images/$t" | awk '{print $1}')"
  done
} > "$ROOTFS/usr/lib/onionhost/images/.hashlines"
_oh_img_combined=$(sha256sum "$ROOTFS/usr/lib/onionhost/images/.hashlines" | awk '{print $1}')
{
  printf 'version: img-%s\n' "${_oh_img_combined:0:12}"
  cat "$ROOTFS/usr/lib/onionhost/images/.hashlines"
} > "$ROOTFS/usr/lib/onionhost/images/IMAGES-VERSION"
rm -f "$ROOTFS/usr/lib/onionhost/images/.hashlines"
install -m 0755 "$WORK/cache/runsc" "$ROOTFS/usr/local/bin/runsc"
chmod 0755 "$ROOTFS"/usr/local/bin/runsc-wrap \
           "$ROOTFS"/usr/local/bin/onionhost-generate-configs \
           "$ROOTFS"/usr/local/bin/onionhost-probe \
           "$ROOTFS"/usr/local/bin/onionhost-nft-gate \
           "$ROOTFS"/usr/local/bin/onionhost-nft-gate-check \
           "$ROOTFS"/usr/local/bin/onionhost-runtime-gate \
           "$ROOTFS"/usr/local/bin/onionhost-runtime-gate-check \
           "$ROOTFS"/usr/local/bin/onionhost-nft-compare.py \
           "$ROOTFS"/usr/local/bin/onionhost-import-images \
           "$ROOTFS"/usr/local/bin/onionhost-grub-stub \
           "$ROOTFS"/usr/local/bin/onionhost-wizard-session \
           "$ROOTFS"/usr/local/bin/onionhost-wizard-helper \
           "$ROOTFS"/usr/local/bin/onionhost-publish \
           "$ROOTFS"/usr/local/bin/onionhost-rekey \
           "$ROOTFS"/usr/local/bin/onionhost-backup \
           "$ROOTFS"/usr/local/bin/onionhost-restore \
           "$ROOTFS"/usr/local/bin/onionhost-app-provision \
           "$ROOTFS"/usr/local/bin/onionhost-appdata-guard \
           "$ROOTFS"/usr/local/bin/onionhost-maintenance \
           "$ROOTFS"/etc/initramfs-tools/hooks/zz-onionhost-cryptsetup \
           "$ROOTFS"/etc/initramfs-tools/hooks/zz-onionhost-keyfile
chmod 0644 "$ROOTFS"/usr/lib/onionhost/phrasegen.py \
           "$ROOTFS"/usr/lib/onionhost/sitegen.py \
           "$ROOTFS"/usr/lib/onionhost/wizard.py \
           "$ROOTFS"/usr/lib/onionhost/backupkeys.py
chmod 0644 "$ROOTFS"/usr/lib/onionhost/templates/*
# rsync -a applies the overlay tree's directory modes to MERGED system
# dirs; the workspace overlay ships 770 dirs, which silently broke the
# live boot (LightDM/dbus could not traverse /etc). Force standard
# modes on every merged parent and verify the critical ones.
for d in etc usr var etc/systemd etc/systemd/system etc/containers \
         usr/lib usr/local usr/local/bin var/lib run; do
  [ -d "$ROOTFS/$d" ] && chmod 755 "$ROOTFS/$d"
done
# Slice 2: generalise - EVERY directory the overlay touches must end
# up 755 in the rootfs. A single new overlay dir at 770 (e.g.
# usr/share/xsessions) otherwise re-breaks the boot for all non-root
# users (observed: /usr/share at 770 killed dbus + LightDM).
( cd "$SRC/rootfs-overlay" && find . -type d -printf '%P\n' ) | \
  while IFS= read -r d; do
    [ -n "$d" ] && [ -d "$ROOTFS/$d" ] && chmod 755 "$ROOTFS/$d"
  done
for d in etc usr var run; do
  [ "$(stat -c %a "$ROOTFS/$d")" = "755" ] || { echo "FATAL: $ROOTFS/$d mode not 755 after overlay merge" >&2; exit 1; }
done
# Calamares jobmodules. Calamares 3.3 searches ONLY
# /usr/lib/x86_64-linux-gnu/calamares/modules and
# /usr/lib/calamares/modules for module code - /etc/calamares/modules
# holds module CONFIG files only. (Verified from the live session log:
# modules placed in /etc/calamares/modules fail startup.)
mkdir -p "$ROOTFS/usr/lib/calamares/modules"
rsync -a --exclude '__pycache__' "$SRC/calamares/modules/" "$ROOTFS/usr/lib/calamares/modules/"
# The compiled viewstep plugins come from $WORK (task 6), replacing
# any stale copy the source tree might still carry.
for m in onionhostphrase onionhostguard; do
  install -m 0644 "$WORK/cache/plugins/$m/libcalamares_viewmodule_$m.so" \
    "$ROOTFS/usr/lib/calamares/modules/$m/libcalamares_viewmodule_$m.so"
done
# The diagnostics probe module must not SHIP in the production image
# at all: it is inert unless sequenced (OH_PROBE controls that), but
# it writes GlobalStorage contents to disk when run - defence in
# depth says it simply does not exist in prod (found in the prod
# squashfs during the step-3 slice-1 audit, 2026-10-12).
if [ "$OH_PROBE" != "1" ]; then
  rm -rf "$ROOTFS/usr/lib/calamares/modules/onionhostprobe"
fi
chmod 0644 "$ROOTFS"/usr/lib/calamares/modules/*/module.desc "$ROOTFS"/usr/lib/calamares/modules/*/main.py
find "$ROOTFS/usr/lib/calamares/modules" -name '*.qml' -exec chmod 0644 {} +
# Slice 5A: replace the stock partition viewmodule with the patched
# build (forced encryption, see build_partition_module above). The
# stock module ships in the base calamares package at exactly this
# path; fail the build if it is not there rather than shipping a
# silently unpatched installer.
PART_STOCK="$ROOTFS/usr/lib/x86_64-linux-gnu/calamares/modules/partition/libcalamares_viewmodule_partition.so"
[ -f "$PART_STOCK" ] || { echo "FATAL: stock partition module missing at $PART_STOCK" >&2; exit 1; }
install -m 0644 "$WORK/cache/libcalamares_viewmodule_partition.so" "$PART_STOCK"
# A19.1 entropy-source gate: the vendored EFF large wordlist must be
# exactly 7776 entries, all unique, or every phrase on every install
# silently loses entropy. Fail the build, not the user.
WL="$ROOTFS/usr/share/onionhost/eff-large-wordlist.txt"
WL_LINES=$(wc -l < "$WL"); WL_WORDS=$(awk '{print $NF}' "$WL" | sort -u | wc -l)
[ "$WL_LINES" = 7776 ] && [ "$WL_WORDS" = 7776 ] || { echo "FATAL: wordlist gate failed (lines=$WL_LINES unique=$WL_WORDS)" >&2; exit 1; }
log "A19.1 wordlist gate OK: 7776 unique words"

# --- factory packages (Gate 4 + A23) ---------------------------------------
# The updater's factory version and the wizard's recipe choices both
# key off dpkg state the overlay alone cannot provide: the platform
# package and the recipe packages must be REGISTERED in the installed
# system's dpkg database. The .debs are built here from this same
# tree and planted in the rootfs; the onionhostfirstrun Calamares
# job dpkg-installs them into the target at install time (their
# postinsts are no-ops until a site selects them). Platform factory
# version is 1.0.0 (Gate 4); recipe versions come from recipe.json.
FACTORY_VERSION="1.0.0"
FPKGS="$WORK/factory-pkgs"
rm -rf "$FPKGS"; mkdir -p "$FPKGS"
OH_OVERLAY="$SRC/rootfs-overlay" bash "$BDIR/build-onionhost-deb.sh" \
  "$FACTORY_VERSION" "$FPKGS" > "$WORK/logs/factory-deb.log" 2>&1
# Repo Review 2 task 3 (B1): recipe archives are gitignored
# vendored inputs - fetch whatever is missing and verify EVERY
# archive against its recipe.json pin before any package is built
# from it. A mismatch aborts here, never inside a signed package.
# Repo Review 3 task 10 (B9): fetch and package EXACTLY the
# selection resolved at the top of this script (default: the
# tracked SHIPPING list - the marketplace cannot enter a release
# build). The fetch script resolves the same selection itself
# from the same SHIPPING list / OH_RECIPES + OH_NONRELEASE_BUILD
# environment.
bash "$BDIR/fetch-recipe-archives.sh" "$SRC/recipes" \
  || { echo "FATAL: recipe archive fetch/verify failed (see above)" >&2; exit 1; }
for rid in "${SELECTED_RECIPES[@]}"; do
  rdir="$SRC/recipes/$rid"
  rver=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["version"])' "$rdir/recipe.json")
  bash "$BDIR/build-recipe-deb.sh" "$rdir" "$rver" "$FPKGS" >> "$WORK/logs/factory-deb.log" 2>&1
done
mkdir -p "$ROOTFS/usr/lib/onionhost/factory-packages"
cp "$FPKGS"/*.deb "$ROOTFS/usr/lib/onionhost/factory-packages/"
{ echo "factory_version=$FACTORY_VERSION"
  for d in "$FPKGS"/*.deb; do echo "factory_pkg $(basename "$d") sha256=$(sha256sum "$d" | awk '{print $1}')"; done
} >> "$WORK/BUILD-INFO"
log "factory packages planted: $(ls "$FPKGS" | tr '\n' ' ')"
# Repo Review 2 task 8 (B8): the BUILD-INFO copies that enter the
# image and the ISO root carry pins and hashes alone. builder_host
# and build_started_utc stay in $WORK's copy (the out-of-image
# build log), so two builds of one commit can produce an identical
# /etc/onionhost-build-info. The live account's password is a
# locked constant for the same reason (customise phase, below;
# owner decision 2026-10-20 on reviewer question 4).
grep -v -E '^(builder_host|build_started_utc)=' \
  "$WORK/BUILD-INFO" > "$WORK/BUILD-INFO.image"

# --- phase B: chroot customisation ------------------------------------------
log "chroot customisation"
mountpoint -q "$ROOTFS/proc" || mount -t proc proc "$ROOTFS/proc"
mountpoint -q "$ROOTFS/sys"  || mount -t sysfs sys "$ROOTFS/sys"
mountpoint -q "$ROOTFS/dev"  || mount --bind /dev "$ROOTFS/dev"
mountpoint -q "$ROOTFS/dev/pts" || mount -t devpts devpts "$ROOTFS/dev/pts"
cleanup_mounts(){ for d in dev/pts dev sys proc; do umount -q "$ROOTFS/$d" 2>/dev/null || true; done; }
trap cleanup_mounts EXIT
cat > "$ROOTFS/tmp/customize.sh" <<'EOS'
#!/bin/bash
set -euxo pipefail
export DEBIAN_FRONTEND=noninteractive LC_ALL=C
FLAVOUR="${OH_FLAVOUR:-prod}"
OH_PROBE="${OH_PROBE:-0}"
TEST_SSH_PUBKEY="${OH_TEST_SSH_PUBKEY:-}"
echo "onionhost-live" > /etc/hostname
# locales: en-US default; keyboard: us primary + de as switchable extra layout
sed -i 's/^# *en_US.UTF-8/en_US.UTF-8/' /etc/locale.gen; locale-gen
# Slice-2 runtime deps (both flavours): the wizard is Python/Tk, and
# the Calamares phrase pages are QML (the stock image ships the Qt6
# QML runtime but NO QtQuick module package - the pages cannot load
# without it).
# NOTE (battery 2026-10-14): the Gate 4 overlay lockdown
# (52onionhost-tor-updates: Dir::Bin::Methods::https "false") is
# already in this rootfs and disables the https method for the
# build's OWN snapshot sources too. Every build-time apt call below
# re-enables the methods for itself only (-o Dir::Bin::Methods::*);
# the shipped image keeps the lockdown untouched.
apt-get -o Acquire::Check-Valid-Until=false -o Dir::Bin::Methods::http=http -o Dir::Bin::Methods::https=https install -y python3-tk python3-pil qml6-module-qtquick age python3-argon2 >/dev/null
printf '%s\n' 'XKBMODEL="pc105"' 'XKBLAYOUT="us,de"' 'XKBVARIANT=""' 'XKBOPTIONS="grp:alt_shift_toggle"' 'BACKSPACE="guess"' > /etc/default/keyboard
# live user: PRE-CREATE it. live-config's user-setup skips users that already
# exist in /etc/passwd - necessary because its built-in default password hash
# (legacy DES crypt of "live") is rejected by trixie's PAM/libxcrypt, which
# breaks BOTH the greeter login AND console/graphical autologin.
id user >/dev/null 2>&1 || useradd -m -s /bin/bash -c "Manioc Live" -G sudo,adm,audio,video,plugdev,netdev user
if [ "$FLAVOUR" = "test" ]; then
  echo 'user:onion' | chpasswd
  # TEST ACCESS (test flavour live session ONLY): operator pubkey +
  # sshd password-auth drop-in (sshd_config.d is read before the main
  # file, so this beats live-config's PasswordAuthentication=no edit).
  apt-get -o Acquire::Check-Valid-Until=false -o Dir::Bin::Methods::http=http -o Dir::Bin::Methods::https=https install -y openssh-server xdotool >/dev/null
  # The operator pubkey arrives via the environment (Repo Review
  # 5 P-4); the outer script already refuses a test build without
  # one, and this guard keeps a hand-run customise honest too.
  if [ -z "$TEST_SSH_PUBKEY" ]; then
    echo "FATAL: test flavour without OH_TEST_SSH_PUBKEY - refusing to build test access with no key" >&2
    exit 1
  fi
  mkdir -p /home/user/.ssh
  printf '%s\n' "$TEST_SSH_PUBKEY" > /home/user/.ssh/authorized_keys
  chmod 700 /home/user/.ssh; chmod 600 /home/user/.ssh/authorized_keys; chown -R user:user /home/user/.ssh
  mkdir -p /etc/ssh/sshd_config.d
  printf 'PasswordAuthentication yes\nPubkeyAuthentication yes\n' > /etc/ssh/sshd_config.d/10-onionhost-test.conf
else
  # PROD (Repo Review 2 task 8; owner decision 2026-10-20 on
  # reviewer question 4): the live account's password is LOCKED -
  # deterministically, not a per-build random value. The live
  # session is autologin-only; the account exists only to carry
  # the live desktop and is deleted from the installed target by
  # onionhostcleanup. A random password bought nothing (nobody
  # knew it either way) and made every build's /etc/shadow unique,
  # so no two builds of one commit could ever be byte-identical.
  # useradd created the account locked already; assert the locked
  # constant rather than assume it, and pin the password-change
  # day to SOURCE_DATE_EPOCH so the whole shadow entry is a
  # constant across builds.
  usermod -p '!' user
  sed -i -r "s|^(user:!):[0-9]+:|\1:$(( ${SOURCE_DATE_EPOCH:-1792765782} / 86400 )):|" /etc/shadow
fi
# live session: LightDM autologin of "user" into XFCE. This is LIVE-ONLY
# mechanics: the onionhostcleanup Calamares job strips the drop-in, the
# autologin settings and the live user itself from the installed target.
sed -i -r -e 's|^#?\s*autologin-user=.*|autologin-user=user|' -e 's|^#?\s*autologin-user-timeout=.*|autologin-user-timeout=0|' /etc/lightdm/lightdm.conf
mkdir -p /etc/lightdm/lightdm.conf.d
printf '[Seat:*]\nautologin-user=user\nautologin-session=xfce\ngreeter-session=lightdm-gtk-greeter\n' > /etc/lightdm/lightdm.conf.d/10-onionhost-live.conf
dpkg -l lightdm-gtk-greeter >/dev/null 2>&1 || apt-get -o Acquire::Check-Valid-Until=false -o Dir::Bin::Methods::http=http -o Dir::Bin::Methods::https=https install -y lightdm-gtk-greeter || true
# Calamares: calamares-settings-debian ships NO partition.conf (module would
# use compiled defaults) - write an explicit one; LUKS2 is mandatory for us.
cat > /etc/calamares/modules/partition.conf <<'EOPC'
efiSystemPartition: "/boot/efi"
efiSystemPartitionSize: 300MiB
userSwapChoices: [none]
drawNestedPartitions: false
allowManualPartitioning: true
defaultFileSystemType: "ext4"
availableFileSystemTypes: ["ext4", "btrfs", "xfs"]
luksGeneration: luks2
# Slice 5A: the "Encrypt system" box starts ticked (the truthful UI
# state - the patched partition module encrypts every automated
# install with the generated phrase whether or not it is ticked).
preCheckEncryption: true
EOPC
# Wire the OnionHost jobmodules into the exec sequence:
#   onionhostbootkey  right after luksbootkeyfile (adds GRUB PBKDF2 slot)
#   onionhostcleanup  right before initramfscfg (strips target scaffolding)
#   onionhostprobe    only when OH_PROBE=1 (diagnostics)
SETTINGS=/etc/calamares/settings.conf
grep -q 'onionhostbootkey' "$SETTINGS" || sed -i 's|^  - luksbootkeyfile$|  - luksbootkeyfile\n  - onionhostbootkey|' "$SETTINGS"
if [ "$OH_PROBE" = "1" ]; then
  grep -q 'onionhostprobe' "$SETTINGS" || sed -i 's|^  - onionhostbootkey$|  - onionhostbootkey\n  - onionhostprobe|' "$SETTINGS"
fi
grep -q 'onionhostcleanup' "$SETTINGS" || sed -i 's|^  - initramfscfg$|  - onionhostcleanup\n  - initramfscfg|' "$SETTINGS"
grep -q 'onionhostbootkey' "$SETTINGS" && grep -q 'onionhostcleanup' "$SETTINGS"
# Slice-2 sequence wiring (idempotent; rootfs is cached across builds):
#   show: the C++ phrase page right after the keyboard page,
#         before partition (the 0,/re/ range limits the edit to the
#         FIRST "- keyboard" line = the show phase). Generation
#         happens inside the phrase view step itself: Calamares 3.3
#         executes job modules ONLY in the exec phase, so a
#         show-phase generation job would never run (found the hard
#         way in slice 2; the stale line is removed below).
sed -i '/^  - onionhostphrasegen$/d' "$SETTINGS"
grep -q 'onionhostphrase' "$SETTINGS" || sed -i '0,/^  - keyboard$/s//  - keyboard\n  - onionhostphrase/' "$SETTINGS"
# Slice 5A: the encryption guard page immediately after the
# partition page (show sequence only: the 0,/re/ range limits the
# edit to the FIRST "- partition" line, which is the show phase).
grep -q 'onionhostguard' "$SETTINGS" || sed -i '0,/^  - partition$/s//  - partition\n  - onionhostguard/' "$SETTINGS"
#   exec: GRUB stub fixes after the bootloader job; first-run S0
#         setup after cleanup (it must see the stripped target).
grep -q 'onionhostgrubstub' "$SETTINGS" || sed -i 's|^  - bootloader$|  - bootloader\n  - onionhostgrubstub|' "$SETTINGS"
grep -q 'onionhostfirstrun' "$SETTINGS" || sed -i 's|^  - onionhostcleanup$|  - onionhostcleanup\n  - onionhostfirstrun|' "$SETTINGS"
grep -q 'onionhostbackupkeys' "$SETTINGS" || sed -i 's|^  - onionhostfirstrun$|  - onionhostfirstrun\n  - onionhostbackupkeys|' "$SETTINGS"
grep -q 'onionhostphrase' "$SETTINGS" && grep -q 'onionhostgrubstub' "$SETTINGS" && grep -q 'onionhostfirstrun' "$SETTINGS" && grep -q 'onionhostguard' "$SETTINGS" && grep -q 'onionhostbackupkeys' "$SETTINGS"
# grub-common's /etc/default/grub is ucf-generated and does NOT materialise
# under mmdebstrap; the installer's grub steps expect it. Synthesise it.
[ -f /etc/default/grub ] || cp /usr/share/grub/default/grub /etc/default/grub
# OnionHost system state: subuid/subgid ranges for rootful --userns=auto
grep -q '^root:' /etc/subuid || echo 'root:100000:655360' >> /etc/subuid
grep -q '^root:' /etc/subgid || echo 'root:100000:655360' >> /etc/subgid
# Podman 5 rootful UserNS=auto allocates per-container ranges from the
# pool of the user named "containers" (observed on the installed
# system: "Cannot find mappings for user containers ... not enough
# unused IDs"). Give that pool user its own non-overlapping range.
id containers >/dev/null 2>&1 || useradd --system --no-create-home --shell /usr/sbin/nologin containers
grep -q '^containers:' /etc/subuid || echo 'containers:2000000:536870912' >> /etc/subuid
grep -q '^containers:' /etc/subgid || echo 'containers:2000000:536870912' >> /etc/subgid
# Sleep is masked: LUKS keys must never sit in a suspended machine.
systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target
# The tor PACKage is in the image only as a source of binaries/data for
# the container rootfs builds; the host must never run its own Tor
# daemon (observed on the installed system: tor@default listening on
# 127.0.0.1:9050). All Tor runs inside the Quadlet containers.
systemctl mask tor.service tor@default.service || true
# OnionHost services on at boot (containers are enabled by Quadlet's
# generator via their [Install] sections).
systemctl enable onionhost-config.service onionhost-images.service \
  onionhost-nft-load.service onionhost-nft-gate.service onionhost-nft-gate.timer \
  onionhost-runtime-gate.timer \
  onionhost-appdata-guard.timer onionhost-loopback.service
# Maintenance console: only reachable via the Maintenance GRUB entry
# (systemd.unit=onionhost-maintenance.target); enabling the service
# just creates its WantedBy symlink under that target.
systemctl enable onionhost-maintenance.service
# build info inside the image (ISO-BUILD-PLAN A14 record)
mkdir -p /etc/onionhost
cp /tmp/BUILD-INFO /etc/onionhost-build-info
# Repo Review 2 (seeded lead 1): mmdebstrap may copy the BUILD
# HOST's /etc/resolv.conf into this rootfs, search domains and all
# (a cloud build host's .internal domain would ship inside every
# image). NetworkManager owns the resolver at runtime on the
# installed system, so ship no static resolv.conf at all. This is
# the LAST resolver step of the customise phase: the chroot's own
# apt calls above still needed the inherited file.
rm -f /etc/resolv.conf
# live initramfs (live-boot + cryptsetup hooks + zz-onionhost-cryptsetup),
# then drop machine-id
update-initramfs -u -k all
: > /etc/machine-id
rm -f /var/lib/dbus/machine-id
EOS
cp "$WORK/BUILD-INFO.image" "$ROOTFS/tmp/BUILD-INFO"
chmod +x "$ROOTFS/tmp/customize.sh"
OH_FLAVOUR="$FLAVOUR" OH_PROBE="$OH_PROBE" OH_TEST_SSH_PUBKEY="$TEST_SSH_PUBKEY" chroot "$ROOTFS" /tmp/customize.sh > "$WORK/logs/customize.log" 2>&1
rm -f "$ROOTFS/tmp/customize.sh"
cleanup_mounts; trap - EXIT
# A19.1 release hygiene: the ISO must NEVER contain a LUKS keyfile (they
# are generated per install by Calamares). Fail the build if one appears.
if [ -e "$ROOTFS/crypto_keyfile.bin" ] || find "$ROOTFS/etc/cryptsetup-keys.d" -type f 2>/dev/null | grep -q .; then
  echo "FATAL: keyfile material present in the ISO rootfs (A19.1)" >&2; exit 1
fi
log "A19.1 check OK: no keyfile in ISO rootfs; kdump-tools present: $( [ -e "$ROOTFS/usr/sbin/kdump-config" ] && echo yes || echo no )"
# Repo Review 2 (seeded lead 1) gate: no build-host resolver data
# may survive into the image - resolv.conf must be gone entirely,
# and no .internal (host search-domain) naming may appear anywhere
# under the image's /etc.
if [ -e "$ROOTFS/etc/resolv.conf" ] || [ -L "$ROOTFS/etc/resolv.conf" ]; then
  echo "FATAL: /etc/resolv.conf survived customisation (build-host resolver data would ship in the image)" >&2; exit 1
fi
if grep -rqs '\.internal' "$ROOTFS/etc" 2>/dev/null; then
  echo "FATAL: '.internal' build-host naming found under $ROOTFS/etc:" >&2
  grep -rl '\.internal' "$ROOTFS/etc" 2>/dev/null | head -5 >&2; exit 1
fi
log "resolver hygiene gate OK: no build-host resolver data in image"
log "customisation done; kernel: $(ls "$ROOTFS"/boot/vmlinuz-* | head -1)"

# --- phase C: ISO tree ------------------------------------------------------
log "assembling ISO tree"
rm -rf "$ISOTREE"; mkdir -p "$ISOTREE/live" "$ISOTREE/boot/grub"
KV=$(basename "$(ls "$ROOTFS"/boot/vmlinuz-* | head -1)")
cp "$ROOTFS/boot/$KV" "$ISOTREE/boot/vmlinuz"
cp "$ROOTFS/boot/initrd.img-${KV#vmlinuz-}" "$ISOTREE/boot/initrd.img"
mksquashfs "$ROOTFS" "$ISOTREE/live/filesystem.squashfs" -comp xz -noappend -wildcards \
  -e "proc/*" "sys/*" "dev/*" "run/*" "tmp/*" > "$WORK/logs/mksquashfs.log" 2>&1
cat > "$ISOTREE/boot/grub/grub.cfg" <<'EOG'
set timeout=5
set default=0
menuentry "Manioc Server (live) - Install" {
    linux /boot/vmlinuz boot=live components quiet
    initrd /boot/initrd.img
}
menuentry "Manioc Server (live, verbose)" {
    linux /boot/vmlinuz boot=live components
    initrd /boot/initrd.img
}
EOG
cp "$WORK/BUILD-INFO.image" "$ISOTREE/BUILD-INFO"
log "squashfs: $(du -sh "$ISOTREE/live/filesystem.squashfs" | cut -f1)"

# --- phase D: hybrid ISO via grub-mkrescue ----------------------------------
log "grub-mkrescue -> $OUT"
rm -f "$OUT"
grub-mkrescue -o "$OUT" "$ISOTREE" -- -volid "$VOLID" > "$WORK/logs/mkrescue.log" 2>&1
sha256sum "$OUT" | tee "$WORK/$(basename "$OUT").sha256"
log "ISO built: $(du -h "$OUT" | cut -f1)  finished $(date -u +%FT%TZ)"

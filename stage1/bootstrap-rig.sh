#!/bin/bash
# OnionHost Stage 1 rig — bootstrap + preflight
# Target: fresh Ubuntu 24.04 LTS VM, GCP n2-standard-4, us-west3,
# nested virtualisation enabled (see ../STAGE1-RIG-SETUP.md).
#
# Usage:
#   ./bootstrap-rig.sh              preflight only (safe anywhere, no installs)
#   ./bootstrap-rig.sh --install    preflight, then apt-install the rig toolset
#
# Preflight NEVER installs anything and NEVER fails hard: it prints one
# PASS / FAIL / MISSING line per capability the deferred Stage 0 gates need,
# so a bad rig is diagnosed in one screen instead of gate-by-gate.
# Every line is also appended to logs/preflight-<timestamp>.log next to
# this script.
set -u

HERE="$(cd "$(dirname "$0")" && pwd)"
LOGDIR="$HERE/logs"
mkdir -p "$LOGDIR"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
LOG="$LOGDIR/preflight-$STAMP.log"

say() { echo "$*" | tee -a "$LOG"; }
check_bin() {
  # $1 = binary, $2 = why it matters
  if command -v "$1" >/dev/null 2>&1; then
    say "PASS    bin:$1 present ($2)"
  else
    say "MISSING bin:$1 absent ($2)"
  fi
}

say "=== OnionHost Stage 1 rig preflight — $STAMP (UTC) ==="
say "host: $(hostname) · kernel: $(uname -r) · os: $(. /etc/os-release 2>/dev/null; echo "${PRETTY_NAME:-unknown}")"

# --- Gate R capability: device-mapper -------------------------------------
if [ -e /dev/mapper/control ] || [ -d /dev/mapper ]; then
  if dmsetup version >/dev/null 2>&1; then
    say "PASS    device-mapper: dmsetup works (Gate R can run for real)"
  else
    say "FAIL    device-mapper: /dev/mapper exists but dmsetup does not run"
  fi
else
  say "FAIL    device-mapper: no /dev/mapper (Gate R would be environment-blocked, as in Stage 0)"
fi
check_bin cryptsetup "Gate R LUKS2 format/open/addkey"

# --- Nested virtualisation --------------------------------------------------
if [ -e /dev/kvm ]; then
  if [ -r /dev/kvm ] && [ -w /dev/kvm ]; then
    say "PASS    /dev/kvm present and accessible (ISO install tests possible)"
  else
    say "FAIL    /dev/kvm present but not accessible by this user (check kvm group / VM config)"
  fi
else
  say "FAIL    /dev/kvm absent (nested virtualisation not enabled on this VM)"
fi
if grep -qm1 -E 'vmx|svm' /proc/cpuinfo 2>/dev/null; then
  say "PASS    CPU virtualisation flags visible in /proc/cpuinfo"
else
  say "FAIL    no vmx/svm flag in /proc/cpuinfo"
fi
check_bin qemu-system-x86_64 "KVM/QEMU guest for ISO tests"

# --- Engine shoot-out capability -------------------------------------------
check_bin podman "Gate 1 rootful-vs-rootless comparison (A5 data clause)"
check_bin runsc "gVisor runtime — MUST be the official binary, not Ubuntu's stale 2023 package"
if command -v runsc >/dev/null 2>&1; then
  say "INFO    runsc version: $(runsc --version 2>/dev/null | head -1)"
  say "INFO    PoC used official release-20251006.0 (sha512-verified). If this says 0.0~20230807, replace it before trusting any gate result."
fi

# --- Resource ceilings: cgroup delegation -----------------------------------
if [ -w /sys/fs/cgroup/cgroup.subtree_control ] || [ "$(id -u)" = "0" ]; then
  say "PASS    cgroup2 subtree_control reachable (fork-bomb / memory ceiling tests can be honest)"
else
  say "FAIL    /sys/fs/cgroup not writable (ceilings would be environment-limited, as in Stage 0)"
fi

# --- Tor / nftables -----------------------------------------------------------
check_bin tor "Gate 1 A-in-gVisor egress + Gate 5 PoW calibration"
if command -v tor >/dev/null 2>&1; then
  say "INFO    tor modules: $(tor --list-modules 2>/dev/null | tr '\n' ' ')"
fi
check_bin nft "Gate 2b back-stop against a live drifted B; Gate 3 production table"
check_bin curl "over-Tor fetch checks"

# --- Headroom -----------------------------------------------------------------
say "INFO    cpu cores: $(nproc 2>/dev/null || echo '?') · mem: $(free -h 2>/dev/null | awk '/^Mem:/{print $2}') · disk free on /: $(df -h / 2>/dev/null | awk 'NR==2{print $4}')"

say "=== preflight done — log: $LOG ==="

if [ "${1:-}" != "--install" ]; then
  say "Preflight only. Re-run with --install to apt-install the toolset."
  exit 0
fi

# --- Install path (only on explicit --install) --------------------------------
if [ "$(id -u)" != "0" ]; then
  say "ERROR   --install needs root (sudo). Nothing installed."
  exit 1
fi
say "=== installing rig toolset via apt ==="
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
# NOTE: runsc is deliberately NOT in this list — Ubuntu's packaged runsc is a
# stale 2023 build (see ../poc/POC-RESULTS.md baseline). Install the official
# gVisor binary separately and sha512-verify it, as Stage 0 did.
apt-get install -y \
  qemu-system-x86 qemu-utils ovmf \
  podman cryptsetup nftables tor curl jq \
  mmdebstrap uidmap slirp4netns fuse-overlayfs
say "=== install done. Reminder: fetch the OFFICIAL runsc binary (not the apt package) and verify its sha512 before running gates. ==="
say "Next: ./run-deferred-gates.sh   (Gate R first)"

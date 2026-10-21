#!/bin/bash
# OnionHost Stage 1 — deferred-gates runner
# Runs the Stage 0 items that were ENVIRONMENT-DEFERRED in Muse's sandbox,
# in the agreed order, Gate R first (it decides real wizard wording).
# Source of the deferred list: ../poc/POC-RESULTS.md ("Still open for Stage 1").
#
# Usage:  ./run-deferred-gates.sh
# Output: one log per gate under logs/, plus a summary at the end.
# Honesty rule (Stage 0 lesson): verdicts come from the on-disk logs and
# direct measurement only — never from an interim summary. A gate whose
# capability is missing reports DEFERRED, not FAIL and never PASS.
set -u

HERE="$(cd "$(dirname "$0")" && pwd)"
POC="$(cd "$HERE/../poc" && pwd)"
LOGDIR="$HERE/logs"
mkdir -p "$LOGDIR"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"

declare -a RESULTS
note() { RESULTS+=("$1"); echo "$1"; }

# ---------------------------------------------------------------- Gate R ----
# Capability probe first: without a working device-mapper this is the same
# environment block as Stage 0, and the gate must say so.
GATER_LOG="$LOGDIR/gateR-$STAMP.log"
if command -v cryptsetup >/dev/null 2>&1 && dmsetup version >/dev/null 2>&1; then
  echo "Gate R running — full log: $GATER_LOG"
  {
    echo "### Gate R (Stage 1 rig run) — $STAMP"
    bash "$HERE/gateR-rig.sh"
  } >"$GATER_LOG" 2>&1
  if grep -q "SHOWKEYS_VERDICT" "$GATER_LOG"; then
    note "Gate R: RAN — verdict line: $(grep 'SHOWKEYS_VERDICT' "$GATER_LOG" | tail -1) (full log: $GATER_LOG)"
  else
    note "Gate R: RAN but produced no verdict line — read $GATER_LOG before claiming anything"
  fi
else
  note "Gate R: DEFERRED — cryptsetup/dmsetup not working on this host (same environment block as Stage 0)"
fi

# ------------------------------------------------- Capability roll-call -----
# The remaining deferred items need a live stack on the rig; this runner
# records whether each is even exercisable here, so the session plan is
# honest before anyone spends trial-clock time.
ROLL="$LOGDIR/capability-$STAMP.log"
{
  echo "### Deferred-item capability roll-call — $STAMP"
  echo "A-in-gVisor egress:      needs runsc + tor + outbound TCP — runsc: $(command -v runsc || echo MISSING), tor: $(command -v tor || echo MISSING)"
  echo "Podman rootful/rootless: needs podman + a pullable/local image — podman: $(command -v podman || echo MISSING)"
  echo "Resource ceilings:       needs writable cgroup2 subtree_control — writable: $([ -w /sys/fs/cgroup/cgroup.subtree_control ] && echo yes || echo no)"
  echo "Gate 2b live back-stop:  needs nft + a drifted B with real egress — nft: $(command -v nft || echo MISSING)"
  echo "Gate 3 production table: needs nft with conntrack (ct state) — test on rig: nft add rule in a scratch netns"
  echo "Gate 5 PoW calibration:  needs A running in gVisor with real egress + a second client tor (see ../poc/scripts/gate5-load.sh)"
  echo "Golden configs carried over from Stage 0: $POC/configs/ (torrc.golden, runsc.golden — runsc.golden REQUIRES --host-uds=create)"
} | tee "$ROLL"
note "Capability roll-call written: $ROLL — work the remaining gates in a live session in this order: A-egress, engine shoot-out, ceilings, 2b live, Gate 3 production, Gate 5."

echo
echo "=== SUMMARY ==="
printf '%s\n' "${RESULTS[@]}"
echo "Reminder: when the session ends, STOP the VM (do not delete it) — stopped ≈ disk cost only; running ≈ \$0.19/hr against the trial credit."

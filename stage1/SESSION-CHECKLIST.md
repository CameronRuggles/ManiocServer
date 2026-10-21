# Stage 1 — Session Checklist (use when the rig VM first exists)

Prepared 2026-10-11 while the build was paused at the Google sign-in, so the
first real session spends its time on gates, not on setup archaeology.
Full context: `../STAGE1-RIG-SETUP.md` · Stage 0 evidence: `../poc/POC-RESULTS.md`.

## Before the session

- [ ] Cameron is signed into the Cloud Console in Muse's browser
      (password + verification-code route — passkey does not work in the
      remote browser; that failure already happened once, 2026-10-11).
- [ ] Do NOT click "Upgrade" in the console — it ends trial status and
      starts real billing. Nothing on this rig needs a paid account.
- [ ] Trial clock: started Sun 2026-10-11 → credit expires **2027-01-09**.

## VM creation (Muse's job, per the setup sheet)

- [ ] Region **us-west3 (Salt Lake City)**, machine **n2-standard-4**
      (4 vCPU / 16 GB), nested virtualisation **enabled**, Ubuntu 24.04 LTS,
      100 GB SSD.
- [ ] Add Muse's SSH key; snapshot the blank VM before any test so a
      failed install reverts in ~1 minute.
- [ ] Install KVM/QEMU + password-gated noVNC console for Cameron's phone.

## First hour on the rig (in this order)

1. [ ] Copy this `stage1/` folder to the VM; run `./bootstrap-rig.sh`
       (preflight only). Every capability the deferred gates need should
       read PASS. If device-mapper or /dev/kvm reads FAIL, fix the VM
       config first — do not run gates into another environment deferral.
2. [ ] `./bootstrap-rig.sh --install`, then install the **official** runsc
       binary (sha512-verified). Ubuntu's packaged runsc is a stale 2023
       build — Stage 0 baseline note; do not use it.
3. [ ] `./run-deferred-gates.sh` — Gate R runs first and logs its verdict
       lines (`SHOWKEYS_VERDICT`, `ADDKEY_VIA_VOLUME_KEY`). That verdict
       decides the installer wizard's re-key wording (A3 fallback stands
       until then).
4. [ ] Remaining deferred items, live-session order from the runner's
       capability roll-call: A-in-gVisor egress → Podman rootful-vs-rootless
       (A5 data clause) → resource ceilings → Gate 2b back-stop against a
       live drifted B → Gate 3 production table (conntrack) → Gate 5 PoW
       calibration. Golden configs: `../poc/configs/` — `runsc.golden`
       **requires `--host-uds=create`** (silent failure without it).
5. [ ] Only after the above: first ISO build + Calamares install tests.

## End of EVERY session

- [ ] **Stop the VM** (not delete). Running ≈ $0.19/hr against the $300
      credit (~65 days to burn it all); stopped ≈ disk cost only,
      a few dollars/month.
- [ ] Export anything worth keeping off the rig before day 90 — trial
      resources stop when the trial ends; the rig is throwaway by design.
- [ ] Record gate verdicts in `../poc/POC-RESULTS.md` style: from the
      on-disk logs, not from interim summaries.

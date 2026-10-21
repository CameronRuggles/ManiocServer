# Stage 1 Rig — Setup Sheet (prepared 2026-10-11, execute when Muse says "now")

Purpose: a cloud VM with REAL virtualisation (nested KVM) + a browser console,
so installer/ISO work and the sandbox-deferred tests (Gate R, Tor-in-gVisor
egress, rootful-vs-rootless Podman, resource ceilings) can run honestly.
Trigger: Stage 0 tranche 2 results are in and Stage 1 is the next step.

## Cameron's part (~10 minutes, only Cameron can do this — his identity + card)

1. Go to **cloud.google.com** → **Start free** (or "Get started for free").
2. Sign in with a Google account (any existing one is fine).
3. Activate the **Free Trial**: $300 credit, 90 days. It asks for a card for
   identity verification — Google states it does NOT auto-charge when the
   trial ends; the account just pauses unless you manually upgrade to paid.
4. Create a project (name it anything, e.g. `onion-rig` — the project name
   is not the product name and can be deleted later).
5. **Stop there and tell Muse "trial is live."** Everything after this
   point is Muse's job.

⚠️ Clock discipline: the 90 days start at step 3. Do NOT do step 3 early
"to get it out of the way" — that's why this sheet waits for the signal.

## Muse's part (after the trial is live)

- **Prepared package: `stage1/`** (built 2026-10-11 while the build was
  paused at the Google sign-in) — `SESSION-CHECKLIST.md` is the session
  run order; `bootstrap-rig.sh` is a no-install preflight (one PASS/FAIL
  line per capability the deferred gates need) with an `--install` mode
  for the toolset; `run-deferred-gates.sh` runs Gate R first via
  `gateR-rig.sh` (the Stage 0 script extended with the dmsetup verdict
  parsing and cleanup Stage 0 couldn't run) and writes a capability
  roll-call for the rest. Both scripts were syntax-checked and dry-run
  in Muse's sandbox on 2026-10-11: they correctly reported that
  sandbox's own blocks (no /dev/mapper, no /dev/kvm, stale packaged
  runsc) instead of faking results.
- Create the VM: region **us-west3 (Salt Lake City)**, machine
  **n2-standard-4** (4 vCPU / 16 GB), **nested virtualisation enabled**,
  Ubuntu 24.04 LTS host, 100 GB SSD.
- Install KVM/QEMU + a password-gated noVNC console so Cameron can watch
  and drive installs in his phone browser; snapshot before each test so a
  failed install reverts to a blank machine in ~1 minute.
- Re-run the deferred Stage 0 items there: Gate R (LUKS keyring/re-key),
  Tor-in-gVisor real egress, rootful-vs-rootless Podman (the A5 data
  clause), fork-bomb/memory ceilings, Gate 5 PoW calibration.
- Then: first ISO build + Calamares install tests.

## Cost discipline

- The VM is roughly **$0.19/hour while running**. Running it 24/7 would
  eat the $300 credit in ~65 days and defeat the purpose.
- Rule: **stop the VM whenever a session ends** (stopped = only the disk
  costs, a few dollars/month). Muse starts/stops it per work session and
  reports the state; it is never left running "just in case."
- Trial content is throwaway test material only — a cloud trial proves
  mechanics and experience, never home-location secrecy.

## Verified 2026-10-11 (against Google's own Free Program docs)

- Trial terms confirmed: $300 Welcome credit, 90 days, no billing during
  the trial. Source: docs.cloud.google.com/free/docs/free-cloud-features.
- If started Sun 2026-10-11, the credit expires **2027-01-09** (Mon
  2026-10-12 start → 2027-01-10). Plenty for Stage 1 + first ISO tests.
- **Do NOT click "Upgrade" in the console.** Google pushes upgrading
  during the trial; upgrading ends the trial status and starts real
  billing for anything not covered by the remaining credit/Free Tier.
  Nothing on this rig needs a paid account.
- If the trial ends or the credit runs out without upgrading, the
  billing account closes and all trial resources stop (with a grace
  window to recover them by upgrading). Fine here — the rig is
  throwaway by design — but export anything worth keeping before day 90.
- Eligibility caveat: the trial is for people who have never been a
  paying Google Cloud / Google Maps Platform / Firebase customer and
  have not used the trial before. If signup refuses on eligibility,
  that's the likely reason — tell Muse and we pick another host.
- Nested virtualisation confirmed supported on the N2 series, and
  us-west3 (Salt Lake City) is a listed N2 region — the machine/region
  choice in this sheet stands.

## As built (2026-10-11)
- Project: **onion-rig** (free-trial billing, never upgraded). VM **onion-rig-1**, **us-west3-a**, n2-standard-4, Ubuntu 24.04, 100 GB pd-ssd, nested virtualisation ENABLED (applied via stop → full-instance update → start).
- External IP **<rig-external-ip>** (ephemeral), internal <rig-internal-ip>, tag `onion-rig`.
- SSH: `ssh -i ~/.ssh/id_ed25519 -o ProxyCommand=none <ssh-user>@<rig-external-ip>` (user `<ssh-user>`, <sudo-posture placeholder — sudo note removed 2026-10-20 — Repo Review 2>). Two gotchas solved: (1) Muse's sandbox must bypass its proxy (`ProxyCommand=none`) — the proxied route times out; (2) metadata SSH keys need `enable-oslogin=FALSE` on the instance and the ssh-keys value stored verbatim (the console initially mangled it with a `hatch:` prefix).
- Verified from inside: /dev/kvm present, /dev/mapper present, vmx flags on — the rig can run everything the sandbox couldn't.
- Incidents during creation (all resolved): API enable failed once (retry OK); number-match verification 76 expired, 64 approved; boot image briefly flipped to Debian in the wizard, caught and reset to Ubuntu before creation.

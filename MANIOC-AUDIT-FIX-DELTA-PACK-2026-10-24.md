# Manioc Server — audit fix batch delta pack (2026-10-24)

For the external auditor's delta re-verification (fix brief
§7.4). Full evidence narrative: the batch report in this same
diff, `MANIOC-AUDIT-FIX-BATCH-REPORT-2026-10-24.md`.

## Pin

- **Branch:** `audit-fix-batch-2026-10-24` (local, unpushed —
  the push is Cameron's step and has not happened; clone the
  pinned tree from this branch. This pack is handed over with
  `AUDIT-FIX-HANDOFF-CORRECTION-2026-10-25.md`, whose
  2026-10-28 addendum records the exact branch tip).
- **Base:** `1d0d86c` (the audited commit).
- **Code head:** `06596fc46226cfd35ccb62bf51d25caf7f2692b0`
  (the last commit that changes code; this pack's own re-pin
  commits sit on top of it and change no code, so the tree the
  auditor clones at the branch tip carries exactly the code
  diff below).
- **Diff range:** `1d0d86c..06596fc`.
- **Commits:** `3accd51` T8 · `6265f64` T1 · `f637a03` T3 ·
  `e09f019` report/closing · `a833625` T3 rig amendment ·
  `bd1a4c7` / `20e735c` / `5df7a55` report addenda (rig
  verdicts) · `b3524b2` / `ea44525` / `a22f1f8` / `06596fc`
  publication-guard hygiene, 2026-10-28 (rig address and rig
  home path scrubbed from the batch report; the Fork A label
  below reworded; `write_status` in `onionhost-update`
  restructured to build its status record field by field —
  same keys, same values, same order, behavior-neutral).
- **Diffstat (through the code head):** 8 files, +923/−45 —
  `wizard.py`, `onionhost-app-provision`,
  `onionhost-generate-configs`, `onionhost-recipe`,
  `onionhost-update`, the T3 test
  (`poc/scripts/t3-reboot-state-test.py`), the batch report,
  and this pack. Nothing else in the tree was touched.
- **Status corrections:** the correction memo named above,
  with its 2026-10-28 addendum, supersedes the B0, regression
  and rig-checklist status text in the sections below; the
  pin in this section is the current one.

## What the pack contains, against the brief's checklist

- **B0 kept-back list:** NOT CAPTURED. The rig was unreachable
  from the executing session (SSH denied at the egress proxy,
  five attempts, evidence in the report). No baseline from a
  booted audited install exists for this batch; B0 must run
  before the batch is treated as fully gated.
- **Regression rows R-27/R-31:** NOT RUN (rig). Outstanding
  with B0.
- **T1 (H2) — threat-model line:** kernel security updates are
  no longer held back by apt's new-package rule, and the
  install phase can no longer be killed mid-dpkg by the
  updater's own timeout; the download phase keeps its timeout
  because a killed download cannot wedge anything. T2's
  surface deliberately untouched.
- **T3 (H2/M3) — threat-model line:** the owner can now see
  that a restart is owed and how long the updater's success
  record has stood; a silently failing updater can no longer
  present a stale result as fresh. Fields implemented,
  escalation thresholds NOT (owner Q4 parked).
- **T8 (H4) — threat-model line:** host root no longer follows
  app-planted symlinks anywhere in the publish/apply path:
  appdata is host-root owned at its root, and every
  ownership/mode/ACL assertion in `onionhost-app-provision`,
  the `onionhost-recipe` apply path and
  `onionhost-generate-configs`' tor state handling runs on
  O_NOFOLLOW descriptors and refuses non-directories, failing
  the publish/apply closed. Local canary evidence: the pre-fix
  code chowns the canary through the planted symlink (positive
  control), the fixed code refuses and leaves it untouched
  (harness 16/16, `/tmp/t8/harness.py` at execution time;
  verdicts in the report).
- **T8 migration note:** on a pre-fix box, appdata is owned by
  the app's own host id; the first publish under the fixed
  code re-roots it to host root (0:0, 0755), after which the
  app's write access runs solely through the granted owner
  ACL. Verified in the local harness (migration + ACL grant
  asserted); the rig-booted confirmation is outstanding
  with B0.
- **Fork rulings:** Fork A (the F2 image channel) and Fork B
  (owner root) were NOT ruled on for this batch; T5 and T7
  are therefore absent from the diff, as is T18 (maintainer
  hardware step — Cameron's). The brief's delta gate applies
  to this executed scope; the deferred tasks each need their
  own delta when they land.

## Outstanding rig checklist (execute on manioc-proof)

1. B0: kept-back `apt-get -s upgrade` list; `podman images` +
   one no-op re-run of the image-import step; install-user
   `id` and `sudo -l`; one clean no-app publish.
2. R1: from inside the app container, attempt the H4 symlink
   plants against appdata; record what gofer permits (decides
   whether T8's host-side plant is the only plant route).
3. T1: with a kernel ABI update pending, one updater run
   installs it (`dpkg -l 'linux-image-*'` before/after).
4. T3: with a kernel update pending reboot, status.json flags
   it and the Dashboard card + check age render.
5. T8: host-side symlink canary → publish fails closed, canary
   untouched; first-publish migration on a pre-fix tree.
6. R2: rig `$WORK` stamps + image-tarball hashes vs. the
   published ISO (snapshot `20261023T142942Z`).
7. Regression rows R-27 and R-31.

**Nothing in this pack is closed until you re-verify it** —
that rule is the batch's own.

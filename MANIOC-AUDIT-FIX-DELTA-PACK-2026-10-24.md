# Manioc Server — audit fix batch delta pack (2026-10-24)

For the external auditor's delta re-verification (fix brief
§7.4). Full evidence narrative: the batch report in this same
diff, `MANIOC-AUDIT-FIX-BATCH-REPORT-2026-10-24.md`.

## Pin

- **Branch:** `audit-fix-batch-2026-10-24` (local, unpushed —
  delivery form per the batch's commission; clone the pinned
  tree from this branch).
- **Base:** `1d0d86c` (the audited commit).
- **Head:** `e09f0198f07dc7bb4ed01e410df22e683c92caf4`.
- **Diff range:** `1d0d86c..e09f019`.
- **Commits:** `3accd51` T8 · `6265f64` T1 · `f637a03` T3 ·
  `e09f019` report/closing.
- **Diffstat:** 6 files, +562/−43 — `wizard.py`,
  `onionhost-app-provision`, `onionhost-generate-configs`,
  `onionhost-recipe`, `onionhost-update`, and the batch report.
  Nothing else in the tree was touched.

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
- **Fork rulings:** Fork A (image delivery shape) and Fork B
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

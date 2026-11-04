# Manioc Server — images-channel fix batch (full-tree audit Findings 1 + 2), 2026-11-03

Source brief: the fresh full-tree audit of main `ab0ad1b`
(2026-11-03), Findings 1 and 2, both Medium, both in the
container-images channel. This batch answers those two findings
only. Finding 3 (Low) is not in this batch's brief. Nothing here
is verified closed: closure is the auditor's re-verification,
per the standing rule.

## Pins

| | |
|---|---|
| Branch | `images-channel-fix-2026-11-03` |
| Base | `ab0ad1b6cd2ff395c5903a81890e4687dc7b0d8c` (main) |
| Code head, Finding 2 | `103ca06` |
| Code head, Finding 1 | `0b88a7a` |
| Tip | this report's commit |

Diff: `build/build-onionhost-images-deb.sh` (+ the new
`build/images-build-counter`), `onionhost-import-images`,
`onionhost-update`, and the `poc/images-delivery` suite
(stub failure injection, cases (g)–(i), two sibling harnesses).

## Finding 1 — the version is ordered now, not hashed

**Design chosen: the auditor's direction (ii).** The package
version is now `1:VERSION+img.<counter>.<hash>`:

- **The counter is the order.** `build/images-build-counter`
  is a tracked file holding one integer (starts at 1); the
  release bumps it in the same commit that cuts an images
  release — the same discipline as the platform VERSION itself,
  and the bump is a reviewable diff. It is never reused and
  never decreased. dpkg therefore orders two builds of a base
  version by build order, and `repo_best_version`'s dpkg-max
  is the newest set again. `IMAGES_BUILD_COUNTER` overrides the
  file for verification builds and tests; a release build reads
  the file, and a missing or non-integer counter fails the
  build loudly rather than minting an unordered version.
- **The hash is demoted, not removed.** It stays as the final
  component — still the content identity (it is the same value
  the IMAGES-VERSION manifest carries as `img-<hash>`), reached
  by dpkg only as a tie-break between equal counters, which
  for identical content is no decision at all. The rebuild
  case the script's header designs for — same base, new
  content — is ordered by the bumped counter and works.
- **The epoch is the transition.** `1:` sorts every counter
  version above every pre-scheme version (`VERSION+img.<hash>`,
  epoch 0). Without it, the first counter release would compare
  against an installed hash-mark digit-run by digit-run and be
  refused as a downgrade on roughly half the installed base —
  the fix would reproduce the finding's first consequence on
  its own rollout. With it, the transition is unconditional,
  and a replayed pre-scheme package is refused under any
  counter mark.

Direction (i) — judging the channel by manifest identity
against the import record — was not taken: the import step
already judges by identity, but the anti-rollback refusal has
to happen *before* install, where the only identity a
repository offers is the package version; an identity history
deep enough to order sets would be a new state machine in the
updater for a problem the version string can simply stop
creating. **The updater is not modified for this finding at
all**, so the platform package's high-water/floor behaviour
cannot have moved — the gates below include the auditor's own
updater harnesses as the evidence.

Reproducibility: the version is a pure function of VERSION,
the counter and the content (no wall clock; a
`SOURCE_DATE_EPOCH`-style component was rejected for exactly
that reason, and because an image-only rebuild without a
platform commit would not advance it). The harness's (v6)
rebuilds identical content at the same counter and gets the
identical version back.

## Finding 2 — importer atomicity + updater judges by record and health

**Design chosen: the auditor's (a) and (b) together** — (a)
alone leaves the updater claiming "still serves" without
looking; (b) alone would have the updater rolling back a
record whose tags the importer had already restored (the
record rewrite in `--rollback` is only correct when the
record advanced).

Importer (`onionhost-import-images`):

- On the change path, any failure after the rollback tags are
  taken — an import dying midway, the restart failing —
  restores `:latest` from `:rollback` and restarts the
  recorded set before exiting non-zero. Contract, now stated
  in the tool's header: on any non-zero exit of the change
  path, the record and the `:latest` tags name the same set.
- An in-progress marker (`images-import-in-progress`, tmp +
  rename) is written after verification, just before the
  first import, and removed when the record is written (and
  on the soft-failure exits, and by `--rollback`). A standing
  marker at entry means a hard kill: before tagging anything,
  the run restores the recorded set from the rollback tags —
  the one move that makes the next `tag_rollbacks` safe. A
  marker naming the recorded version is litter from a run
  killed on its way out after recording; it is removed, not
  restored.

Updater (`onionhost-update`, images phase only):

- An importer non-zero is now read against the record. If the
  record did not advance, the branch health-checks: healthy →
  `update-failed` (exit 4) with a log line that says the check
  *confirmed* the recorded set serves; unhealthy → restart the
  recorded set (`_restart_recorded_set`, the platform
  recovery's shape) and re-check — recovered → exit 4;
  still unhealthy → fail closed (gateway stopped first,
  marker written, exit 5). If the record DID advance despite
  the non-zero exit, the run falls through to the existing
  health judgement exactly like a reported success.
- The sentence "the importer refused or failed - the previous
  image set still serves" no longer exists. Every
  `update-failed` status this branch emits ("running the
  previous version") is now preceded by a health confirmation
  or a successful restart of that set in the same run.

**Interleavings checked** (each driven, see Gates):

- I1 verification refusal (hash mismatch): exit 2 before any
  import; record, tags and the running set untouched — the
  pre-existing case (d), re-run green.
- I2 an import failing midway (2nd of 3 tarballs): the partial
  import is undone in the tags; record unchanged; case (h).
- I3 the restart failing after a full import (the auditor's
  reproducer): `:latest` restored, record unchanged, and the
  next run — successful or not — cannot destroy the rollback
  copy, because `tag_rollbacks` now re-tags the set the record
  names; case (g) plus a re-run of the auditor's reproducer.
- I4 importer succeeds, health fails: the pre-existing
  `--rollback` path, unchanged — its record rewrite is correct
  precisely because the record advanced; suite case (e) and
  the platform suites re-run green.
- I5 the run after any failure above: the change is retried
  from a consistent state (recorded set tagged and serving);
  rollback depth stays 1; case (g)'s retry leg.
- I6 a change run SIGKILLed mid-import: the marker drives the
  next run's restore-before-tagging; the rollback copy after
  recovery is the pure old set, not the half-imported mix;
  case (i).
- Updater side, the same failure with the recorded set
  healthy / down-then-restarted / down for good / the record
  advanced anyway: cases (u1)–(u4).

**A trap found while building this** (recorded because it is
the kind that survives review): the first cut guarded
`import_all` with `if !`, which suspends `set -e` through the
function's whole body — a midway import failure stopped
aborting the sequence and the run imported on, reporting
success over a mixed set. Case (h) caught it. The shipped
shape captures status with `set +e` around the call and gives
`import_all` explicit `|| return 1` chains, so its result no
longer depends on `set -e` at all.

## Gates

Positive controls first, all against a pristine `git archive`
of `ab0ad1b`:

- The auditor's Finding 2 reproducer, re-run as delivered:
  run 2 (restart fails) — exit 1, record still v1, `:latest`
  = v2, `:rollback` = v1; run 3 — `:rollback` = v2, the v1
  copy gone. Reproduced exactly.
- New poc cases (g)–(i) against the unmodified importer: the
  pre-existing 45 assertions pass; exactly the 5 defect
  assertions fail (latest not restored; rollback destroyed on
  retry; mixed `:latest`; no marker; rollback = the mix).
- `updater_failure_tests.py` against the base tree: 15 of 20
  assertions fail — no probe is ever consulted, the old
  wording stands, the tags stay stranded on the new set, no
  restart, no fail-closed, and the record-advanced exit is
  misjudged as a failure.
- `version_order_tests.py` against the base tree and its
  pre-scheme build script: 5 of 6 fail — `repo_best_version`
  returns the OLDER set (higher hash), the newer build
  compares `lt` against the older mark (refused), and the
  older set is not refused under the newer mark.

Post-fix, on the branch:

- `poc/images-delivery/run_tests.py` (which now also runs the
  two sibling harnesses): **78 assertions, 0 failed** —
  importer (a)–(i), updater (u1)–(u4), version order (v1)–(v6).
- The auditor's reproducer against the fixed importer: run 2
  leaves record / `:latest` / `:rollback` all at v1; run 3
  identical — the defect outcome no longer occurs.
- `poc/recipe-extract`, `poc/runsc-wrap`: 0 failed.
  `poc/runtime-gate`: 68 assertions, 0 failed.
  `poc/scripts` t1 / t3-debian / t3-reboot / t8: all pass.
  `poc/backup-proof`: ALL 27 CHECKS PASS (portable
  `MANIOC_TREE` run).
- The auditor's 2026-11-02 harnesses against this tree:
  `fuzz_legs.py` — ROWS 46, CRASH 0, WRONG 0, controls 12/12;
  `update_values.py` — 0 CRASH, 9/9 CLEAN, S8-c included.
  The F1 change does not touch the updater, and the F2 change
  does not move any of their rows.
- ci-scan on a pristine archive of the branch tip (this
  report included): **PASS (312 files), zero hits** — run as
  the archive's own `build/ci-scan.sh` against the archive.
  (Invoked from outside the tree, the scanner's path-based
  self-exclusion misses and it flags its own pattern list;
  that artefact is the invocation, not the tree.)

## Disclosures

- ShellCheck is not installed in the build sandbox; the two
  edited shell tools pass `sh -n` / `bash -n`, and every
  behavioural claim above is from the driven suites, not from
  reading.
- `poc/installer-policy` was not re-run: it needs the
  network-fetched recipe archives, and nothing in this batch
  is among its inputs (it never invokes the images build
  script — verified by grep, not assumed).
- Observed, pre-existing, not changed: after a healthy images
  update the images phase writes an `updated` status and the
  run's final write then records `up-to-date`; that layering
  is identical at the base commit. The (u4) case asserts the
  real end-state rather than the transient one.
- The counter starts at 1 with this batch; the first release
  built from the fixed script should carry counter 1 — the
  file in the tree already says so.

# Manioc Server — S8 value-guard batch (2026-11-02)

Source brief: the external auditor's fuzz re-verification of
2026-11-02 (Ask 2), new finding S8. His verdict on the parent
branch stands and is not re-argued: fuzz-fix-batch-2026-10-30 is
MERGEABLE as-is; S8 is a pre-existing Low his sweep found one
level below the batch's own fixes — the S7 pattern at value
level. This batch is that follow-up, stacked on the fuzz tip.
(It replaces the fuzz batch's own BATCH-REPORT.md at this
branch's tip, as each stacked batch's report has; the fuzz
batch's report remains in history at the parent tip.)

## Baseline

- Branch: `s8-value-guard-2026-11-02` off the fuzz branch tip
  `5cf9e1643d04a11497173df09d74548bbfb54b8a` (code head
  `c29feee00252af4fb0fe006760ecef5246e57a71`), in a fresh clone.
  Cameron's checkout was not worked in.
- Code head of this batch: `ec0b37348bbf1684306ff68fb005d30aac99a8fe`
  (this report is the tip commit on top of it).
- Diff vs the fuzz tip: 1 file, +40/−2
  (`onionhost/rootfs-overlay/usr/local/bin/onionhost-update`).

## The defect (auditor S8)

S7's `load_json` guard checks the ROOT type of `highwater.json`
and `floors.json`, but the values inside went to `dpkg_compare`
unchecked, and `dpkg_compare` puts its arguments straight into
subprocess argv. A non-string value (int, list) therefore died
with `TypeError: expected str, bytes or os.PathLike` — five
crash shapes through the real `main()`:

- **S8-a** — highwater value int / list: the mark comparison
  runs every run after fetch, before anything rewrites
  `highwater.json`, so one bad value wedges the platform update
  channel until the file is edited by hand — the S7-b/c
  permanence class.
- **S8-b** — floors value int, on the signed-floor path and on
  the recovery path.
- **S8-c** — the images phase's highwater value int.

Reachability (auditor): root-owned, tool-written state; every
writer now writes validated strings (S7-d), so the trigger is
local corruption or a manual edit. Pre-existing at base
`720aafa` — not a regression of the fuzz batch.

## The fix (one commit, `ec0b373`)

The auditor's suggested shape. A new shared helper
`_pruned_state(data, path)` sits beside `_floor_value`, and the
two dict reads in `main()` run through it:

```python
highwater = _pruned_state(load_json(hw_path, {}), hw_path)
floors = _pruned_state(load_json(fl_path, {}), fl_path)
```

- An entry survives only if its value passes the batch's
  existing `_floor_value` rule (a non-empty string) — the same
  rule the floor readers already enforce, applied here through
  the rule itself rather than a second copy of it, so the sites
  cannot drift apart.
- Every dropped entry is logged through the tool's `log()` with
  its file and key, e.g. `dropping highwater.json entry
  'onionhost-images': value 9 is not a non-empty string`.
- **All three consumers are covered by the two prunes.** The
  platform phase reads the `highwater` dict; the floor paths
  read the `floors` dict; the images phase reads
  `highwater.get(IMAGES_PACKAGE)` from the SAME `highwater`
  dict (there is no second read of the file anywhere in the
  tool — verified by grep over every `load_json` call). One
  prune per file, at the read, serves all three.
- **Seeding logic untouched, and confirmed in code before
  relying on it:** a dropped highwater entry is absent at the
  baseline step, which seeds it from the installed version
  (`if inst and pkg not in highwater`); the images mark seeds
  the same way; a dropped floor seeds from the disk floor
  (`if disk_floor and pkg not in floors`). Factory behaviour —
  a dropped mark cannot move below what is installed.
- **Posture: drop-and-log**, the auditor's primary suggestion.
  His fail-closed alternative (refuse the run on a corrupted
  mark rather than re-seed) is a posture call for the owner; it
  is recorded here as not implemented, not silently decided.

## Gates

Positive control first; the auditor's own harness is the gate
throughout (`harnesses/update_values.py` and
`harnesses/fuzz_legs.py` from his 2026-11-02 evidence zip,
driving the real tools):

- **Positive control (unmodified `c29feee`):** `update_values.py`
  reproduces the auditor's `outputs/s8-values-c29feee.txt`
  verdict rows exactly — 5 CRASH (S8-a ×2, S8-b ×2, S8-c ×1),
  the null row and all three controls CLEAN. (His saved output
  omits the tool's own log lines, which interleave on stdout in
  a live run; the verdict rows are identical.)
- **Post-fix (`ec0b373`):** the same harness reports **0 CRASH**,
  all 9 rows CLEAN. Controls identical to the pre-fix run,
  including the valid-strings row, the refused-downgrade row
  (returned rc=2), the S7-b root-list row, and the S8-a null
  row. The S8-c case now logs its drop, re-seeds the mark from
  the installed 2.0, and the images phase installs 2.0 → 2.1
  under the harness stubs (run completes, rc=0).
- **Fuzz gate stays green:** `fuzz_legs.py` against the new
  head — ROWS 46, CRASH 0, WRONG 0, OTHER 0, controls-OK 12/12;
  verdict rows identical to the auditor's `fuzz-c29feee.txt`.
- **Suites** (this sandbox, invoked as the auditor invoked
  them): recipe-extract 0 assertions failed; images-delivery
  0 assertions failed; runtime-gate `run_sim.py` 68 assertions,
  0 failed — on the fixed tree and, as a control, on an
  unmodified `c29feee` worktree (an earlier run pointed at the
  wrong directory aborted in both trees alike; the rooted
  reruns above are the evidence); backup-proof ALL 27 CHECKS
  PASS.
- **ci-scan** on a pristine `git archive` export of this
  branch's tip (this report included): PASS (297 files — the
  same count as the fuzz tip; this report replaces the parent
  batch's report file in place, it does not add a file).

## Position

The branch stacks on the fuzz tip, so it lands after (or with)
the fuzz branch — which the auditor's merge-order constraint
already requires to reach main no later than the stack that
carries S7-f's other half. Nothing else moves: no seeding, no
`dpkg_compare`, no writer changes. Closure is the auditor's
re-verification against `ec0b373`, per the standing rule.

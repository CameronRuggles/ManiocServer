# Manioc Server — fuzz fix batch extension: auditor seventh-site (S7) fixes, 2026-10-30

Source: external auditor re-verification 2026-10-30 §3
(`MANIOC-AUDITOR-REVERIFICATION-2026-10-30`), seventh-site sweep.
Approved under Cameron's standing direction 2026-10-30 (do everything
code-wise possible without a human). This batch extends
`fuzz-fix-batch-2026-10-30`; it does not touch the audit-fix branch.

## Baseline

- Clone: fresh clone of `~/workspace/manioc-fuzz-fix-2026-10-30` at
  `~/workspace/manioc-fuzz-s7-2026-10-30/` (the original fuzz-fix
  clone and `~/workspace/onion-host-os` were NOT worked in).
- Branch: `fuzz-fix-batch-2026-10-30`, starting head
  2d23617 (fuzz batch tip; code head 7866162) on base
  720aafac2d9ec75f2eaff677c19f891787a63772 (public main).
- Tree state at start: clean.
- This clone's final head supersedes 2d23617 as the branch's
  canonical local head.

## The S7 sites (auditor's table, §3)

All are the fuzz batch's root-cause pattern (parsers assume
`json.load` returned a dict / version-floor values are strings) at
sites the original F1–F6 batch did not list:

- S7-a: `onionhost-update` `main()` — `prev_status.get` on a
  non-dict `status.json`. Low, but it runs first thing every run,
  before fetch, and nothing rewrites the file: a bad file wedges
  every run permanently. Same placement class as F5.
- S7-b: `main()` — `highwater.json` int/list → TypeError. Same
  placement.
- S7-c: `main()` — `floors.json` list/str → TypeError. Same
  placement.
- S7-d: `deb_floor` returns a floor value read from the signed
  candidate .deb unvalidated → `dpkg_compare` TypeError downstream,
  and `main()` may `save_json` the bad value into `floors.json`
  first (permanent until a fixed package ships). Low–Medium.
- S7-e: `onionhost-recipe` `_validate_manifest_paths` — list-valued
  manifest fields are not type-checked: `"native_files": 5` →
  TypeError at the bare iteration.
- S7-f: `write_status` on the **audit-fix branch** — same shape as
  S7-a (`load_json(status, {})` then `.get`). This batch does NOT
  edit the audit-fix branch: `write_status` there reads through
  this same `load_json` helper, so Task 1's type guard closes
  S7-f on the merged tree whichever batch lands first. That is the
  closure path, recorded here and in the pack addendum.

Fix shape follows the auditor's suggestion: one type guard in
`load_json`; one shared floor-value validation for `deb_floor` /
`disk_floor_for`; per-field type checks in
`_validate_manifest_paths`.

## Positive control (gate proves it can fail) — BEFORE any fix

Auditor's harness `fuzz_delta_harness.py` (from
`auditor-evidence-2026-10-30.zip`), run as
`python3 -I fuzz_delta_harness.py <tree> <reproducers>` with the
reproducers from `~/workspace/manioc-fuzz-2026-10-28/reproducers/`.

1. Against pristine base 720aafa (the clean CodeQL scratch clone,
   HEAD verified 720aafac2d9ec75f2eaff677c19f891787a63772): the run
   reproduces the auditor's `results-fuzz-base-720aafa.txt`
   row-for-row — **28 CRASH rows** (F1–F6 reproducers/probes plus
   S7-a ×2, S7-b ×2, S7-c ×2, S7-d ×2, S7-e ×1), all 11 controls
   CLEAN, S7-e string case CLEAN (clean ValueError), S7-f "n/a" on
   this tree. The only diffs vs the auditor's file are Python
   stdlib frame line numbers (`<frozen codecs>:322` vs his `:325`,
   `subprocess.py:1885` vs `:1922`) — a Python version difference,
   not a behaviour difference.
2. Against the pre-S7 fuzz head 2d23617 (this clone, before any
   S7 commit): all F rows CLEAN; S7-a ×2, S7-b ×2, S7-c ×2,
   S7-d ×2 and S7-e (int) still CRASH; S7-f n/a. Exactly the gap
   this batch exists to close.

## Task 1 — `load_json` type guard (onionhost-update)

- Commit: **9de9b3f** — "Fuzz fix batch S7 task 1: load_json type
  guard in onionhost-update (S7-a/b/c, F4 root cause, S7-f closure
  path)".
- Change: `load_json(path, default)` now returns `default` when
  the parsed result is not `type(default)` — the auditor's
  suggested one-helper shape. Every call site in the tool passes
  a dict default (`_installed_recipe`, `_recipe_app_name`, and
  `main()`'s highwater/floors/prev_status reads), so the guard is
  uniform with no call-site changes.
- Consistency check: the fuzz batch's explicit `isinstance`
  checks in `_installed_recipe` / `_recipe_app_name` are now
  redundant but harmless — they state each function's own
  contract at its own site and were left in place deliberately;
  behaviour is identical with or without them.
- S7-f closure path: S7-f lives in the audit-fix branch's
  `write_status`, which this batch does not edit. That function
  reads `status.json` via `load_json(..., {})`; on the merged
  tree it receives `{}` for a non-dict file, so its `.get` calls
  are safe. Whichever batch lands first, the merged tree carries
  this guard. (On this tree the harness's S7-f row reads "n/a —
  no T3 write_status", as on base.)
- Harness after this commit: S7-a ×2, S7-b ×2, S7-c ×2 all CLEAN
  ("reached first external command (site passed)"); F4 rows and
  all controls unchanged CLEAN; only S7-d ×2 and S7-e (int) still
  CRASH — Tasks 2 and 3.

## Task 2 — shared floor-value validation (onionhost-update)

- Commit: **5392b7c** — "Fuzz fix batch S7 task 2: shared
  floor-value validation in deb_floor/disk_floor_for (S7-d)".
- Change: new `_floor_value(data, pkg)` helper — returns the
  floor only when the document is a dict, the key is present,
  and the value is a **non-empty str** (the auditor's suggested
  shared shape; it also tightens the F5 fix, which checked `str`
  but not empty). `deb_floor` now returns the helper's result
  instead of `data[pkg]` unvalidated (bad value → keep looking /
  no floor, so `main()` can no longer persist it into
  `floors.json`); `disk_floor_for` calls the same helper instead
  of its inline F5 condition.
- Harness after this commit: S7-d ×2 CLEAN (returned None); F5
  rows unchanged CLEAN (int value row still returns None);
  control "valid disk floor -> '1.0'" unchanged. Only S7-e
  still CRASH — Task 3.

## Task 3 — per-field type checks in `_validate_manifest_paths` (onionhost-recipe)

- Commit: **c29feee** — "Fuzz fix batch S7 task 3: per-field
  type checks in _validate_manifest_paths (S7-e)".
- Change (onionhost-recipe only): two helpers called from
  `_validate_manifest_paths` at load time, before any join or
  placement, all rejections via `ValueError` (the recipe tool's
  clean `fail()` path):
  - `_check_manifest_file_entries` for the {src, dst} object
    lists `native_files` and `extra_files`: the field must be a
    list, each entry a dict (the pre-existing native_files entry
    check, generalised), each src/dst through the existing
    relative-path check. `extra_files` entries previously had no
    load-time check at all (their use site does `item["src"]`).
  - `_check_manifest_str_list` for the path lists `data_dirs`,
    `exclude_paths`, `install_files`, `config_carryover`: the
    field must be a list of strings, each entry through the
    relative-path check (these are all paths the applier joins).
- Shipped-manifest safety: all five shipped recipes
  (dokuwiki, gitea, marketplace, smf, wordpress `recipe.json`)
  pass the extended validation — verified by calling
  `_validate_manifest_paths` on each directly. Their values are
  plain relative paths / {src, dst} objects, as the consumers
  assume.
- Harness after this commit: S7-e int CLEAN (ValueError "is not
  a list"), S7-e string CLEAN (same ValueError — stricter than
  base, where a string iterated into a per-character entry
  error; both are the clean path, and a string is not a list of
  file entries under any reading).

## Final gate — on code head c29feee

Auditor's harness, same invocation as the positive control,
against this tree: **all 42 rows CLEAN, 0 CRASH** — F1–F6
reproducers/probes, S7-a ×2, S7-b ×2, S7-c ×2, S7-d ×2, S7-e ×2
all follow the tools' error discipline, S7-f "n/a" on this tree
(closure path via Task 1's guard, above), and all 11 valid-input
controls return exactly what they return on base (valid manifest
dict, floor refusal 1, above-floor None, installed True/record,
'Forum', '1.0', '3.1', the three `_debver_cmp` controls).

Original batch's 33-case runner: the original
`/tmp/check_fuzz.py` no longer exists (/tmp is ephemeral), so it
was reconstructed from BATCH-REPORT.md's enumeration
(`/tmp/check_fuzz_s7.py`, kept out of the repo). Validation of
the reconstruction: on pristine base it reports **33 cases,
23 VIOLATION** — the original's exact positive-control count.
On this head: **33 cases, 0 VIOLATION**, all 8 controls
returning their base values.

Suites, each run separately on the final head:

- `build/ci-scan.sh` — **PASS** (296 files scanned), exit 0.
- `poc/recipe-extract/run_tests.py` — **PASS**, 0 failed.
- `poc/images-delivery/run_tests.py` — **PASS**, 0 failed.
- `poc/backup-proof/proof.py` — **PASS**, "ALL 27 CHECKS PASS".
- `poc/runtime-gate/run_sim.py . all` — **PASS**, 68 assertions,
  0 failed.
- `poc/runtime-gate/test_runtime_dashboard.py <wizard.py>` —
  **PASS**, 0 failed.
- `poc/runsc-wrap/run_tests.py` — **PASS**, 0 failed.
- `python3 -m py_compile` on both edited tools — **OK**.

Did NOT pass — pre-existing fixture absences, verified identical
on pristine base 720aafa in this session (same commands, same
failures before any product code runs; not regressions, not
claimed as passes):

- `poc/recipes-marketplace/unit-test.py` — fixture .deb
  `poc/recipes-marketplace/pkgs/onionhost-recipe-marketplace_
  0.1.0+oh.1_amd64.deb` absent at base and head alike
  (dpkg-deb exit 2 on the missing file). The clean-clone gap the
  test-hardening branch addresses.
- `poc/installer-policy/run_proofs.py` — fixture archive
  `wordpress-7.1.3.zip` not fetched at base and head alike
  (expects `build/fetch-recipe-archives.sh`); its path check
  itself reports OK before the pin check stops the run.

## Final state

- Branch `fuzz-fix-batch-2026-10-30` in THIS clone
  (`~/workspace/manioc-fuzz-s7-2026-10-30`): S7 commits 9de9b3f,
  5392b7c, c29feee (code head) on top of 2d23617, plus this
  report and PACK-ADDENDUM-S7.md in one report commit directly
  above the code head. This clone's head supersedes 2d23617 as
  the branch's canonical local head.
- Local only — NOT pushed, NOT merged. The original fuzz-fix
  clone and `~/workspace/onion-host-os` were not touched.
- S7 diff vs the original fuzz code head 7866162: onionhost-update
  +45/−6 (Tasks 1–2), onionhost-recipe +47/−10 (Task 3).

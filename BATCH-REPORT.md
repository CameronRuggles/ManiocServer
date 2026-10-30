# Manioc Server — parser fuzz fix batch, 2026-10-30

Source findings: `~/workspace/manioc-fuzz-2026-10-28/FUZZ-REPORT-2026-10-28.md`
(fuzz F1–F6 — a numbering series separate from the Oct 25 review's F-numbers).
Approved by Cameron 2026-10-30.

## Baseline

- Clone: fresh clone of `~/workspace/onion-host-os` at
  `~/workspace/manioc-fuzz-fix-2026-10-30/` (the source checkout was NOT
  worked in or touched; its `main` was verified at
  720aafac2d9ec75f2eaff677c19f891787a63772 before cloning).
- Branch: `fuzz-fix-batch-2026-10-30`
- Starting commit: 720aafac2d9ec75f2eaff677c19f891787a63772 (public main)
- Tree state at start: clean (no tracked changes, no untracked files).

## Positive control (gate proves it can fail) — BEFORE any fix

Runner: `/tmp/check_fuzz.py` (loads both tools from this clone, feeds the
six reproducers in `~/workspace/manioc-fuzz-2026-10-28/reproducers/` plus
probe variants and valid controls; classifies escapes of
AttributeError/TypeError/UnicodeDecodeError as VIOLATION).

Result on unmodified 720aafa: **33 cases, 23 VIOLATION — all six findings
reproduce from their minimal reproducers**, all valid controls clean:

- F1: reproducer `42` + list/string/null manifest roots → AttributeError
- F2: reproducer version=5 → TypeError; floor root list/int →
  AttributeError; floor value list/int → TypeError
- F3: reproducer `3` + list/string state roots → AttributeError
- F4: reproducer `3` + list/string state roots, list/int manifest roots →
  AttributeError
- F5: reproducer `7` + list/string/null floor roots → TypeError.
  Note: floor value list/int did NOT crash here pre-fix — they were
  returned unvalidated (a non-string floor propagates to callers); the
  fix validates them anyway, per the batch's one-pattern rule.
- F6: reproducer bad UTF-8 + bad UTF-8 after the version line →
  UnicodeDecodeError

Controls (all clean pre-fix, must stay clean): valid manifest, below-floor
refusal (returns fail() code 1), above-floor OK (None), valid installed
state (True / record dict), valid manifest name ('Forum'), valid disk
floor ('1.0'), valid version file ('3.1').

## Task 1 — onionhost-recipe (F1, F2, F3)

- Commit: **51dea25** — "Fuzz fix batch task 1: validate JSON types in
  onionhost-recipe (fuzz F1-F3)" (1 file, +11/−1)
- Changes (onionhost-recipe only):
  - `_load_manifest`: non-dict root → ValueError (main()'s clean tuple).
  - `_load_state`: non-dict root → {} (its existing default for
    unreadable state).
  - `_check_install_floor`: non-dict floor root → None (its existing
    no-constraint return for an unreadable floor file).
  - `_debver_cmp`: non-string version/floor argument → ValueError.
- Local check: `python3 -m py_compile onionhost-recipe` OK; check runner
  re-run — **F1/F2/F3 all 16 cases CLEAN** (ValueError / clean returns;
  controls unchanged: below-floor refusal still returns 1, above-floor
  None, valid installed state True). F4/F5/F6 still violated at this
  point, as expected before Task 2 (11 violations, all in
  onionhost-update).

## Task 2 — onionhost-update (F4, F5, F6)

- Commit: **7866162** — "Fuzz fix batch task 2: validate JSON types in
  onionhost-update (fuzz F4-F6)" (1 file, +7/−2)
- Changes (onionhost-update only):
  - `_installed_recipe`: non-dict state root → None (its existing
    not-installed return).
  - `_recipe_app_name`: non-dict manifest root → recipe id (its
    existing fallback).
  - `disk_floor_for` (F5, Medium): a candidate is used only when its
    root is a dict AND the floor value is a string; otherwise the
    candidate is skipped, exactly like its existing
    (OSError, ValueError) skip.
  - `_version_field`: also catches UnicodeDecodeError → None. Note:
    a file with a valid version line followed by invalid UTF-8 now
    returns None (file treated as unreadable) instead of crashing;
    previously it crashed, so no working behaviour is lost.
- Local check: `python3 -m py_compile onionhost-update` OK; check
  runner re-run — **all 33 cases CLEAN, 0 VIOLATION** (see final gate).

## Final gate — on final head 7866162

Post-fix reproducer check (same runner as the positive control):
**33 cases, 0 VIOLATION.** Per finding:

- F1 CLEAN — reproducer + list/string/null roots → ValueError (clean
  fail() path); valid manifest still loads.
- F2 CLEAN — reproducer version=5 → ValueError; floor root list/int →
  None (no constraint); floor value list/int → ValueError; controls
  unchanged (below-floor refusal returns 1, above-floor None).
- F3 CLEAN — reproducer + list/string roots → False (not installed);
  valid installed record still True.
- F4 CLEAN — state roots → None; manifest roots → recipe-id fallback;
  valid state/manifest controls unchanged.
- F5 CLEAN — reproducer + list/string/null roots → None (candidate
  skipped); non-string floor values now skipped too (None); valid
  floor still returns '1.0'.
- F6 CLEAN — reproducer + bad UTF-8 after the version line → None;
  valid file still returns '3.1'.

Suites (each run separately on the final head; exit = failed
assertions where the harness uses that convention):

- `build/ci-scan.sh` — **PASS** (295 files scanned), exit 0.
- `poc/recipe-extract/run_tests.py` — **PASS**, 0 assertions failed.
- `poc/images-delivery/run_tests.py` — **PASS**, 0 assertions failed.
- `poc/backup-proof/proof.py` — **PASS**, "ALL 27 CHECKS PASS".
- `poc/runtime-gate/run_sim.py <repo> all` — **PASS**, 68 assertions,
  0 failed.
- `poc/runtime-gate/test_runtime_dashboard.py <wizard.py> <sim dirs>`
  — **PASS**, 0 assertions failed (needs the wizard.py path argument;
  first invocation without it failed on argument parsing, before any
  check ran).
- `poc/runsc-wrap/run_tests.py` — **PASS**, 0 assertions failed.
- `python3 -m py_compile` on both edited tools — **OK**.
- `_debver_cmp` controls: (1.0~rc1, 1.0) → −1, antisymmetric 1,
  equal 0; the Info-only non-ASCII-digit nuance is unchanged, as
  directed (out of scope).

Did NOT run / did not pass (pre-existing fixture absences at base
720aafa, unrelated to this diff — not claimed as passes):

- `poc/recipes-marketplace/unit-test.py` — FAILED before any product
  code ran: its fixture `poc/recipes-marketplace/pkgs/
  onionhost-recipe-marketplace_0.1.0+oh.1_amd64.deb` is absent from
  the tree at base (dpkg-deb: No such file or directory). This is the
  known clean-clone gap the unmerged test-hardening branch addresses.
- `poc/installer-policy/run_proofs.py` — FAILED in its package-build
  step: fixture `wordpress-7.1.3.zip` archive missing (the suite
  expects it fetched via build/fetch-recipe-archives.sh). No product
  code under test was reached.

## Final state

- Branch `fuzz-fix-batch-2026-10-30`, local only — NOT pushed, NOT
  merged. Commits: 51dea25 (task 1), 7866162 (task 2), plus this
  report committed last.
- `~/workspace/onion-host-os` was not touched (read/clone source only).
- The `/usr/share/onionhost` fixture dir created temporarily by the
  disk_floor_for checks was removed after each run.

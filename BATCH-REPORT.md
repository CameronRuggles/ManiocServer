# Manioc Server — F3 carryover no-follow batch (2026-11-03)

Source brief: Finding 3 (Low) of the fresh full-tree audit of main
`ab0ad1b` (2026-11-03). One batch, one tool
(`onionhost-recipe`), plus a new poc test for the previously
unexercised path. Local only; not pushed, not merged. Findings
close only on the auditor's re-verification.

## Pins

| | |
|---|---|
| Branch | `f3-carryover-nofollow-2026-11-03` |
| Base | `ab0ad1b6cd2ff395c5903a81890e4687dc7b0d8c` (main) |
| Code head | `81ff90eb89cff345c5bb2850d125bd4f9cc93a85` |
| Tip | this report's commit (adds only BATCH-REPORT.md) |
| Diff | `onionhost-recipe` + a new `poc/scripts/f3-carryover-test.py`; 450 insertions, 29 deletions |

## The defect (auditor's finding, restated)

T8-B's invariant — host root never follows a symlink while
carrying app data across the trust boundary — was held for final
path components only. Two live-tree carryovers in
`onionhost-recipe` resolved multi-component manifest paths by
path:

- the data-directory carryover in `apply_recipe` did
  `os.path.isdir(live)` + `_copy_tree(live, staged)`; the copy's
  no-follow open guards only the final component, so a planted
  intermediate symlink (`wp-content` in WordPress's
  `wp-content/uploads`) was followed by both the check and the
  open, and the target's matching child landed in staging;
- `_copy_config_carryover` opened `os.path.join(www, name)`
  no-follow — final component only — so a planted intermediate
  `conf` symlink was followed for DokuWiki's `conf/local.php`.

## Positive control (run first, on unmodified ab0ad1b)

A scratch harness (kept in the builder's scratch space, not
shipped) with a fake live tree — `www/wp-content` and `www/conf`
each planted as a symlink to a host directory holding
`uploads/secret.txt` and `local.php`:

- data-dir site, driving the carryover exactly as `apply_recipe`
  composed it at base (`isdir` + `rmtree` + `_copy_tree`): the
  host secret **landed in staging**;
- config site, driving the tree's real `_copy_config_carryover`:
  returned True and staged the **host secret bytes**;
- honest controls (real directories): owner's files carried
  over, no secret present.

Both disclosures reproduce exactly as the audit describes. The
same harness's config section re-run at the fixed head returns
False with nothing staged; the honest control is unchanged.

## The fix

One new helper and one factoring; both carryovers now resolve
the live path the way the rest of T8-B does — by descriptor,
per component.

- **`_live_parent_fd(www, rel)`** opens the directory holding
  `www/rel`, walking each intermediate component with an
  `O_RDONLY|O_DIRECTORY|O_NOFOLLOW` open through the previous
  descriptor (the `_makedirs_owned` / `_native_parent_fd`
  pattern). It reports three outcomes: a parent descriptor, a
  plain missing component, or the first component that exists
  but cannot be resolved no-follow.
- **Data directories:** `apply_recipe`'s loop body is extracted
  unchanged into **`_carry_data_dir(www, dirname, staging)`**,
  which opens the final component no-follow through the walk's
  descriptor and hands it to **`_copy_tree_from_fd`** —
  `_copy_tree`'s body, factored out so `_copy_tree` itself is
  behaviour-identical (it still opens its own source).
- **Config:** `_copy_config_carryover` opens the leaf
  no-follow through the walk's parent descriptor; the rest of
  the function (regular-file check, descriptor copy, mode,
  fsync) is untouched.

Behaviour by case:

| Live path shape | Before | After |
|---|---|---|
| honest multi-component | copied by path | copied from the walk's descriptor — byte-identical staging (gate below) |
| intermediate missing | staging dir created | same, silent |
| intermediate symlink / plain file | **followed; target copied** | carryover refused for that path: WARNING on stderr, nothing copied, staging keeps the archive's copy |
| final component a symlink | data dir: the copy's open raised, aborting the apply; config: refused silently | **unchanged** — the final component is opened exactly as before, through the walk's descriptor |
| single-component names | safe (final-component no-follow) | unchanged — there is no intermediate to walk |

## Judgement calls (flagged for the auditor)

1. **Refusal shape: skip-with-warning per path, not an
   apply-wide abort.** The auditor offered "refuse or skip
   that path". The tool's existing refused carryovers report
   exactly this way — `_copy_config_carryover` returns False
   and the caller proceeds as for a missing config;
   `_copy_tree` prints a WARNING per skipped link and
   continues. `_own_data_dirs`' raise guards the platform's
   own staging tree, a different trust position: the live
   tree is app-shaped by design, and aborting the whole apply
   on any planted intermediate would hand a compromised app a
   standing refusal of every re-publish. The one abort that
   existed — a planted FINAL component raising out of the
   copy — is preserved as-is.
2. **The staged copy is removed after the no-follow open
   succeeds**, not before the copy as the old loop did. The
   difference is observable only inside an apply that aborts
   on the planted final component anyway (staging is a
   throwaway build tree either way); for the refused
   intermediate case it is what lets staging keep the
   archive's copy.
3. **The intermediate refusal prints a WARNING.** The old
   code printed nothing for a refused final-component config
   (and the intermediate case was the bug, not a refusal).
   New visibility, in the file's existing WARNING format; a
   missing component stays silent, as before.

## Gates

- **New poc test** `poc/scripts/f3-carryover-test.py` (the
  previously unexercised path): 25 checks, **ALL PASS** —
  honest multi-component data dir and config, both planted
  intermediates refused loudly with nothing copied and the
  staged archive copy intact, plain-file intermediate, missing
  dir, single-component honest + planted-final (raises, as
  before), config planted-final and missing. Disclosure about
  the control direction: the test's data-dir cases cannot run
  on the base tree (`_carry_data_dir` does not exist there);
  the base disclosure for that site is the scratch-harness
  positive control above, and for the config site the shipped
  function's base behaviour is the disclosure, reproduced by
  the same harness.
- **Honest-case byte-compare**, base vs head (scratch script):
  identical honest WordPress + DokuWiki trees run through the
  base composition and the fixed helpers — the full staging
  maps (names, kinds, bytes, modes) are **identical**, and the
  inner-symlink skip warning fires on both.
- **Suites at the fixed head:** `poc/scripts/t8-rework-test.py`
  ALL PASS (the T8-B demos); `poc/recipe-extract` 0 assertions
  failed; `poc/runtime-gate/run_sim.py . all` 68 assertions,
  0 failed (an earlier invocation with a wrong argument form
  errored in the harness itself — the documented form passes
  on the base tree too, 68/0); `poc/backup-proof` ALL 27
  CHECKS PASS (portable `MANIOC_TREE` run);
  `poc/installer-policy/run_proofs.py` PASS, 0 assertions
  failed, run twice — it is build-from-source: the recipe
  archives were fetched first with
  `build/fetch-recipe-archives.sh`, which pin-verified
  WordPress, DokuWiki and Gitea clean (SMF vendored, as
  documented).
- **ci-scan** is run on a pristine archive of this branch's
  tip, this report included; the result is recorded with the
  ferry delta pack (a report cannot truthfully carry the scan
  of the commit that contains it).

## Not changed

No other tool, no test file, no manifest. `recipes-marketplace`
unit tests remain unrunnable in this sandbox (they need
prebuilt marketplace .debs that are gitignored and absent) —
the same wall the audit recorded; the marketplace is excluded
from shipping.

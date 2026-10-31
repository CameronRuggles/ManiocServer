# Addendum to FUZZ-FIX-DELTA-PACK-2026-10-30 — the S7 extension

For the external auditor. This addendum supersedes the fuzz delta
pack's pins. The pack itself (`Manioc-Audit-Packs-2026-10-30.zip`)
is unchanged and is NOT re-issued: everything in it stands except
the branch head it points at, because the auditor's own
re-verification (2026-10-30, §3) found a seventh site — six
further sites of the fuzz batch's root-cause pattern — and this
extension folds his suggested fixes into the same branch before
his legs 2–3 run.

## New pins

- Branch: `fuzz-fix-batch-2026-10-30` (still local-only; the push
  remains Cameron's tap, and legs 2–3 remain blocked on it,
  exactly as the auditor's §5 states).
- **New code head: `c29feee00252af4fb0fe006760ecef5246e57a71`**
  — run legs 2–3 against THIS head.
- New branch tip: the single report commit directly above the
  code head, adding only `BATCH-REPORT-S7.md` and this addendum
  (`git diff c29feee..HEAD --stat` shows no code files).
- Base unchanged: `720aafac2d9ec75f2eaff677c19f891787a63772`.
- Diff ranges: original batch `720aafa..7866162` (unchanged);
  this extension `7866162..c29feee` — three commits:
  - `9de9b3f` onionhost-update: `load_json` type guard (+19/−1)
  - `5392b7c` onionhost-update: shared floor-value validation
    (+26/−5)
  - `c29feee` onionhost-recipe: `_validate_manifest_paths`
    per-field type checks (+47/−10)

## What changed vs the pack

The pack's F1–F6 fixes are untouched in substance, with two
refinements the auditor's shape implies:

1. **`load_json(path, default)` type guard** (his suggested
   shape, verbatim in effect): a parsed result that is not
   `type(default)` returns the default. This closes the root
   cause *behind* F4 — the fuzz batch's per-call-site
   `isinstance` checks in `_installed_recipe` /
   `_recipe_app_name` remain in place, now redundant but
   harmless — and closes sweep sites **S7-a** (status.json in
   `main()`), **S7-b** (highwater.json) and **S7-c**
   (floors.json), whose placement (first step of every run,
   nothing rewrites the files) matches F5's.
2. **One shared floor-value validation** `_floor_value(data,
   pkg)`: dict root, key present, value a non-empty `str`.
   `deb_floor` now uses it — closing **S7-d** (an unvalidated
   floor value from the signed candidate .deb crashed
   `dpkg_compare` downstream and could be persisted into
   `floors.json` first) — and `disk_floor_for` uses it too,
   which tightens the pack's F5 fix from "str" to "non-empty
   str" with no behaviour change for any valid floor.
3. **`_validate_manifest_paths` per-field type checks** closing
   **S7-e**: the object lists `native_files` / `extra_files`
   must be lists of {src, dst} objects, and the path lists
   `data_dirs` / `exclude_paths` / `install_files` /
   `config_carryover` must be lists of strings, every entry
   through the existing relative-path check, all rejections via
   the recipe tool's clean `ValueError`/`fail()` path. All five
   shipped recipes pass the extended validation.

**S7-f** (the audit-fix branch's `write_status`) is not edited
by this batch and needs no edit there: that function reads
`status.json` through this same `load_json`, so the type guard
closes it on the merged tree whichever batch lands first.

## Evidence carried with this addendum

- `BATCH-REPORT-S7.md` (same commit as this addendum): baseline,
  positive control, per-task harness results, final gate.
- Positive control: the auditor's own `fuzz_delta_harness.py`
  against pristine 720aafa reproduces his
  `results-fuzz-base-720aafa.txt` row-for-row (28 CRASH; only
  Python stdlib frame line numbers differ).
- Final gate on `c29feee`: the same harness reports **all 43
  rows CLEAN, 0 CRASH**, all 11 controls identical to base; the
  original batch's 33-case runner (reconstructed from its
  BATCH-REPORT after the /tmp original expired; validated by
  reproducing its exact 23-violation positive control on base)
  reports 0 violations; ci-scan PASS (296 files);
  recipe-extract, images-delivery, backup-proof (27/27),
  runtime-gate (68/68 + dashboard), runsc-wrap all PASS.
  recipes-marketplace and installer-policy still fail on their
  pre-existing missing fixtures, verified identical on base —
  disclosed, not claimed.

## Ask of the auditor

Run legs 2–3 (your harness, this head) as planned. The S7 rows
are part of the same harness run; per-finding acceptance is the
pack's three legs applied per row: reproduce on base → CLEAN on
`c29feee` with the discipline above → valid-input controls
unchanged. Findings close only on your re-verification, as
before.

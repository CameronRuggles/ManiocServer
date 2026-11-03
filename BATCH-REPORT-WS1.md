# Manioc Server — WS1 parser-hardening batch (2026-10-31)

Source brief: the additive verification pass of 2026-10-31,
WS1 (fuzz of the backup/restore metadata parsers) plus the
WS3 app-init nit. This batch is the fix path for those
findings. Nothing here is closed until the auditor
re-verifies it; the harness and suite runs below are the
fix author's evidence, offered for re-run.

## Baseline

- Fresh clone of github.com/CameronRuggles/ManiocServer,
  branch `ws1-parser-hardening-2026-10-31` off the
  t8-rework-followups tip `a0e935c` (code head `60398a9`).
- Code head of this batch: `7ea0192`. Commits:
  - `bb14636` — restore (R1–R6, plus the unused-import nit)
  - `f84b059` — backup + sitegen (B1, B2, S1)
  - `7ea0192` — golden app-init.sh env validator (WS3 nit)
  - this report (tip, no code)
- Diff vs the followups tip: 4 files, +110/−21.

## Positive control (before any fix)

The additive pass's own harness (`harness-ws1-fuzz.py`,
copied to scratch outside the tree) run against the
unmodified head reproduced the report exactly: **73 recorded
outcomes — 39 CRASH, 2 WRONG, 1 uncaught OSError** (a
FileNotFoundError out of `_verify`'s onion stage).

## The fix shape

The pattern S7 ratified for onionhost-update, applied per
tool: close it in the parser, not per call site. A parsed
JSON root must be a dict before any `.get`; every value
consumed as a string is isinstance-checked at the point of
parse; failures raise the tool's existing shaped error
(RestoreError in restore, the `_fail` return in backup,
ValueError in sitegen) or degrade exactly as the site's
valid-input error path already does.

## Per-site results

### Restore (onionhost-restore)

- **R1 `_read_wrapper`:** a non-dict meta.json raises the
  shaped "could not be read as an OnionHost backup"
  RestoreError; previously `meta.get` ran after the try and
  escaped as AttributeError (4 shapes).
- **R2 `_decrypt`:** `salts` must be a dict and `salts.main`
  a string before `.get`/`fromhex`; failures raise the
  existing damaged-key-information RestoreError (4 shapes).
- **R3 `_verify`:** the staged manifest must be a dict,
  `entries` a list of dicts, and each entry's `path` a
  string before `startswith`; failures raise a
  damaged-checklist RestoreError in the neighbouring
  wording (9 shapes). The app section now reuses the
  validated `entries` list instead of re-reading the raw
  manifest value.
- **R4 `_verify` structural:** a manifest that omits the
  onion files now meets a shaped RestoreError ("website
  identity is damaged") on the public-key and hostname
  reads instead of an uncaught FileNotFoundError. The
  site section's `current.txt` read got the same wrap
  ("published website is incomplete").
- **R5 `_write_recipe_selection` (the Medium placement,
  mid-`_install`):** a non-dict staged site model raises
  RestoreError before anything is written. The `recipe`
  value must be a string matching the recipe-id rule
  sitegen enforces — first char `[a-z0-9]`, rest
  `[a-z0-9-]*`, checked with `re.fullmatch` on the same
  pattern — or RestoreError is raised and nothing is
  written and nothing is cleared. This closes the crash
  shapes (3) and both WRONG shapes (an int recipe was
  written as `123`, a list as `['gitea']`). A missing or
  unreadable site.json, and a model with no recipe key,
  keep the old behaviour exactly (selection cleared, no
  error). One judgement call, stated plainly: a `recipe`
  of `""` or `false` now raises instead of silently
  clearing — sitegen's validation rejects both as a bad
  recipe id, so neither can appear in a platform-written
  record.
- **R6 `_root_disk_prefix`:** a non-dict luks-roles.json
  or a non-string `device` degrades to the function's
  existing fallback for unreadable files (return None,
  exclude nothing) instead of crashing (4 shapes).
- Nit from the same WS3 list: the unused `io` import is
  removed; `re` is added for the R5 match.

### Backup (onionhost-backup)

- **B1 `create_backup` key record:** a parsed record that
  is not a dict, a `main` entry that is not a dict, or a
  recipient/salt that is missing or not a string now
  returns the existing shaped `_fail("the backup key
  record is damaged")` — the same outcome invalid JSON
  already produced. This tool has no catch-all, so the 7
  shapes were raw tracebacks; now every backup attempt on
  a damaged record ends with that one line.
- **B2 `_site_db_engine`:** a recipe manifest that parses
  to a non-dict now takes the function's documented
  unreadable-manifest outcome (MariaDB for php, none for
  native). A `db` value of the wrong shape (null, a bare
  string, a list) reads as no record at all, so the `{}`
  default decides — `{"db": null}` no longer defeats the
  default. Valid manifests decide exactly as before
  (required false → none, engine postgres → postgres).

### Site model (sitegen.py)

- **S1 `validate_model`:** `pages`/`entries` must be
  lists before `len()` and iteration; an item `id`, an
  entry `photo`, and an entry `date` must be strings
  before their regex matches. The four TypeError leaks
  now raise the designed ValueError with the neighbouring
  messages ("bad or duplicate item id", "bad photo name",
  "bad entry date"), so callers catching
  (ValueError, OSError) see the shaped error.

### App-init nit (golden app-init.sh, WS3 Info)

- The app.env line validator's malformed arm now also
  matches `[0-9]*`: a name beginning with a digit is
  reported as a malformed line and skipped, like every
  other malformed line, instead of being admitted and
  then silently refused by `export`. Valid identifiers
  and the platform-managed names are untouched (checked
  against a case-statement replica: `1BAD`/`9` malformed;
  `GOOD_1`, `_X`, `X9` still exported; `PATH` still
  platform-managed).

## Final gate — WS1 harness

Same harness, final head: **69 recorded outcomes, 0 CRASH,
0 WRONG.** The count drops from 73 because the R6 fallback
and the B2 fallback return by design (the harness records
returns only for its named controls, which all pass). The
lines the harness labels OTHER are the shaped outcomes it
has no clean-type registered for at those two sites: the
R5 RestoreError (5 lines) and the B1 `_fail` return
(7 lines) — both are the designed shaped paths, named in
its own detail text. Valid-input controls are unchanged
across every site: valid meta/decrypt/verify controls,
the valid recipe selection still writes `gitea`, the
valid luks-roles record still returns `vda`, the db
controls still return postgres / mariadb / none as before,
and the valid site model still loads.

## Existing suites

- `poc/scripts/t8-rework-test.py` — ALL CHECKS PASSED.
- `poc/scripts/t1-followups-test.py` — ALL CHECKS PASSED.
- `poc/scripts/t3-debian-status-test.py` — ALL CHECKS
  PASSED.
- `poc/scripts/t3-reboot-state-test.py` — FAILURES: 0.
- `poc/runtime-gate/run_sim.py` — aborts with the same
  AssertionError (line 253, marker assert) at the branch
  base `a0e935c` and at this head, run both ways in this
  session; a sandbox environment limit, and this batch
  touches no runtime-gate file. Not claimed.
- `poc/backup-proof/proof.py` — cannot run against this
  branch in this sandbox: the script hardcodes its tree
  to another checkout (line 36) and needs an `age`
  binary and `/var/lib/onionhost`, both absent here.
  Not run, not claimed; the same wall the auditor and
  the followups batch recorded. The backup/restore
  valid-input behaviour control for this batch is the
  WS1 harness's valid controls plus the suites above.

## ci-scan

To be run on a pristine `git archive` export of the
branch tip (including this report) before the ferry; the
result is stated in the ferry note. The expectation,
from the branch base's own scan profile, is exactly the
2 inherited ISO-BUILD-LOG.md hits and zero in touched
files, this report included.

## Disclosures

- Harness venues use the additive pass's own staging
  (faked `open` where a path is hardcoded); the parse code
  under test is the real code, as in the source pass.
- The R5 judgement call on `""`/`false` recipe values is
  the one place behaviour changes for an input the old
  code tolerated; it is argued above and flagged for the
  auditor.
- T8-A rig legs remain pending on the GCP hold and are
  not claimed here. This branch is local only; the push
  is Cameron's tap.

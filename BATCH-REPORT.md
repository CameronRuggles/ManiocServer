# Manioc Server — WS1 R5 rework batch (2026-11-02)

Source brief: the external auditor's re-verification of
2026-11-02 (`AUDITOR-REVERIFICATION-2026-11-02`), Ask 1:
**SEND BACK — R5 only**. Every other WS1 site passed as built
(R1–R4, R6, B1, B2, S1, the app-init nit) and is untouched by
this batch. This batch answers R5 and nothing else.

Approved under Cameron's standing direction (do everything
code-wise possible without a human); ferry and merge remain
his taps.

## Baseline

- Clone: fresh clone of github.com/CameronRuggles/ManiocServer
  at ~/workspace/manioc-ws1-r5-2026-11-02 (Cameron's checkout
  ~/workspace/onion-host-os NOT worked in; the WS1 batch clone
  NOT touched).
- Branch: `ws1-r5-rework-2026-11-02` off the WS1 branch tip
  136059e7d26ae571cfde7065103d245dc25e5db6 (code head
  7ea0192).
- One code commit: 4064aef — `onionhost-restore` only,
  +66/−26. This report is the tip commit on top of it.

## The defect (auditor's finding, sandbox-proven by him)

WS1's R5 fix made `_write_recipe_selection` refuse a damaged
staged site record with
`RestoreError("This backup's website record is damaged.
Nothing was changed.", 4)`. But that function is called only
from `_install_app`, inside `_install`, AFTER the content
store (step 1), the app trees, the DB credentials and the
runtime marker have already been swapped. The auditor's
sandbox (`r5_midinstall.py`, driving the real `_install` with
an app backup whose site.json is `[1, 2]`) showed five owner
files CHANGED by the time the code-4 "Nothing was changed"
refusal surfaced — the head was less honest than the base,
whose catch-all ("the restore did not finish") was accurate.
The check has to live in the pre-install parser, not only in
the install path.

## Positive control (before any fix)

The auditor's `harnesses/r5_midinstall.py`, unmodified,
against the unmodified WS1 code head (7ea0192, this branch's
base):

```
RESULT: RestoreError code=4, owner is told: "This backup's
website record is damaged. Nothing was changed."
  CHANGED  home/owner/.config/onionhost/site.json
  CHANGED  var/appdata/www/index.php
  CHANGED  etc/app-db.env
  CHANGED  var/app-runtime
  CHANGED  var/app-site
  same     var/tor/hs/hostname, etc/recipe-selection, var/state
```

His result reproduced exactly.

## The fix (commit 4064aef, onionhost-restore only)

1. **One shared helper, `_site_record_recipe(stage)`.** Reads
   the staged `content/site.json`; returns the recipe it
   selects, or None for the long-standing clear-and-continue
   cases (model missing/unreadable, or no recipe carried).
   Raises ValueError when the model parses but is not shaped
   like a site model: a non-dict root, or a `recipe` that is
   not None and not a str fullmatching
   `[a-z0-9][a-z0-9-]*` — exactly the checks
   `_write_recipe_selection` applied in the WS1 batch, moved
   into one place so the two call sites cannot drift.
2. **`_verify` applies it pre-install.** Right after the
   checklist/extra-files checks, when `"content/site.json"`
   is among the verified manifest entries (`listed`),
   _verify runs the helper and a ValueError becomes
   `RestoreError("This backup's website record is damaged.
   Nothing was changed.", 4)` — the same shaped refusal as
   before, now at a point where the wording is true.
   Call order, confirmed in `main()`: `_read_wrapper` →
   `_decrypt` → `_verify` (line ~1001) → `_install`
   (line ~1006). _verify extracts only into the throwaway
   stage directory; nothing on the machine has moved when
   it refuses. The gate is the manifest entry, so it covers
   every backup that stages a `content/site.json` (backup
   writes that entry for every backup —
   onionhost-backup's `add("content/site.json", ...)`),
   not only app-section ones.
3. **`_write_recipe_selection` keeps the check as
   belt-and-braces** — the same helper — but if it ever
   fires (the staged record changed after verification),
   the refusal is honest and in the catch-all's family:
   `RestoreError("This backup's website record is damaged.
   The restore did not finish; you can try again.", 1)`.
   Code 1, never "Nothing was changed." The write/clear
   behaviour below the check is byte-for-byte the WS1
   batch's: a valid recipe is written; no recipe, a missing
   model or an unreadable model clears any stale selection.

## Considered and NOT adopted: full validate_model in _verify

The auditor's "better still" option was to run
`sitegen.validate_model` on the staged record in `_verify`,
so a backup could not install a site record the publisher
would refuse. Not adopted, on these facts:

- `validate_model` is applied NOWHERE in the restore path
  today: restore does not import sitegen at all; the
  function runs only inside sitegen's own load/save/publish
  paths (sitegen.py's `load_model` and publish flow).
  Adopting it would be a new policy for restore, not a
  restored one.
- Restore's contract is to reinstate records the platform
  wrote at backup time, including records written by older
  platform versions. `validate_model` is the CURRENT
  publisher's contract and it tightens over time — the
  auditor's own S1 Info note in this same re-verification
  records a validate_model tightening changing which inputs
  are accepted. Gating restore on it would let a publisher
  tightening retroactively make old backups unrestorable.
- The R5 defect is specifically the recipe value flowing,
  unchecked-then-mid-install, into the recipe selection.
  The targeted dict+recipe check closes it without
  narrowing restore compatibility. If the owner later wants
  restore held to the publisher's full model contract, that
  is a policy decision to take on its own, with the
  old-backup consequences counted first.

## Branch state, stated exactly (R4)

The auditor ratified R4's extra wrap and noted the WS1 pack
understated it. For the record, the R4 change in `_verify`
wraps THREE reads, each raising a shaped RestoreError
instead of an uncaught FileNotFoundError:

1. the bundled onion public key
   (`onion/hs_ed25519_public_key`) — "website identity is
   damaged",
2. the bundled hostname (`onion/hostname`) — "website
   identity is damaged",
3. the published-site sequence (`site/current.txt`, static
   backups) — "published website is incomplete".

This batch does not touch any of them.

## Gates

- **Positive control** — above; the auditor's harness on
  the unmodified head reproduces his result exactly.
- **Acceptance A (new gate).** A purpose-built driver
  (kept in scratch, out of the tree) builds REAL, fully
  valid app-backup payloads — correct manifest sha256/size
  entries, a consistent onion identity computed with the
  real `backupkeys` — that differ only in
  `content/site.json`, then drives `_verify` / `_install`
  in main()'s order against a pre-seeded "old site"
  machine:
  - site.json `[1, 2]`: **_verify refuses, code 4,
    "Nothing was changed.", and the before/after snapshot
    of every owner file is identical** (site record, app
    tree, db env, runtime markers, hostname, selection,
    state — nothing moved; _install never called).
  - site.json `{"recipe": 123}`: the same code-4 refusal
    from _verify, no owner file changed.
- **Acceptance B (the auditor's requested control).** A
  valid app backup (well-formed model, recipe `gitea`)
  passes _verify and **completes the sandbox restore end
  to end**: site record replaced, app tree swapped, DB
  env and runtime markers written, recipe selection
  written as `gitea` — the selection behaviour exactly as
  before the rework. A second control with a valid
  recipe-less model also completes, and the stale
  selection is cleared, as before.
- **Acceptance C.** `_write_recipe_selection` called
  directly on the damaged staged record raises
  RestoreError **code 1** with "The restore did not
  finish; you can try again." — no "Nothing was changed."
  The auditor's own `r5_midinstall.py` (which drives
  `_install` directly, bypassing _verify) now reports the
  same: code 1, honest wording, with the CHANGED lines his
  proof documented — the state the wording now admits to.
- **WS1 harness** (`harness-ws1-fuzz.py`, unmodified, run
  against this tree): **69 outcomes, 0 CRASH, 0 WRONG** —
  identical totals to the WS1 head. Row-for-row against the
  auditor's own head run (his evidence outputs), the ONLY
  differences are the five R5 shaped rows, whose message is
  now the honest in-install wording; every control row is
  identical.
- **Existing suites:** t8-rework ALL PASSED;
  t1-followups ALL PASSED; t3-debian-status ALL PASSED;
  t3-reboot-state FAILURES: 0.
- **backup-proof: ALL 27 CHECKS PASS**, run the auditor's
  way — main's portable `proof.py` (MANIOC_TREE, from
  720aafa) placed inside this tree's `poc/backup-proof/`
  and run against this tree. (The branch's own proof.py
  still hardcodes another checkout, as disclosed in the
  WS1 batch; the portable run closes that gap for this
  branch. The proof is a static-site round trip and does
  not exercise R5's app path — acceptance A/B above are
  the R5 evidence.)
- **ci-scan** on a pristine `git archive` of this branch's
  tip (this report included): exactly the 2 inherited
  ISO-BUILD-LOG.md findings (lines 7068, 7429), zero in
  touched files.

## Disclosures

- The acceptance driver lives in scratch (`/tmp`), not in
  the tree — same status as the auditor's harnesses: gate
  evidence offered for re-run, not shipped test code. It
  stubs ownership/ACL/subprocess calls exactly as the
  auditor's sandbox does; the parse, verify and install
  code under test is the real code, and the payloads are
  real tar.gz backups with real hashes and a real onion
  identity.
- Acceptance A's payloads pass every pre-existing _verify
  check by construction (valid manifest, hashes, onion
  three-way agreement, app-section sanity), so the code-4
  refusal is attributable to the new site-record check
  alone; acceptance B proves the same construction restores
  cleanly when the record is valid.
- No other WS1 site was touched: the diff is
  `onionhost-restore` only (+66/−26), and within it only
  `_site_record_recipe` (new), the `_verify` gate, and
  `_write_recipe_selection`.
- Nothing pushed, nothing merged. Merge path is unchanged:
  this branch stacks on `ws1-parser-hardening-2026-10-31`;
  the auditor's merge-order constraint from the same
  re-verification (the stack must not reach main without
  the fuzz branch — S7-f) is unaffected and still stands.

# Manioc Server — T8 rework follow-up batch (2026-10-31)

Source brief: the fresh external auditor's T8 rework
re-verification of 2026-10-31
(`MANIOC-T8-REWORK-REVERIFICATION-2026-10-31`), which verified
the rework's T8-B six sites, T3-1 and T1-1, and returned three
NEW findings: §3 (a seventh T8-B site — the native apply path),
§5 (a T8-A migration residual in the rework's own new code),
and §8 (the T1-2 kernel purge mis-selecting "newest" on
Debian `+deb13` names). This batch is the fix path for exactly
those three. Nothing here is closed until the auditor
re-verifies it; the harnesses are the fix author's evidence,
offered for re-run. (This file replaces the parent batch's
report, which remains in history at the branch base.)

## Baseline

- Fresh clone of github.com/CameronRuggles/ManiocServer,
  branch `t8-rework-followups-2026-10-31` off the pushed
  rework tip `67832e05643b73a62a886331504d3fa6d8cac5d6`
  (code head `44200856070dbd76fe067d3bcf5e5f673dac30ac`).
  Cameron's checkout (~/workspace/onion-host-os) and the
  rework clone were not worked in.
- Commits, one per fix (harness extensions in the same
  commits):
  - `dd3c602` — Fix 1, §3 seventh T8-B site (native apply).
  - `9797183` — Fix 2, §8 T1-2 kernel ordering.
  - `60398a9` — Fix 3, §5 migration quarantine. **Code head.**
  - This report is the tip commit; it adds no code.
- Diff vs the rework tip: 5 files, +706/−89 (3 production
  files +413/−83, 2 harness files).
- Local only: not pushed, not merged. Merge path unchanged:
  followups → `t8-rework-2026-10-30` →
  `audit-fix-batch-2026-10-24` → `main`.

## Positive controls (BEFORE each fix, unmodified branch head)

All three findings reproduced against the real code:

1. **Native apply follows links.** Driving the real
   `apply_recipe → apply_native` on a non-first apply with
   three destination names in `native/` pre-planted as
   symlinks to markers outside the tree (no system paths):
   all three markers ended with the recipe's bytes, mode
   0o755, and container-mapping owners, and `native/app` was
   left as a symlink to the outside binary target.
   Verdict: FOLLOWS.
2. **Kernel victim selection.** Driving the real
   `_purge_superseded_kernels` with the production name form:
   A (installed 6.12.107+deb13 / 6.12.113+deb13, running 107)
   purged **113 — the new kernel**; B (three kernels, running
   107) purged **both newer**; C (classic 6.1.0-15/-21/-23,
   running -21) correctly purged only -15.
3. **Migration resurrection.** The auditor's 5-step sequence
   through the real provision (fresh → OLD root copy + NEW
   import/ staging → publish, conflict warns → consume
   import/ → publish again) ended with `import/` = OLD-DUMP:
   RESURRECTED.

## Fix 1 — §3: apply_native places files through descriptors

`onionhost-recipe`: `apply_native`, `_makedirs_owned`, and
the native half of `rollback_recipe` placed/chmodded/chowned
by path over the app-writable `native/` tree; commit
`42300a5` (the T8-B rework) never touched them. The auditor
rates the site High (integrity/DoS; pre-existing in main).

- New `_place_file_fd(dir_fd, name, src, mode, uid, gid)`:
  the source is opened O_NOFOLLOW and must be regular; the
  destination is handled through the `native/` directory
  descriptor. **Semantics chosen at an existing destination
  name** (the platform's fail-closed stance on planted
  names, as in provision and the staged import): a REGULAR
  file is an ordinary refresh — unlinked through the fd and
  recreated `O_CREAT|O_EXCL`; **any other name (symlink,
  fifo, directory) refuses the apply with OSError, target
  never touched.** Mode/owner are asserted through the fd
  before the bytes land; managed files keep the payload's
  times (the old `shutil.copy2` behaviour).
- The `native_files` loop and the binary staging both go
  through it (parents via `_native_parent_fd` /
  `_ensure_dir_fd`, created parents owned as before). The
  `app` / `.app-prev` swap is now an fd-relative rename,
  which acts on the directory entry itself — a link sitting
  at that name is replaced, not followed. A planted `.app.new` link
  therefore refuses the apply and the live binary is not
  swapped.
- `_makedirs_owned` rewritten component-safe: an fd walk
  with O_NOFOLLOW opens, creating and chowning only the
  directories the call itself creates (its original
  contract); a planted component raises.
- `_atomic_write` at its two apply_native uses (config
  render, first-boot env): **assessed and left unchanged** —
  it never opens the destination by path for writing; it
  unlinks the temp name, creates the temp `O_CREAT|O_EXCL`
  (a planted temp link fails with EEXIST rather than being
  followed), fsyncs, and renames over the destination name.
  The by-path `os.chown` calls that followed it WERE in the
  §3 pattern and are now `_fchown_nofollow` (fd-based,
  regular-file-only, raises on a link).
- `rollback_recipe`: the restored binary's chown is
  fd-based through the native dir fd; when the restored
  name is a link or cannot be opened no-follow, it is
  skipped with a warning (the auditor's suggested shape)
  instead of landing on the target.
- Honest case preserved: same end modes/owners (managed
  files container-root mapping with manifest mode, binary
  www mapping 0755, `.app-prev` kept one generation),
  first-install gating and publish flow unchanged — harness
  leg D applies twice (install + refresh) and asserts all
  of it.

## Fix 2 — §8: kernel purge orders by dpkg's comparison

`onionhost-update`: `_purge_superseded_kernels`' nested
`_kkey` stopped at the first non-pure-digit component, so
`6.12.107+deb13` and `6.12.113+deb13` both keyed to `(6, 12)`
and `max()` returned the oldest; the purge then removed the
newest kernel. Introduced by the rework batch itself;
production naming confirmed `+deb13` (rig record:
`linux-image-6.12.113+deb13-amd64`).

- "Newest" is now `max()` over `functools.cmp_to_key` with
  `_debver_cmp` — dpkg's full version ordering (epoch,
  upstream, revision). Note on the brief's premise:
  `_verrevcmp`/`_debver_cmp` ship in **onionhost-recipe**,
  not in this module (this module has only the subprocess
  `dpkg_compare`); they were ported verbatim into
  onionhost-update, the platform tools being standalone
  with no shared module to import, rather than shelling out
  to dpkg once per comparison inside a best-effort helper.
- The comparison runs over the version part: `_kversion`
  strips the `linux-image-` prefix and the trailing flavour
  tail (the same tail the running release carries, e.g.
  `-amd64`), leaving `6.1.0-23` / `6.12.113+deb13`.
- Running-kernel protection, the purge invocation, and the
  log lines are unchanged.

## Fix 3 — §5: migration conflict quarantines the root copy

`onionhost-app-provision`: in the migration conflict case
(root staging AND `import/` staging both present), the root
copy was warned about and left in place; after the container
consumed the `import/` copy, the next publish migrated the
stale root copy in, and it was imported over live data.

- The conflict case now **renames the root copy through the
  appdata fd** to `db-import.sql.gz.superseded` and fsyncs
  the appdata fd, keeping the warning (reworded to say what
  happened). Chosen over unlink-first because the stale
  dump stays recoverable by hand while being inert.
- The name is safe: every reader of the root-level name was
  checked — provision's migration and `onionhost-recipe`'s
  `_staged_import_exists` read the exact name
  `db-import.sql.gz` only, `onionhost-restore` uses that
  name only inside `import/`, and app-init reads only
  `import/db-import.sql.gz`. Nothing treats the
  `.superseded` name as a staged import (harness-checked).
- If the rename raises, the fallback unlinks the root copy
  through the fd after the warning — either way it can
  never be migrated later. The non-conflict migration path
  is unchanged.

## Gates (all run at the code head 60398a9)

- **Positive controls, post-fix:** ctl1 — apply refuses
  (OSError), all three outside markers byte/mode/owner
  identical, `native/app` untouched. ctl2 — A: no purge;
  B: purges only 113; C: purges only -15 (classic unchanged).
  ctl3 — step 5 leaves `import/` empty; the root copy sits
  quarantined as `db-import.sql.gz.superseded` with its
  bytes intact.
- **poc/scripts/t8-rework-test.py — 56 checks, ALL PASS.**
  The same harness run against the pre-fix tree records
  exactly 12 FAILs (the 8 native planted-link checks and 4
  quarantine/conflict checks); every other check passes on
  both trees, including the honest apply/refresh guards.
- **poc/scripts/t3-debian-status-test.py — 15/15.**
- **poc/scripts/t1-followups-test.py — 14 checks, ALL
  PASS** (11 original + 3 new `+deb13`). Against the pre-fix
  tree the 3 new checks FAIL and the 11 original pass.
- **poc/scripts/t3-reboot-state-test.py — FAILURES: 0.**
- **poc/runtime-gate/test_runtime_dashboard.py — 11 PASS,
  0 failed** (same at base).
- **Prior auditor's T8-B demos at the new head:** copytree
  demo copies only the valid file, both planted links
  skipped with warnings; mode-exceptions demo leaves the
  host file 0600 before and after. Both clean.
- **poc/installer-policy/run_proofs.py — 0 assertions
  failed. poc/runsc-wrap/run_tests.py — 0 assertions
  failed** (same at base).
- **ci-scan: exactly 2 findings, both the pre-existing
  ISO-BUILD-LOG.md hits inherited from the branch base;
  zero in touched files.**

## Disclosures — suites that do not complete in this sandbox

Named, not claimed (each verified identical at the branch
base, so none is a regression of this batch):

- **poc/runtime-gate/run_sim.py** aborts partway in this
  sandbox (9 passes, then the all-wrapper judge leg fails,
  then an assertion) — IDENTICALLY at base and at the code
  head. This batch touches no runtime-gate file.
- **poc/backup-proof/proof.py** cannot run here: the `age`
  binary is not installed in this sandbox (the auditor hit
  the same wall in his §9). Identical failure at base.
- **poc/recipes-marketplace/unit-test.py** fails
  identically at base and head inside its fixture stage
  (`dpkg-deb -x` on the fixture .deb exits 2) — the
  pre-existing fixture failure prior batches recorded.

Further honest limits:

- Harness venues lower the container uid base to 10000
  (the sandbox's user namespace does not map the production
  base 2300000) — the same workaround every prior batch
  used; the planted-link and quarantine legs are
  uid-base-independent in shape.
- Fix 1's semantics refuse the whole apply on a planted
  native destination name. A compromised app can therefore
  block its own re-publish until the owner clears the name
  by hand — accepted deliberately: the alternative
  (unlinking a planted link and proceeding) would let the
  app silently trade names inside a security assertion,
  and every other planted-name site in the platform fails
  closed the same way.
- Adjacent observation, NOT fixed (outside the brief):
  `_reboot_state`'s `_vkey` in onionhost-update splits on
  "+" before "-", so it orders `+deb13` names correctly,
  but on classic names it keys only the upstream part
  (6.1.0-21 and 6.1.0-23 compare equal there). It only
  feeds the reboot-required heuristic, never a purge;
  flagged here for the auditor's judgement.
- The T8-A rig legs from the rework pack are still pending
  (the GCP rig hold is the owner's appeal); this batch
  neither runs nor claims them. Fix 3 is statically and
  harness verified only, like the rest of T8-A.

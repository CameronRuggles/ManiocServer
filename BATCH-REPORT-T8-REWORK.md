# Manioc Server — audit-fix follow-on batch (T8 rework, T3-1, T1-1/T1-2), 2026-10-30

Source brief: the external auditor's re-verification of 2026-10-30
(`MANIOC-AUDITOR-REVERIFICATION-2026-10-30`), §2. The auditor's
verdict on the parent branch stands: commit `3accd51` (T8) must
not merge until T8-A is fixed. This batch is that fix path, plus
the T3-1 and T1 follow-ups. T1 and the T3 restart half were
VERIFIED by the auditor and are not rewritten; the follow-ups
are additive.

Approved under Cameron's standing direction of 2026-10-30 (do
everything code-wise possible without a human).

## Baseline

- Clone: fresh clone of github.com/CameronRuggles/ManiocServer
  branch `audit-fix-batch-2026-10-24` at
  ~/workspace/manioc-t8-rework-2026-10-30 (Cameron's checkout
  ~/workspace/onion-host-os NOT worked in).
- Branch: `t8-rework-2026-10-30` off branch tip
  d05b7135967c39a377e8b9325ce23510f5394f0c (code head 06596fc).
- Tree state at start: clean.

## Positive controls (BEFORE any fix, unmodified branch head)

Auditor evidence scripts run 2026-10-30 in this session:

- `t8b_copytree_demo.py` (real `_copy_tree` at 06596fc):
  REPRODUCED. A planted dir symlink `attachments/k -> tor/hs`
  arrived in staging as a plain `k/hs_ed25519_secret_key`
  (content SECRET-ONION-KEY) and a planted file symlink
  `s.txt -> /etc/shadow` arrived as a plain file with the
  shadow contents.
- `t8b_mode_exceptions_demo.py` (real `_apply_mode_exceptions`
  with the shipped marketplace list): REPRODUCED. Host file
  mode 0600 before, 0755 after.
- `t8a_appdata_perm_demo.py`: COULD NOT RUN in this
  environment — `os.chown` to uid 2300000 fails with EINVAL
  (this sandbox's user namespace does not map the production
  id base; the same limit the original T8 harness worked
  around by lowering the base to 10000). T8-A therefore rests
  on code-reading evidence, re-verified site by site in this
  session against 06596fc:
  * `onionhost-app-provision:182-183` fchowns appdata to 0:0
    and fchmods 0755 at every publish;
    `onionhost-generate-configs:275-276` births it 0:0 0755.
  * `app-init.sh` (MariaDB path) runs
    `rm -f "$DATA/db-import.sql.gz"` after a successful
    import, and the PostgreSQL path does the same; no host
    tool ever deletes that file (grep across the overlay:
    recipe stages it, restore stages it, only app-init
    deletes it).
  * `app-init.sh` start_pg runs `mkdir -p "$DATA/pgdb"`;
    provision creates only www/db/native, so on any appdata
    born after T8 the datadir cannot be created at the
    (now host-root-owned) appdata root.
  The parent session independently confirmed the same two
  Highs before dispatch.

## Task 1 — T8-A: managed import directory + pre-created pgdb

DONE. The auditor's suggested shape, implemented:

- `onionhost-app-provision`: births and asserts `import/`
  and `pgdb/` alongside www/db/native, through `_dir_fd`
  like the other managed dirs, both container-root owned
  (CONTAINER_UID:CONTAINER_UID) 0700. appdata itself stays
  host-root 0:0 0755 — T8's property (the app cannot create,
  rename or delete names at the appdata root) is preserved.
  Provision also migrates a lingering pre-T8-A root-level
  `db-import.sql.gz` into `import/` (descriptor-to-descriptor
  copy, O_NOFOLLOW + O_CREAT|O_EXCL on the destination,
  source unlinked through the appdata fd) — only when
  `import/` holds no staged import; when it does, the root
  copy is left in place and a warning printed (the import/
  copy is the live staging; nothing is silently overwritten
  or dropped).
- `onionhost-generate-configs`: births import/ and pgdb/ in
  the same end state ($OH_BASE:$OH_BASE, 0700).
- `onionhost-recipe`: the seed is staged into
  `appdata/import/db-import.sql.gz` via `_write_staged_import`
  — a dir-fd open with O_NOFOLLOW|O_CREAT|O_EXCL. An existing
  regular-file staging wins (returns False, seed block keeps
  the old "already staged wins" semantics, including a
  lingering root-level file via `_staged_import_exists`);
  a non-regular file at the staged name (a planted symlink
  also raises EEXIST under O_EXCL) is distinguished by an
  fd-relative lstat and FAILS the apply closed. The import
  directory itself is opened via `_dir_fd`, creating +
  asserting it (container-root 0700) on boxes provisioned
  before T8-A.
- `onionhost-restore`: the dump is staged into
  `appdata/import/db-import.sql.gz` through the directory
  descriptor (O_NOFOLLOW|O_CREAT|O_EXCL, 0600, APP_UID);
  the import directory is asserted first (0700, APP_UID),
  and an existing staging is unlinked through the same
  descriptor and replaced — a restore is the owner's chosen
  state, so its dump wins wholesale.
- `app-init.sh`: the ONLY behaviour changes are the import
  location and its documentation. A new `IMPORT_FILE=
  "$DATA/import/db-import.sql.gz"` is referenced by both
  engines' test/gunzip/delete/message sites (10 sites moved;
  no `$DATA/db-import.sql.gz` reference remains). pgdb
  needed no change: init's existing `mkdir -p` +
  chown-to-postgres now operate on provision's pre-created
  directory.

Harness (new, `poc/scripts/t8-rework-test.py`, t3 style,
id base lowered to 10000): 20/20 PASS — provision births +
appdata-root property, migration both ways, recipe staging
round-trip / second-staging-loses / lingering-file counts
as staged, symlinked import dir and symlinked staged name
both fail closed with the host target untouched, app-init
statics (definition, no direct reference, 2 delete sites,
2 test sites).

RIG LEGS RECORDED AS RIG-PENDING (auditor's list; not run —
no rig in this batch): (1) SQL-seeded recipe fresh install
→ write → restart the app twice → the write survives;
(2) restore → write → restart → the write survives;
(3) fresh native+postgres install starts (pgdb pre-created);
(4) post-migration, from inside the container,
`rm /srv/appdata/<x>` and `mv /srv/appdata/www …` both
fail, while `rm /srv/appdata/import/db-import.sql.gz`
after a successful import succeeds.

## Task 2 — T8-B: never copy through links

DONE. All five sites plus the Low, in `onionhost-recipe`
and `onionhost-backup`:

1. **Data-dir/tree carry-over** (`_copy_tree`): the
   `shutil.copytree(symlinks=False)` implementation (which
   copies link TARGETS) is replaced by a descriptor walk —
   `_dir_fd` roots, a no-follow open per component, regular
   files copied from their descriptors
   (`_copy_file_between_fds`), directories created through
   the destination fd with their modes asserted on the way
   out. Symlinks and non-regular files are skipped and
   logged. `__pycache__` and `exclude_rels` behaviour is
   unchanged (harness-checked). The same fix covers the
   archive-tree build, which uses the same function.
2. **Config carry-over**: new `_copy_config_carryover` —
   open O_NOFOLLOW|O_NONBLOCK, require S_ISREG, copy from
   the fd. A refused carry-over leaves the staged name
   absent, exactly as a missing config would.
3. **Mode exceptions** (`_apply_mode_exceptions`): a
   symlinked target is skipped with a warning; a regular
   file is chmod'd through `_fchmod_nofollow` (fd + fchmod),
   never by path.
4. **Backup** (`onionhost-backup`): the app-tree walk in
   `_collect_app` prunes symlinked directories and skips
   symlinked files, recording both in `_SKIPPED_LINKS`;
   the payload copy for app-data entries goes through
   `_copy_file_nofollow` (a name swapped between collection
   and copy is skipped + recorded, never followed); the
   manifest's `skipped` list now names the links with their
   own reason beside the *.tmp records (S12 pattern).
5. **Nested data dirs** (`_own_data_dirs`): every path
   component of a declared data directory is link-checked,
   not just the last — a planted middle component refuses
   the apply with ValueError before the fwalk.
6. **Low** (`_grant_owner_acl`): the open gains
   O_DIRECTORY|O_NONBLOCK.

Gates for this task:
- Auditor's demos against the FIXED functions:
  `t8b_copytree_demo.py` now copies only the valid file
  (avatar.png) — the shadow contents and the onion key are
  gone; `t8b_mode_exceptions_demo.py` — host file 0600
  before AND after. Both were reproduced on the unmodified
  head as the positive control (see above).
- Harness T8-B section (17 checks): all PASS on the fixed
  tree. Run against the pre-fix tree (worktree at the
  task-1 commit) the same section records 8 FAILs (dir/file
  link targets copied, secret content present in the copy,
  config helper absent, host file chmod'd through the
  link, nested component not refused, backup collecting
  the planted file link) and then errors on the
  skipped-links record, an attribute that does not exist
  pre-fix — the gate proves it can fail.
- Two honest non-discriminations: the FIFO/ACL leg passes
  both ways in THIS environment (the open fails fast here
  rather than hanging), so the Low rests on the code change
  and the auditor's reasoning, not a local repro; and the
  backup dir-link leg also passes pre-fix (os.walk does
  not follow directory links by default — the file links
  were the live hole, as the auditor's item 4 states).

## Task 3 — T3-1: Debian phase outcome in status.json + Dashboard

DONE. In `onionhost-update`:
- New module state `DEBIAN_PHASE_OK` (None until the phase
  runs), maintained exactly as `CHECK_SUCCEEDED` maintains
  the project channel's pair (A6: the channels fail
  independently, so their freshness records do too).
- `main()` captures the Debian phase's own results
  (`apt-get update` rc and the install rc) and sets the
  outcome before the run's status writes.
- `write_status` now writes `debian_ok` and
  `debian_last_successful_check` — but ONLY once a phase
  outcome exists; before that (mid-run writes, and every
  write an older updater made) the record carries the
  previous values forward, and a first-ever record has no
  Debian keys at all. **Every pre-existing key is written
  exactly as before**: the auditor's own
  `write_status_equivalence.py`, run base-vs-new after
  this change, reports `identical=True` in all four of
  its cases (the project-channel equivalence and the T3
  restart-half behaviour are untouched — the T3 suite
  still reports FAILURES: 0).
- The final "up-to-date" write's detail no longer claims
  "Everything is current" when the Debian phase failed;
  it says the platform software is current and the Debian
  phase will be retried.
In `wizard.py` (`update_status_text`): when the record's
`debian_ok` is False, the Dashboard renders a distinct
line — the system-package (Debian) check is not
completing, with the age of `debian_last_successful_check`
("it has not completed yet" when it never has) — instead
of any "up to date" wording. Records without the key (all
pre-T3-1 records) render exactly as before.
New harness `poc/scripts/t3-debian-status-test.py`:
15/15 PASS (record shape, advancement rules, carry-
forward, and all four Dashboard renderings). The runtime
dashboard harness still reports 0 failed assertions.

## Task 4 — T1-1 + T1-2 (Low)

DONE, both in the Debian phase of `onionhost-update`:
- **T1-1**: the untimed install call now runs
  `--no-download` (it installs only from the completed
  download phase), and when the timed download phase
  returns non-zero the install is SKIPPED entirely — the
  phase result is the download's own result (`rc = dl`,
  which also feeds T3-1's `debian_ok`). The old log line
  said the install "re-fetches what it needs"; the new
  comment block records why that shape is closed.
- **T1-2**: new `_purge_superseded_kernels()`, called
  after a successful install phase: it purges every
  installed versioned `linux-image-*` except the running
  kernel's package and the newest installed. Log-only by
  design — a listing or purge failure is recorded and
  changes nothing else (in particular not `debian_ok`).
Harness `poc/scripts/t1-followups-test.py`: 11/11 PASS
(call shapes; purge victim selection in three staged
package sets incl. running≠newest; untimed purge; both
failure modes absorbed). The T3-1 harness (15/15) and
the T3 reboot-state suite (FAILURES: 0) still pass with
the restructured phase.

## Out of scope, recorded so it is not lost

- Auditor §2, T1 out-of-scope note (T2 surface, PARKED, not
  fixed here): the managed platform install
  (`onionhost-update`, the `apt-get install` call for MANAGED
  packages) still runs under `timeout=1800` with its download
  inside the same timed call — the same kill-mid-dpkg shape T1
  fixed for the Debian phase. Also, a download-phase timeout
  in that path raises an uncaught `TimeoutExpired` (traceback;
  holds are left until the next run unholds them).
- Auditor §3 seventh-site sweep (S7-a..f) and T3-2/T3-3: not
  in this batch's brief (they belong to the fuzz batch's
  follow-on). Noted here only to say they were seen and are
  NOT silently dropped; they are outside this batch.

## Gates (final, at branch tip 4420085 + this report)

Each suite reported separately, as run:

- **Auditor's T8 demos**: t8b_copytree_demo — CLEAN at tip
  (only the valid file copies; reproduced dirty at base).
  t8b_mode_exceptions_demo — CLEAN at tip (host file 0600
  before and after; reproduced dirty at base).
  t8a_appdata_perm_demo — CANNOT RUN in this sandbox
  (chown to the production uid base raises EINVAL in the
  sandbox user namespace — true at base and tip alike);
  T8-A rests on the code-reading evidence and the harness
  below. Rig legs remain **rig-pending** (auditor's list):
  SQL-seeded install → write → restart twice → write
  survives; restore → write → restart → survives; fresh
  native+postgres install starts; in-container rm/mv at
  the appdata root still fail while import delete works.
- **Batch harnesses**: t8-rework-test.py (T8-A 20 + T8-B
  17) ALL PASSED; t3-debian-status-test.py 15/15;
  t1-followups-test.py 11/11. Positive controls: the T8-B
  section FAILs 8 ways on the pre-fix tree; the auditor's
  write_status_equivalence.py reports the new
  write_status byte-identical to base in all 4 cases.
- **ci-scan**: FAIL — 2 findings, both pre-existing
  ISO-BUILD-LOG.md hits at the branch base (identical at
  d05b713; they vanish in the merged tree per the parent
  branch's verification). Zero findings in any file this
  batch touched.
- **runtime-gate suite**: 68 assertions, 0 failed.
  Runtime dashboard harness: 0 failed.
- **backup-proof**: ALL 27 CHECKS PASS.
- **T3 suite** (t3-reboot-state-test.py): FAILURES: 0.
- **recipe-extract suite**: 2 assertions failed —
  IDENTICAL failures at the unmodified base d05b713. The
  suite exists only on main (written against main's newer
  tool versions); it was staged into this tree temporarily
  for the run and removed. Not a regression of this batch.
- **images-delivery suite**: 18 assertions failed —
  IDENTICAL failures at the unmodified base, same staging
  note as recipe-extract. Not a regression of this batch.
- **installer-policy**: PASS (0 assertions failed) at tip
  AND at base in clean runs. (An earlier "fails at base"
  note traced to disk pressure — the suite's venues are
  large and /tmp here is a 512M tmpfs; recorded so the
  correction is on the record.)
- **recipes-marketplace**: FAILS at tip and IDENTICALLY
  at base — its fixture .deb extraction errors before any
  code under test runs (pre-existing fixture failure in
  this environment; not claimed as a pass).

Nothing was pushed or merged. This branch is the fix
path for the auditor's DO NOT MERGE verdict on 3accd51;
closure is the auditor's re-verification, not this
report.

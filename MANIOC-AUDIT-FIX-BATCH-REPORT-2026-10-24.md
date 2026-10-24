# Manioc external-audit fix batch — report (2026-10-24)

**Pin / branch.** `main` @ `1d0d86c`; work on branch
`audit-fix-batch-2026-10-24` (local only, not pushed). Brief:
`MANIOC-AUDIT-FIX-BRIEF-2026-10-23.md`. Audit:
`~/workspace/user/files/Manioc_Server_code_audit___main___1d0d86c_1_r922.md`.

**Scope executed.** The unambiguous scope only: B0, R1, T1, T3, T8, R2.
T5 (Fork A), T7 (Fork B), T18 (Cameron's hardware-token step) and the
brief's §6 list were not touched.

## Rig access — BLOCKED (evidenced)

Every rig item (B0 guest captures, R1, R2, and the rig-side acceptance
checks for T1/T3/T8) needs SSH to `rig@34.185.89.126`. In this session
raw SSH egress is denied by the sandbox harness on every attempt
(four attempts, 2026-10-24): the connection is reset by the egress
proxy (`198.19.0.1:3128`) and each attempt is flagged
`backgroundEgressRestrictions: read_only_preparation`. Proxied HTTPS
egress works; direct TCP does not. Rig items are therefore recorded
below as **not run — blocked**, never as passed. The code tasks were
verified locally as far as the sandbox allows (harnesses below), and
their rig acceptance checks remain outstanding.

## B0 — baseline

Local/tree half, captured before any edit:

- HEAD `1d0d86c` on `main`; tracked tree clean; untracked files are
  the known brief/audit/run-record documents only.
- H4 mechanism reproduced locally at baseline (positive control):
  the pre-fix `onionhost-app-provision` (git HEAD version), run
  against a staged appdata whose `www` is a symlink to a root-owned
  canary directory, **chowned the canary to the www mapping**
  (canary owner became the container www uid/gid) — i.e. host root
  followed the app-planted symlink exactly as the audit describes.
  Harness: `/tmp/t8/harness.py` (control section), all control
  checks PASS.
- Tree-side baseline facts (from the 2026-10-23 spot-verification,
  re-confirmed in this session's reads): `onionhost-import-images`
  imports once behind `/var/lib/onionhost/.images-imported`;
  `onionhost-update` runs a single `apt-get -y upgrade`
  (Debian phase, timeout 3600) with no `--with-new-pkgs`; nothing in
  the tree reads `/run/reboot-required`; firstrun writes the
  `%sudo` NOPASSWD helper rule and nothing removes the install user
  from `sudo`.

Guest half (kept-back `apt-get -s upgrade` list, `podman images` +
import no-op re-run, install-user `id`/`sudo -l`, clean publish on
`manioc-proof`): **not run — rig blocked (above).**

## R1 — gofer symlink question (report-only)

**Not run — rig blocked.** Whether gVisor's gofer lets the app plant
the H4 symlinks from inside the container remains undetermined in
this batch. T8 was implemented and accepted on the assumption the
audit directs: if the app cannot plant the symlink, T8 stands as
defence-in-depth and its acceptance test plants the symlink
host-side (which is exactly what the local harness does).

## R2 — M5 vs the published ISO (report-only)

**Not run — rig blocked.** The `$WORK` stamps and image-tarball
hash comparison against snapshot `20261023T142942Z` requires rig
access. No verdict (clean / stale / indeterminable) can be stated;
the question stays open and flagged — it is NOT resolved by this
batch.

## T8 — Host root stops following app-planted symlinks (H4)

**Code changes** (one commit, task ID in message):

- `onionhost-app-provision`: new `_dir_fd()` (O_RDONLY |
  O_DIRECTORY | O_NOFOLLOW). appdata is now fchown'ed to host
  root (0:0, 0755) — the migration lands at first publish on
  pre-fix boxes; www/db/native are opened by descriptor and
  fchown/fchmod'ed; the owner ACL grant takes the descriptor
  (`os.fstat` + `os.setxattr(fd, …)`); the L1 healer traverses
  with `os.fwalk(follow_symlinks=False)` and fchown's the
  yielded dirfd. `main()` catches OSError and fails the publish
  closed with the reason logged. The only remaining path-based
  chown/chmod is `_atomic_write`'s tmp file in platform-owned
  directories (created by root itself; not audit-flagged).
- `onionhost-recipe`: same `_dir_fd()` helper; `_own_www_root`
  and `_own_native_root` assert via fchown/fchmod on the
  descriptor; `_grant_owner_acl` opens O_NOFOLLOW and works
  through the fd; `_own_data_dirs` refuses a symlinked data
  directory (raises, aborting the apply) and asserts via
  `os.fwalk`. `_chown_tree` already used `lchown` and is
  unchanged.
- `onionhost-generate-configs`: the `chmod 0700` on
  `/var/lib/onionhost/tor{,/hs,/data}` (inside container A's own
  tree — the audit's :37) is replaced by a descriptor block
  (O_NOFOLLOW open + fchmod, refusing non-directories, exit 1);
  freshly created `appdata` is now born host-root owned (0:0)
  instead of container-owned (db/www/native creation unchanged).
  Observed, not changed (outside the flagged lines): the
  `chmod 0700` on `/var/lib/onionhost/client{,/data}` is the same
  pattern inside container U's tree — follow-up candidate.

**Local acceptance evidence** (harness `/tmp/t8/harness.py`,
16/16 PASS; id base lowered to 10000 because the sandbox
filesystem rejects uid 2300000 — mechanism identical):

- Positive control (pre-fix code): canary chowned through the
  symlink — bug reproduced (see B0).
- Fixed provision, legitimate tree with appdata pre-owned by the
  container root (pre-fix state): succeeds; appdata migrated to
  (0,0) 0755; www (www-mapping, 02775); db (container root, 0750).
- Fixed provision, `www` symlinked to a root-owned canary:
  raises OSError (refusal); canary owner/mode/content untouched.
- Recipe: `_own_www_root` on a symlink refuses, canary untouched;
  on a real dir it asserts (www-mapping, 02775); `_own_data_dirs`
  asserts a real data dir via fwalk and aborts (ValueError) on a
  symlinked one, canary untouched.
- generate-configs tor block, extracted and run against a staged
  tree: asserts 0700 on tor/hs/data; with `hs` replaced by a
  symlink to a canary it exits 1 and the canary keeps mode 0755.

**Rig acceptance (outstanding — rig blocked):** the audit's
canary publish on a guest, planted per R1, and the pre-fix-box
first-publish migration check on a guest, have not run.

## T1 — Kernel updates actually install (H2, Debian phase)

**Code change** (one commit, task ID in message):
`onionhost-update`'s Debian phase now runs the upgrade in two
calls: `apt-get --download-only -y --with-new-pkgs upgrade`
under the existing 3600 s timeout (a killed download is safe),
then the same install with `timeout=None` — `run()` passes the
value straight to `subprocess.run`, so the install call cannot
receive a kill. `--with-new-pkgs` admits new package names
(kernel ABI packages behind `linux-image-amd64`) and never
removes. Floor logic and the HELD set across the phase are
unchanged. The T2 surface was not touched: `run()`'s
TimeoutExpired behaviour, start-of-run `dpkg --configure -a`
and `DPkg::Lock::Timeout` remain exactly as they were (the
split landed without needing any of them).

**Local evidence:** `py_compile` clean; the two new call sites
are the only `upgrade` invocations in the file. A mechanism demo
on the sandbox's own apt was inconclusive (the sandbox has no
pending upgrades and no kept-back packages), recorded as such —
the flag's semantics are standard apt behaviour, but this batch
does not claim the demo as evidence.

**Rig acceptance (outstanding — rig blocked):** on a guest with
a pending kernel ABI bump, one `onionhost-update` run installs
the new `linux-image-*` (`dpkg -l` before/after). Not run.

## T3 — Restart state and check age reach the owner (H2, M3)

**Code changes** (one commit, task ID in message):

- `onionhost-update`: `write_status` now records in status.json
  `reboot_required`, `reboot_reason` (from `/run/reboot-required`
  and its `.pkgs` sibling, contents named; plus a needrestart
  KCUR/KEXP mismatch when needrestart exists) and
  `reboot_required_since` (first recorded observation, carried
  across runs), and maintains `last_successful_check`, which
  advances only on runs whose repository check succeeded
  (`CHECK_SUCCEEDED`, set by main() after the project-repo
  check passes) — a fetch-failed run leaves the previous stamp
  standing, which is the M3 fix. The reboot path is
  env-overridable (`ONIONHOST_REBOOT_REQUIRED`) like the other
  test-venue paths.
- `wizard.py`: the Dashboard's up-to-date line carries the
  check's age ("last checked today / 1 day ago / N days ago",
  from `last_successful_check`, falling back to `checked_at`
  for pre-T3 status files), and a new `reboot_status_text()`
  restart card (own label, refreshed with the other status
  lines) shows the pending restart and its waiting age, silent
  when nothing is pending and silenced by the fail-closed
  marker. **No escalation colours or thresholds** — owner
  question 4 stays parked, as the brief directs.

**Local acceptance evidence** (harness `/tmp/t3/harness.py`,
16/16 PASS): updater field lifecycle (no-success leaves the
stamp null; success stamps it; a later failed check does not
refresh it; reboot appears with the requesting package named
in the reason; `reboot_required_since` is stamped once and
carried, then cleared with the flag) and wizard rendering
(stale check shows "last checked 9 days ago"; fresh says
"today"; restart card shows "waiting 3 days"; no card when no
reboot is pending; marker silences the card).

**Rig acceptance (outstanding — rig blocked):** with a kernel
update pending reboot on a guest, status.json says a restart
is needed and the Dashboard shows the card and the check's
age. Not run.

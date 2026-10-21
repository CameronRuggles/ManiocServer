# Backup / Restore — acceptance checklist for the next build (2026-10-12)

Assembled from the settled design record before the backup/restore build
starts (announced in chat 2026-10-12 as "the last piece Stage 2 needs",
after the encryption-guard fix build). Nothing here is new design — every
item cites its source. One genuinely open decision is flagged at the end.

Sources:
- DESIGN-v1.md §8 (backup contents, same-address restore, wizard copy)
- DESIGN-v3-amendments.md A3 (age derivation, spare recipient, revocation
  honesty — the spare provisions since removed by A25) and A12 point 4
  (manifest extensible to DB dumps / app data)
- WALKTHROUGH-SPEC-v1.md C3/C4 (create/restore UX, Maintenance-only restore)
- STAGE2-RUNBOOK.md step 8 (the real-hardware lifecycle drill)
- Demo run 2026-10-12: Dashboard "Back up" button exists but is not wired

## Create — must pass

1. **No phrase to create.** Backup export works from a normal session
   with no phrase prompt (A3). If a phrase is requested at create time,
   the build fails this item.
2. **Encrypted to the right recipients.** Archive is `age`-encrypted to
   the install-derived recipient (argon2id over the disk phrase +
   per-install salt, derived at install). If a spare key exists, the
   archive is encrypted to BOTH recipients (A3).
   **Status (2026-10-20):** the spare clause is moot — A25 removed the
   spare feature; the archive is encrypted to the main recipient only,
   which is what the shipped code does.
3. **Contents complete.** Archive contains: site content, DB dump,
   onion key, config (DESIGN-v1 §8). Manifest format must not assume
   "files only" — extensible to DB dumps and app data (A12.4).
4. **Salt travels with the backup.** The per-install salt is in the
   backup's plain metadata, so backup file + phrase alone are sufficient
   to restore on a fresh install (A3). Test: restore machine has never
   seen the original install's stored salt.
5. **Useless to a holder.** A backup file copied elsewhere cannot be
   opened without the phrase (verify by attempting decryption with no /
   wrong phrase — must fail cleanly, no partial plaintext).
6. **Dashboard wiring.** The Dashboard "Back up" button (present but
   unwired in the 2026-10-12 demo) actually produces the archive, with
   plain success/failure wording. Copy includes: "This backup IS your
   website. Guard it like the Recovery Sheet." (DESIGN-v1 §8) and
   "Don't keep the backup stick in the same drawer as the paper."
   (WALKTHROUGH C3).

## Restore — must pass

7. **Maintenance only.** Restore is offered only in Maintenance
   (pre-login, after LUKS unlock, no site services, no networking),
   with the phrase typed at a console (WALKTHROUGH C3/C4). No restore
   path from a normal Dashboard session.
8. **Same .onion address.** Fresh install from the same USB + restore
   brings back the SAME .onion address (DESIGN-v1 §8; STAGE2-RUNBOOK
   step 8). Verify from outside over Tor, not just locally.
9. **Content identical.** After restore, the site serves the entries as
   they were at backup time (retitle + published entry from the demo
   are the natural test fixture), and the health probe reports up.
10. **Wrong phrase fails safe.** Wrong phrase at restore: clear words,
    no partial restore, system left in Maintenance, retry possible.
11. **Restore is logged.** The restore event appears in the Dashboard
    log, as every Maintenance use must (WALKTHROUGH C4).

## Revocation honesty — must pass

12. **Spare revocation copy is honest.** After a spare is revoked, the
    Dashboard wording states that backups made BEFORE revocation still
    open with the old spare phrase, and that "Change the lock
    completely" (cryptsetup reencrypt) is the only true revocation
    (A3 / WALKTHROUGH C4). No copy may imply revocation reaches old
    backups.

    **Status note (2026-10-20):** item 12 is MOOT — the spare feature
    itself was removed by owner decision the same day (DESIGN-v3 A25):
    there is no spare, no spare LUKS slot, and no spare backup
    recipient, so there is nothing to revoke and no revocation copy to
    keep honest. The item is retained as the honesty spec any future
    second-key design must satisfy before it ships.

## Stage 2 drill integration

13. Items 1–11 are proven in QEMU/rig first; item 8 is re-proven on
    real hardware as STAGE2-RUNBOOK step 8 (backup → wipe → reinstall
    from the same USB → restore → same address). Stage 2 is not
    complete until step 8 passes on Cameron's spare machine.

## OPEN DECISION — needs Cameron's call before the build hardens

**Backup-destination setup: required wizard step, or strong
first-Dashboard prompt?** WALKTHROUGH-SPEC-v1 C3 and §6 item 2 record
this as raised 2026-10-11 and still unresolved in any design file.
The backup build has to pick one: a required step guarantees every
install has a destination chosen before the first backup matters; a
Dashboard prompt keeps the wizard shorter but risks backups never
being set up. This is the only backup/restore question the design
record leaves open.

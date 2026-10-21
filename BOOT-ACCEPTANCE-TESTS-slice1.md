# Boot acceptance tests — step-3 slice 1 ISO (A19.1 boot path)

Prepared 2026-10-11 (Sun evening) for the next QEMU tranche on the rig.
Scope: the slice-1 build now in the tree — `onionhostbootkey` Calamares
module (converts the phrase slot to PBKDF2-only, relocates the keyfile to
`/etc/cryptsetup-keys.d/root.key`, dir 0700 / file 0400, UMASK=0077),
`onionhostcleanup` (strips live-session scaffolding), the A18
`--disable-keyring` initramfs hook, containers A/B/U + nft gate.
Design basis: DESIGN-v3-amendments A19 as superseded by A19.1 (three-slot
layout, argon2id dropped entirely). The previous ISO proved live boot,
clean install (40/40 jobs), and reboot *to* the GRUB LUKS prompt — and
failed at the prompt (argon2id). These tests start from there; don't
re-run the old (a)/(b)/(c) as if they were the bar. The bar is booting
*past* the prompt.

## Boot path (the release gate for this tranche)

1. **Slot layout.** Clean install, then `cryptsetup luksDump` on the
   installed volume: NO argon2id passphrase slot remains; the phrase slot
   is PBKDF2 (SHA256) with the iteration count the module set; the keyfile
   slot is present. Expected at this slice: exactly 2 slots (phrase +
   keyfile) — SPARE does not exist in the installer yet (see Deferred).
   Record the slot-role map in the build log.
2. **Full boot, one prompt.** Reboot the installed qcow2 with no ISO:
   GRUB prompt → correct phrase → system boots all the way to the login
   screen, phrase typed exactly ONCE (initramfs must open via the
   keyfile, no second prompt). Measure GRUB unlock time and record it
   (A19: benchmark against the actual signed GRUB, not cryptsetup).
3. **Wrong phrase.** At GRUB, a wrong phrase is rejected and a retry with
   the correct phrase still boots (no lockout corruption, no scary
   fall-through from an unsupported slot — there should be no unsupported
   slot left to hit).
4. **Keyfile hygiene on the installed system.**
   - `/etc/cryptsetup-keys.d/` is 0700, `root.key` is 0400 root:root.
   - crypttab references that exact file (and its slot explicitly).
   - The generated initramfs image is 0600 and lives only on the
     encrypted /boot; mount the ESP and confirm no credential-bearing
     file (initramfs, keyfile, .old images) is on it or any plaintext
     partition.
   - `update-initramfs -u` on the installed system keeps the image 0600
     and on encrypted storage (the A19 update invariant, as a hard check).
5. **The ISO contains no keyfile.** Search the built ISO/squashfs for
   `cryptsetup-keys.d` / `root.key` material: none. Then install twice
   into two qcow2s and confirm the two keyfiles differ (per-install
   CSPRNG generation, A19.1 release gate).
6. **No secrets in logs.** On the installed system, grep the Calamares
   log and all of /var/log for the install passphrase and for keyfile
   bytes (hex/base64 fragments): zero hits. (A19.1: logs scrubbed *and
   verified*, not assumed.)
7. **A18 in the initramfs-created mapping.** On the booted installed
   system, `dmsetup table --showkeys` for the root mapping shows the raw
   key (keyring disabled) — proving the zz-onionhost-cryptsetup hook
   took effect in early userspace, not just as a running-system setting
   (A19: a later setting does not retroactively change how the initramfs
   opened it).

## Scaffolding strip (ISO-BUILD-LOG blocker #2, `onionhostcleanup`)

8. Installed system has: no live user, no LightDM autologin drop-in, no
   sshd test drop-in or baked authorized_keys, no xdotool. First boot is
   the stock target state, not the live session.
9. Sleep/suspend/hibernate targets masked; no unencrypted swap in
   crypttab/fstab (A19.1: unencrypted swap can page out the keyfile,
   volume key, or phrase; kdump off or encrypted-target-only — check
   whichever the build claims).

## Slice-1 smoke (containers + gate; full gates were proven on the rig)

10. A/B/U Quadlet units start on the installed system; B reports no
    network (probe), A speaks Tor only, the http.sock symlink-swap works.
11. nft gate negative test: hand-edit one live nft rule → gate comparison
    fails → Tor refuses to start (fail closed, never open).

## Explicitly deferred (do NOT mark these failed — they aren't built yet)

- SPARE phrase boot/revoke tests — MOOT since 2026-10-20: the spare
  feature was removed entirely (DESIGN-v3 A25). There is no spare
  slot and no spare boot path; nothing exists to test.
- Entropy-source audit (getrandom blocking, full 7776-word list, no
  modulo bias) — release gate for the phrase-generator module, not this
  slice.
- Maintenance re-key transaction tests (add → test → kill → regen →
  real-GRUB boot before "done") — Maintenance mode isn't built yet.
- Keyfile rotation procedure test — its own tested path, lands with
  Maintenance.

## Explainer accuracy note

EXPLAINER.md §7 currently says the skeleton ISO "builds and installs
end-to-end." Until test 2 above passes, that is ahead of the record
(install completes; boot past GRUB is exactly what's being fixed).
Suggested replacement once test 2 is run, whichever way it lands:
- Pass: keep the sentence, add "and boots through its encrypted /boot
  with one phrase entry (PBKDF2 slot per A19.1)".
- Not yet: "a skeleton installer ISO builds and installs; the boot-chain
  fix (PBKDF2-only phrase slots, A19.1) is in the tree and under test."
The project's own rule applies: if the explainer and the design record
disagree, the design record wins.

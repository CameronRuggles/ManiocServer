# Rig battery defect — regression-proof checklist (2026-10-14)

Prepared 2026-10-14 (background research) from the battery's own draft
log: `battery-rig-evidence/BATTERY-LOG-DRAFT.md` (Part 2, "DEFECT
FOUND"). The battery was still running when this was written (install
retry screenshots in `battery-rig-evidence/gprod-shots/` timestamped
after the log draft). This checklist exists so the proof the log itself
says is owed cannot get lost between battery passes. Nothing here
publishes or changes anything.

## The defect, in one paragraph

Battery build #2 installs cleanly but the installed system does not
boot: GRUB accepts the disk phrase, then initramfs loops —
`cat: /etc/cryptsetup-keys.d/root.key: No such file or directory`. Root
cause traced in the log: `build-onionhost-deb.sh` flattened every staged
file to mode 644 and restored 755 only for `usr/local/bin/*` and
`usr/lib/apt/methods/*`. The two initramfs hooks
(`zz-onionhost-cryptsetup`, the A18 --disable-keyring wrapper, and
`zz-onionhost-keyfile`, the keyfile embedder) shipped at 644 in every
platform .deb built since Gate 4; `update-initramfs` silently skips
non-executable hooks. The battery's new firstrun factory-install wrote
the 644 hooks over the image's 755 ones before Calamares built the
initramfs — keyfile-less initramfs, unbootable install.

## Blast radius (per the log's own audit — re-verify before quoting)

- The two hooks are the ONLY executables outside the two restored
  directories; recipe .debs flatten only data payloads (correct at 644).
- Latent, worse path: any machine taking a platform update via the
  Gate 4 channel gets 644 hooks on disk. The running initramfs is
  unaffected, but the NEXT initramfs rebuild (e.g. a routine Debian
  kernel security update) silently produces a keyfile-less initramfs
  without the A18 wrapper — bricked box + silent loss of A18. Gate 4's
  proof never rebuilt an initramfs after an update, so it passed.
- No field machines have taken a platform update — the update repo has
  only ever served proof rigs — so no user machine is affected.

## Public download is NOT the defective build — verified 2026-10-14

Checked the live page at vespiary.org/onionhost/ on 2026-10-14
(~17:30 UTC, background run):

- Page offers: 1,146,880,000 bytes,
  SHA-256 `080e45ac048e9999d2de57f199d5411c53a442f4a7a7daaa49a92c0e4cb2b1c1`
  — the existing prod rebuild 2.
- Defective battery build #2: 1,361,817,600 bytes,
  SHA-256 `0b4df12c3aa24a2cb31a6f225c08039b6ba8511716420e0555d597af096bd786`
  — different file, and the log states it was never published.

So testers downloading today get the older, bootable alpha. Do not
update the page's size/hash until a post-fix build passes every proof
below.

## Fix as logged (verify in the tree, don't take this sheet's word)

- `build-onionhost-deb.sh`: after the 644 flatten, restore +x for every
  staged file whose source-overlay counterpart carries any execute bit
  (derived from the source tree, not a hardcoded list).
- New build-time MODE GUARD: the build fails if any source-executable
  would ship non-executable.
- Log reports sandbox verification: hooks now ship 755 in the .deb,
  data files stay 644, binaries stay 755.

## Regression proofs owed before any new ISO is published

The log names the core proof ("Post-fix regression proof owed, added to
Part 3"); expanded here into a checkable list:

- [ ] Fresh build with the fix; mode guard demonstrably trips on a
      deliberately flattened executable (negative test), passes clean
      on the real tree.
- [ ] Fresh UEFI install from that build boots: phrase typed once,
      root keyfile present in the initramfs
      (`etc/cryptsetup-keys.d/root.key`), no cryptsetup loop.
- [ ] Real v1 → v2 platform update over Tor (Gate 4 channel), then in
      the guest: `update-initramfs -u`, and verify the REBUILT
      initramfs still contains `etc/cryptsetup-keys.d/root.key` and
      the executable A18 wrapper hook.
- [ ] Reboot after that rebuild: machine comes back with the phrase
      typed once.
- [ ] Both hooks on disk are 755 after the update (not just inside the
      initramfs).
- [ ] Shipped apt lockdown untouched (Gate 4's tor-only update config
      intact in the new rootfs) and the build-time apt override from
      Bug A has not leaked into the shipped image.
- [ ] Only after all of the above: publish, updating the download
      page's byte count + SHA-256 together, and append the completed
      battery log to ISO-BUILD-LOG.md.

## Standing constraint reminder

All rig work at ordinary load only — the GCP appeal commitment (no
CPU-saturating benchmarks on GCP; load testing on own hardware) binds
this battery and any re-run of these proofs.

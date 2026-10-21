# OnionHost OS — First ISO Build Plan (alpha pipeline)
## Prepared 2026-10-11 while Stage 1 rig gates run. Execute on the rig once Gate R + Podman verdicts land (Gate R decides wizard recovery copy; A5 data clause decides rootful/rootless defaults baked into the image).

## Pipeline choice
- **live-build is deprecated-ish on Debian 13; use a scripted debootstrap/mmdebstrap + squashfs + xorriso pipeline** (the reproducible-builds-friendly route per A14): mmdebstrap (trixie, signed snapshot) → chroot customisation → mksquashfs (deterministic: fixed timestamps from SOURCE_DATE_EPOCH, sorted) → xorriso ISO with isohybrid. Build script lives in repo as `build/build-iso.sh`; every step logged.
- Target: amd64, UEFI + legacy boot (test UEFI first on rig's QEMU/OVMF), Secure Boot via Debian's signed shim/grub packages (do NOT self-sign for alpha).

## Image contents (from DESIGN-v2 + v3 amendments)
- Debian 13 base, kernel from snapshot, chrony (NTS), nftables golden table units, Podman + Quadlet units for containers A (tor) / B (web) / U (client tor), runsc (official binary, pinned + sha512), tor from Tor Project repo (pinned), nginx + headers-more from Debian.
- Calamares with OnionHost modules: welcome/claim page (A10 narrowed claim + A17 disclosure paragraph), disk+LUKS (generated 7-word phrase flow), locale/keyboard (incl. layout test field), summary, install; post-install first-boot wizard service (autologin state machine S0→S1→S2 per A16/Y16 in v3 amendments).
- Golden configs generated at install time (torrc, nft golden table, container units) by the `onionhost` package's installer helpers — nothing hand-placed in the image that the golden-config gate can't regenerate.
- Desktop: minimal (XFCE or GNOME — DECISION PENDING, default XFCE for hardware floor), LightDM, native GTK dashboard stub (status cards only for alpha).

## Build order
1. Skeleton ISO that boots live + installs vanilla Debian via Calamares on rig QEMU (proves pipeline + nested-virt speed).
2. Add LUKS-mandatory Calamares config + phrase module (stub generator OK for first pass).
3. Add onionhost package: containers, golden configs, firewall gate, first-boot service.
4. Snapshot-test installs in QEMU on the rig: fresh install → reboot → unlock → wizard stub → Go-Live stub → onion reachable from outside (fetch via tor on Muse's VM).
5. Only then: Stage 2 USB on Cameron's hardware.

## Alpha test list additions (from TEST-PLAN)
- Power-pull at each autologin state (S0/S1/S2) — state machine must resume safely.
- Initramfs keymap on AZERTY/QWERTZ layouts (QEMU keymap injection is partial — flag for Stage 2 real hardware).
- Calamares logs/globalstorage leak sweep for the phrase.
- Phrase never in swap/journal: image ships with encrypted swap inside LUKS only.

## Reproducibility (A14)
- All packages pinned to one snapshot.debian.org timestamp, recorded in the ISO's `/etc/onionhost-build-info` (snapshot ts, git commit, SOURCE_DATE_EPOCH). Two clean builds must hash-match before any ISO leaves the project.

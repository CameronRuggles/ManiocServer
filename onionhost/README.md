# onionhost — step 3 package skeleton (source tree)

This directory is the source for everything the ISO build adds on top
of the Debian skeleton for step 3 slice 1. It is overlaid into the
image rootfs by `build/build-iso.sh` (phase B2).

## Layout
- `rootfs-overlay/` — files copied verbatim into the image root:
  - `etc/containers/systemd/*.container` — Quadlet units for
    containers A (Tor gateway), B (website, no network), U (client
    Tor). Rootful Podman, `PodmanArgs=--runtime=runsc-wrap`,
    `UserNS=auto`, explicit `Network=` in every unit (DESIGN-v3 A5).
  - `etc/containers/containers.conf` — registers the `runsc-wrap`
    runtime (A18: podman runtime entries take no arguments).
  - `usr/local/bin/runsc-wrap` — podman→runsc wrapper: always injects
    `--host-uds=all`; strips the bundle netns entry and selects
    `--network=host` (tor) / `--network=none` (nginx) per A18.
  - `usr/local/bin/onionhost-generate-configs` + `onionhost-config.service`
    — renders golden templates from `usr/lib/onionhost/golden/` into
    `/etc/onionhost/` at boot and maintains the `http.sock` symlink.
  - `usr/local/bin/onionhost-nft-gate` + `onionhost-nft-compare.py` +
    `onionhost-nft-load.service` / `onionhost-nft-gate.service` /
    `.timer` — the A8 firewall gate (scratch-netns golden load,
    canonical-JSON comparison, same nft binary both sides).
  - `usr/local/bin/onionhost-import-images` + `onionhost-images.service`
    — one-shot `podman import` of the locally built image tarballs in
    `usr/lib/onionhost/images/` (populated by the ISO build; A6).
  - Slice 6B (dynamic tier): `etc/containers/systemd/onionhost-app.container`
    — the combined app container (nginx + PHP-FPM or a native program
    + MariaDB in one gVisor sandbox, no network), selected over
    `onionhost-b.container` by the `/var/lib/onionhost/app-site`
    marker via Quadlet conditions. Its configs render from
    `usr/lib/onionhost/golden/` (`nginx-app-*.conf.tmpl`,
    `php-fpm-app.conf.tmpl`, `my-app.cnf.tmpl`, `app-init.sh`) via
    `onionhost-generate-configs`; `onionhost-app-provision` creates
    the app-data volume + per-install DB credentials;
    `onionhost-appdata-guard` (+ timer) enforces the volume quota.
    The owner contract is `APP-SITES.md`; backups (format 2) carry
    the app files + a MariaDB dump (see `onionhost-backup`).
  - `etc/initramfs-tools/hooks/zz-onionhost-cryptsetup` — initramfs
    hook implementing the A18 `--disable-keyring` ruling by wrapping
    the cryptsetup binary inside the initramfs only (trixie's
    cryptroot exposes no option for it; see the hook's header).
  - `etc/tmpfiles.d/onionhost.conf`, `var/lib/onionhost/site/` —
    runtime dirs and the placeholder site.
  - Sleep/suspend/hibernate are masked by the build script
    (`systemctl mask` in the chroot), per DESIGN-v2.
- `calamares/modules/` — python jobmodules copied to
  `/etc/calamares/modules/` and wired into `settings.conf` by the
  build:
  - `onionhostbootkey` (after `luksbootkeyfile`) — boot credentials
    per DESIGN-v3 A19.1: relocates the Calamares keyfile into
    `/etc/cryptsetup-keys.d/root.key` (dir 0700, file 0400, crypttab
    updated, UMASK=0077) and CONVERTS the phrase slot to PBKDF2-only
    (adds PBKDF2-SHA256, verifies, kills the argon2id phrase slot) so
    GRUB 2.12 can unlock the encrypted /boot and no dual-KDF slot
    remains. Fails the install loudly if it cannot.
  - `onionhostcleanup` (before `initramfscfg`) — strips live-session
    scaffolding from the installed target (live user, autologin,
    sshd test access, xdotool).
  - `onionhostprobe` — diagnostics only; the build inserts it into the
    exec sequence only when `OH_PROBE=1`. Never ships in a release.

Wizard UI is explicitly out of scope for this slice.

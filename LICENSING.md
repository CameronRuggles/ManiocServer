# Licensing map — Manioc Server

Added 2026-10-20 (Repo Review 2, P8).

The project's own code is licensed **Apache 2.0**; see `LICENSE` at the
repository root. That is the default for files in this repository
**except** the files listed below, which carry their own licence.
A licence header or SPDX identifier in a file governs that file.

## GPL-3.0-or-later

These files carry an `SPDX-License-Identifier: GPL-3.0-or-later`
header:

### Calamares plugin sources

- `onionhost/calamares/plugin-src/onionhostphrase/OnionHostPhraseViewStep.cpp`
- `onionhost/calamares/plugin-src/onionhostphrase/OnionHostPhraseViewStep.h`
- `onionhost/calamares/plugin-src/onionhostguard/OnionHostGuardViewStep.cpp`
- `onionhost/calamares/plugin-src/onionhostguard/OnionHostGuardViewStep.h`

### Calamares job modules

- `onionhost/calamares/modules/onionhostfirstrun/main.py`
- `onionhost/calamares/modules/onionhostbackupkeys/main.py`
- `onionhost/calamares/modules/onionhostbootkey/main.py`
- `onionhost/calamares/modules/onionhostcleanup/main.py`
- `onionhost/calamares/modules/onionhostgrubstub/main.py`
- `onionhost/calamares/modules/onionhostprobe/main.py`

### Calamares patch

- `onionhost/calamares/patches/0001-onionhost-force-encryption.patch`
  — a patch to Calamares itself, and therefore a derivative of
  GPL-licensed Calamares code; treat it as GPL-3.0-or-later.

### Other files carrying the same SPDX header

- `onionhost/rootfs-overlay/usr/lib/onionhost/phrasegen.py`
- `onionhost/rootfs-overlay/usr/lib/onionhost/sitegen.py`
- `onionhost/rootfs-overlay/usr/lib/onionhost/backupkeys.py`
- `onionhost/rootfs-overlay/usr/lib/onionhost/wizard.py`
- `onionhost/rootfs-overlay/usr/local/bin/onionhost-app-provision`
- `onionhost/rootfs-overlay/usr/local/bin/onionhost-backup`
- `onionhost/rootfs-overlay/usr/local/bin/onionhost-grub-stub`
- `onionhost/rootfs-overlay/usr/local/bin/onionhost-maintenance`
- `onionhost/rootfs-overlay/usr/local/bin/onionhost-publish`
- `onionhost/rootfs-overlay/usr/local/bin/onionhost-rekey`
- `onionhost/rootfs-overlay/usr/local/bin/onionhost-restore`
- `onionhost/rootfs-overlay/usr/local/bin/onionhost-wizard-helper`

## EFF large wordlist — Creative Commons Attribution

- Path: `onionhost/rootfs-overlay/usr/share/onionhost/eff-large-wordlist.txt`
  (installed on the image as `usr/share/onionhost/eff-large-wordlist.txt`)
- This is the EFF large (Diceware) wordlist, published by the
  Electronic Frontier Foundation (EFF). Attribution: Electronic
  Frontier Foundation.
- Licence: Creative Commons Attribution, as stated on EFF's
  copyright policy page, <https://www.eff.org/copyright> — that
  page is the source for this attribution. The version is the
  one stated there (the policy page names CC BY 4.0 for EFF
  site content, while EFF's badge has linked CC BY 3.0 US);
  this record cites the policy page rather than asserting a
  single version for the wordlist itself.
- The wordlist file itself carries no licence header; this section
  is its attribution in this repository.

## WordPress must-use plugin — GPL-2.0-or-later

- Path:
  `onionhost/recipes/wordpress/files/wp-content/mu-plugins/onionhost-sealed.php`
- Licence: **GPL-2.0-or-later**, declared in the file's own header.
  It is distributed alongside WordPress, which is licensed
  GPL-2.0-or-later, and is licensed to match the WordPress it
  ships with.

## Marketplace media-worker — AGPL-3.0-or-later, source pointer

- The marketplace recipe declares its application, including the
  `media-worker` helper, as **AGPL-3.0-or-later**:
  see the `app.license` field in
  `onionhost/recipes/marketplace/recipe.json`.
- Source: the companion repository
  <https://github.com/CameronRuggles/polyculture-markets>
  (Polyculture Markets).
- For the exact source provenance of the shipped binary — the
  repository, the pinned commit, the toolchain and the build
  command — see the provenance fields in
  `onionhost/recipes/marketplace/recipe.json`. No commit hash is
  stated in this file; the recipe is the source of truth for it.

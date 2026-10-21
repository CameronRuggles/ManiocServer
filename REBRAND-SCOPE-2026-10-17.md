# Rebrand scope — "OnionHost" / "Vespiary Market" → Manioc Server / Polyculture Markets

Prepared 2026-10-17, the day the names were decided (see `NAMING-DECISION-SHEET-2026-10-16.md`, DECIDED section).

**This is an inventory and classification only. Nothing has been renamed.** The live site at vespiary.org/onionhost/ was not touched, and no server state was changed. Method: grep of both project trees (`~/workspace/onion-host-os/` and `~/workspace/monero-marketplace-v2/`) for `OnionHost`, `onionhost`, `Vespiary Market`, and `vespiary-market`, then hand-classification of the surfaces that matter. Dated evidence bundles, PoC drivers, and mutant-run logs also contain the strings; they are records, not surfaces, and are covered once at the end.

The names decided: the OS is **Manioc Server**; the marketplace software is **Polyculture Markets**. No domains are registered yet, so every public item below is gated on Cameron's registration step before it can fully land.

## (a) PUBLIC BRAND — adopt the new names

### OS — explainer/recruiting site and ISO download

- `site/index.html` — the source of the page live at vespiary.org/onionhost/: `<title>` (line 6, "OnionHost OS — host a website from home…"), the `<h1>` (line 13), and the working-title disclaimer (line 96: "OnionHost OS is a working title; the final name is still being chosen" — false the moment the rename lands, and the natural place the decision gets announced). Uploading the edited page is a separate, later step; this inventory does not touch the live page.
- ISO download filename — produced at `build/build-iso.sh:30` (`onionhost-amd64.iso` for the prod flavour, `onionhost-<flavour>-amd64.iso` otherwise); current artefacts: `releases/onionhost-amd64.iso`, `releases/onionhost-prod-amd64.iso`. The filename is what downloaders see and what the site links to, so it follows the pattern over (e.g. `maniocserver-amd64.iso`); the build-log entries and runbooks that quote the old URL (`ISO-BUILD-LOG.md`, `STAGE2-RUNBOOK.md`, `PROD-DOWNLOAD-GATE-2026-10-12.md`) are records — see the records note below.
- ISO volume label `ONIONHOST_LIVE` — `build/build-iso.sh:530` (the name a file manager shows for the USB stick). Cosmetic, per-ISO, no installed-system compatibility effect.

### OS — owner-facing product UI (ships inside the image)

- First-boot wizard and dashboard strings — `onionhost/rootfs-overlay/usr/lib/onionhost/wizard.py`: window titles "OnionHost Setup" (line 625) and "OnionHost" (line 1105), the welcome heading "Welcome to your OnionHost" (line 664), and body copy at lines 793, 796, 814, 974, 1209.
- Desktop entry display names — `onionhost/rootfs-overlay/etc/xdg/autostart/onionhost-dashboard.desktop` (`Name=OnionHost`) and `onionhost-wizard.desktop` (`Name=OnionHost Setup`). The `Name=` values only; the filenames are internal (class b).
- Default placeholder site page — `onionhost/rootfs-overlay/var/lib/onionhost/site/releases/0/index.html`: `<title>OnionHost</title>`, "This OnionHost site is running." This is the page a fresh owner's onion address serves, so it is public-facing.
- Installer page strings — the user-visible text in the three Calamares C++ view steps, `onionhost/calamares/plugin-src/onionhostphrase/`, `onionhostspare/`, and `onionhostguard/` (strings only; the class and factory names in the same files are internal, class b).

### Marketplace — display names

- OS recipe catalogue names — `onionhost/recipes/marketplace/recipe.json:7` (`"name": "Vespiary Market"`) and `:24` (`"Marketplace (Vespiary Market)"`): what the wizard's app list shows. Becomes the Polyculture Markets forms. The recipe's own doc section follows: `onionhost/APP-SITES.md:571–573`.
- Demo/deploy display values — `~/workspace/monero-marketplace-v2/marketplace/deploy/env.demo.template:20` (`SITE_NAME=Vespiary Market`) and `marketplace/deploy/marketplace-demo.service:2` (`Description=Vespiary Market — demo instance (stagenet)`). The running demo's header comes from these / the compiled default (class c).
- Ops doc default shown to operators — `~/workspace/monero-marketplace-v2/marketplace/docs/operations.md:23` (the `SITE_NAME` row). The `MARKETPLACE_ID` row on line 22 does **not** change (class b).

Note: OS-installed marketplace instances carry no "Vespiary Market" default to fix — the recipe renders `SITE_NAME` from the owner's wizard title (`onionhost/recipes/marketplace/seed/app.env.tmpl:26`). Any instance can likewise set `SITE_NAME` in its env today; the brand work is in the defaults and the catalogue, not in per-instance data.

### Living documents and unsent copy

Documents that describe the products in the present tense should adopt the new names when next edited (historical entries inside them stay as written): `EXPLAINER.md`, `OWNER-GUIDE-2026-10-15.md`, `onionhost/README.md`, `onionhost/APP-SITES.md`, `MAINTAINER-RUNBOOK-2026-10-15.md`, and the unsent drafts in `outreach/LAUNCH-POSTS-DRAFT-2026-10-12.md` (which also point at the vespiary.org/onionhost/ URL — see class c, item 2).

## (b) INTERNAL IDENTIFIER — keep stable

One reason covers the whole class: **installed machines already update by these names.** Package names, unit names, on-disk paths, and the signed update repository are the update contract between the platform and every machine in the field; renaming any of them breaks or orphans existing installs, and none of them is public-facing beyond log lines. "OnionHost" therefore survives indefinitely as the internal identifier, exactly as plenty of products keep a codename in their plumbing.

OS side:

- Debian packages: the platform package `onionhost` (`build/build-onionhost-deb.sh:59`) and the recipe packages `onionhost-recipe-<id>` — including `onionhost-recipe-marketplace` (`build/build-recipe-deb.sh:48`). These are what the Gate 4 signed repo serves and what installed machines have in their dpkg databases.
- Paths: everything under `/etc/onionhost/` (including the per-install credentials record `/etc/onionhost/app-db.env`), `/usr/lib/onionhost/`, and `/var/lib/onionhost/` — layout mirrored in `onionhost/rootfs-overlay/`.
- systemd and Quadlet names: `onionhost-*.service` / `.timer` / `.target` under `etc/systemd/system/`, and `onionhost-a.container`, `onionhost-b.container`, `onionhost-u.container`, `onionhost-app.container`, `onionhost.network` under `etc/containers/systemd/`.
- `ONIONHOST_*` environment variables throughout the golden tooling (e.g. `onionhost/rootfs-overlay/usr/lib/onionhost/golden/app-init.sh`: `ONIONHOST_RUNTIME`, `ONIONHOST_APP_SOCKET`, `ONIONHOST_APP_DB`, `ONIONHOST_OWNER_GID`).
- Calamares module names (`onionhostphrase`, `onionhostspare`, `onionhostguard`, `onionhostbootkey`, `onionhostcleanup`, `onionhostfirstrun`, `onionhostgrubstub`, `onionhostbackupkeys`, `onionhostprobe`) and the C++ plugin class/factory names (`OnionHostPhraseViewStep`, …).
- Plumbing filenames: `etc/tmpfiles.d/onionhost.conf`, `etc/initramfs-tools/hooks/zz-onionhost-*`, `etc/apt/apt.conf.d/52onionhost-tor-updates` and `99-onionhost-grub-stub`, `etc/chrony/sources.d/onionhost-nts.sources`, the `onionhost-*.desktop` filenames, and build tooling names (`build/build-onionhost-deb.sh`, `build/make-onionhost-repo.sh`).

Marketplace side:

- **`marketplace_id` = `vespiary-market` — do not rename.** It is a protocol constant that happens to spell a name. It is baked into the canonical signed-statement string sellers sign with their wallet keys (`xmr-direct-v1|vespiary-market|<network>|…` — `~/workspace/monero-marketplace-v2/marketplace/crates/app/src/payments.rs`, doc comment at line 40, format exercised at line 760), stored per batch in `payment_batches.marketplace_id`, and set as the config default at `crates/app/src/config.rs:156` (env `MARKETPLACE_ID`, `docs/operations.md:22`, `deploy/env.demo.template:19`). Renaming it would invalidate every signed pool statement sellers have already produced. It is additionally pinned verbatim by the locked blind suites (`marketplace/tests/security/blind_stage10.rs`, `blind_direct_v1.rs` — `PAY_MKT`), and the pre-mainnet sheet already carries the warning in its own words: "`vespiary-market` marketplace_id is baked into real payment messages" (`PRE-MAINNET-CONFIRMATION-SHEET.md:22`).

## (c) NEEDS CAMERON'S CALL

1. **The compiled-in `site_name` default, "Vespiary Market"** — `~/workspace/monero-marketplace-v2/marketplace/crates/app/src/config.rs:162`. It is the marketplace UI's header on any instance that doesn't set `SITE_NAME`, so it is a brand surface — but the string is pinned verbatim by the locked Stage 10 blind suite (A8, "brief default site name"), so changing it is a code change through the marketplace's own gate process, not a rename edit. Options: leave the default and let instances/config carry "Polyculture Markets", or schedule the default change with a gate run.
2. **The public URL.** The explainer page lives at vespiary.org/onionhost/. Moving it under maniocserver.org (once registered) — and whether the old URL redirects, stays as a mirror, or is retired — is Cameron's call, tied to the domain registration step that is also his.
3. **Repository and workspace names for the planned GitHub upload.** No public repo exists yet, so names there are cheap now and sticky later: name the repos for Manioc Server / Polyculture Markets from birth, or keep the working names? Same cosmetic question, lower stakes, for the local tree directories (`~/workspace/onion-host-os/`, `~/workspace/monero-marketplace-v2/`).
4. **The donations / first-follower page.** The chosen message ("I am just the shirtless guy, please join me") is personal. Whether its page is branded as Manioc Server / Polyculture Markets, or stays a personal Cameron page that points at both products, is a positioning call only Cameron can make.

## Records — leave as written

Dated logs, reports, briefs, and evidence keep the working names, because they record what things were called when the work was done: `ISO-BUILD-LOG.md`, the stage and recipe reports (`STAGE*-REPORT.md`, `DIRECT-PAYMENTS-V1-REPORT.md`, `RECIPE-MARKETPLACE-REPORT.md`, …), the design set (`DESIGN-v2.md`, `DESIGN-v3-amendments.md`, `SPEC-V2-AMENDMENTS.md`, `STAGE10-BRIEF.md`), the `*-evidence/` bundles, `poc/` drivers, and the `mutants.out/` / `mutants-stage10/` run logs. New entries written after the decision use the new names for the products and the old ones only where the internal identifiers (class b) are meant.

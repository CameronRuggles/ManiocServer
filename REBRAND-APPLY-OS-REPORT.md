# Rebrand applied — OS tree (Manioc Server / Polyculture Markets)

**Date:** 2026-10-17
**Scope:** Bucket (a) PUBLIC BRAND items for the OS tree only, per
`REBRAND-SCOPE-2026-10-17.md`. Tree files only — the live
vespiary.org site was not touched, nothing was published, no ISO
was built, and the next ISO publish still waits on the rig
regression checklist. The marketplace tree
(`~/workspace/monero-marketplace-v2/`) was not touched.
Build record: `ISO-BUILD-LOG.md`, section "PUBLIC REBRAND
APPLIED — MANIOC SERVER / POLYCULTURE MARKETS (2026-10-17)".

## Changed

### Explainer/recruiting site copy — `site/index.html`
- Line 6 `<title>`: "OnionHost OS — host a website from home…"
  → "Manioc Server — host a website from home…"
- Line 13 `<h1>`: "OnionHost OS" → "Manioc Server"
- Line 96 footer: the now-false disclaimer ("OnionHost OS is a
  working title; the final name is still being chosen") replaced
  with "Manioc Server — developed under the working title
  OnionHost OS." The rest of the sentence (alpha test build, not
  a finished public release) is unchanged.
- Lines 53/55 (same pass, required by the ISO rename below): the
  download link, link text, and the sha256sum/shasum
  instructions now name `maniocserver-amd64.iso`. Note the
  coupling: the tree page now names a file only a future build
  produces — the live page keeps serving prod rebuild 2 as
  `onionhost-amd64.iso` until a new ISO publishes and the edited
  page is uploaded (both separate, gated steps).

### ISO filename + volume label — `build/build-iso.sh`
- Line 30: output is now `maniocserver-amd64.iso` (prod) /
  `maniocserver-<flavour>-amd64.iso` (other flavours).
- Line 530: `grub-mkrescue -- -volid ONIONHOST_LIVE` →
  `MANIOC_LIVE`.
- Existing artefacts under `releases/` were NOT renamed — they
  are records of what shipped.

### Owner-facing wizard strings — `onionhost/rootfs-overlay/usr/lib/onionhost/wizard.py`
- Line 625: window title "OnionHost Setup" → "Manioc Server Setup"
- Line 664: "Welcome to your OnionHost" → "Welcome to your Manioc Server"
- Line 793: "OnionHost will run a program that you install…" →
  "Manioc Server will run…"
- Line 796: "the same sealed room as every OnionHost site" →
  "every Manioc Server site"
- Line 814: "OnionHost can set one of these up for you" →
  "Manioc Server can…"
- Line 974: "use the OnionHost app on the desktop" →
  "the Manioc Server app"
- Line 1105: dashboard window title "OnionHost" → "Manioc Server"
- Line 1209: "OnionHost serves its files" → "Manioc Server serves…"
- Prose otherwise intact; no other wizard text changed.

### Desktop entries — `onionhost/rootfs-overlay/etc/xdg/autostart/`
- `onionhost-dashboard.desktop`: `Name=OnionHost` → `Name=Manioc
  Server`; `Comment=` follows ("Your Manioc Server website: …").
- `onionhost-wizard.desktop`: `Name=OnionHost Setup` →
  `Name=Manioc Server Setup`; `Comment=` follows.
- Filenames and `Exec=` paths unchanged (bucket b).

### Default placeholder site page — `onionhost/rootfs-overlay/var/lib/onionhost/site/releases/0/index.html`
- `<title>OnionHost</title>` → `<title>Manioc Server</title>`;
  "This OnionHost site is running." → "This Manioc Server site
  is running."

### Calamares view steps — NO CHANGE (verified no-op)
`onionhost/calamares/plugin-src/onionhostphrase|onionhostspare|onionhostguard/`:
grep-verified — the user-visible strings in all three steps
(`prettyName()`, titles, body copy) contain **no product name at
all**; their copy is passphrase/encryption only ("Disk
passphrase", "Spare passphrase", "Encryption check", …). Every
"OnionHost" occurrence in plugin-src is a class/factory name, an
`#include`, a log-line prefix derived from the class name, or
the `/* === OnionHost OS === */` file-header comment — all
bucket (b) / internal, left as written.

### Marketplace display names inside this tree → Polyculture Markets
- `onionhost/recipes/marketplace/recipe.json:7`:
  `"name": "Vespiary Market"` → `"Polyculture Markets"`
- `onionhost/recipes/marketplace/recipe.json:24`:
  `"name": "Marketplace (Vespiary Market)"` →
  `"name": "Marketplace (Polyculture Markets)"`
- `onionhost/APP-SITES.md:571` (section heading) and `:573`
  (lead sentence): "Vespiary Market" → "Polyculture Markets".
  The rest of APP-SITES.md still refers to the platform by its
  internal name where it documents plumbing — that is the
  platform's own documentation voice, not an app display name,
  and was outside this pass.

## Verification

- `bash -n build/build-iso.sh` — clean.
- `python3 -m py_compile wizard.py` — clean.
- `recipe.json` parses as JSON.
- Marketplace recipe unit harness
  (`poc/recipes-marketplace/unit-test.py`): **31/31 checks
  passed**. (The harness pins the applier's file-level contract
  and asserts no display-name strings; it runs against the
  existing oh.1/oh.2 payload debs — a recipe .deb rebuild
  carrying the new catalogue name happens at the next recipe
  build, not in this pass.)
- SMF and Gitea recipe files were not touched, so their
  harnesses were not re-run.
- Post-edit grep: "Vespiary Market" now occurs in this tree
  only inside `REBRAND-SCOPE-2026-10-17.md` itself (the
  inventory quoting the old values — a record). Its remaining
  occurrences anywhere are in the marketplace tree (deploy
  defaults — bucket (a) of the other pass / bucket (c) for the
  compiled-in default), untouched here.

## Remaining "OnionHost" hits, grouped by justification

1. **Bucket (b) internal identifiers — deliberate, permanent.**
   Package names (`onionhost`, `onionhost-recipe-*`); all
   `/etc/onionhost`, `/usr/lib/onionhost`, `/var/lib/onionhost`
   paths and their overlay mirrors; systemd/Quadlet unit and
   container names; `ONIONHOST_*` env vars; Calamares module
   names and C++ class/factory names; plumbing filenames
   (tmpfiles, initramfs hooks, apt config, chrony source,
   `.desktop` filenames, build tooling names); recipe seed
   internals (e.g. `onionhost-sealed.php` mu-plugin filename
   and its contents' hook names).
2. **Format identifier tied to bucket (b).** `wizard.py:1301`
   — the backup dialog's `("OnionHost backup",
   "*.onionhost-backup")` filetype and the
   `.onionhost-backup` extension (also the module docstring at
   `wizard.py:3`, and restore-tool messages naming an "OnionHost
   backup"). The extension is the backup format's identifier;
   renaming it orphans existing backup files' recognition, so
   it stays with the plumbing.
3. **Internal tooling text.** Comments, docstrings, and
   generated-config header comments in the golden tooling
   (`onionhost-generate-configs`, `app-init.sh`, `phrasegen.py`,
   `sitegen.py`, Calamares jobmodule docstrings and progress
   labels such as "OnionHost cleanup" — the labels are derived
   from the bucket (b) module names), plus build-script
   comments in `build/build-iso.sh`. None is a product display
   surface per the inventory.
4. **Historical records — leave as written.** `ISO-BUILD-LOG.md`
   prior entries, all dated reports/briefs (including
   `REBRAND-SCOPE-2026-10-17.md` and the naming decision
   sheet's history), `*-evidence/` bundles, `poc/` drivers,
   mutant logs, and the `releases/` artefact filenames.
5. **Living docs not in this pass.** Per the inventory these
   adopt the new names when next edited: `EXPLAINER.md`,
   `OWNER-GUIDE-2026-10-15.md`, `onionhost/README.md`,
   `MAINTAINER-RUNBOOK-2026-10-15.md`,
   `outreach/LAUNCH-POSTS-DRAFT-2026-10-12.md`.

## Flagged leftovers — owner-visible, NOT classified by the inventory, left untouched

These are display strings of the same family as the changed
items, but they appear nowhere in `REBRAND-SCOPE-2026-10-17.md`,
so this pass left them for a one-line follow-up decision
rather than expanding scope silently:

- `build/build-iso.sh:515,519` — GRUB boot menu entries
  "OnionHost OS (live) - Install" / "OnionHost OS (live,
  verbose)" — what an owner sees when booting the stick.
- `build/build-iso.sh:378` — the live user's GECOS/full name
  "OnionHost Live" (shown by the graphical login greeter).
- `onionhost/rootfs-overlay/usr/share/xsessions/onionhost-wizard.desktop`
  — a third desktop entry (the kiosk session definition):
  `Name=OnionHost Setup` and `DesktopNames=OnionHost`, shown
  in the display-manager session picker. (The two autostart
  entries named in the brief were changed; this one was not
  in the inventory.)

Each is a one-line change if Cameron wants them swept.

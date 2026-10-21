# OnionHost — prod ISO download gate + page patch draft (prepared 2026-10-12 evening)

Purpose: Cameron ruled (2026-10-12, clarified in chat 2026-10-13 UTC) that when a
prod ISO is ready for others' or his own testing, it goes on the recruiting page
at vespiary.org/onionhost/ at that time — with its SHA-256 on the page and a
refreshed copy in Drive. This file makes that publish step turnkey and prevents
the one dangerous mistake: publishing a test-flavour build.

## Hard gates — ALL must be true before the download section goes live

1. **Slice 5B (backup/restore) has passed** its acceptance checklist
   (BACKUP-RESTORE-ACCEPTANCE-2026-10-12.md, items 1–12 in the rig;
   item 13 / runbook step 8 is the real-hardware re-proof and is a Stage 2
   completion item — note on the page if the download precedes it).
2. **The ISO is a PROD-flavour build cut AFTER 5B lands** — not the Slice 5A
   ISO and not any test build. Test-flavour images carry test scaffolding
   and must never be published. Verify the build log for this exact ISO
   states prod flavour and lists no test accounts / remote-access hooks.
3. **SHA-256 computed from the final file** that is actually uploaded
   (recompute after any re-cut; the number on the page must match the
   uploaded bytes, not the build-rig copy).
4. **Drive copy refreshed and verified** for this same SHA-256 (rclone
   check, 0 differences), replacing the slice-3-era ISO currently in the
   OnionHost-Stage2 Drive folder — that old ISO predates the website
   tiers and every fix since 5A/5B and should not remain the downloadable
   copy once the new one lands.
5. **Page footer corrected in the same edit**: the current live footer says
   "there is no public download yet, deliberately: the public repository
   and a reproducible, independently verified build come first." Publishing
   the tester download changes that statement — replace it with the alpha
   wording in the draft section below rather than leaving the two in
   contradiction. Do NOT claim reproducible/independently verified unless
   that gate has actually passed.

## Draft download section (placeholders — fill only from the verified build)

Insert as a new <section id="download"> before the "Help us build it"
section in workspace/onion-host-os/site/index.html, and update the footer
line noted in gate 5 in the same commit.

---
## Try the alpha test build

This is an **alpha test build** — [VERSION], cut [DATE], [SIZE] bytes.
SHA-256: `[SHA256]`

Download: [LINK to the hosted ISO file]

Install it only on a machine you can erase. It is a test build for the
tester / reviewer / builder roles below — expect rough edges, and please
report where you got stuck; that report is the point. The checksum above
lets you confirm the file you downloaded is the file we published.

Footer replacement line: "OnionHost OS is a working title; the final name
is still being chosen. This page offers an alpha test build for testers —
it is not a finished public release."
---

## Publish steps (when gates pass)

1. Fill placeholders from the verified prod ISO; paste the section in.
2. Upload site/index.html (+ any style tweak) to vespiary.org/onionhost/
   using the proven hosting SSH pattern (see TOOLS.md); chmod 644.
3. Upload the ISO to its hosting location and to Drive (OnionHost-Stage2),
   then rclone-check the Drive copy.
4. Fetch the live page and the live ISO checksum path once to confirm what
   a visitor actually gets matches this file's recorded SHA-256.
5. Record version, date, size and SHA-256 here, and in ISO-BUILD-LOG.md.

## Still Cameron's calls (not blockers for the tester download, do not invent)

- Product name (OnionHost is a working title only).
- Licence choice (GPLv3 recommended in the design record; awaiting his OK).

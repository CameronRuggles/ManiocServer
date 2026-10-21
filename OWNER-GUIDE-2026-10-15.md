# OnionHost — Owner Guide (draft)

Plain-language companion to MAINTAINER-RUNBOOK-2026-10-15.md, consolidated
2026-10-15 from Cameron's owner-responsibility questions in chat, checked
against the updater and recipe behaviour described there. This is the
owner's side of the contract: the list is short because the maintainer
side (see the runbook) carries the rest.

STATUS: draft for the packaged-app product. One section (§4, persistence
of owner-added plugins/packages across platform updates) depends on
Cameron's pending decision in LOCAL-MODS-UPDATE-POLICY-BRIEF-2026-10-15.md
and is marked as such — do not publish that section until he rules.

## 1. How updates work — you don't run them

Everything on the box updates through one signed channel, over Tor, on a
randomized daily schedule. The box never reaches out on the clearnet.

- **The system itself** (Debian, kernel, Podman, MariaDB, PHP, Tor)
  upgrades from Debian's own archive over Tor, on the same run. Proven on
  real hardware with a packet capture running: zero clearnet traffic.
- **The platform** (wizard, Dashboard, firewall machinery) ships as
  signed packages from the project's own repository, also over Tor.
- **gVisor** is not a Debian package, so a pinned, checksum-verified copy
  rides inside the platform package. It updates when the platform does;
  it never phones Google itself.
- **The apps** (forum, WordPress, wiki, Gitea) update as signed recipe
  packages through the same pipeline.

Two protections, automatic:

- Every update is health-checked afterwards through the real onion path.
  If the site doesn't answer, the update rolls back on its own. If a
  rollback would land on a known-vulnerable version, the box takes the
  site *down* rather than serve vulnerable software, and heals itself
  when the next good update lands.
- The box never reboots itself. A kernel update installs quietly and
  takes effect whenever you next restart.

One honest limit: a major Debian jump (13 → 14 someday) is not a
background update. That ships as a guided project migration.

## 2. Your responsibilities — the whole list

1. **Keep the paper disk phrase safe.** It is the one real secret. Lose
   it and the machine's data is gone — that is the product working as
   designed, not a malfunction.
2. **Be there when it restarts.** After a power cut or a restart you
   choose, someone types the phrase or the box sits sealed at the
   prompt. It can never unlock itself.
3. **Keep it plugged in** — power and wired Ethernet. Updates only arrive
   while it's on and online. A month offline just means a bigger
   catch-up run; nothing breaks.
4. **Back up now and then.** One button in the Dashboard onto a USB
   drive; making a backup needs no phrase. Restoring onto a new machine
   brings back the *same* .onion address — but the restore asks for the
   original disk phrase, so phrase + a backup stored somewhere sensible
   is your disaster kit.
5. **Glance at the Dashboard occasionally.** Green means live. In the
   rare fail-closed case there is a Repair path in Maintenance mode, and
   the forgotten-login-words fix lives there too — the disk phrase
   resets them.
6. **Run your own website.** The app admin password you chose, your
   content, your forum members. Everything underneath it is the
   platform's job.
7. **Physical reality:** off means sealed. A running machine being seized
   is outside what this can promise — and the setup wizard already tells
   you plainly not to host from home if being located would put you in
   danger.

## 3. Adding your own software and plugins

Per ruling A20, owners may install software in the app slot — containment
is a property of the wiring, not curation.

**WordPress plugins and themes — yes, two ways in:**

- Copy the plugin's files into the site folder from the desktop, then
  activate it in WordPress admin. Or use wp-admin's "upload plugin" zip
  option.
- What can never work: browsing the wordpress.org plugin directory from
  inside wp-admin. That directory is fetched by the server, and the
  server has no internet. Download plugins elsewhere (phone, another
  computer) and bring the files over.

**Photos and location data — read this before uploading anything:**
the location-metadata scrubbing in the product description belongs to
the *built-in* page/journal editors only. The platform does **not**
scrub uploads made through apps. A photo you — or a member of your
forum — uploads through WordPress, SMF, or your own installed software
is published exactly as that app handles it, and a phone photo usually
carries GPS coordinates in its metadata (EXIF). Publishing one can put
the photo's location on your site for every visitor to read. Strip
location data before uploading, or use an app or plugin that strips
it for you; nothing downstream will catch it.

Limits that follow from the sealed design:

- Any plugin that needs the internet is crippled in that feature:
  Akismet's cloud spam filtering, Jetpack, licence-key activations,
  cloud backups, embedded Google fonts — all dead. Purely on-box plugins
  (galleries, local forms, SEO tools, page builders) work fine.
- Nothing on the box sends email, ever — so a contact-form plugin that
  delivers by mail silently goes nowhere, the same reason WordPress
  itself can't email you a password reset (the recipe warns about this
  at setup).
- No plugin auto-updates. Updating a plugin means replacing its files by
  hand, same as installing.

**Why WordPress can't update itself:** its core updater is
download-first — wp-admin asks wordpress.org what's new and the *server*
downloads the release. There is no "here's the zip, I brought it myself"
path for core. And server-side download is impossible here twice over:
the app container has no outbound network at all, and the update
machinery is switched off in the config so you never see an "update
available" button that could never work. An app container that can reach
wordpress.org can reach anything — that phone-home path is exactly the
deanonymization route the product exists to close. Core updates arrive
through the signed recipe channel instead (§1).

**SMF forum packages — easier, by design:** SMF's Package Manager accepts
an *uploaded* file, and official point-release security patches ship as
packages. So the sealed-box flow works end to end: download the patch
package on a phone or another computer, upload it in the forum admin, and
SMF rewrites its own files in place. Only the expected parts are dead:
browsing/downloading from a package server, and the version check.

**Your own install instead of a packaged app:** if you want to drive an
app entirely yourself — hand updates included — install it into the app
slot as your own app (the A20 door). Every file is then yours. What you
give up is the signed channel: verified provenance, security floors, and
automatic rollback. That trade is yours to choose.

## 4. PENDING — what happens to your additions when WE update an app

Not yet settled; do not treat this section as a promise.

Today, a platform recipe update swaps the app's whole code tree.
Uploads and config carry over, but owner-added WordPress plugins/themes
—and SMF source patches applied by package— currently do not, and the
swap is silent. The proposed policy (LOCAL-MODS-UPDATE-POLICY-BRIEF-
2026-10-15.md) is: owner additions persist, shipped files win, and
nothing an owner did is ever reverted silently. The one open decision is
Cameron's: when a local modification is detected, does an update
warn-and-proceed, hold-and-ask, or split by whether the update raises the
security floor. This guide gets its final §4 wording once he rules.

## 5. The honest one-liner

Your job is: keep the paper safe, keep the box plugged in, be there when
it restarts, back up now and then, and run your website. Everything else
— updates, patching, rollback, the Tor plumbing — is the platform's job
and the maintainer's job, not yours.

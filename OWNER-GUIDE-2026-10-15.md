# OnionHost — Owner Guide (draft)

Plain-language companion to MAINTAINER-RUNBOOK-2026-10-15.md, consolidated
2026-10-15 from Cameron's owner-responsibility questions in chat, checked
against the updater and recipe behaviour described there. This is the
owner's side of the contract: the list is short because the maintainer
side (see the runbook) carries the rest.

STATUS: draft for the packaged-app product. §4 states the app-update
policy Cameron settled on 2026-10-21 (amendment A26 — recipes are
installers, not update channels), which supersedes the open question
in LOCAL-MODS-UPDATE-POLICY-BRIEF-2026-10-15.md.

## 1. How updates work — you don't run them

Everything on the box updates through one signed channel, over Tor, on a
randomized daily schedule. Updates themselves always travel over Tor.
The box still touches the clearnet in two narrow ways: it keeps its
clock honest with time (NTS) connections, and it connects to the Tor
network over the clearnet — unless bridges are turned on, which is what
hides that second one.

- **The system itself** (Debian, kernel, Podman, MariaDB, PHP, Tor)
  upgrades from Debian's own archive over Tor, on the same run. Proven on
  real hardware with a packet capture running: zero clearnet traffic.
- **The platform** (wizard, Dashboard, firewall machinery) ships as
  signed packages from the project's own repository, also over Tor.
- **gVisor** is not a Debian package, so a pinned, checksum-verified copy
  rides inside the platform package. It updates when the platform does;
  it never phones Google itself.
- **The apps** (forum, WordPress, wiki, Gitea) are the exception, on
  purpose: a signed recipe package *installs* an app once, and after
  that the app is yours — updating it is your job (§4). The platform
  never changes an installed app.

**What the update channel itself can see — the honest bound.** Your
box stays anonymous: nothing in an update run carries your address,
your site's name, or anything that identifies you. But the two ends
of the channel each learn one narrow thing. The project's repository
operator can see *that* an anonymous box polled, and when — the
polls are deliberately randomised and spread across the day so they
don't even reveal your timezone, and every box looks the same to
the repository. And the Debian mirrors your box downloads from over
Tor can see *which package versions* an anonymous box fetched, and
when — which tells them roughly how current that box's software is,
never whose it is or where it lives.
That is the whole of it: timing and version freshness, visible to
the channel's operators, attached to no identity.

Two protections, automatic (they cover the system and the platform —
your app is never touched by an update run, so it needs neither):

- Every system and platform update is health-checked afterwards
  through the real onion path.
  If the site doesn't answer, the update rolls back on its own. If a
  rollback would land on a known-vulnerable version, the box takes the
  site *down* rather than serve vulnerable software, and heals itself
  when the next good update lands.
- The box never reboots itself. A kernel update installs quietly and
  takes effect whenever you next restart.

One honest limit: a major Debian jump (13 → 14 someday) is not a
background update. That ships as a guided project migration.

One more honest limit, for now: the site containers themselves —
the Tor gateway, the web server, and the software inside your app
container — are not yet updated by this channel. They stay at the
versions in the ISO you installed from. To refresh them today,
back up your site, then reinstall from the current ISO. Delivering
container updates through the same signed channel is planned;
until it ships, a reinstall is the refresh path.

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
   is your disaster kit. One heads-up: if your app keeps its data in a
   SQLite database, a backup briefly pauses the site while it runs.
5. **Glance at the Dashboard occasionally.** Green means live. In the
   rare fail-closed case there is a Repair path in Maintenance mode, and
   the forgotten-login-words fix lives there too — the disk phrase
   resets them.
6. **Run your own website.** The app admin password you chose, your
   content, your forum members — and keeping the app itself updated
   (§4). Everything underneath it is the platform's job.
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
- One habit worth forming for those downloads: a download ties the
  software to whatever network and account fetched it. If that
  association matters to you, fetch over Tor (Tor Browser is fine for
  this) or from a device and account you don't mind being linked to
  the software you run — the same applies to the app releases in §4.

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
deanonymization route the product exists to close. Core updates are
yours to make by replacing the files from the desktop (§4) — the
same door your plugins already come through.

**SMF forum packages — easier, by design:** SMF's Package Manager accepts
an *uploaded* file, and official point-release security patches ship as
packages. So the sealed-box flow works end to end: download the patch
package on a phone or another computer, upload it in the forum admin, and
SMF rewrites its own files in place. Only the expected parts are dead:
browsing/downloading from a package server, and the version check.

**Your own install instead of a packaged app:** if you want to drive an
app entirely yourself from the first minute, install it into the app
slot as your own app (the A20 door). Every file is then yours,
including the installing. What you give up is the packaged start: the
verified, pre-configured first install a recipe gives you. Either
way, updates after install are yours — that is the same for packaged
apps and your own (§4).

## 4. Updating your app — it's yours

The rule, settled 2026-10-21: **we install it; updating it afterwards
is yours.** A packaged app is installed once, by the signed recipe.
From that moment the platform never changes it — no update run
touches an installed app's files, ever, and nothing you added to it
(a plugin, a theme, a patch, an upload) can be reverted or replaced
by one. This section replaces the question this guide used to leave
open: there is no platform app update for your additions to survive,
because there is no platform app update.

What you will see: when a newer version of your app gets packaged,
the Dashboard mentions it — as information, not an alarm. The
packaged version is also what a *fresh* install gets: a new machine,
or a first install, always starts from the newest package the box
carries. Your installed copy stays exactly as it is until you change
it. Three ways to change it, all of them yours:

- **The app's own upload tools.** Some updates arrive as a file you
  upload inside the app, and those work exactly as they would
  anywhere: SMF's Package Manager takes the official point-release
  patch packages (§3), and WordPress takes plugin and theme zips in
  wp-admin. What can never work is an updater that wants the
  *server* to download the update — the sealed room has no internet
  (§3) — so you bring the file to the app, on a phone or another
  computer, and upload it.
- **Replace the files from the desktop.** You have access to your
  site folder from the desktop. Download the app's new release
  elsewhere, copy its files over the ones in the site folder, and
  keep your own state: for WordPress keep `wp-config.php` and
  everything inside `wp-content` (your uploads, plugins and themes);
  for DokuWiki keep the `data` and `conf` folders (your pages and
  settings); for SMF keep `Settings.php` and the `attachments` and
  `custom_avatar` folders; for Gitea replace the single program
  file and leave its data folder and settings alone. Then open the
  app — most apps run their own database tidy-up on the next visit
  or from their admin page.
- **Do nothing.** That is allowed, and it is a real choice: plenty
  of sites run an older app for years. The risk is also yours — an
  unpatched app can be defaced or have its own contents messed
  with. What it cannot do is reveal this computer's address: the
  sealed room holds no matter what state the app is in, patched or
  not. Keeping the app current is maintenance; your address's
  safety never depended on it.

## 5. The honest one-liner

Your job is: keep the paper safe, keep the box plugged in, be there when
it restarts, back up now and then, and run your website — including
updating its software (§4). Everything else — system updates, rollback,
the Tor plumbing — is the platform's job and the maintainer's job, not
yours.

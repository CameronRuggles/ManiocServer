# Manioc Server
## What this is, how it works, and what it does not do
### Public explainer — DRAFT v0, 2026-10-11. Written for people exploring the project: curious users, reviewers, and future contributors. The full design record (design documents, external reviews, proof-of-concept results, build logs) lives in this repository alongside it.

---

## 1. What it is

A free, open-source operating system (a Debian 13 derivative distributed as an installable ISO) that turns a spare home computer into a personal web server reachable only as a **Tor onion service**.

You boot the installer USB, click through a short walkthrough, copy down one generated password phrase onto paper, choose a simple site type, and press **Go Live**. Your site gets an `.onion` address that works from anywhere, with no port forwarding, no public IP address, no domain name, no hosting account, and no monthly bill — because onion services connect *outward* to the Tor network, visitors' browsers meet your computer in the middle.

It is built for non-technical owners. The whole user-facing model is four ideas: a paper phrase, short login words, a status dashboard, and a repair path. Everything else is the machine's problem.

**Version 1 hosts the Pages and Journal tiers, plus a dynamic app slot** — simple pages and a journal (a static site generator with a local editor; no comments, no database, no visitor logins), and one app slot where a signed recipe installs a packaged dynamic app — a forum, WordPress, a wiki, or Gitea. The platform installs the app once; from then on it is the owner's to run and maintain.

## 2. The one claim we make — and the ones we don't

**We claim exactly this:** the system hides your computer's *network address* — from your site's visitors, and from the website software itself. If your site is hacked, the attacker gets the site. They do not get your home's IP address, your local network, or the key that makes the site *your* site.

**We do not claim:**
- **That nobody can ever locate the computer.** Tor hides where the server is on the network; it does not hide *when* the server is online. Someone patient who records your site's uptime and compares it with publicly reported power and internet outages may narrow down a region over time. Battery backup, a backup connection, and good defaults make that slower and noisier; nothing makes it impossible. The setup wizard shows this warning in plain language, including the sentence: *if being physically located would put you in danger, do not rely on hosting from your home.*
- **Protection against adversaries who can watch large parts of the Tor network itself.** That is a different, harder problem, and no home-hosting product solves it.
- **Protection of a running machine that someone has already compromised or seized.** The ironclad state is *powered off* (see §4). A machine that is on and unlocked is defended, but it is not magic.
- **An authenticated, tamper-proof boot.** The boot files are encrypted and the bootloader chain is Debian's signed one, but the system does not prove to you at every boot that nothing in the boot path was ever touched. We say so rather than implying otherwise.

## 3. How it works (the architecture in one page)

Three sandboxed containers (Podman + gVisor), one rule: **each part can only do its one job.**

- **Container B — your website.** Nginx serving your static site. It has **no network at all**: no interface but loopback, no routes, no DNS. It cannot phone home, scan your LAN, or leak an address it has never seen. It never holds the site's onion key, so a fully compromised website cannot impersonate your site after a rebuild.
- **Container A — the Tor gateway.** The only container allowed to talk to the internet, and it speaks only Tor. It holds the onion private key and reaches the website over a **Unix socket** (not a network connection): the web server's pages pass through a file-like channel that carries no IP address to leak. Tor's modern defences are on by default: proof-of-work, introduction-point rate limits, per-circuit stream caps.
- **Container U — a client-only Tor helper.** Used by the system itself to check “is my site reachable from the outside?” and to fetch project packages, so maintenance traffic never reveals the server's own Tor identity and never goes over the open internet to a project server that could log your home address.

Around them:
- **A host firewall with a self-checking golden configuration.** The expected firewall is regenerated from the design, and the live firewall is compared against it (as canonical data, not by eyeballing text) on a timer and on system events. If they don't match, Tor refuses to start: the system fails *closed*, never open.
- **A health probe, not a promise.** A fixed check fetches the site's front page through the client-only Tor container (Container U) and reports only a status code. Separately, a runtime gate checks that each onionhost container's OCI runtime is the gVisor wrapper (`runsc-wrap`); that gate is proven in the sandbox, with rig confirmation still pending, and it does not by itself prove anything about a container's network, read-only files, or exact mounts. The dashboard turns codes into plain-language cards (“Your site is up”, “Something needs attention”). The probe reads facts; it does not render the site, so a hacked page can't attack the owner through the dashboard. There is deliberately **no browser on the box**; you view your site from your phone, via a QR code.
- **Rotation without downtime theatre.** When the site software is rebuilt (updates, publishing), the new instance starts beside the old; a host-side link is atomically switched once the new one passes its health check, and the old one drains and exits. The Tor gateway is restarted rarely and at randomised times, because restarting it is the one visible hiccup (well under two minutes).
- **Updates that don't leak your timezone.** System updates and rebuilds are scheduled randomised across the full UTC day — “random in the evening” would still be a pattern. Website edits never restart Tor. Response headers carry no wall-clock time (no `Date`; cache validators are derived from content), and photos added through the built-in page and journal editors have their EXIF metadata (capture time, sometimes GPS) stripped automatically. That scrub belongs to those editors, not the whole platform: a photo uploaded through an installed app (a forum, WordPress) is published the way the app handles it, location data included, unless the app strips it itself.

## 4. The disk, the phrases, and recovery

- The whole disk is encrypted (LUKS2). **The phrase is typed at every boot.** There is no auto-unlock: unplug the machine and it is a sealed brick until the phrase is typed. Sleep and hibernation are disabled for the same reason.
- **One paper secret:** a 7-word phrase the *computer generates* (about 90 bits of randomness — you never invent a password anywhere in this product). You copy it onto paper by hand, on its own installer page, and prove the copy by re-typing chosen words. The entropy source is audited as part of the build: proper system randomness, the full wordlist, unbiased selection. A weak random generator would quietly defeat everything else, so it is treated as a release-blocking check. It is also the *only* key there is: no spare phrase, no second copy, no back door. A sealed machine whose paper is lost is gone for good — backups included, since they open with the same phrase.
- **Login words** are a separate, shorter generated phrase for the desktop/dashboard — locking the screen is not the same job as unlocking the disk.
- **Lost the paper?** If the machine is still running, Maintenance mode lets you set a brand-new phrase without the old one — this is a deliberate, reviewed design decision (the boot process is configured so the running system can do this), because “the server is right there, working, but can never be safely rebooted again” is the failure real people actually hit.
- **Backups need no phrase to make** (they're encrypted to a key derived from the disk phrase at install time) **and the phrase to restore** — so backups are safe to keep on an external drive — the backup file is encrypted, and nothing on its outside names your site or when it was made — and restoring one brings back the *same* `.onion` address.

Boot details for the technically curious (they were reviewed externally, twice): the bootloader can't process the strongest passphrase derivation, so — since the phrases are machine-generated at ~90 bits — the phrase slots deliberately use the widely compatible derivation, plus a separate random *keyfile* that lets the system finish booting after you've typed the phrase once. That keyfile is treated as the sensitive object it is: generated per-install, locked permissions, and **excluded by the operating system itself — not by instructions to the user — from every backup and diagnostic export**. A disk key riding along inside a backup would silently undo the product's main promise, so the OS enforces the rule.

## 5. Major decisions, and why (the short version)

- **Website container has no network** (stronger than “firewalled network”) — because every design review agreed the socket pattern removes whole attack classes instead of filtering them.
- **No browser on the server** — the locked-down browser in an early design pointed at the one site assumed to be hacked; a browser exploit there would have landed in the owner's own session. The phone + QR replaced it.
- **Rootful container engine** — not ideology: measured. The rootless mode could only run by disabling the resource limits it was supposed to prove. Fork bombs and memory hogs are contained by tested ceilings.
- **Static-only v1** — a database tier multiplies what a compromise can steal and adds a web-admin attack surface. It comes later, behind its own design and review.
- **No multi-host redundancy in v1** — running the same site from several homes sounds like an easy availability win; external review showed the failure modes (key in many houses, unreliable failover) cost more than they buy. A battery backup and a backup internet connection are the recommended v1 answer to outages.
- **Adults-only positioning, narrow claims** — the legal and ethical review surface of a privacy hosting tool is real; the product says what it does, warns about what it doesn't, and doesn't host or index anyone's site: there is no directory, no telemetry, no operator relationship with your content at all.

## 6. How it was built (and how you can check)

This project is developed in the open, design-first: every major decision went through written external security review *before* it was built (the reviews, including the ones that corrected us, are in this repository), and the core mechanisms were proven in staged tests — first the container stack alone, then on a virtualised test rig, then real hardware — with published pass/fail results, including the failures. Known limitations are written down in the same place as the features.

Releases are **reproducible**: the ISO is built from a pinned snapshot of the Debian archive, and a release only counts as verified when independent rebuilders produce a bit-identical image matching the published, signed checksum. The “verify your download” instructions ship with every release.

## 7. Status and what's next

As of this draft: the design (v2 + amendments) has passed two full external reviews; the container stack and the deferred security tests have passed on the test rig; a skeleton installer ISO builds and installs end-to-end; the walkthrough, dashboard, and publishing tools are in active construction. Not yet done: real-hardware lifecycle testing, novice user testing, the external review of the *built* system, the legal review, the final product name (the licence is decided: Apache 2.0). Nothing in §2's claim list ships until those gates pass.

*If you find a gap between this document and the design record, the design record wins — and please open an issue; keeping the public explanation honest is part of the project's definition of done.*

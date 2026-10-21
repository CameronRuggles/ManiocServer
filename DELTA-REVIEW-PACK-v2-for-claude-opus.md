# DELTA REVIEW PACK — OnionHost OS, Design v2
## For: Claude Opus 5.5, high thinking — "attack the fixes"
## Prepared: 2026-10-10 · Status: v2 design written; PoC not yet run; no code exists.

---

# PART 0 — MESSAGE TO THE REVIEWER

You reviewed v1 of this design (the "OnionHost OS" review pack) and returned:
**build it, with changes** — 12 major findings (M1–M12), 17 contradictions
(X1–X17), verdicts on 12 claims, and three priority changes. The author
adopted your review nearly wholesale and produced Design v2.

**This pack is NOT a re-review of v1. Your job now: attack the fixes.**
Every mechanism in Part 2 is new since your review — most of them are *your*
suggestions, implemented by the author, or the author's inventions built on
them. Fixes are where second-order bugs live: a fix can be individually sound
and still contradict another fix, quietly reopen the hole it closed, or be
unimplementable in the form stated. That is what we are paying for this round.

Order of work (same discipline as last time):
1. **Steelman each fix briefly** — state the strongest implementable version
   (name the real mechanism where the author hand-waved).
2. **Then attack that version**: concrete scenario → which v2 claim or v1
   finding it reopens → shippable correction, a downgrade of the claim, or
   "this fix creates a worse problem than the original finding."
3. **Verdict per fix-cluster** (Part 2, clusters A–K):
   FIX HOLDS / FIX HOLDS WITH CORRECTIONS / FIX IS FLAWED — REPLACE.
4. Answer Part 4's questions, add PoC tests to Part 5, and end with the
   Part 6 template, including a go/no-go for starting the alpha build.

Rules:
- Do not relitigate your own M/X findings unless a v2 fix mishandles one.
- The FIXED axioms from the v1 pack are unchanged: non-technical user (adult
  audience, 12-year-old capability benchmark, no terminal ever); LUKS phrase
  typed at every boot, no auto-unlock; website in a Docker-compatible
  container (Dockerfiles); no exit relay, ever; no inbound ports; works
  behind NAT/CGNAT. Flag a fix that violates one as a first-class finding.
- The author has seeded suspected weak spots in the fixes (Part 3, S1–S10).
  Confirm or clear each — and treat the seeded list as a floor, not a ceiling.
- Where a question is empirical (only testable on a machine), say so and
  specify the exact test for the PoC list instead of speculating.

---

# PART 1 — RECAP (so this pack stands alone)

**The product:** a Debian-based ISO that turns a spare home desktop into a
Tor onion-service web host for non-technical adults. Click-through install
(Calamares), mandatory LUKS2 full-disk encryption, generated credentials,
first-boot wizard, click Go Live, get a `.onion` address. The core v1
architecture you validated: the website lives in a hardened container that
can reach almost nothing; a separate Tor component holds the onion private
key; if the website is fully hacked, the attacker should learn nothing that
locates the household and cannot steal the site's identity.

**Your v1 verdicts that v2 acted on:** the "nobody can locate it" tagline
was unsound (timing/uptime/clock channels) → claim narrowed to network-
address secrecy, with the residual stated to users. C4 (wizard completable)
unproven → five-novice gate before any public ISO. C7 (self-check) unsound
as written → rebuilt (cluster G). Everything else was sound-with-fixes, and
the fixes are Part 2.

**What did NOT change in v2:** the compartment idea itself, mandatory LUKS
with per-boot phrase (owner-settled), relay policy (off; bridge opt-in;
exit never), adult positioning with the honest claim, the pre-public gates
(novice sessions, external security review, legal counsel).

---

# PART 2 — THE FIXES, IN IMPLEMENTABLE DETAIL
*(Each cluster: your finding → what v2 does → where the author is unsure.)*

## Cluster A — Website has NO network; Tor↔website over a unix socket (M2, your priority change #1)

- Website container (B): Podman network mode `none`. Only loopback exists.
- nginx-unprivileged inside B listens on a unix socket,
  `/run/web/http.sock`, on a dedicated volume shared between B and the Tor
  container (A) — and nothing else.
- A's torrc: `HiddenServicePort 80 unix:/run/web/http.sock`.
- Both A and B run under gVisor `runsc`, **mandatory**: if runsc cannot
  start B, Go Live refuses with a plain error (no runc fallback, X3).
- A itself is now hardened per M8: distroless locally-built image,
  read-only rootfs except DataDirectory/key volume (small, quota'd),
  host-generated torrc, PoW defences and intro-DoS defence ON,
  `HiddenServiceMaxStreams 50` + close-circuit, control via unix socket
  to a host status daemon only, `SocksPort 0`.
- Blog-tier database container from v1 is **gone** (see cluster I), so the
  "second socket for the DB" problem is deferred, not solved.
- **Seamless rotation of B** (part of M1, detailed in cluster H): two
  socket files; start the new B on socket 2, reload tor to point at it,
  stop the old B.
- Author's flagged unknown (PoC gate #1): nginx under runsc creating a
  unix socket on a shared host volume needs the runtime's host-UDS
  creation support — if it fails, v2's documented fallback is your M2
  fallback (internal network + conntrack direction rules + static IPs).

## Cluster B — ONE human secret (M4, X1, X5, X6, Q7, Q8; your priority change #2)

- The only paper secret is the **disk phrase: 7 Diceware words, no digit**
  (~90 bits, EFF list, ASCII-only), **hand-copied** on its own page
  (no print flow for the phrase). Verification re-typing uses
  **randomised word positions**.
- The `.onion` address + QR move to a **separate, non-secret page**
  (display/print freely; QR page explains Tor Browser / Onion Browser).
- Login is a **user-chosen convenience PIN/short password** set in the
  first-boot wizard. It guards screen unlock and routine sudo only; the
  design explicitly does not count it as a data-protection secret.
  First session after install is **one-time autologin** into the wizard.
- Website admin password: generated at Go Live, shown once; only its hash
  exists on the box. **Nothing secret is stored in any keyring.**
- **"Reset passwords" boot entry**: a GRUB entry that boots to a special
  systemd target. The flow runs *after* the normal LUKS unlock prompt;
  whoever passed it can reset the login PIN and regenerate the website
  admin password. A Dashboard equivalent exists behind polkit.
- **Re-key flow**: Dashboard "Make a new disk password" — a root helper adds
  a new LUKS keyslot (author notes: using the live volume key if that path
  verifies at build time, else prompting for the current phrase), then
  kills the old slot. The user hand-copies the new phrase.
- **Spare key**: optional wizard step creates a *second* phrase in a second
  LUKS keyslot for a named trusted person; revocable from Dashboard
  (kills that slot).
- **Backups**: `age` passphrase mode (scrypt) under the disk phrase;
  contains site content, onion key, config. Exporting a backup from the
  Dashboard requires **typing the disk phrase into the app**, verified
  against the LUKS header (`cryptsetup` test-passphrase on stdin) before
  the export runs.

## Cluster C — Engine switch: Podman rootless + Quadlet (X2, your alternatives verdict)

- Engine is now **Podman, rootless, via Quadlet systemd units**. Images are
  ordinary OCI/Dockerfiles — the fixed "Docker-compatible" requirement is
  interpreted as satisfied by Dockerfile compatibility.
- Documented fallback branch if cluster A's PoC gate fails on
  Podman+runsc: rootful Docker + runsc, no userns-remap.
- `userns-remap` is deleted from the design in all branches.

## Cluster D — Trust chain: local image builds + one signed package (M5, X4, X9, R6, R10, Q13/Q14; your priority change #3)

- Host apt runs over **plain HTTPS** (apt-over-Tor dropped entirely).
- Container images are **built on the user's own machine** (mmdebstrap →
  OCI) from the same signed Debian + Tor Project packages. When a source
  package updates, images **rebuild and roll automatically** (the apt
  signature is the gate; approval-gating remains only for user-visible
  app changes, with rollback via previous image tags).
- The build is triggered by package changes (dpkg/apt hook → systemd
  service), runs unattended, and must keep the previous working images
  until the new set passes the self-checks (cluster G).
- The maintainer signs exactly one small `onionhost` package (golden
  config, wizard, dashboard, units) with a hardware key; ISO and package
  builds are reproducible.
- The `onionhost` repo metadata carries `Valid-Until`; installs fetch it
  from an onion mirror. Staleness UX: >90 days → amber "project may be
  unmaintained, Debian fixes continue to ~2030"; at base-release EOL →
  red + one-click "Back up and shut down."
- **Restart honesty**: automatic updates install, but the Dashboard tracks
  running-vs-installed kernel/gVisor: "Restart needed for a security fix —
  have your disk password ready," amber 7 days, red 30. "Up to date" is
  only claimed for the *running* system.

## Cluster E — Firewall gate (M3, Q13)

- Dedicated `table inet onionhost` (nftables), own drop-policy base chains,
  loaded by `onionhost-fw.service` ordered `Before=` the container engine;
  the unit never flushes or edits other tables.
- A's Quadlet unit `Requires=` the firewall unit and `ExecStartPre=` hashes
  the live table (normalised `nft list`) against the golden hash, plus
  asserts container IPv6 sysctls are off. Mismatch → A does not start.
- Re-check: systemd timer every 5 minutes AND triggers on engine restart /
  package installation / nft change. On mismatch **A is stopped** and the
  Dashboard goes red: "Safety settings changed — click Repair."
- A egress rule: outbound TCP to any port (guards use arbitrary ORPorts —
  v1's port allowlist was X16), UDP dropped.
- Golden-config single source generates the nft table, torrc, units,
  self-check expectations, and Dashboard claim strings; a build-time check
  fails on drift between them (X8).

## Cluster F — Admin surface rebuilt (M6, R7)

- **Dashboard is a native GTK app** talking to a polkit-guarded helper over
  a unix socket. There is **no TCP listener for admin at all** — no
  localhost web UI, so no DNS-rebinding/CSRF surface.
- The local site **editor is part of this native app**; publishing goes
  through a host-side publisher helper (same socket/polkit pattern) that
  is the only writer of the content volume B mounts read-only. The
  publisher scrubs uploads (image/media/document metadata incl. PNG text
  chunks and HEIC, random renamed files, quotas).
- **Tor Browser on the box is policy-locked** (`policies.json`
  WebsiteFilter): only the box's own onion address and the Tor download
  page are reachable. General browsing on the server is designed out.
- Host strip list: no avahi, cups-browsed, bluetooth, ModemManager;
  generic DHCP hostname.

## Cluster G — Self-checks rebuilt (M9, X10, X11, C7)

- B contains no probe tools and is never asked to test itself. Checks run
  from a **probe workload launched with B's exact unit/runtime policy**
  (same Quadlet template, probe image) against the socket volume and the
  system state: no network namespace route, socket permissions, key
  unreadable from B's mount view, firewall hash, Tor reports the service
  published, no unexpected host listener.
- Card text is literal: **"Website sealed off: passed"** (never "location
  hidden").
- Schedule: Go Live, every boot, every cluster-E trigger event, hourly.

## Cluster H — Timing/availability mitigations (M1, X12)

- nginx: `Date`, `Last-Modified`, `ETag` stripped or frozen (the images are
  built locally per cluster D, so a headers-more style module can be
  compiled in deliberately); `server_tokens off`; custom error pages;
  no default favicon (a generic one is generated per install).
- All containers run UTC; no local-time artefacts in B.
- B restarts are seamless (cluster A's dual-socket handover) or, if a real
  outage is unavoidable, scheduled at a **daily-redrawn random UTC time**.
- Residual risk disclosed to users in one plain sentence (uptime-watching
  can still teach an observer rough, timezone-scale facts).

## Cluster I — Tiers rebuilt (M7, X14, X15)

- **Simple pages** (default): form-built static site.
- **Journal** (replaces "blog"): static generator + owner-only editor.
  No WordPress, **no comments in v1**, no database container. Admin reset
  is the §B disk-gated flow.
- **Private files**: reachable only under Tor v3 **client authorisation** —
  only devices the owner invites can resolve/connect at all. The invite
  flow is wizard-driven (the owner generates an invite in the Dashboard;
  the exact key-handing UX is sketched as "show a QR / copy a block the
  guest pastes into Tor Browser") — author flags this as under-specified.
- **BYOC: cut from v1 entirely.**

## Cluster J — Host & install changes (M4 keymap, M10, M11, M12)

- **Debian 13 base**, live-build, Debian signed shim → Secure Boot works
  without BIOS changes; per-vendor boot-menu-key guide ships with the
  USB instructions.
- Calamares: LUKS2/argon2id (1 GiB floor, ~2 s unlock target), custom QML
  page generates the disk phrase in-process, passed to cryptsetup on
  **stdin, never argv**; live session `noswap`.
- **Initramfs carries the console keymap** matching the installer's layout
  choice (the AZERTY/QWERTZ lockout trap).
- Erase screen names the detected OS/data ("Windows 11 — ~412 GB incl.
  Photos and Documents") and requires **typing a confirmation word**.
- **Sleep/suspend/hibernate masked.** Auto-lock 5 min. **All site services
  run with nobody logged in.**
- First-boot confidence screen after the first real unlock ("you just
  typed it at the real prompt — it works").
- Install-USB watcher: final wizard screen waits until the USB is removed
  (udev); disk-first boot order set where possible.
- Honest UI line: encryption protects the site only when the computer is
  **fully shut down**. The Dashboard's red button is **"Shut down now"**
  (stops site + powers off); key-shredding survives only as an expert
  action paired with immediate power-off.

## Cluster K — Claims & positioning (C11, Q9, Q11)

- The only marketing claim: the product hides the computer's **network
  address** from visitors and from the website software itself.
- Public positioning: *"No technical skills needed. For adults (18+)."*
  The 12-year-old is an internal benchmark only, on no public surface.
- Wizard/docs state: the ISP sees 24/7 Tor use; uptime-watching teaches
  rough facts; **not for use where Tor is blocked or illegal**;
  pluggable transports for the server's own connection are v1.1.

---

# PART 3 — AUTHOR'S SUSPECTED WEAK SPOTS IN THE FIXES (confirm, clear, or escalate each)

- **S1 — The dual-socket handover may not hand over.** Tor with two
  `HiddenServicePort` lines for the same virtual port selects a target —
  the author's reading of the man page says *at random*. If so, cluster A's
  "start new B on socket 2, reload, stop old" serves some visitors from the
  OLD B (with old content) indefinitely, or fails connections when the old
  socket dies. Is the correct mechanism instead: same socket path, drained
  restart (seconds of outage at a random time — i.e. cluster H's fallback
  becomes the primary)? Or a tiny socket-proxy that can re-point — and does
  adding that proxy reintroduce the third parser cluster-thinking removed?
- **S2 — The Reset-passwords boot entry is a new privileged pre-login
  surface.** It runs as root before any user login, takes input, and can
  change account credentials. The author's defence is "it runs only after
  LUKS unlock, and whoever has the phrase already owns the box." Attack
  that: parser risk in the reset tool itself, GRUB-entry editing paths,
  the entry's existence changing the value of a stolen *login PIN* (can
  the reset path be reached WITHOUT the disk phrase via initramfs
  tampering on the unencrypted /boot — the evil-maid the design declares
  out of scope — and does the reset entry widen that hole from "tamper"
  to "clean credential reset")?
- **S3 — One-time autologin.** If power dies mid-wizard, or the wizard
  crashes, what state is the box in? The author intends a flag consumed
  atomically on wizard completion. Failure modes: autologin persists and
  the box sits at an open desktop (guarded only by LUKS-at-rest); or the
  flag logic bricks setup and a novice can never re-enter the wizard.
  Specify the state machine you would accept.
- **S4 — The chosen PIN reintroduces a user-invented password.** v1's fixed
  rule was "never invents a password"; cluster B lets the user invent the
  PIN. On a stolen *running* machine, the session is the only thing between
  the sibling/thief and the Dashboard (which can export the onion key after
  phrase verification — but the phrase is asked INSIDE that session).
  PAM faillock presumably throttles guessing. Is "convenience PIN +
  faillock + 5-minute autolock" honestly sufficient, or should login be the
  disk phrase too (one secret meaning ONE secret), with the PIN only as a
  screen-unlock convenience *within* a session?
- **S5 — Typing the disk phrase into a desktop app** (backup export,
  cluster B) puts the crown jewels through the GUI stack: keyloggers in
  the session, accessibility tools, the app itself, crash dumps,
  swap/hibernation of the app process (hibernate is masked; swap is inside
  LUKS — but page-cache/swap of a *running* system is exactly the running-
  seizure case). Is verify-in-app acceptable, or should exports/re-keys be
  forced into the pre-login environment (cluster B's reset target) so the
  phrase is only ever typed at console prompts?
- **S6 — The on-host image builder is a new root-with-network service.**
  Cluster D runs builds unattended on the user's machine, triggered by
  package changes, fetching from the network. The author's defence: apt
  already installs those same packages as root on the host, so the build
  adds little. Attack the delta honestly: build-time scripts/hooks run in
  a *different* context than package install; mmdebstrap/OCI tooling parses
  registries and manifests; a poisoned-but-signed package (or a malicious
  mirror serving validly-signed-but-old packages — rollback) now ALSO gets
  executed in a build pipeline that produces the Tor container — the one
  image that must never be wrong. And rollback tags: what stops an
  attacker (or a bug) from "rolling back" A to an ancient vulnerable tor?
- **S7 — The probe workload needs engine privileges to exist.** Cluster G
  launches a probe with B's exact policy. Who launches it — a root helper
  on a timer? That helper can launch *arbitrary* units in principle; its
  unit-template handling is now part of the trusted computing base, and it
  runs on triggers an attacker who owns B might influence (can B force
  probe launches as a DoS? can probe output leak into the Dashboard
  unsanitised?). Also: a probe with B's policy is not B — what class of
  real failure does it structurally miss?
- **S8 — Client-auth invite flow (cluster I) is hand-waved at exactly the
  secret-handling step.** A v3 client-authorisation private key must move
  from the owner's box to the guest's Tor Browser. The sketched QR/paste
  flow puts that key on screens, clipboards, possibly photos — the same
  artefacts Part 5 of the v1 pack attacked for the Recovery Sheet. Does
  the invite flow leak the *site's existence/address* to anyone holding a
  screenshot? Is per-guest keys + revocation the minimum viable design,
  and can a novice actually operate it?
- **S9 — Header stripping may fight the web, and the check may not notice.**
  Removing `Date`/`Last-Modified`/`ETag` breaks caching semantics and some
  clients; nginx needs a non-standard module path for full `Date`
  suppression — is the clock-skew protection actually achieved if `Date`
  remains but is *frozen/rounded* (e.g. to the hour)? Quantify what's
  enough against the Murdoch-style skew attack: is per-response accuracy
  the leak, or load-induced *drift*, which header games cannot hide?
- **S10 — Randomised restart timing vs the redraw mechanism.** Cluster H's
  daily-redrawn random UTC restart time is decided *by software on the
  box*. If B is compromised, can the attacker learn or influence the
  schedule (the timer is host-side, but B's restart is orchestrated by a
  host service whose logs/timing B's attacker can observe through response
  behaviour)? And if restarts are seamless (S1's question), is the random
  schedule dead code that only fires in the failure case — i.e. precisely
  when an observer learns the most?
- **S11 — Valid-Until + onion mirror reveals the fleet.** Cluster D's
  installs fetch repo metadata from an onion mirror run by the maintainer.
  The mirror operator (the maintainer, or whoever seizes that service)
  learns install IPs? (No — onion circuits; but timing/count and the
  update *fetch pattern* fingerprint installs, and a malicious mirror can
  serve stale-but-valid metadata to targeted installs within the
  Valid-Until window.) Is the staleness UX (amber at 90 days) calibrated
  against an attacker who keeps re-signing while serving a frozen tree?
- **S12 — Fixes vs the fixed user.** Count the concepts v2 now asks the
  user to hold: disk phrase, spare key for a named person, a chosen PIN,
  a shown-once website password, client-auth invites, a restart-needed
  card that wants the phrase, a repair button for firewall drift. Each is
  simple; the SUM may exceed the capability ceiling that Fixed #1 sets.
  Which single concept would you cut first?

# PART 4 — TARGETED QUESTIONS (answer each briefly)

- **DQ1.** Cluster A: give the correct seamless-B-rotation mechanism, or
  rule that brief random-time restarts are the honest design. Include what
  a visitor mid-download experiences in your version.
- **DQ2.** Does rootless Podman + Quadlet change any of your v1-review
  positions (especially the firewall-gate design and the "rootful engine"
  resolution of X2)? Name anything in Quadlet/systemd-unit generation that
  silently drops hardening options (e.g. does every hardening flag in the
  unit survive `podman generate`/Quadlet translation — seccomp, cap drops,
  read-only, network none, runsc runtime selection)?
- **DQ3.** Is `HiddenServiceMaxStreams 50` + PoW + intro-DoS the right
  default bundle for a *novice's popular* site (cluster H's viral case),
  or do those caps become the outage? Recommend numbers with reasoning.
- **DQ4.** Cluster D rollback: design the anti-rollback rule for container
  images in one paragraph (monotonic version floor? tor version floor tied
  to the signed `onionhost` package? what if Debian itself must roll back
  for a broken update?).
- **DQ5.** The reset/re-key/export trio (cluster B): should ALL phrase-
  handling move to the pre-login target (S5), with the desktop Dashboard
  reduced to *requesting* a reboot into that target? Cost-benefit for the
  target user.
- **DQ6.** Spare keyslot (cluster B): does revocation actually work as
  users will understand it ("I took back the spare key") given the holder
  may have photographed it? Phrase the Dashboard's revocation copy honestly.
- **DQ7.** Cluster F's policy-locked Tor Browser: WebsiteFilter is an
  enterprise policy — can a user (or malware in the session) edit
  `policies.json` and silently unlock browsing? Where must that file live
  and who may write it, for the lock to mean anything?
- **DQ8.** Cluster G: is there a check that proves the NEGATIVE that
  matters most — "B cannot reach the internet" — when B has `network:
  none`? What, exactly, is left to check (namespace config drift in
  Podman? a future tier re-adding a network by default?) and how would
  drift actually manifest?
- **DQ9.** Anything in v2 that reintroduces a DNS path *anywhere* (host
  apt, image builds, Tor itself, the Dashboard helper, time sync)? List
  every resolver the finished system runs and who can query it.
- **DQ10.** Time sync, revisited for v2: the host needs an accurate clock
  for Tor; NTP is a network fingerprint and a skew source. What does v2
  ship (systemd-timesyncd? NTS? Tor-consensus-based time?) and is the
  choice consistent with cluster H's anti-skew posture?

---

# PART 5 — THE PoC, AND WHAT IT MUST TEST (add, remove, re-prioritise)

The author's planned proof-of-concept (one afternoon, stack only, no ISO —
per your own Q12 scoping) will attempt, in order:

1. **Gate #1 (cluster A/C):** rootless Podman + `runsc`: nginx in B
   (`network: none`) creates `/run/web/http.sock` on a shared volume;
   tor in A serves it as an onion service; a page loads over Tor.
2. **Gate #2:** B's view of the world from inside — no interface but
   loopback, no socket except its own, no key material reachable.
3. **Gate #3 (cluster E):** separate nft table + `ExecStartPre` hash gate
   under Quadlet units: corrupt the live table → A refuses to start /
   is stopped, and the failure is visible.
4. **Gate #4 (cluster D):** a package update triggers a local image
   rebuild and a clean roll of A/B with rollback to the previous tags.
5. **Gate #5:** `tor --list-modules` on the shipped tor build (PoW module
   present?) and PoW defences actually engaging under a load test.
6. **Gate #6 (cluster B):** `cryptsetup` re-key on a running LUKS system
   via the live-volume-key path (and the phrase-prompt fallback).

Reviewer: what is missing from this list that could kill a *fix* (not v1)
if it fails? Which gate should be first? Are any of these gates testing the
wrong thing — i.e., is there a cheaper test that proves more?

# PART 6 — RESPONSE TEMPLATE (return your review in this shape)

```
1. FIX VERDICTS — clusters A–K table (HOLDS / HOLDS WITH CORRECTIONS /
   FLAWED — REPLACE), one line of reasoning each
2. STEELMANNED CORRECTIONS — for each flawed or corrected fix, the
   mechanism as you would implement it
3. NEW CONTRADICTIONS INTRODUCED BY V2 (the Y-list) — scenario → what
   breaks → correction
4. S-LIST DISPOSITIONS — S1–S12 confirmed / cleared / escalated
5. ANSWERS — DQ1–DQ10
6. PoC LIST AMENDMENTS — added / removed / reordered gates, with reasons
7. IF YOU COULD REVERT EXACTLY ONE FIX back to its v1 form, which and why
8. GO / NO-GO for starting the alpha build on Design v2 as amended by
   your corrections — and the single correction that is non-negotiable
```

---
*End of delta pack. The full Design v2 document exists separately
(DESIGN-v2.md, 435 lines); this pack contains every mechanism at the
detail the author has specified it. Where this pack and v2 differ in
emphasis, this pack is the newer statement of intent. Attack accordingly.*

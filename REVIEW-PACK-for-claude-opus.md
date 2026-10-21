# REVIEW PACK — OnionHost OS (working name)
## For: Claude Opus 5.5, high thinking — steelman first, then red-team
## Prepared: 2026-10-10 · Status of the project: DESIGN ONLY. No code, no ISO exists yet.

---

# PART 0 — MESSAGE TO THE REVIEWER (read this first)

You are reviewing the design of a proposed Linux distribution. You have no prior
context; everything you need is in this document. Do not browse for the project —
it does not exist publicly. Judge what is written here.

## Your job, in this exact order

### Step 1 — STEELMAN (do this before any criticism)
Reconstruct the **strongest possible version** of this design:
- Assume the designers are competent. Where a passage is ambiguous, sloppy, or
  under-specified, first state the most defensible interpretation a competent
  implementer would build — *then* judge that version.
- Where the design gestures at a mechanism without specifying it, supply the
  best-known real-world mechanism (name actual software, configs, prior art)
  and evaluate the design *with* that mechanism in place.
- Explicitly list the design's genuinely good ideas — the ones a lesser design
  would have missed — and say why they are good. Be specific; flattery without
  mechanism is worthless.
- Produce a short section titled **"The strongest version of this design"**:
  the design as you would state it if you had to defend it in a room of
  Whonix, Tor Project, and Qubes engineers.

### Step 2 — ONLY THEN, RED-TEAM
Attack the steelmanned version, not the sloppy reading. Every criticism must
name: the concrete failure scenario (who does what, in what order), which
design claim it breaks (claims are numbered in Part 4), and a fix that a real
implementer could actually ship — or an honest statement that no fix exists
within the design's constraints.

### Step 3 — VERDICTS
Give a verdict on every numbered load-bearing claim in Part 4
(SOUND / SOUND WITH FIXES / UNSOUND), every pre-registered risk in Part 7
(re-rate severity × likelihood yourself; say if the author's rating is wrong),
and every question in Part 8 (answer, or state what evidence would answer it).

## Rules of engagement

- **No generic Tor/container boilerplate.** "Containers aren't VMs" and "Tor
  isn't perfect" are known and already conceded in the design. A criticism
  earns its place only if it identifies something this specific design gets
  wrong, misses, or contradicts itself on.
- **Internal contradictions are the highest-value finds.** The author suspects
  several already (Part 7.2). Find the rest.
- **Respect the user constraint.** Every proposal must remain operable by the
  target user (Part 2, §D2). A fix that requires a terminal, a config file, or
  a judgement call the user cannot make is not a fix — unless you argue the
  feature needing it should be cut.
- **Feasibility is in scope.** If a component cannot actually be built the way
  the design describes (API doesn't exist, two named features are mutually
  exclusive, a tool can't do that job), that is a first-class finding, with
  the working alternative named.
- **Separate your findings into:** (a) fatal — kills the concept or its core
  promise; (b) major — must fix before real users; (c) minor/polish;
  (d) inherent limits — restate them in one honest sentence each, the way the
  product itself should.

## Fixed vs negotiable (do not relitigate the fixed list unless it is FATAL)

**FIXED — settled by the product owner, treat as axioms:**
1. Target user: non-technical. Capability ceiling = a motivated 12-year-old.
   No terminal, no config editing, no invented passwords, ever.
2. Full-disk LUKS encryption, mandatory, with the passphrase typed at EVERY
   boot. No TPM/auto-unlock. Design intent: if the machine is unplugged and
   seized, it is a brick until the admin types the phrase.
3. The website runs in a Docker(-compatible) container. This is a product
   requirement, not just an implementation choice.
4. No exit relay is ever offered. Ever.
5. No port forwarding / no inbound ports on the user's router or host.
6. The product must work for a user behind NAT/CGNAT with no public IP.

**NEGOTIABLE — attack these freely if you have something better:**
- Base distro (Debian 12), installer (Calamares), desktop (stripped Xfce).
- Docker Engine vs rootless Docker vs Podman-with-Dockerfiles; gVisor vs
  runc vs Kata/microVM for the website container.
- Tor in its own container vs Tor on the host vs Tor in a separate VM.
- Diceware word phrases vs other generated-credential schemes; the Recovery
  Sheet concept; storing phrases in the OS keyring.
- Static-site default tier; the blog/files/BYOC tiers; the site editor model.
- Bridge relay opt-in; apt-over-Tor; local-only dashboard; update policy.
- The very name, framing, and whether minors are the audience or merely the
  capability benchmark.

## How to return your review (use Part 9's template)
Steelman first. Then findings by severity. Then claim verdicts, risk
re-ratings, and answers to Part 8's questions. End with: **"If I could change
exactly three things"** and **"Should this be built? — yes / yes with changes /
no, because…"**

---

# PART 1 — CONTEXT & GROUND FACTS (verified by the author, 2026-10-10)

- **What exists today:** this design, and feasibility checks. NO code, NO ISO,
  NO prototype. Do not assume any component has been validated in practice.
- **Feasibility already established:** every component named is off-the-shelf
  (Debian, Calamares, Docker, Tor onion services v3, gVisor, nftables, LUKS2).
  Onion services need only outbound connections → NAT/CGNAT/port-forwarding
  constraints (Fixed #5, #6) are satisfiable in principle.
- **Precedent the design consciously borrows:** Whonix (gateway/workstation
  split, applied here to inbound hosting), Diceware (generated passphrases),
  Calamares-based distros (Manjaro et al.), FreedomBox/Start9/YunoHost-style
  appliance UX (the comparison class — see Part 3).
- **Builder's estimate (challenge this too):** afternoon for an ugly
  end-to-end proof-of-concept; 3–5 days of build/test cycles for an alpha the
  author would run at home; weeks — dominated by hardware variance, Secure
  Boot, Wi-Fi firmware, and novice user testing, NOT by coding — for a
  product safe to hand to strangers.
- **Build environment constraint:** the builder's VM has no KVM acceleration;
  ISO install tests run under slow emulation. No physical test hardware has
  been used yet.
- **Business/distribution context:** a solo developer would publish the ISO
  for anyone to download. There is no company, no support team, no telemetry
  (telemetry would contradict the product's purpose). Support burden,
  distributor liability, and update infrastructure are therefore one-person
  scale — judge operational proposals against that.

---

# PART 2 — THE DESIGN, LAID OUT IN FULL (Design v1, with owner's 2026-10-10 encryption decision applied)

## D1. Vision

**Any ordinary home desktop can become a private website that nobody can
locate — installed by someone with no technical training, in one sitting, by
clicking through a wizard.**

The user never sees a terminal, never edits a config file, never forwards a
port on their router, and never invents a password. The system generates every
credential, proves to the user with plain-language checks that the site is
live and that its real location is hidden, and keeps the website in a sealed
box so that even a fully hacked website reveals nothing about the machine it
runs on.

The promise: 1. Download. 2. Boot from USB and click through the install.
3. Write down the passwords it gives you. 4. Name your site, click **Go Live**.
You get a `.onion` address and a QR code. That's the whole skill requirement.

Non-goals / limits the design itself concedes:
- It protects the server's *location and identity*, not the user from what
  they themselves publish (EXIF GPS, real name in a post). The wizard strips
  EXIF and warns; it cannot read minds.
- It does not defeat a global traffic-correlation adversary (Tor's own limit).
- If an attacker gets the admin/disk password, or physical access to the
  *running* machine, the game is over. Encryption protects a powered-off one.
- Docker alone is not a VM; the design layers isolation (§D5) to compensate.

## D2. Target user & capability ceiling

Design ceiling: a motivated 12-year-old. Reading level ~grade 6. Every screen
has ONE decision, defaults pre-selected. No typing long random strings
(passwords are generated word phrases, §D4). No question whose wrong answer
breaks the install; dangerous options are absent, not warned about. Success
is shown, not asserted: green check cards, a working QR code, a "visit my
site" test button.

## D3. The journey

**Stage A — Get it.** Download ISO (~2–3 GB) + one-page "make a USB stick"
guide (balenaEtcher, 3 clicks, Windows/Mac/Linux).

**Stage B — Install (Calamares graphical installer, ~7 screens).**
1. Language (auto-detected). 2. Timezone map + keyboard (auto-matched).
3. Internet: Ethernet automatic; Wi-Fi = list + password. (Internet is for
Tor, NOT for installing — the ISO installs fully offline.)
4. Disk: one friendly option, *"Use the whole disk — this erases everything
on this computer,"* the disk named in plain words. Manual partitioning behind
an Advanced door. **Full-disk LUKS2 encryption is NOT optional.**
5. Disk password: a generated word phrase (§D4); user writes it down and
proves possession by re-typing two of its words.
6. Name & login: user picks a username; login password is a second generated
phrase (different from the disk phrase).
7. Install progress (10–20 min) → "Remove the USB stick and press Restart."

**Boot behaviour (FIXED #2):** disk phrase typed at EVERY boot; no
TPM/auto-unlock. Unplugged or power-cut machine returns locked and stays
locked — site down, data unreadable — until the admin physically types it.
Screen 5 states this trade plainly.

**Stage C — First-boot wizard (OOBE, ~5 screens; desktop shows nothing else
until done).**
1. **Name your site** (title + one sentence; the `.onion` address itself is
cryptographic, unchoosable; vanity addresses are a deliberate non-feature).
2. **Site type**, risk-tiered cards, safest first:
   - *Simple pages* (DEFAULT): text/photos built from a form. Static.
   - *Blog*: adds a database container (§D5).
   - *Files*: private upload/download page.
   - *Bring your own Docker container* (Advanced): user's image under the
     same sealed network rules — it physically cannot get internet access.
3. **Website password**: generated phrase (§D4), for site types with a login.
4. **Help the Tor network?** Optional relay question, default OFF (§D7).
5. **Go Live**: builds containers, starts Tor, waits until the onion service
is reachable, runs the self-check battery (§D6). Ends on: the `.onion`
address large, QR code, **[Print my Recovery Sheet]**, **[Visit my site]**
(pre-installed Tor Browser opens the new address).

**Stage D — Daily life (stripped Xfce desktop, 4 big icons).**
- **My Site**: local-only editor; publishes into the read-only web volume via
  a host-side publisher service (§D5).
- **Dashboard**: green/amber cards only — Site is live · Location-hidden
  test: passed (with date) · Backups · Updates. One red **Site OFF** button
  (stops Tor; site unreachable in seconds). Key-shredding "panic wipe" sits
  behind hold-to-confirm (destroying the onion key is irreversible).
- **Backup** (§D8). **Settings**: updates, relay toggle, passwords.
- No other inbound service. SSH is OFF and absent from the UI. Dashboard
  binds to 127.0.0.1 only. Remote admin, if ever shipped, would be a SEPARATE
  admin onion service with Tor client-authorization — never the public
  site's login page.

## D4. Generated passwords

Random strings (`xK9$mQ2!`) fail this user — untypeable, unwritable, lost.
Every human credential is instead a generated **Diceware-style word phrase**:
- Disk passphrase: 6 words + a digit (~77 bits), e.g.
  `cleft apricot 7 banjo tundra velvet moss`.
- Login password: 5 words, different draw. Website admin: 5 words, different.
- Machine-only secrets (database etc.): 256-bit, never shown, stored as
  Docker secret files; the user never meets them.

Rules:
- **Never reuse** one phrase across jobs. Wizard's explanation: *"If someone
  finds one paper, they shouldn't get everything."*
- **Prove possession, gently:** after showing a phrase it is hidden; user
  re-types word #2 and word #5. Fail → shown again. No scolding.
- **Recovery Sheet** (the centrepiece): ONE printable page — `.onion` address
  + QR, **all three phrases** labelled in plain words ("Disk password — you
  type this when the computer starts"), date, and *"Keep this paper somewhere
  private. Anyone with this paper controls your site."* Also offered as a
  file encrypted under the disk phrase, saved to a USB stick. Printing is
  nudged hard; a warning shows that photographing it into cloud photos is
  making a copy of the keys.
- The phrases ALSO live in the local OS keyring, viewable by a logged-in
  admin behind the login password, so the paper is a backup rather than the
  only copy. (Author's accepted trade-off: convenience for this user over
  marginal risk, because the disk itself is encrypted.)

## D5. Architecture

**The traffic fact the whole design turns on:** an onion service never uses
an "exit" relay. Visitor and server meet *inside* the Tor network at a
rendezvous point; neither leaves Tor; neither learns the other's IP. The
server's Tor process makes only OUTBOUND connections (to its guard). Hence:
no inbound ports, no router changes, works behind NAT/CGNAT.

**Compartments** (the Whonix gateway/workstation split, inverted for inbound
hosting — Tor gets its own container, which is the ONLY container allowed to
reach the internet, and all it speaks is Tor):

```
Visitor's Tor Browser
   │  Tor network (guard → rendezvous)     server connects OUT; nothing inbound
   ▼
HOST OS — Debian 12, LUKS2, minimal. No website code, no inbound ports,
          nftables default-drop in AND out except the exceptions below,
          AppArmor, unattended security updates, dashboard on 127.0.0.1 only.
   │
   ├─ CONTAINER A — TOR GATEWAY. tor daemon only; no shell tools, no web
   │     code. HOLDS THE ONION PRIVATE KEY (the site's identity) in its own
   │     volume, mode 0700. SocksPort OFF. ControlPort = unix socket, never
   │     shared with B. HiddenServicePort 80 → B:80.
   │        │  A initiates to B:80. B may initiate NOTHING to A or anywhere;
   │        ▼  replies travel on established connections only.
   ├─ CONTAINER B — WEBSITE. nginx-unprivileged (uid 101) + site files
   │     (static by default). Read-only rootfs, cap_drop ALL,
   │     no-new-privileges, seccomp + AppArmor, gVisor (runsc) runtime,
   │     resource ceilings. NO internet route, NO DNS, NO docker socket,
   │     NO keys, NO credentials (blog tier: a DB secret only).
   │        │  backend network only
   │        ▼
   └─ CONTAINER C — DATABASE (blog tier only). Own volume. Reachable only
         from B; reachable from nothing else; on no other network.
```

**Networks (Docker):**

| Network | Members | internal | Gateway/DNS | Purpose |
|---|---|---|---|---|
| tor-egress | Tor gateway only | no | host NAT, egress-filtered | A ↔ internet, Tor ports only |
| onion-front | Tor gateway + Website | YES | none / none | A forwards visitor requests to B:80 |
| site-back | Website + Database | YES | none / none | B ↔ C only |

B sits on NO network with a gateway. In B's routing table: the front-network
peer (replies only) and C. No DNS server is configured — names are
meaningless inside B by design. Site content is mounted into B **read-only**;
the only writer is a host-side publisher service reachable from no network.

**Host firewall (nftables) — second, independent wall** (Docker config alone
is not trusted): INPUT default drop; from onion-front/site-back subnets, drop
everything toward the host except the single forwarded web path;
FORWARD/OUTPUT default drop for container subnets except A → internet on
Tor-usable ports (443/9001…) via IPv4 NAT; **IPv6 from all container networks
dropped entirely**. Host's own egress (updates) is a separate host-only rule
containers cannot use; apt-over-Tor is the stated hardening for OS updates,
"where the package source supports it," default-on for Tor's own updates.

**Why the key lives in A, not B (design's #1 decision):** the `.onion`
address *is* its private key. B parses untrusted input all day and is the
component most likely to be compromised; therefore B must never hold the
identity it serves. Hacked site → delete and rebuild B in minutes, address
survives. Stolen key → attacker *becomes* the site, permanently, from
anywhere.

**Container hardening:** rootless Docker / userns-remap (root inside =
unprivileged outside — NOTE: author lists both; see Part 7.2); read-only
rootfs; single small tmpfs /tmp; cap_drop ALL; no-new-privileges; default
seccomp + AppArmor; **gVisor runsc is the DEFAULT runtime for B** (fallback
to runc only if hardware can't, and Dashboard shows an amber card — the user
sees the downgrade); CPU/RAM/PID ceilings on B and C; images pinned by
digest, signature-checked (cosign) at build/first run; B's image has no
package manager and minimal tooling.

## D6. If the website is fully hacked — the design's attack walk

Assume RCE in the website, escalated to root inside container B:
1. **"What's the server's IP?"** No default route, no DNS — outbound attempts
   die in the internal networks. Hostname (`onionhost`), env, /etc/hosts are
   generic. The only gateway-like address visible is a private Docker bridge
   IP, which identifies nothing.
2. **"Scan the home LAN / attack the router"** — no route exists; host
   firewall independently drops container→LAN.
3. **"Steal the onion identity"** — key is in A; B has no socket, port, or
   mount that reaches it. Tor control socket not shared.
4. **"Persist / botnet / mine"** — read-only rootfs; nightly automatic
   restart restores a pristine image; no egress makes it useless as a
   botnet/spam node even while compromised; ceilings cap mining.
5. **"Attack Tor"** — B can initiate nothing to A; A listens on no
   front-network port; only flow is A's forwarded HTTP to B:80 + replies.
6. **"Read the PC's other data"** — B's mounts: site content (ro), nothing
   else. No home dir, no docker.sock, host /proc masked (gVisor).
7. **Detection** — egress attempts, ceiling hits, integrity drift are logged
   host-side; Dashboard's "Location hidden" card goes amber; daily
   self-checks fail loudly instead of silently.

Conceded attacker wins: defacing/deleting the *public site content itself*
(answer: backups, §D8) and reading whatever the site itself can read (blog DB
contents in tier 2 — why the default tier is static and holds no secrets).

**Self-check battery** (at Go Live and daily, shown as plain cards): from
inside B, attempts that must all FAIL — reach the internet by raw IP, resolve
a DNS name, reach the host, reach the LAN router, reach A's control port,
read the onion key. From the host: no inbound ports listening, Tor reports
the service published, firewall matches the golden config. Any unexpected
pass → site does not go live / Dashboard red.

## D7. The relay question — separate feature, default OFF

Hosting needs NO relay. A relay donates bandwidth to strangers' circuits.
- **Bridge** (unlisted; helps censored users connect): low bandwidth, low
  risk. The one friendly wizard option — still default OFF, with a monthly
  bandwidth cap.
- **Middle/guard relay**: needs a publicly reachable port (fails on CGNAT);
  Advanced door only.
- **Exit relay**: NOT OFFERED (Fixed #4). A consumer product must not put a
  novice household's IP at the receiving end of strangers' exit traffic,
  abuse complaints, and police visits.
A (the site's own Tor gateway) is not a relay in this sense — it carries only
the site's own onion-service circuits.

## D8. Backup, restore, updates, off-switch

- **Backup**: one button → encrypted archive (described as "age/LUKS-
  encrypted under the disk phrase") containing site content, DB dump, onion
  key, config. Restore onto a fresh install reproduces the SAME `.onion`
  address. Wizard: *"This backup IS your website. Guard it like the Recovery
  Sheet."*
- **Updates**: host + Tor security updates automatic. Container images update
  via a Dashboard approval card with one-click rollback (a bad unattended
  update must never brick a novice's site at 2 a.m.).
- **Off**: Site OFF stops container A; address becomes unreachable almost
  immediately. Disk stays encrypted at rest.

## D9. Settled defaults (author's table — all NEGOTIABLE except where Fixed)

Debian 12 · Calamares · stripped Xfce (4 icons) · LUKS2 mandatory ·
Diceware phrases (3, separate) · boot unlock typed every boot, no auto-unlock
· static site default · Docker + gVisor for the website · Tor in own
container holding the key · relay off, bridge opt-in · SSH off, not in UI ·
admin local-desktop only · container IPv6 blocked.

## D10. What the design concedes it cannot do

- Global traffic-correlation adversary (inherited Tor limit).
- gVisor reduces, does not eliminate, kernel/host risk. A v2 could use a
  microVM (Kata/Firecracker) for B under the same wizard; compartment lines
  in §D5 were drawn so that swap changes nothing else.
- The human is the softest part; the Recovery Sheet is the design's answer
  and the author claims there is no better one for this user.

---

# PART 3 — ALTERNATIVES YOU MUST ARGUE (against the design, seriously)

For each alternative: state its strongest form, where it BEATS this design,
where it loses, and whether the design should switch, borrow, or stay.
Do not strawman any of them.

1. **Whonix-style two VMs** (gateway VM + workstation/server VM under KVM)
   instead of two containers on one host. Stronger isolation; heavier RAM,
   harder install on random old desktops, more moving parts for a novice.
2. **Podman (rootless by default, daemonless, Quadlet/systemd units)**
   instead of Docker Engine. The design's Fixed #3 says "Docker(-compatible)"
   — is Podman within the spirit? What breaks (gVisor runtime wiring,
   Docker network `internal` semantics, user familiarity)?
3. **Tor on the HOST, website in the only container.** Simpler networking,
   one less container to attack through — but the key then lives on the host
   and HiddenServicePort must target a published container port. Compare
   honestly against §D5's key-isolation argument.
4. **Existing products**: FreedomBox, YunoHost, Start9, Umbrel, CasaOS —
   could this product BE a Tor-hosting app/profile on top of one of them
   instead of a new distro? What does a new ISO buy that a profile doesn't?
   What does it cost (maintenance, trust, install base)?
5. **Live/amnesic model (Tails-style)**: boot-from-USB, site lives only while
   booted, optional encrypted persistence. Rejected implicitly by the
   install-to-disk design — was that right for a *server*?
6. **NixOS / image-based immutable host** (or Fedora CoreOS-style) instead of
   mutable Debian + unattended-upgrades. Declarative rollback vs the
   one-person maintenance reality in Part 1.
7. **No custom OS at all**: a one-click installer *application* for existing
   Ubuntu/Debian machines. Argue for or against killing the ISO.

# PART 4 — LOAD-BEARING CLAIMS (verdict required on each)

If one of these falls, a major part of the design falls with it. For each:
**SOUND / SOUND WITH FIXES / UNSOUND** + your reasoning + the fix, if any.

- **C1 — Location secrecy under full website compromise.** An attacker with
  root inside B cannot learn the host's public IP, LAN topology beyond the
  bridge, or any identifier that locates the household.
- **C2 — Key isolation.** B's compromise cannot yield the onion private key,
  and rebuilding B preserves the address. (Includes: is A's attack surface
  really as small as claimed, given A must parse Tor protocol traffic and
  initiate connections to B?)
- **C3 — No-egress containment.** A compromised B is useless as a botnet/
  spam/mining node and cannot be used to attack third parties, not merely
  prevented from reaching the internet "by IP" (consider: DNS-over-HTTPS to
  allowed-looking endpoints, traffic via A somehow, ICMP, timing channels,
  the rendezvous path itself as an exfil/relay channel — the attacker DOES
  have one legitimate channel: serving HTTP responses to visitors, possibly
  including colluding visitors).
- **C4 — The wizard is completable by the target user.** A motivated
  12-year-old, alone, with only the USB guide and the screens described,
  reaches Go Live with a working, *correctly secured* install — including
  the passphrase write-down-and-verify ritual and the whole-disk erase
  decision.
- **C5 — Generated Diceware phrases are net-safer than user-chosen passwords
  for this population**, counting real-world behaviour (loss, reuse across
  the three phrases, photographing the sheet, family members finding it),
  not just entropy arithmetic.
- **C6 — Manual LUKS unlock at every boot is the right fixed trade** for a
  home server: seizure protection bought, power-cut downtime and
  "user just leaves it off / writes phrase on the case" failure modes paid.
- **C7 — The self-check battery can actually detect the failures that
  matter**, including silent ones (firewall rule lost after a Docker daemon
  restart/update, IPv6 re-enabled by a kernel update, a container quietly
  re-created by compose without `internal: true`).
- **C8 — Updates will not eventually break or silently de-harden the box**
  under the stated policy (automatic host/Tor, approval-gated container
  images, one solo maintainer, no telemetry).
- **C9 — Calamares can deliver this install** — offline install including
  Docker + Tor packages, LUKS2-by-default, and either a generated-phrase
  flow in-install or a pre-install generator that hands the phrase to the
  installer without leaking it (to logs, process lists, swap, the live
  session's own persistence).
- **C10 — gVisor as B's default runtime is compatible** with everything B
  must do (nginx serving, the blog tier's stack, the BYOC tier's arbitrary
  images) at acceptable performance on old home hardware — and the fallback
  story doesn't quietly become the universal reality.
- **C11 — "Nobody can locate it" is an honest product claim** as the public,
  ISPs, Tor directory infrastructure, and a determined investigator each see
  the system. State the precise claim the product MAY make, worded exactly.
- **C12 — The Recovery Sheet system survives contact with reality**: printers
  (shared, work/school, print logs), photos/cloud sync, household members,
  house fires, and the user's future self who lost it. What then?

# PART 5 — EXHAUSTIVE AUDIT CHECKLISTS (go beyond what's listed)

## 5.1 IP/identity leak vectors — audit each, then add any we missed
Outbound application calls (update checks, oEmbed, gravatar, webmentions,
plugin phone-home) · DNS (system resolver, DoH/DoT from inside B, DNS via A)
· IPv6 (link-local, ULA, RA/SLAAC inside containers, host stack) · NTP/clock
(theft of timing, clock-skew fingerprinting, Tor's own clock needs) ·
Docker metadata (bridge IPs, container hostnames, /etc/resolv.conf contents,
MAC addresses, image labels) · HTTP layer (Server header, error pages,
ETag/timestamps, TLS certs if any, favicon hashes) · Tor layer (guard
selection & persistence, HSDir descriptors, intro-point behaviour, v3 client
authorisation absence, proof-of-work/DoS settings, Tor version fingerprint)
· Host layer (apt traffic, crash reports, mDNS/LLMNR/SSDP, CUPS/printer
discovery, Bluetooth/Wi-Fi beacons, hostname from DHCP, ISP-visible Tor
usage itself) · Content layer (EXIF, usernames, writing style, posting
times/timezone, language/locale of the OS install) · Admin layer (Dashboard
on localhost vs the user's normal browsing — DNS rebinding, CSRF, a malicious website
in a browser reaching 127.0.0.1 services, the local editor's preview
server) · Physical layer (suspend/sleep leaving LUKS keys in RAM, screen
lock vs disk lock, swap/hibernation images, SSD wear-levelling remnants,
the install USB left in the machine).

## 5.2 Attack trees to flesh out (attacker goals; design must break each path)
(1) Locate the household. (2) Become the site (key theft / descriptor
manipulation). (3) Persist across the nightly restart. (4) Pivot to the home
LAN or the admin's other devices. (5) Use the box against third parties.
(6) Ransom/lock the owner out of their own site. (7) Identify the OWNER (not
the box) — including via the Recovery Sheet, the backup file, printer/cloud
artefacts, and the act of downloading the ISO itself. (8) Supply-chain:
compromise the ISO or an update such that ALL installs leak at once.

## 5.3 UX failure modes (assume the user is 12, tired, and rushing)
Erases the family PC's disk despite the warning · cannot re-type words #2/#5
(dyslexia, non-native language, wordlist language mismatch — whose wordlist,
which languages?) · writes phrases on the PC case / a sticky note on the
monitor · Go Live self-check fails red with no comprehensible next step ·
power cut mid-install · Wi-Fi-only install on a chipset needing non-free
firmware the ISO lacks · Secure Boot refuses the USB and the guide's answer
("disable Secure Boot") teaches a dangerous habit or strands the user in
BIOS screens the design pretends don't exist · printer absent (Recovery
Sheet becomes a photographed screen) · the site works but the QR scan opens
the address in a normal browser and "fails," convincing the user it's broken.

## 5.4 Operational failure modes (month 6, not day 1)
Disk fills (logs, file-tier uploads, DB growth) → LUKS/Tor/Docker behaviour
when full · Tor guard rotates or the ISP starts blocking Tor → bridges for
the *server's own* outbound connection (pluggable transports for onion
services — does the design need them?) · Docker daemon or nftables rules
regress after a security update · container image upstream disappears or is
compromised · the solo maintainer disappears — what do installed boxes do in
year 2? · Tor network deprecates v3 feature the design relies on · user
forgets DISK phrase (total loss — is that acceptable product behaviour, and
does the wizard make the consequence truly understood?) · backup restore
never tested by the user until the disk dies.

# PART 6 — SCENARIOS (walk each; does the design hold?)

1. **The raid.** Police seize the DESKTOP WHILE IT IS RUNNING and keep it
   powered in transport. Then the same raid, machine found OFF. Then found
   ASLEEP/SUSPENDED. What does LUKS + this design actually deliver in each?
2. **The defacer.** Skilled attacker, full B compromise, one goal: figure
   out where in the world this house is, with a week to try.
3. **The curious sibling.** Teen in the same house, physical access to the
   running, logged-in desktop, no passwords. What can they get?
4. **The bad update.** A routine automatic host update changes Docker's
   default network behaviour. Walk what users experience and how (if ever)
   anyone notices.
5. **The viral moment.** The site gets linked somewhere big; 50k visitors in
   a day hit an onion service on a home connection and an old desktop. What
   breaks first — and does it break *safe*?
6. **The second user.** A visitor uses the Files tier to upload illegal
   material to someone's box. The owner doesn't know. Who is holding what,
   legally and practically? (Also: what does this imply for the DISTRIBUTOR
   of the ISO?)

---

# PART 7 — RISK REGISTER

## 7.1 Author's pre-registered risks (re-rate each: severity × likelihood)

| # | Risk | Author rating |
|---|---|---|
| R1 | Container escape (kernel/gVisor bug) → host, from a fully-hacked B | High sev · Low lik |
| R2 | Firewall rules silently lost/reordered after Docker or OS update; site keeps "working" while leaking or exposed | High · Medium |
| R3 | User behaviour defeats credential design (photo of sheet in cloud, phrase on the case, sheet lost = total loss) | High · High |
| R4 | Secure Boot / Wi-Fi firmware / BIOS variance strands novices mid-install; support burden lands on one person | Medium · High |
| R5 | Tor-level DoS against the onion service; design currently names NO specific countermeasure | Medium · Medium |
| R6 | Update/signing infrastructure (ISO + image updates) is a single point of total compromise for all installs | Critical · Low |
| R7 | The local Dashboard/editor/publisher services become the soft underbelly — host-side code reachable or triggerable in ways the containers never were | High · Medium |
| R8 | Product/distributor risk: the tool foreseeably hosts harmful/illegal sites; a 12-year-old capability benchmark drifts into marketing TO minors | High · Medium |
| R9 | Performance: gVisor + old desktop + Tor + a traffic spike = site dies, or gVisor gets switched off by users/guides and stays off | Medium · Medium |
| R10 | Solo-maintainer bus factor: updates stop, Tor/Debian move on, installed fleet quietly rots while dashboards stay green | High · Medium (long horizon) |

## 7.2 Internal inconsistencies the author ALREADY suspects (confirm, resolve, find more)

- **X1 — The Recovery Sheet contradicts the separation rule.** §D4 says
  phrases are separated so "one paper" shouldn't yield everything, then puts
  ALL THREE phrases on ONE sheet. Resolve: is the sheet one secret (accept
  it and rewrite the rule) or should disk phrase be sheet-only and the rest
  elsewhere?
- **X2 — Rootless AND userns-remap.** §D5 lists both; in Docker these are
  alternative daemon modes, not stackable settings. Which one does the
  design actually mean, and does gVisor change the answer?
- **X3 — gVisor is "optional" in §D1/§D10 but "default" in §D5/§D9.** Decide,
  and state what the product may claim in each case.
- **X4 — apt-over-Tor bootstrap.** Updates "over Tor, default-on for Tor
  itself" — Tor updating itself through itself, before first Tor start, and
  apt's metadata/timing exposure. Specify a non-circular update path.
- **X5 — Backup "encrypted under the disk phrase."** A human phrase as the
  sole protection for a file containing the onion KEY: offline attack if the
  backup is stolen, KDF unspecified, and phrase reuse across disk+backup.
  Specify (e.g., age/scrypt parameters) or redesign.
- **X6 — Keyring storage vs separation.** All phrases in the OS keyring
  behind the login phrase collapses three secrets into one for anyone who
  gets a logged-in session (scenario: the curious sibling, Part 6.3). Is the
  accepted trade-off actually acceptable?
- **X7 — "No shell tools" Tor container that must also be updatable,
  diagnosable, and PoW-configurable by a UI a novice uses.** Where do
  diagnostics run, and does adding them reopen the surface?
- **X8 — Self-check section cross-references itself** (§D6 calls the battery
  "§6" inside §6; document rot in miniature). Trivial — included as a canary:
  if the DESIGN DOC drifts this fast, what keeps the golden firewall config,
  docs, and dashboard claims in sync in the real product?

# PART 8 — SPECIFIC QUESTIONS (answer each, briefly, after your main findings)

**Architecture**
Q1. Two containers, one host — or is a VM boundary for B (Kata/Firecracker)
   actually REQUIRED for C1 to be claimable? State the exact wording C1
   survives under each option.
Q2. Is there any legitimate flow in which B initiates a connection the design
   missed (healthchecks, OCSP, NTP, logging, metrics)? List them all.
Q3. Should A and B communicate over a shared internal network at all, vs
   alternatives (A publishes 127.0.0.1 via a socket-proxy; vsock; a
   file/pipe rendezvous)? Compare attack surface concretely.
Q4. Tor onion-service DoS: should the design enable Tor's proof-of-work
   defence, connection limits, or intro-point controls by default? What does
   each cost a legitimate visitor on Tor Browser?
Q5. Pluggable transports for the SERVER's own guard connection (ISP Tor
   blocking, hostile networks): in-scope for v1, or a documented dead end for
   users in censored countries? The vision says "anyone, anywhere."

**Credentials & recovery**
Q6. Wordlist: EFF large list is English. Design the non-English story, or
   explicitly scope it out?
Q7. If the disk phrase is lost, total loss is by design. Should the wizard
   offer ANY escrow (e.g., a sealed second copy flow — a second USB "spare
   key" created at install)? Argue both sides against the Fixed constraints.
Q8. Recovery Sheet printing: home printer vs none — is a hand-copy-only flow
   (no print button, write it by hand, verified by re-typing) actually
   SAFER and better for this user? 

**Product & safety**
Q9. Is "capability ceiling = 12-year-old" a design benchmark or a marketing
   audience? If a real 12-year-old uses this to host a site, what duties
   appear (safeguarding, parental consent, jurisdiction) that the design
   currently ignores? Recommend exact positioning language.
Q10. The distributor's exposure: shipping a turnkey anonymous-hosting OS —
    what should the solo developer do/avoid (hosting the download, signing
    keys, a project website on the clearnet, a support forum) to not become
    the de facto operator in investigators' eyes?
Q11. Name the honest one-sentence claim (for C11) that marketing may use,
    and three claims it must NEVER use.

**Build & operations**
Q12. Builder's tier estimates (Part 1) — realistic? Re-estimate each tier
    with your reasoning, naming the tasks the author has forgotten.
Q13. The golden-config drift problem (R2/C7/X8): design ONE concrete
    mechanism (not "monitoring") that makes de-hardening loud and rare.
Q14. Bus factor (R10): what is the minimum viable "this project is dead"
    graceful-degradation design for installed boxes?

# PART 9 — RESPONSE TEMPLATE (return your review in this shape)

```
1. THE STRONGEST VERSION OF THIS DESIGN (steelman — mechanisms named)
2. WHAT THIS DESIGN GETS GENUINELY RIGHT (specific, earned)
3. FATAL FINDINGS (or "none" — with what you checked to be sure)
4. MAJOR FINDINGS (scenario → claim broken → shippable fix)
5. MINOR FINDINGS & POLISH
6. CLAIM VERDICTS — C1..C12 table
7. RISK RE-RATINGS — R1..R10 table + any risks the author missed entirely
8. INCONSISTENCY RESOLUTIONS — X1..X8 + new ones found
9. ALTERNATIVES — Part 3 verdicts (switch / borrow / stay, per item)
10. ANSWERS — Q1..Q14
11. SCENARIOS — Part 6 walkthroughs, one paragraph each
12. IF I COULD CHANGE EXACTLY THREE THINGS
13. SHOULD THIS BE BUILT? yes / yes-with-changes / no — and the single
    strongest reason
```

---
*End of review pack. Reviewer: everything above the line is the complete
brief. The design's own document is Part 2; Parts 3–8 are the author's
attempt to make your attack as strong as possible. Do the same for us.*

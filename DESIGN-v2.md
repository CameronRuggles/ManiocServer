# OnionHost OS — Design v2 (working name)
## Revised 2026-10-10 after Claude Opus 5.5 design review of v1
## Status: DESIGN ONLY. No code, no ISO exists yet.

# 0. What changed from v1, in one paragraph

Opus's verdict on v1: build it, with changes — no fatal findings against the
concept, one fatal finding against the tagline. v2 adopts all twelve major
findings (M1–M12), all eight author-suspected contradictions (X1–X8), and
most of the nine new ones (X9–X17). The three structural changes: **(1)** the
website container now has *no network at all* — Tor reaches it over a unix
socket; **(2)** there is now exactly *one human secret* — a 7-word disk
phrase, hand-copied — and every other credential is resettable through it
instead of stored or printed beside it; **(3)** the trust chain is
Debian-native — container images are built locally from signed Debian / Tor
Project packages and rebuilt automatically, the maintainer signs only one
small package, and a hash-gated firewall table decides whether Tor may start
at all. Base moves to **Debian 13**. Two tiers are cut from v1 (BYOC,
WordPress-style blog) and one is restricted (Files becomes invite-only).
Full mapping to the review: Appendix A.

# 1. Positioning and honest claims (was v1 §1, rewritten per M-Claims/Q9/Q11)

**Audience: adults.** "Simple enough for a 12-year-old" remains the internal
usability benchmark and appears on NO public surface (site, docs, README).
Public positioning, in full: *"No technical skills needed. For adults (18+)."*

**The one claim marketing may make** (reviewer's wording, adopted):
"OnionHost publishes your website as a Tor onion service, which hides your
computer's network address from visitors and from the website software
itself."

**Claims never made:** "nobody can locate you" / "untraceable"; "anonymous"
applied to the owner; "safe to publish anything."

**Stated plainly in the wizard and docs:**
- Your internet provider can see that this computer uses Tor, around the
  clock. What Tor hides is *which site* it serves and *where visitors are*.
- Someone patiently watching when the site is up or down can learn rough
  facts (timezone-scale) about where it lives. Timing mitigations (§5) shrink
  this; they do not erase it. (M1)
- Encryption protects the site only when the computer is **fully shut down**
  — not when running, locked, or (sleep is disabled, §2) asleep. (M11)
- Not for use where Tor is blocked or illegal. Pluggable transports for the
  server's own connection are a v1.1 item (§8), not a v1 promise — the v1
  vision line "anyone, anywhere" is withdrawn. (X17)
- Evil-maid attacks against the unencrypted /boot are out of scope.

**Differentiation** (the comparison v1 missed): OnionShare already does easy
point-and-click onion hosting on an existing computer — with no containment,
no persistence-as-server, and the key living next to everything. StartOS and
its peers ship onion addresses without promising containment under compromise.
OnionHost's reason to exist is precisely: **hardened, persistent, contained.**

# 2. Base system and install (M4, M10, M12)

- **Debian 13 (trixie), minimal**, built with live-build on Debian's signed
  shim/GRUB/kernel → boots under Secure Boot; the user never opens BIOS
  settings *for signatures*. (The boot-*menu* key problem remains and is
  handled by a per-vendor F12/F11/Esc guide in the USB instructions — R4.)
- **Stripped host**: no avahi, no cups-browsed, no bluetooth, no
  ModemManager (M6). DHCP hostname is generic. Sleep/suspend/hibernate
  targets are **masked** — the machine never sleeps with keys in RAM (M11).
  Screen auto-locks after 5 minutes; **all site services run with nobody
  logged in** — a reboot lands on a login screen and the site comes up
  regardless once the disk is unlocked.
- **Calamares 3.3.x**, `luksGeneration: luks2`, argon2id with a floor of
  1 GiB memory cost and ~2 s unlock-time target (low-RAM machines, review §5).
  Unencrypted /boot; root+swap inside LUKS2. Live session boots `noswap`.
- **Custom QML installer page generates the disk phrase in-process** and
  feeds it to cryptsetup **on stdin, never argv** (nothing in process lists
  or logs; Calamares globalstorage checked for dumps at build time, C9).
- **Keymap trap fixed (M4/N2):** the initramfs carries the console keymap
  matching the installer's layout choice (`KEYMAP=y` etc.), so the phrase
  verified under the installer's keymap is the phrase that works at the
  boot prompt under AZERTY/QWERTZ/etc.
- **Erase screen (M10):** the installer detects existing OSes/data and names
  them ("Windows 11 — about 412 GB of files, including Photos and Documents,
  will be erased"), and requires **typing a confirmation word**, not a
  click. The download guide leads with: *"This computer will only run your
  website. Use a spare one."*
- **First-boot confidence screen:** after the install reboot and first real
  unlock, one screen: "You just typed your disk password at the real boot
  prompt — it works. Keep the paper safe." (Turns the scariest failure —
  locked out at first reboot — into a verified success before setup begins.)

# 3. Credentials v2 — ONE human secret (M4, X1, X6, Q7, Q8)

The v1 model's three printed phrases collapse into this:

- **The disk phrase is the only paper secret.** 7 words, Diceware-style from
  the EFF large list (ASCII-only words, ~90 bits), **no digit** (digits were
  a keymap/shift trap). **Hand-copied by default**, on its own page — the
  printer flow is not offered for the phrase (spool files, network-printer
  logs, other people's printers, review Q8). Verification re-typing uses
  **randomised word positions** (not always #2/#5 — v1's predictable pair
  taught users to memorise two words).
- **The .onion address + QR live on a SEPARATE, non-secret page.** It can be
  displayed/printed freely; nothing secret shares its page, so no single
  artefact links owner → address → keys. QR page carries: "Open with Tor
  Browser (Android) or Onion Browser (iPhone)" plus a second QR to the Tor
  download page (review §5 — QRs opened in a phone's stock browser "fail"
  and convince users the site is broken).
- **Spare key (optional wizard step):** a second, different phrase in a
  second LUKS keyslot, hand-copied on a "Spare key" page; the wizard asks
  the user to name who will hold it. Revocable in Dashboard (kills the
  slot). Still typed, never automatic — inside Fixed #2. (Q7)
- **Computer login = a convenience PIN/short password the user chooses** in
  the first-boot wizard (first session is one-time autologin into setup).
  Its only jobs are screen-unlock and everyday sudo. It is explicitly NOT a
  data-protection secret: the disk phrase is. Forgetting it is recoverable
  (below), so its strength barely matters.
- **Website admin password:** generated at Go Live, shown once. Only its
  hash exists on the box (in the site config). It is stored NOWHERE in
  readable form — the keyring copy from v1 is **deleted** (X6: anything in
  the logged-in session could read it; the "re-prompt" was a UI curtain).
- **Reset, don't store:** a "Reset passwords" entry in the boot menu runs
  *after* LUKS unlock and lets whoever passed the disk prompt reset the
  login PIN and regenerate the website password. Day-to-day equivalent:
  Dashboard → Reset, behind a polkit prompt.
- **Re-key, don't retrieve (M4):** "Lost your paper?" while the box runs →
  Dashboard "Make a new disk password": a root helper adds a new keyslot
  (using the live volume key; implementation to verify at alpha — fallback:
  prompt for the current phrase, standard `luksAddKey`) and kills the old
  slot. The user hand-copies the NEW phrase. The old paper becomes waste.
  This is why the disk phrase needs no stored copy anywhere: the circle in
  v1 (keyring copy readable only after unlock, i.e. only when unneeded) is
  gone.
- **Backups** are encrypted with `age` in passphrase mode (scrypt) under the
  disk phrase (X5 resolved): disk and backup protect the *same* asset, so
  reuse is sound at ~90 bits; wizard adds "Don't keep the backup stick in
  the same drawer as the paper." Exporting a backup from Dashboard requires
  typing the disk phrase (verified against the LUKS header), so a borrowed
  logged-in session cannot silently exfiltrate the onion key.

# 4. Compartments v2 (M2, M8, X2, X3)

Engine decision (flagged, see Appendix B): **Podman, rootless, via Quadlet
systemd units**, running OCI images built from ordinary Dockerfiles. This
keeps the product requirement — the website ships and runs as a Dockerfile —
while gaining daemonless operation and native systemd ordering/gating, which
the firewall gate (§6) needs. Documented fallback if the PoC gate (App. B)
fails: rootful Docker + `runsc`, no userns-remap. `userns-remap` is dropped
from the design in both branches (X2: it never stacked with the other modes
anyway; gVisor's Sentry is the boundary that does the work).

```
Visitor's Tor Browser ── Tor network ──► (server connects OUT to its guard)
HOST — Debian 13, LUKS2, stripped (§2). No inbound ports. No TCP admin
       listeners at all. Golden-config source generates everything (§6).
 │
 ├─ A — TOR GATEWAY (container, runsc, MANDATORY)
 │     tor from Tor Project signed repo, repackaged locally into a
 │     distroless OCI image (§7). Read-only rootfs except DataDirectory +
 │     key volume (own small quota'd volume, so a full disk can't starve
 │     Tor state). SocksPort OFF. Control = unix socket to the HOST status
 │     daemon only. Diagnostics run host-side via that socket (X7).
 │     torrc (host-generated): onion v3, PoW defences ON, intro-DoS defence
 │     ON, MaxStreams 50 + close-circuit, vanguards-lite as shipped.
 │     Egress: outbound TCP to ANY port, UDP dropped (§6 — guards sit on
 │     arbitrary ORPorts; v1's "443/9001 only" broke guard selection, X16).
 │        │  HiddenServicePort 80 → unix:/run/web/http.sock
 │        ▼
 ├─ B — WEBSITE (container, runsc, MANDATORY — no runc fallback)
 │     network: none. There is no network. nginx-unprivileged listens on
 │     a unix socket in a dedicated socket-volume shared with A only.
 │     No route, no DNS, no ARP peer, no bridge, no host IP to find,
 │     no IPv6 question to ask. (M2)
 │     Read-only rootfs, cap_drop ALL, no-new-privileges, seccomp/AppArmor,
 │     CPU/RAM/PID ceilings, UTC, C.UTF-8, generic hostname, no product
 │     labels in the image. If runsc cannot start B, Go Live REFUSES with
 │     a plain error — the downgrade is no longer a silent amber state for
 │     the core promise (X3); amber exists only for non-core degradations.
 │     Headers: Date / Last-Modified / ETag stripped or frozen; 
 │     server_tokens off; custom error pages; no default favicon
 │     (its hash fingerprints the product); content metadata scrubbed
 │     by the publisher (§5) before B ever sees a file.
 │
 └─ (No database container in v1. See tiers, §5.)
```

Why A is a container, stated correctly this time (review §9.3): not "to hide
the key from B" — a B escape reaches the host in either topology — but **to
contain tor itself**: tor is a large C parser of hostile network input that
holds the key AND has egress; a tor RCE inside A still faces gVisor,
a read-only rootfs, and no path to the LUKS session or Dashboard. A runs
under `runsc` for the same reason B does (M8). A migration path to Arti
(Rust tor) is noted for when its onion-service support is production-grade.

**The colluding-visitor channel, conceded precisely (C3):** B's one
legitimate output channel — HTTP responses — can be used by a compromised B
to serve data to a colluding visitor. This cannot be closed. It exposes only
what B can read, and B can read nothing secret: no keys, no credentials, no
non-public data in the default tiers. v2's wording: the website "can't attack
others and holds nothing worth stealing," never "is useless to an attacker."

# 5. Site tiers and daily life v2 (M6, M7, X14, X15)

**v1 tiers — three, all static under the hood:**
1. **Simple pages** (default): form-built static site.
2. **Journal**: the blog tier, rebuilt — a static generator plus the
   owner-only editor. No WordPress (it phones home, its password reset
   needs email that can't exist, comments are stranger-submitted content on
   a novice's box), **no comments in v1**, admin reset = the disk-gated
   flow (§3). There is no database container until a future tier truly
   needs one; if one arrives, it joins over a unix-socket volume like B.
3. **Private files**: upload/download reachable ONLY under v3 client
   authorisation — devices the owner invites can even *see* it; to everyone
   else the address does not exist. **Anonymous public uploads never.**
   (M7/Scenario 6: a public upload drop makes the owner an unwitting host
   of strangers' material on an encrypted disk in their house.)

**Cut from v1: Bring-your-own-container** (X14 — it required exactly the
terminal/registry skills Fixed #1 forbids, and arbitrary images mostly break
with no egress). It may return as a curated-image feature, never as raw BYOC.

**Editor & publisher:** the editor is a local app; publishing flows through
a host-side publisher helper (unix socket, polkit) that is the ONLY writer
of the content volume B mounts read-only. The publisher scrubs uploads:
EXIF and metadata across images (incl. PNG text chunks, HEIC/AVIF), media
files and documents, renames files randomly, enforces quotas (a full content
volume must never starve Tor's volume or the disk, review §5).

**Dashboard: a native GTK app** talking to a polkit-guarded helper over a
unix socket. **No TCP listener, local or otherwise** (M6 — a localhost web
UI was a DNS-rebinding/CSRF target for every other browser on the box).
Cards say exactly what they test: **"Website sealed off: passed"** — never
"Location hidden" (X11). Plus: site status, backups, relay toggle, and the
restart-needed card (§7). The red button is renamed for honesty:
**"Shut down now"** — stops the site and powers the machine off (the real
seizure response, M11). The old "panic wipe" (shred onion key) survives only
as an expert action paired with immediate power-off, labelled with what it
does and does not do.

**Tor Browser on the box is locked down (M6/N3):** shipped with an
enterprise `policies.json` WebsiteFilter allowing ONLY the box's own onion
address (plus the Tor download page). "Visit my site" is its job; general
browsing on the server is designed out — the server is not the owner's
browsing machine, and a browser exploit on the host bypasses every
compartment.

# 6. Firewall and self-checks v2 (M3, M9, Q13, X8)

**One source of truth:** a single golden-config file in the `onionhost`
package generates the nftables table, torrc, container units, self-check
expectations, AND the dashboard's claim strings. A build/CI check fails if
any generated artefact drifts from it (X8 — documents, rules, and UI copy
can no longer quietly disagree).

**Firewall:** a dedicated `table inet onionhost` with its own drop-policy
base chains, loaded by `onionhost-fw.service` ordered `Before=` the container
engine. The unit never flushes or touches other tables; because a packet
must be accepted at a hook by every base chain in play, the engine rewriting
its OWN chains cannot open a hole in this table (M3). Rules: host INPUT
default drop, no inbound anything; container-side traffic can originate only
from A, TCP-out only, UDP dropped; B has no network to firewall — the
strongest rule is the absent interface.

**The gate (Q13):** A's unit `Requires=` the firewall unit and runs an
`ExecStartPre` that hashes the live `inet onionhost` table (normalised) and
compares it to the golden hash, plus asserts container IPv6 is disabled.
A re-check runs every 5 minutes AND on triggers (engine restart, package
install, nft change). **On mismatch: A is stopped** — the site goes down,
nothing is exposed — and Dashboard shows red: *"Safety settings changed —
click Repair."* De-hardening fails closed and loud (C7 fix).

**Self-checks, honestly scoped (M9):** B contains no probe tools and is never
asked to test itself. Checks run from a sibling **probe workload** launched
with B's exact unit/runtime policy against the socket volume, verifying
*policy* — no network namespace route exists, the socket perms are right,
the key is unreadable from B's mount view, firewall hash matches, Tor
reports the service published, no host port is listening. Schedule: at Go
Live, at every boot, on every trigger event, and hourly — not daily.
Failing any check blocks Go Live or stops A per the gate above.

# 7. Updates and trust chain v2 (M5, X4, X9, R6, R10, Q14)

- **Host apt over HTTPS on the clearnet.** apt-over-Tor is dropped entirely
  (X4: it was circular — Tor updating itself through a SOCKS port the design
  had switched off — and pointless: the ISP already sees 24/7 Tor; "this
  machine also fetches Debian packages" reveals nothing comparable).
- **Images are built locally, automatically.** A/B images are OCI builds
  (mmdebstrap) from the same signed Debian + Tor Project packages the host
  uses; when those packages change, images rebuild and containers roll —
  **automatically**, because the apt signature IS the gate. The v1
  contradiction (Tor "automatic" but also "approval-gated image") is gone
  (X9). Approval-gating survives ONLY for user-visible app changes (e.g. a
  Journal major version), with one-click rollback.
- **Restart honesty (M5/N4):** kernel/gVisor updates install automatically
  but only take effect at reboot — and reboot needs the disk phrase, so the
  dashboard tracks *running vs installed*: card "Restart needed for a
  security fix — have your disk password ready," amber at 7 days, red at
  30. "Updates ✓" is only ever shown when the RUNNING system is current.
- **The maintainer signs exactly one thing:** the small `onionhost`
  package (golden config, wizard, dashboard, units), with a **hardware
  key**, and ISO + package builds are **reproducible** so third parties can
  verify them (R6: a solo dev's laptop is a realistic target).
- **Dead-project degradation (Q14/R10):** the `onionhost` repo metadata
  carries `Valid-Until`, re-signed on a cadence; installs fetch it from an
  onion mirror. Stale >90 days → amber card: *"This project may no longer
  be maintained. Your site still runs and still gets security fixes from
  Debian until ~2030."* At the base release's end of support → red card +
  one-click "Back up and shut down." Because images rebuild from Debian/Tor
  packages, the fleet keeps patching **without the maintainer** for the
  life of Debian 13 (full security support to 2028, LTS to 2030 — verified
  against Debian's published lifecycle, Oct 2026).

# 8. Relay, transports, scenarios — deltas only

- **Relay: unchanged.** None needed for hosting; bridge opt-in, default off,
  bandwidth-capped; middle relay Advanced-only; **exit never** (Fixed #4).
- **Pluggable transports (Q5/X17): v1.1**, behind a wizard item "My internet
  blocks Tor" (obfs4/webtunnel; Snowflake is too unreliable for a 24/7
  server). v1 ships with the §1 wording limiting where it should be used.
- **Raid scenarios, as the UI now states them:** found OFF → brick (argon2id
  + ~90-bit phrase; the paper is the residual risk). Found RUNNING → LUKS
  delivers nothing; auto-lock protects the session, not the disk. Found
  ASLEEP → impossible by design (sleep masked). "Shut down now" is the
  honest panic action.
- **Viral load:** the bottleneck is tor's CPU in A (mostly single-threaded
  circuit/intro work), then home upload bandwidth — not nginx/gVisor. It
  degrades to slow/unreachable and leaks nothing; induced-load clock attacks
  are blunted by the stripped `Date` header (§4). PoW defences engage under
  hostile load at seconds-per-puzzle cost to real visitors (verify the PoW
  module ships in the chosen tor build — App. B).
- **Install USB watch:** final wizard screen says "Remove the USB now" and
  waits until it's actually gone (udev); disk-first boot order set where
  the platform allows (a forgotten stick would otherwise boot the live
  system at the next power cut).

# 9. Gates before any public ISO (new in v2 — C4/Q12/Q14 consequences)

1. **At least five usability sessions with real novices** on real hardware,
   including one non-US keyboard layout and one Wi-Fi-only machine. C4 is
   UNPROVEN until then — the review's single "unproven" verdict, accepted.
2. **External security review** of the built alpha (not just the design).
3. **Legal counsel** before distribution (reviewer suggests the EFF as a
   first call): distributor posture is *publisher, not operator* — host no
   sites, keep no directory of users' sites, no telemetry, publish an
   acceptable-use statement, never engage support with specific content.
4. Reproducible ISO + hardware-key signing live (§7) before strangers
   download anything.

# Appendix A — Review mapping (condensed)

- **M1 timing/availability channels** → §4 headers stripped/frozen, all-UTC,
  seamless B rotation via dual-socket handover with tor reload (fallback:
  brief restart at a daily-redrawn random UTC time), §1 disclosure line.
- **M2 A→B network weak** → §4: B has NO network; unix-socket handoff.
- **M3 firewall vs Docker** → §6 separate table, no global flush, A egress
  TCP-any-port (X16 with it).
- **M4 credentials/keymap** → §3 one secret, 7 words no digit, randomised
  verify, initramfs keymap, re-key flow.
- **M5 update contradictions** → §7 (X4, X9, X13 resolved there).
- **M6 host soft underbelly** → §2 stripped host, §5 native dashboard +
  locked-down Tor Browser.
- **M7 tiers** → §5: BYOC cut (X14), Files client-auth-only (X15), blog
  rebuilt as static Journal.
- **M8 tor is the valuable target** → §4: A under runsc, distroless,
  host-generated torrc, Arti path noted.
- **M9 self-check overclaim** → §6 probe workload, honest card text,
  event-triggered checks (X10, X11 resolved there).
- **M10 family-PC erase** → §2 named-data erase screen + type-to-confirm +
  spare-computer guidance.
- **M11 physical states** → §2 sleep masked, auto-lock, session-independent
  services; §5 "Shut down now."
- **M12 Debian 12** → §2 Debian 13 (dates verified by author, Oct 2026).
- **X1 sheet vs separation** → §3: separation now means *a leak doesn't
  spread across assets*, and only one secret is on paper at all.
- **X2 rootless/userns-remap** → §4 engine decision; remap language deleted.
- **X3 gVisor optional/default** → §4 mandatory for A and B; runsc failure =
  no Go Live.
- **X5 backup under phrase** → §3 age/scrypt, specified; drawer warning.
- **X6 keyring** → §3: nothing stored; reset/re-key replace retrieval.
- **X7 shell-less A diagnostics** → §4 host-side via control socket.
- **X8 doc rot** → §6 single golden source + drift check.
- **X12 restart leaks timezone** → M1 line above.
- **X17 anywhere claim** → §1 wording + §8 transports v1.1.
- **Claims:** C1/C2/C3/C5/C6/C8/C9/C10 sound-with-fixes → fixes above.
  C7 unsound-as-written → §6. C11 unsound → §1. C4 unproven → §9 gate 1.
  C12 sound-with-fixes → §3.
- **New risks N1–N7** → N1 §1/§4, N2 §2, N3 §5, N4 §7, N5 §4, N6 §2,
  N7 §3 (separate pages; download/print artefacts named in docs).

# Appendix B — Qualified / verify-at-build items (author's notes on the review)

The review was adopted nearly wholesale. These items are accepted as
*direction* but carry build-time verification, and two estimates were
re-based rather than copied:

1. **runsc + unix-socket creation**: nginx under gVisor binding a socket on
   a shared host volume needs the runtime's host-UDS creation support
   (review flags `--host-uds=create`-equivalent). **PoC gate #1** — if it
   fails on the chosen Podman/runsc versions, fallback is the review's own
   M2 fallback (internal network + conntrack direction rules + static IPs),
   NOT a silent weakening.
2. **Podman vs Docker engine**: v2 follows the review's "switch, lean yes"
   because Fixed #3 was always "Docker(-compatible)" and Dockerfiles are
   untouched — but this is the one change the product owner should confirm
   explicitly, since "Docker" is the word users will say. Fallback branch
   documented in §4.
3. **Tor PoW module**: verify `tor --list-modules` on the shipped build
   (historically a build-flag matter) before claiming PoW in UI copy.
4. **Re-key via live volume key**: verify the exact cryptsetup path at
   alpha; the phrase-prompt `luksAddKey` fallback keeps the feature either
   way.
5. **Estimates, re-based:** reviewer (assuming a solo human) put home-alpha
   at 3–6 weeks and strangers-ready at 4–9 months, and listed scope v1's
   estimate forgot (custom Calamares module, the editor as a product in
   itself, signing/reproducible builds, boot-key guide, translations,
   novice sessions, external review). Author's revision: **PoC still an
   afternoon** (compose/Podman stack + tor + nginx over the socket — the
   reviewer explicitly agrees an ISO is not part of a PoC); **home alpha
   2–4 weeks of calendar time** with an AI builder doing the coding —
   test cycles on unaccelerated emulation and the editor/dashboard scope
   are the binding constraints, not typing speed; **strangers-ready stays
   months (plan on the reviewer's 4–9)** because §9's gates are calendar
   events no builder can compress.

# Appendix C — Settled defaults v2 (replaces v1 §9)

Debian 13 · Calamares 3.3.x · LUKS2/argon2id mandatory, phrase every boot,
no auto-unlock · ONE human secret (7-word phrase, hand-copied) + optional
revocable spare keyslot · Podman rootless + Quadlet (Dockerfiles
throughout) · runsc mandatory for A and B · B has no network; A↔B is a unix
socket · Tor in own container, holds the key, PoW + intro-DoS on · separate
hash-gated nft table; Tor cannot start if the table is wrong · native GTK
dashboard, no TCP listeners · static tiers only in v1: Pages, Journal,
Private Files (client-auth) · BYOC and WordPress: cut · relay off, bridge
opt-in, exit never · updates: apt HTTPS, images rebuilt locally and
automatically, restart tracked honestly · positioning: adults, network-
address claim only · sleep disabled · SSH absent.

---
*Design v2 — supersedes DESIGN-v1.md. Still design only; nothing is built.*

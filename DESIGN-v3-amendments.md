# OnionHost OS — Design v3 Amendments
## 2026-10-10 · Amends DESIGN-v2.md after the Opus 5.5 delta review of v2
## Reviewer verdict: **GO for the alpha, with corrections.**
## Where this document and v2 conflict, THIS document wins. Unmentioned v2 sections stand.

The delta review's shape: 2 clusters hold as written (J host/install,
K claims), 8 hold with corrections, 1 must be replaced (F's browser part).
It introduced 16 new contradictions in v2's fixes (Y1–Y16). Two are called
non-negotiable by the reviewer; both are adopted here without reservation.

---

# A1. NON-NEGOTIABLE 1 — Tor Browser is REMOVED from the box (Y1, Cluster F replaced)

v2 policy-locked Tor Browser to the box's own onion address. The reviewer
inverted it: the one site that browser may visit is the site the entire
architecture assumes *will be hacked*. A browser exploit there lands in the
owner's desktop session (keylogged PIN/phrase), and Tor Browser's own
bundled tor requires the desktop user to have internet egress — quietly
breaking the "only A has egress" model (and DQ7: `policies.json` cannot be
locked meaningfully in a user-writable, self-updating install anyway).

v3 replacement for "Visit my site":
1. **Dashboard status card**, fed by the probe path: a client-only tor
   container **U** (new, see A4) fetches the site *through Tor* and the
   card shows a fixed golden string — "Your site answered over Tor at
   HH:MM UTC" — with **no HTML ever rendered** on the box.
2. **QR code for the owner's phone** — the more truthful external test
   anyway, and the phone is not the server.
Consequence, adopted: the desktop user gets **zero egress** in the firewall
(Cluster E identity rules, A5). Nothing on the box browses the web.

# A2. NON-NEGOTIABLE 2 — The login is GENERATED (Y13, Fixed #1 restored)

v2's user-chosen PIN violated the fixed rule "the user never invents a
password" — a rule from the owner's original vision (passwords generated
by default). v3:
- Login = a **generated 3-word phrase** (~39 bits), shown and verified like
  the disk phrase, protected online by `pam_faillock` (deny=5,
  unlock_time=900 → roughly 480 guesses/day → centuries online; offline
  guessing is moot because the disk is LUKS-encrypted).
- The user is **removed from sudo**; all privileged Dashboard actions go
  through polkit.
- Loss of the login words is a non-event: the Maintenance flow (A3)
  regenerates them. They are a session convenience, never a root of trust.
- The **website admin password is DELETED entirely** (Y5): no v1 tier has
  a web login (editing is local; Private Files was client-auth and is now
  deferred, A7). Its reset flow is deleted with it.

# A3. Credentials — the rest of Cluster B as corrected

- **Phrase is typed ONLY at console prompts**: the boot LUKS prompt, and
  the pre-login **Maintenance target** (the v2 "Reset passwords" boot
  entry, kept — S2 was *cleared*: GRUB/initramfs tricks still run after
  the LUKS prompt, so it grants nothing without the phrase; the target
  must not start A or networking, and every reset is logged to the
  Dashboard so a phrase-holding housemate's reset is visible).
  Re-key and spare-key creation live in Maintenance. The Dashboard merely
  offers "Restart into Maintenance (site offline ~5 min)."
- **Backups need NO phrase to create** (fixes S5/Y6): at install, while the
  installer still holds the disk phrase, the system derives an age X25519
  identity from it (`argon2id(phrase, per-install salt)`). Only the
  **public recipient** is stored. Backups are `age -r <recipient>` —
  exportable from a normal session by anyone, and useless to them.
  **Restore** is where the phrase is typed (at a console, in Maintenance),
  the identity re-derived, the backup opened. The per-install salt is not
  secret: it is stored on the system AND in each backup's plain metadata,
  so a backup file alone + the phrase is sufficient to restore.
- **Spare key covers backups too**: the spare phrase derives a second
  recipient at spare creation (in Maintenance); every backup is encrypted
  to BOTH recipients. Revoking the spare removes its recipient from future
  backups.
- **Revocation honesty (Y14/DQ6)**: killing a LUKS keyslot does NOT change
  the volume key — a disk/header image made while the spare was live still
  opens with the old spare phrase. Dashboard copy says exactly that,
  including for backups made before revocation, and offers **"Change the
  lock completely"** (`cryptsetup reencrypt`, takes hours, site stays up)
  as the only true revocation against imaged disks.
- **Implementation status (2026-10-20)**: SUPERSEDED by A25 — the spare
  feature was REMOVED entirely by owner decision the same day (the
  revocation promise was first withdrawn, then the owner went further:
  no second phrase at all). No spare slot is enrolled, no spare backup
  recipient is created, and no copy offers one. The spare design in
  this amendment — dual recipients, revocation, revocation honesty —
  is retained as history only; A25 is the governing record.
- **Re-key after lost paper (Y12)**: v2's "live volume key" path is
  *suspect* — LUKS2 normally references the key via the kernel keyring
  (`:logon:`), so the raw key may not be extractable from the running
  mapping. **PoC Gate R decides** (see A9). If it fails, v3's honest rule
  is pre-committed: *while running with a lost phrase, your only moves are
  (a) use the spare key if one exists, or (b) back up everything and
  reinstall* — and the wizard will say so, in those words, at spare-key
  step ("this is your only insurance if you lose the main paper").

# A4. NEW component — U, a client-only Tor container (Y2)

v2 fetched `onionhost` repo metadata "from an onion mirror" with no Tor
client to fetch it with (A has SocksPort 0), and the clearnet fallback
would have handed the maintainer a list of every install's home IP.
v3 adds **U**: a tor instance in client mode only — no onion service, its
own guards (disjoint from A's), SocksPort exposed only as a unix socket to
two host consumers: the repo-fetch helper (A6) and the Dashboard status
probe (A1). U holds no keys and no identity. If U dies, updates of the
`onionhost` package pause and the status card goes stale — A and the site
are unaffected.

# A5. Engine REVERTED to rootful (delta §7; Y3, Y4) — with a data clause

- v3 default: **rootful Podman + Quadlet + runsc**, `--userns=auto` so A
  and B get **disjoint subuid ranges**. Podman/Quadlet stay; *rootless*
  goes. Reasons adopted: rootless routes A's egress through pasta as
  host-user traffic (firewall identity rules stop matching — Y3); a
  single rootless service user puts B's escape-uid adjacent to A's key
  (Y4); rootless runsc is the least-proven mode and may silently drop
  cgroup ceilings (test: fork bomb); linger/socket-permission friction.
  On top of runsc, rootless bought little: Sentry already runs namespaced
  and seccomp'd, so an escape needs Sentry + kernel bugs either way.
- **Data clause (reviewer's own)**: PoC Gate 1 runs BOTH ways. If rootless
  passes every sub-test cleanly — ceilings enforced, two-user sockets,
  egress correctly attributable — the choice reopens on complexity alone,
  as an owner decision with the data on the table.
- Quadlet facts to verify at PoC (DQ2): no first-class runtime key (use
  `PodmanArgs=--runtime=runsc`, confirm via inspect); **gVisor ignores
  AppArmor** — v2's AppArmor claims for A/B are deleted, AppArmor now
  applies to host services only; omitting `Network=` in a unit means
  *default* networking, not none — every unit states its network
  explicitly and Gate 2b tests the omission.

# A6. Trust chain corrected (Cluster D, Y7, Y8, DQ4)

- Builder: mmdebstrap **`--mode=unshare`** under a dedicated unprivileged
  builder user (maintainer scripts run in a fakeroot user namespace, not
  as host root); inputs are apt-verified signed .debs; images enter Podman
  via **`podman import`** of the built tarball — no registry is ever
  parsed. nginx header control uses Debian's packaged
  `libnginx-mod-http-headers-more-filter`; **nothing is compiled locally**.
- **Anti-rollback (DQ4)**: every image carries a manifest of exact package
  versions; the host persists a **high-water mark per package**; the
  builder refuses inputs below the mark (compatible with Debian practice —
  Debian's own rollback versions sort higher). The signed `onionhost`
  package carries a **security floor** (e.g. minimum tor version).
  Rollback to a previous image is allowed only if it is at/above every
  floor. **Y8 fail-closed**: if the new A fails checks AND the old A is
  below the floor, the site goes OFF with a red card — it never keeps
  serving on a below-floor tor to stay up.
- **Update timing (Y7)**: apt timers move to `OnCalendar=*-*-* 00:00:00
  UTC` + `RandomizedDelaySec=24h`. Every A rebuild costs a **30–120 s
  republish outage** (A cannot rotate seamlessly — one key, one tor;
  accepted) and it now happens at a random UTC time, not ~06:00 local.
- **Mirror calibration (S11, mostly cleared)**: Valid-Until 45 days,
  re-signed monthly on the hardware key; the amber card fires when apt
  actually reports expiry; "project may be unmaintained" shows 90 days
  after expiry; fetch times randomised (via U, A4) so the mirror cannot
  count the fleet by the hour. A frozen mirror can only freeze the small
  `onionhost` package — Debian/Tor security updates flow independently.

# A7. Tiers: Private Files DEFERRED to v1.1 (Y9, Y10, S8)

Client authorisation is per onion *service*: Private Files was always a
**second onion identity** (own key, own descriptor), linkable to the first
by shared guards and identical uptime — never disclosed in v2. It also
needed per-guest named revocable keys (an invite screenshot = access) and,
if guests could upload, a writable B volume + the privileged publisher
parsing strangers' files. All beyond the v1 novice ceiling.
**v1 ships exactly two tiers: Simple Pages and Journal.** Private Files
returns in v1.1 designed openly as a second identity: linkability
disclosed, per-guest keys, **guests download-only, permanently** — only the
owner ever publishes.

# A8. Firewall, probe, timing, time — corrected mechanics (E, G, H, DQ8–DQ10)

- **Firewall comparison without text hashing (Y11)**: the expected state
  is computed at check time by loading the golden table into a scratch
  network namespace and comparing **canonicalised JSON** listings from the
  *same* nft binary on both sides — an nftables upgrade changes both
  sides equally and no longer false-alarms the site down. Triggers:
  an `nft monitor` watcher + engine restart + dpkg hooks + 5-minute timer.
- **Egress by identity (DQ9)**: A's netns: TCP out, any port. `root`,
  `_apt`, `_chrony`: only what updates and NTS need. **Desktop user:
  nothing.** Resolvers in the finished system, exhaustively: host stub
  resolver usable only by root/`_apt`/`_chrony`; A: `--dns=none`;
  U: resolves through Tor only; B: none; Dashboard/publisher: no network.
  What the ISP sees in DNS is Debian/Tor/NTS hostnames — which 24/7 Tor
  already announces.
- **Probe (G/Y15)**: one fixed shipped unit, `onionhost-probe.service`,
  no runtime templating. It inspects the **running** B (`podman inspect`:
  runtime=runsc, NetworkMode=none, ReadonlyRootfs, CapDrop=ALL, exact
  mounts) and `nsenter`s the sandbox netns (must show only `lo`, no
  routes). It returns **exit codes only**; the Dashboard maps codes to
  golden strings. Watchers observe host-owned paths only, never the
  socket directory B can write to.
- **Timing (H/S10)**: there are **no scheduled outages**. If B's seamless
  swap fails, the old B keeps serving and the card goes amber — failing
  safe means staying UP. B rotation uses the **symlink swap** (S1
  resolved): sockets `b1.sock`/`b2.sock` in the volume, tor targets the
  fixed path `http.sock`, a host-owned symlink atomically renamed once the
  new B answers a health request through the idle socket; old nginx gets
  SIGQUIT with a 60 s drain cap (a mid-download visitor finishes or gets
  cut at 60 s; Range support makes retries resume). Rotation *time* is
  still randomised daily in UTC (an attacker inside B notices eviction —
  S10). NEVER two `HiddenServicePort` lines for one virtual port.
  Fallback if gVisor doesn't follow the renamed symlink (test at Gate 1b):
  single-line rewrite + SIGHUP.
- **Headers**: `Date` removed via headers-more; `Cache-Control` set
  explicitly; the publisher sets each file's mtime to
  `fixed_epoch + (sha256(content) mod 10^8)` seconds, so ETag/Last-Modified
  are **content-derived** — no edit times leak and caching still works.
  Optional hardening noted: `net.ipv4.tcp_timestamps=0`.
- **Time sync (DQ10)**: **chrony with NTS** (Debian 13's timesyncd is
  unauthenticated SNTP — an on-path attacker could shift the clock tor
  depends on). `makestep` at boot only, slew after; `cmdport 0`; serves
  time to nobody; RTC in UTC. NTS failure + tor's own skew warning → amber
  card.
- **DoS numbers (DQ3)**: MaxStreams 50/circuit with close-circuit;
  intro-DoS defaults (25/s, burst 200, 3 intro points ≈ 75/s capacity);
  `HiddenServicePoWQueueRate` set to ~2× the sustained rendezvous rate
  measured at PoC Gate 5 — not the 250/s default an old CPU can't service.

# A9. PoC gate order v3 (replaces the delta pack's Part 5 list)

Cheap fix-killers first; the costly rebuild gate moves to alpha:
0. **Smoke (5 min)**: tor build lists the PoW module; runsc/systrap works
   in the no-KVM VM; tor accepts the full golden torrc.
R. **Re-key path (15 min)**: LUKS2 volume, default open, inspect
   `dmsetup table --showkeys` (key vs `:logon:` reference); try passphrase-
   less `luksAddKey`. Decides A3's lost-paper rule.
1. **Gate 1, BOTH engines**: rootful vs rootless runsc + network-none +
   host-UDS socket creation; nginx serves through tor. Fork-bomb and
   memory-hog in B must hit ceilings. Decides A5 with data.
1b. **Rotation**: symlink swap during a looping 200 MB download (count
   dropped requests; confirm runsc follows the rename); SIGHUP fallback;
   measure A's restart-to-reachable time.
2. **Running-B inspection** per A8 (not "look inside B" — true by
   construction; inspect the live instance).
2b. **Drift negative test**: delete `Network=none`, restart B → probe red
   within one trigger AND nft back-stop drops B's traffic meanwhile.
   Repeat with a drop-in override.
3. **Firewall gate**: manual corruption stops A; simulated nft version
   change does NOT false-alarm; `nft monitor` triggers fire.
H. **Headers over Tor**: no `Date`; content-derived ETag/Last-Modified;
   edit → revalidation works; no wall-clock edit time anywhere.
5. **PoW under load**: drive rendezvous load to queue engagement; record
   sustained rate → set `PoWQueueRate`.
(→ alpha) **Gate 4**: local rebuild, floors, Y8 fail-closed case.
**Alpha-only gates**: real AZERTY/QWERTZ keyboards at the initramfs prompt
(console prompt, NOT plymouth, until that's tested — Cluster J note);
autologin state-machine power-pulls (below); Calamares stdin phrase with
a logs/globalstorage sweep for leaks.

# A10. Autologin state machine (S3/Y16 — Cluster J completion)

- **S0 Installed**: LightDM autologins into a **kiosk session running only
  the wizard** — no desktop exists yet. The wizard's FIRST step generates
  and verifies the login words (A2), so a lockable secret exists before
  anything else can happen.
- **S0→S1, atomically**: `chpasswd` → remove autologin drop-in → `fsync`
  → write `state=1`. Power loss before the final write simply repeats S0;
  nothing can be half-set.
- **S1**: normal login screen; the wizard resumes at its saved step after
  login. **S1→S2** at Go Live success.
- Below S2 the Dashboard shows only "Finish setup." The wizard is always
  re-enterable — it can never strand the user.

# A11. Concept count, final (S12)

After all cuts, the user holds exactly five concepts: **disk phrase** ·
**optional spare key** · **generated login words** · **restart-needed
card** · **Repair button**. Everything else from v2's list is deleted,
deferred, or automated. The reviewer judged this within the ceiling;
v3 treats five as a hard budget for any future feature.

---
*Design v3 = DESIGN-v2.md as amended by this document. Status remains:
DESIGN ONLY, nothing built. Next step when authorised: PoC per A9,
starting at Gate 0.*

# A12. Full dynamic (PHP) sites — END GOAL, deliberately deferred (2026-10-10)

Cameron's stated end goal includes full dynamic sites (PHP and similar)
running on this server eventually. Decision (Muse's call, owner accepted):
**do not design or build that tier now.** Reason: every review round has
shown scope discipline is what keeps the core shippable — the static core
must prove the compartment model end-to-end first. The architecture already
generalises (Tor → nginx socket → PHP-FPM socket → DB socket, zero
networks), so deferral costs nothing *provided* the alpha respects these
forward-compatibility reservations from day one:

1. All inter-container communication is via unix-socket volumes only;
   nothing may introduce a container network "temporarily."
2. The golden config's unit/probe/firewall generation is **list-driven**
   (a list of web-stack containers), never hard-coded to a single website
   container — adding PHP-FPM and DB units is adding list entries.
3. Volume and quota naming reserves an app-data class (writable, quota'd)
   alongside content (read-only) and tor state, even though v1 ships only
   the latter two.
4. The backup manifest format is extensible to database dumps and app
   data from the first version — backups must never assume "files only."
5. Any future web-admin surface follows the Private Files precedent:
   a **separate onion identity**, never admin paths on the public service.

**Trigger to design the tier:** static core passes the PoC gates (A9) and
installs end-to-end as an alpha ISO. At that point the PHP tier gets its
own design pass — and its own Opus delta review — before any code, with
the known problem list as its starting brief: writable uploads volume with
no script execution, app/DB data raising the value of a compromise (the
network-address and key-isolation promises are unaffected; the
"nothing worth stealing" comfort is), app updates exclusively via the
image-rebuild pipeline (in-app auto-updaters disabled), and no email —
resets and contact become in-app flows.

# A13. Hardware guidance (2026-10-10, estimate — validate at PoC Gate 5)

For a forum-class dynamic site at 1,000–10,000 visitors/day (worst case
≈150k page views/day, ~15–20 dynamic requests/sec at peak hour):

- **Floor** (1k/day dynamic, or 10k/day static): any 4-core x86-64 from
  ~2013+, 8 GB RAM, 120 GB+ SSD, wired Ethernet. A used office desktop
  qualifies.
- **Recommended** (10k/day forum): 4–6 reasonably modern cores (Intel
  8th-gen i5 class, or an N100-class mini PC, or better), 16 GB RAM,
  500 GB SSD/NVMe, wired gigabit. RAM split at peak: host ~1.5 GB, Tor
  ~1 GB, PHP-FPM pool 2–3 GB, DB buffer pool 2–4 GB, rest page cache.
- **Bottleneck order** (the PC is rarely #1): ① home **upload** bandwidth
  — ~20 Mbps upload minimum for the forum case, 40+ Mbps comfortable;
  image-heavy content multiplies this, the CPU doesn't care. ② the single
  tor process's CPU under rendezvous load/attack (PoW verification);
  Gate 5 measures the sustained rate on real hardware. ③ PHP CPU —
  budget ~⅓ extra for gVisor overhead. ④ disk: an SSD is effectively
  mandatory once a database exists; HDD is static-tier-only.
- Wi-Fi is disqualified for the server (wired only); a mini PC at ~10 W
  idle costs roughly $15–25/year in electricity to run 24/7.
- Beyond 8 cores / 32 GB buys attack headroom and growth, not normal
  operation; nothing a bigger PC does fixes Tor's inherent latency.

# A14. Open-source & verifiable-release protocol (2026-10-10, draft for owner OK)

Why it's load-bearing here, not decoration: this product asks strangers to
trust a binary with their anonymity. If they can't verify the ISO is what
the source says, they're trusting the publisher — the exact trust the
design removes everywhere else. Reproducible builds are a release gate,
same tier as the security review.

1. **Licence**: project code (installer glue, wizard, dashboard, publisher,
   golden-config generator, `onionhost` package) under **GPLv3** —
   derivatives stay open; matches the Debian/Tor ecosystem it ships.
   Shipped components keep their own licences (Debian archive, Tor:
   BSD-style). The **name and logo are not** covered by the code licence —
   trademark is handled separately (see the legal pass), so forks must
   rebrand if they diverge.
2. **Repo public before any public ISO.** Everything needed to build is
   in it: build scripts, golden-config templates, package sources, this
   design lineage. No secrets ever (signing keys live on the hardware
   key; nothing sensitive exists in the codebase by design). Security
   issues: `SECURITY.md` with a coordinated-disclosure address.
3. **Reproducible ISO build**, using the Debian reproducible-builds
   playbook: all packages pinned to a dated snapshot.debian.org snapshot;
   `SOURCE_DATE_EPOCH` from the release commit; deterministic filesystem
   image (fixed mtimes/ordering in squashfs + xorriso); the build runs
   twice in clean environments and the hashes must match before signing.
4. **Independent rebuilders**: a release is only "verified" when at least
   two people who aren't the builder rebuild from the tag and match the
   published SHA-256. Their attestations ship with the release. This is
   the bridge for novices, who will never rebuild anything: they check
   one signed checksum; the *crowd* checks the checksum means something.
5. **Release artefacts**: signed git tag; ISO + SHA256SUMS signed with
   the maintainer hardware key; build log + snapshot timestamp +
   provenance note published with the release; "verify your download"
   instructions in plain language on the download page.
6. **Source compliance for shipped binaries**: the pinned Debian snapshot
   IS the source for archive packages (snapshot.debian.org serves it);
   project packages' source is the public repo. Licence texts ship inside
   the ISO. (Confirm the exact written-offer mechanics in the legal pass.)
7. **Timing**: repo can go public as soon as the PoC passes — the design
   has already survived two external reviews; openness from alpha onward
   is free security review. Contributions welcome, but the five-concept
   budget (A11) is a contribution filter, not a suggestion.

# A15. I2P eepsite mirror — FUTURE, explicitly not now (2026-10-11)

Cameron asked whether the same site could also be served as an I2P
eepsite later. Assessment: **no architectural break** — the gateway
pattern clones. A new container **I** (i2pd under runsc, hardened like A)
holds the I2P destination key (a second network identity, same handling
as A) and reaches B's socket like A does. One shim is needed: I2P server
tunnels target TCP, not unix sockets, so I runs a localhost-only
socket→TCP bridge internally; B stays networkless and unchanged.

The real issues are policy-level, and they are why this is a future
decision, not a silent extension:
1. **I2P routers participate.** Unlike a Tor onion service (client-only
   posture, outbound TCP only, UDP dropped, no inbound anything), an I2P
   router normally relays encrypted transit traffic for others, speaks
   UDP heavily, and works best with an inbound port. Restricted/hidden
   modes exist and keep the doors shut, at reduced reliability. Enabling
   I2P therefore means the OWNER explicitly relaxing two v1 fixed points
   (no-inbound, Tor-only egress) for I2P mode — a deliberate, disclosed
   choice per install, never a default snuck in.
2. **Linkability.** Same content, same uptime on both networks links the
   .onion and .b32.i2p as one operator — fine for "same site, two
   networks" (the actual ask), disqualifying for separate personas.
   Must be disclosed in the wizard copy if the feature ever ships.
3. **Bootstrap contacts.** A fresh I2P router reseeds over HTTPS from
   public reseed servers — a small, one-time clearnet fingerprint,
   comparable to Tor's directory fetches. Noted, not solved.

Forward-compat reservations (cheap now, painful later):
- The golden config's gateway handling is list-driven alongside A12.2 —
  A is the first gateway entry, not a special case.
- **The site generators and templates must never hardcode the .onion
  address** — relative URLs everywhere; the same content root must be
  servable under any address. (This is also just correct for backups and
  address rotation.)
- The firewall model keeps per-gateway egress profiles, so an I2P
  profile (UDP, transit limits) can be added without weakening A's.

# A16. Distributed / standby hosting — assessed, future-listed (2026-10-11)

Cameron's scenario: a single home server's downtime pattern is itself a
fingerprint — correlate site outages with public power-grid and ISP
outage data and you narrow region + provider, even though Tor hides the
address. Correct, and it is exactly the residual availability-correlation
risk (v1 review M1) the narrowed claim already discloses. Distribution
is the only real answer to it; three shapes, in rising order of pain:

1. **Cold standby ("guardian box")** — the only novice-plausible shape.
   A second machine at a DIFFERENT location (different power grid AND
   different ISP — same house buys nothing) holds an encrypted replica
   and a copy of the onion identity, syncs content over Tor, and starts
   serving only when the primary has been unreachable for a sustained
   threshold (minutes, not seconds — avoids descriptor fights and
   flapping). An observer then sees the site survive any single
   location's outage, and the correlation signal collapses to "down only
   when BOTH locations are down."
2. **Active-active via OnionBalance** — Tor's real scaling mechanism
   (several backend instances aggregated under one address). Genuinely
   distributed, but an operator-grade tool: multiple identities, a
   frontend descriptor publisher, real monitoring. Not novice-shaped.
3. **Swarm/IPFS-style content distribution** — changes the trust model
   entirely and cannot host dynamic content. Out of scope.

Costs and honest limits:
- **Static tiers distribute well; dynamic (PHP/forum) barely does.** A
  database wants one writer: distribution there means primary/standby
  with asynchronous replication over Tor and manual-ish promotion —
  shape (1) with a colder, staler standby, not true distribution.
- **Every node is another physical target** holding the identity key
  and the data. The standby doubles the seizure/theft surface to halve
  an inference risk — a trade the owner must choose knowingly.
- **Sync must travel over Tor** (a client-only instance like U);
  nodes that talk to each other directly link themselves instantly.
- **Boot still needs a human at each location** (LUKS phrase). A standby
  at a relative's house means the phrase problem exists twice.
- **Partial natural mitigation already exists**: Tor clients cache
  descriptors, so outages of seconds-to-a-few-minutes often never
  register as downtime to visitors at all. The signal an attacker can
  actually harvest is sustained outages (storms, long ISP cuts) —
  which is why the standby threshold and the honest answer are both
  measured in minutes, not seconds.
- Concept budget: pairing a guardian box is +1 user concept. It joins
  PHP (A12) and I2P (A15) on the future list; v1 stays single-node.

Descriptor mechanics behind the standby rule (Cameron's follow-up,
2026-10-11): a v3 .onion address IS the service's public key — there is
no registry and no "first host wins" race a stranger can enter. A
visitor fetches the service's signed descriptor from directory relays
(deterministic placement, derived from the address + time) and verifies
the signature against the key embedded in the address; a descriptor
signed by any other key is invalid regardless of who serves it. Two
consequences the design already assumes, now stated explicitly:
(1) **Key theft is total and irrevocable** — whoever holds the private
key IS the site, cryptographically indistinguishable, and no authority
can revoke or reassign the address; the only recovery is a new key =
a new address, announced out-of-band. This is why the key lives only
in the Tor container and the website container never touches it.
(2) **Two live publishers of the same key split visitors** — if owner
and thief (or primary and guardian) both publish valid descriptors,
relays keep the freshest they have seen and visitors flap between the
two. Hence the guardian MUST stay dark until the primary is confirmed
down past the sustained threshold, and OnionBalance (separate backend
keys, one master key publishing a combined descriptor) is the only
clean active-active shape — operator-grade, future list only.


---

## A17 — Timing/availability analysis: external review outcome (2026-10-11)

Source: TIMING-ANALYSIS-PACK-for-claude-opus.md → v2 (defensive rewrite after Claude's safeguards flagged BOTH versions “[cyber]” and downgraded the session to Opus 4.8); the returned review (TIMING-REVIEW-RESPONSE-2026-10-11.md) came via Cameron from another frontier model. Verdicts adopted after internal consistency check; two of OUR premises were corrected.

**Corrections to our model (accepted):**
- (i) **Descriptor caching does not blur real outages the way the pack's C4 claimed.** Directories cache contact information, not service. A dead host's introduction circuits die with it; a visitor with a valid cached descriptor still fails to connect. Correct statement: short interruptions may be missed through sampling/timeouts/ordinary Tor variability — nothing stronger. Any earlier statement of “seconds invisible, minutes smeared” is RETRACTED.
- (ii) **No universal time-to-identification exists.** A single distinctive outage can be informative; some patterns may never identify. Never ship a numerical minimum.

**P1 (Cameron's multi-host same-key mirroring) — downgraded.** Simultaneous same-key publishers yield UNCERTAIN benefit: descriptor competition reintroduces partial downtime, failover is not reliably minutes-scale, and visitors can observe instance transitions. Placement: **future experimental — never a v1 claim, never owner-facing availability language.** (A16's cold-standby guardian is a DIFFERENT shape — only one publisher at a time — and keeps its future listing, now with the added requirement of measured handover testing before any copy is written.)

**OnionBalance is the preferred future multi-host form** (distinct backend keys, aggregated descriptor) — as product engineering done BY the project (automatic pairing, authenticated snapshot sync over Tor, no node identifiers), never as an owner-operated recipe. Open checks before it can be scheduled: the current OnionBalance manual lists C-Tor-only and **no onion-service PoW compatibility** — since v3 mandates PoW on A, OnionBalance cannot ship until that combination is verified on the exact release; publisher placement (one home vs both vs separate) is an unresolved custody trade-off to decide at design time. Multi-host failure testing (fresh/cached clients, host failure, publisher failure, partition, restoration) is a hard gate.

**Adopted as v1 defaults (mostly already in the design — now explicit):**
- **D7 lifecycle/schedule hygiene** (already: sleep masked, maintenance randomised in UTC) + the distribution caveat: randomisation must span the full UTC day, not the owner's waking hours.
- **D8 static/publication hygiene**: atomic content replacement, uniform error behaviour, no public uptime/version/node identifiers, stripped build/file timestamps, bounded request/response resources.
- **D5 tested Tor protections** + NEW explicit rule: **Tor state (especially guard state) is preserved across gateway-container rebuilds/rotations** — rotation must never mint fresh guard state. (Rotation design already restarts tor rarely; state persistence is now a checked golden-config property.)
- **D4**: gateway stays connected whether or not the website process is serving (already true architecturally); stock connection padding stays ON; custom cover traffic is NOT a v1 promise.

**Adopted as v1 opt-in guidance (owner-facing, hardware-optional):**
- **D1 ride-through**: the wizard/docs may recommend a UPS sized to the whole chain (host + router + modem/ONT) and, where available, an automatic backup connection. Copy presents “backup power” / “backup connection,” never configuration. D1 is the strongest single-host O1 defence in the review because it removes events instead of adding noise.

**Rejected: D2 decoy downtime** — for v1 and as advertised privacy defence generally (reviewer's refused-to-ship pick; we concur): real availability cost, filterable by any patient observer, decoy-vs-real failures are distinguishable, misleading-copy risk.

**Deferred:** D3 restore-delay (measurement research only; the human boot-phrase delay already smears restoration), D6 static export/mirror (v1.1 candidate, aligns with backup/export machinery), D9 private mode (already the Private Files v1.1 direction).

**Disclosure copy:** the review's Section D paragraph is ADOPTED as the wizard's residual-risk text (with its sooner/never qualifications intact) and replaces any earlier blurring language wherever it appears. See TIMING-REVIEW-RESPONSE-2026-10-11.md §D.


### A17.1 — Reconciliation addendum: a SECOND timing review arrived (2026-10-11, later)

Cameron supplied a second, independent review of the same pack (TIMING-REVIEW-2-2026-10-11.md). Where both reviews agree, confidence is high; where they differ, the calls below govern. A17 stands except where this addendum amends it.

**Convergent (treat as settled):** P1 same-key mirroring is not a v1 feature and “stays up” is not defensible copy — at best “recovers within minutes”; OnionBalance is the only multi-host form worth future engineering; **D1 ride-through is the strongest practical single-host defence and the opt-in to actually recommend**; **D2 decoy downtime is rejected/refused by both, for the same reasons**; D3 is weak; D6 relocates rather than removes signal; PoW + intro-DoS stay default-on (already in design); no numerical time-to-identification may ever be claimed.

**Blurring — final position:** Review 1's mechanism point stands (cached descriptor ≠ serving; a dead host's intro circuits are dead). Review 2 adds the observer-side nuance: the estimate roughly holds against a *passive* reachability logger and collapses against an *active prober* — and a patient O1 observer will probe. Copy is written to the weaker case. The A17 retraction stands.

**NEW — application-layer timestamp leaks (Review 2, adopted):** the static tiers leak time through feed/RSS `pubDate`, `Last-Modified`, visible post dates, and **EXIF metadata in owner-uploaded images (capture time, sometimes GPS)** — which would defeat the UTC-maintenance randomisation from inside the content. Added to the D8 default hygiene set, now explicit: **the publisher scrubs EXIF on ingest, feed and file timestamps are content-derived or build-fixed (extending the Gate H header work into content), and no local-time strings are emitted anywhere.** This is a real catch for the Journal tier in particular.

**NEW — two named channels for the threat-model text:** (i) **performance fingerprinting** (latency distribution shifts with household load and replica count — a continuous channel, not just up/down); (ii) the **“too reliable” anomaly** (a home server never down in any local outage itself evidences redundancy — defences can create signal). Neither changes v1 engineering; both belong in the internal model and temper all multi-host copy.

**Client authorisation — Review 2 pushes it to “default-offer for personal sites”; adopted in part.** For a *private* audience, client auth collapses most O1/O3 probing (unauthorised observers cannot even fetch the descriptor) — the strongest single measure in either review. But v1's two tiers are public by design; making them key-gated changes the product, not the defaults. Resolution: client auth remains the Private Files mechanism (v1.1), and A17.1 records that Review 2 materially strengthens that tier's case — when Private Files is designed, client auth is presented as its headline privacy property, and the wizard's tier-choice screen may say, truthfully, that a private site is also the hardest to probe for uptime. Not adopted as a v1 default.

**Disclosure paragraph — superseded.** Review 2's §D paragraph replaces Review 1's as the adopted wizard text: it covers the outage-correlation risk accurately AND names the larger truth Review 1 left implicit — availability hiding does not protect against adversaries who monitor large parts of the Tor network, and it closes with the plain safety line (“If being physically located would put you in danger, do not rely on hosting from your home.”) That paragraph, not Review 1's, is what ships, subject to the same fact-check pass as all wizard copy.

**D4 — final position:** Review 2's “reject, do not roll your own padding” and Review 1's “stock padding by default” are compatible and both adopted: stock Tor padding stays on; constant-presence is never claimed as a defence; no custom cover traffic, ever, without published evidence behind it.


---

## A18 — Stage 1 rig verdicts (2026-10-11; evidence: poc/POC-RESULTS.md “Stage 1 rig run”)

**Gate R DECIDED.** Under a default `cryptsetup luksOpen`, the volume key exists only as a non-extractable kernel-keyring reference (`:logon:`; `keyctl pipe` as root → Permission denied), and a new passphrase CANNOT be added without the old one — the A3/Y12 suspicion was correct. **With `luksOpen --disable-keyring`, the raw volume key is visible in `dmsetup table --showkeys`, and `luksAddKey --volume-key-file` adds a new keyslot with no old passphrase (verified end-to-end).**

**A3 ruling (adopted; CONFIRMED by Cameron 2026-10-11 after a pros/cons review): the production initramfs opens the root volume with keyring disabled** (`systemd-cryptsetup` equivalent option), keeping the lost-paper Maintenance re-key promise. The trade is recorded honestly:
- *Cost*: while the system runs, the raw volume key is readable by root in the dm table. A one-time host-root compromise therefore persists across later passphrase changes until a full `cryptsetup reencrypt`. Mitigation already in design: “Change the lock completely” (reencrypt) is the documented response to any suspected compromise, and root compromise of a *running* host is already outside the solved threat model (the sealed-when-off guarantee is untouched — the key exists in RAM in any design once unlocked).
- *Benefit*: the one-secret promise survives losing the paper — the alternative (spare-or-reinstall fallback as the ONLY recovery) would be the first thing real novices hit.
- Implementation pitfall (from the rig): `luksAddKey --volume-key-file` takes the NEW passphrase as the POSITIONAL key file; the `--key-file` form hangs on a hidden prompt.

**Golden runsc flags — per container (measured, not guessed):**
- **B: `--host-uds=create`** (publishes nginx's socket to the host).
- **A: `--host-uds=all`** (creating is not enough — A must be able to *connect* to B's socket through the gofer; with defaults tor logs connection-refused while the socket answers the host fine), **and A's OCI spec must NOT request its own network namespace** (with one, gVisor egress silently black-holes; strip the netns entry, use `--network=host`).
- **Podman integration: a wrapper runtime is REQUIRED** (`runsc --host-uds=all "$@"` registered as a podman runtime). Plain runsc runtime and OCI annotations both fail silently. Quadlet units reference the wrapper.
- Stale-descriptor behaviour observed live (clients holding pre-restart descriptors fail for minutes) — consistent with the accepted 30–120 s A-republish outage; no design change.

**A5 data clause CLOSED: engine is rootful Podman** — now evidence-backed. Rootful: serving PASS, memory ceiling enforced (OOM-kill at limit), fork bomb contained. Rootless FAILED as exercised: containers die at creation in a headless context (“Interactive authentication required”) and only run under `--ignore-cgroups`, surrendering the ceilings — the delta review's DQ2 failure mode, confirmed empirically. Rootless is not revisited without new evidence.

**Recorded behaviour caveat (runsc burst-fork):** under gVisor, burst forking makes a shell exit almost immediately at any pids-limit (containment achieved via gVisor fragility, not the numeric ceiling; spaced forks are fine). Consequence: container workloads must avoid burst-fork patterns; the golden images' startup paths are to be fork-profiled in alpha testing. Not a blocker.

**Gate 5 (rig baseline):** 134/134 requests OK, 2.23 req/s sustained, ~7 s mean latency — a rendezvous-bound floor from one client vantage, NOT a service ceiling (Stage 0's 7.66 req/s measured a shorter path). PoW engagement remains UNMEASURED; `PoWQueueRate` calibration (DQ3) still needs a dedicated multi-client load run in alpha. Defaults stand meanwhile.


---

## A19 — Boot chain ruling (2026-10-11; Opus review of BOOT-CHAIN-PACK, verdict adopted)

**Decision: Option A.** /boot stays encrypted. Every phrase that must work at GRUB is enrolled TWICE — one argon2id slot + one PBKDF2 slot (parameters benchmarked against the actual signed GRUB on target hardware, highest iterations inside the boot-time budget). The initramfs opens the root volume with a SEPARATE random keyfile credential (32 random bytes, its own argon2id slot). **Slot layout is five slots, documented in a recorded slot-role map**: MAIN-argon2id, MAIN-pbkdf2, SPARE-argon2id, SPARE-pbkdf2, KEYFILE-argon2id. An attacker targets the cheapest slot; the retained argon2id slots serve external recovery compatibility and add no guessing protection while PBKDF2 twins exist — accepted because phrases are machine-generated at ~90 bits (two independent phrases ≈ 1 bit of aggregate margin, not a collapse). Generation soundness (CSPRNG, wordlist, sampling, no logging) is therefore a load-bearing assumption and a tested property.

**Honesty limit (copy rule):** Option A provides powered-off CONFIDENTIALITY of boot artifacts. It does NOT provide authenticated boot through the passphrase prompt: Debian's signed shim/GRUB/kernel chain does not authenticate our locally generated initramfs or every boot-path decision, and an attacker may redirect boot toward alternative early userspace. **Never describe the boot chain as evil-maid-proof.** (Option B was rejected: plaintext initramfs is an exposed credential-prompt implementation, and the tamper-then-owner-boots scenario — hostile household member, repeated property access, compromised repair — is a realistic home-user risk, not a nation-state footnote.)

**Keyfile hygiene (release blockers, from the review):** source keyfile only in `/etc/cryptsetup-keys.d/` (dir 0700, file 0600, root-owned); narrow single-file inclusion into initramfs, `UMASK=0077`; crypttab references the exact file and its slot explicitly; images and build/extraction temp dirs only on encrypted or memory-backed storage; the keyfile NEVER appears in backups, support/diagnostic bundles, installer logs, the ESP, or any plaintext partition — export paths exclude initramfs images and their contents by default. **Update invariant as a hard failure, not a warning**: after install and every kernel/initramfs update, verify every credential-bearing image sits on encrypted storage, none is on the ESP, the image contains the intended keyfile (never a phrase or maintenance secret), it unlocks its slot, and retained older images remain compatible. **Keyfile rotation is its own tested procedure** (new keyfile → enrol → rebuild all retained images → validate → remove old slot → purge artifacts); deleting image files alone revokes nothing.

**Transactional credential management (release blocker for Maintenance):** phrase changes are STAGED transactions, never in-place slot edits: maintenance lock → verify UUID/mapping/volume-key → add BOTH new slots (explicit KDF per slot) from the volume key held only in protected memory-backed storage (never argv/env/logs/temp files) → `cryptsetup open --test-passphrase` per slot with exact normalized phrase bytes (ASCII words, single spaces, NO trailing newline) → durable non-secret role-map commit → retire the old pair ONLY after validation, with a real-GRUB boot of the new phrase as best assurance and an idempotent interruption-recovery state. The failure modes are asymmetric and both bad: only-argon2id updated = new phrase fails at GRUB while the old phrase still boots (“rotation succeeded” lie); only-PBKDF2 updated = old phrase still unlocks via argon2id outside GRUB. **Invariant: a completed rotation replaces every slot holding that phrase; no obsolete copy remains.** A phrase-only change needs no initramfs rebuild; a keyfile change does.

**Header backups are security-sensitive artifacts** (consistent with A3/Y14): removing a slot does not revoke a stolen older header while the volume key is unchanged; retention/revocation policy must say so. **Re-encryption as compromise cure must actually replace the volume key** and must not retain compromised credentials — a stolen keyfile left enrolled unlocks the re-encrypted volume; rotate the keyfile and retire compromised phrases during the same operation.

**GRUB mixed-slot acceptance tests (release gate for the boot path):** argon2id-lower/PBKDF2-higher and reverse orderings; MAIN and SPARE independently; wrong phrase; PBKDF2 slot removed; header state after interrupted maintenance. GRUB slot selection must be TESTED on the exact signed build — priority flags are not a coordination mechanism and GRUB is not assumed to honour LUKS2 slot priority. Also verify the initramfs-created mapping itself has the A18 keyring-disabled property (a later running-system setting does not retroactively change how early userspace opened it).


### A19.1 — Second boot-chain review: the argon2id correction (2026-10-11; SUPERSEDES A19's slot layout)

A second independent review of the same pack (BOOT-CHAIN-REVIEW-2-2026-10-11.md) reached verdict A but corrected A19's five-slot dual-derivation layout. The correction is ADOPTED; A19's honesty limits, keyfile hygiene, transactional principles, and header-backup rules all stand, amended as follows:

- **Slot layout is now THREE slots: MAIN (PBKDF2), SPARE (PBKDF2), KEYFILE (random, KDF immaterial). Argon2id is dropped entirely.** Reason (decisive): a volume's offline resistance is the MINIMUM over its keyslots — an attacker ignores the argon2id twin and attacks the PBKDF2 slot, so the twin adds zero protection while doubling every re-key operation and creating two silent partial-update failure modes (new phrase rejected at GRUB / revoked phrase still unlocking). Review #1 conceded the math but kept argon2id for “external recovery compatibility”; Review #2's counter wins — modern recovery tooling reads PBKDF2 fine, and deleting a failure class beats retaining a vestige. The SPARE in argon2id would have reproduced the original GRUB bug on the worst possible day; both phrases are PBKDF2, benchmarked against the signed GRUB on target hardware.
- **Entropy-source audit is a release gate** (the true single point of failure): phrase generator must use `getrandom()` blocking until seeded (fresh installs on minimal hardware are entropy-starved at the critical moment), the full ~7776-entry unique wordlist, and bias-free selection; these are tested properties, recorded with the build.
- **Added hygiene (from Review #2):** keyfile mode **0400** root:root; **swap is encrypted with a random key or absent** (unencrypted swap can page out keyfile/volume key/phrase; no hibernation — already aligned with masked sleep); **kdump disabled** or encrypted-target-only; **Calamares logs scrubbed and verified** to contain neither phrase nor keyfile material, and a post-install sweep confirms no secrets anywhere in /var/log; **the ISO must never contain a keyfile** (per-install CSPRNG generation is verified in install tests); `.old` initramfs images must not accumulate outside encrypted /boot; etckeeper-style /etc versioning must exclude credential paths.
- **Re-key procedure simplified** to Review #2's sequence: extract volume key (protected, shred-on-exit) → add new PBKDF2 slot → test-passphrase → kill old slot → regenerate initramfs → **a real GRUB boot test is required before the re-key is declared done** (cryptsetup success does not prove GRUB acceptance). Reencrypt re-wraps existing slots automatically (Review #2), BUT A19's compromise rule stands: rotating credentials is still required when a credential itself (not just the volume key) may be compromised — re-wrap preserves whatever credentials remain enrolled.
- **GRUB acceptance tests shrink accordingly**: MAIN, SPARE, wrong phrase, removed slot, interrupted maintenance — no mixed-KDF ordering tests, because the ambiguity is designed out.
- **Parked (explicitly not v1): detached LUKS header on removable media** as a future advanced opt-in (“seal-when-off++”); barred from v1 by the concept budget.

---

## A20 — Owner-installed software allowed (2026-10-12; Cameron's ruling, supersedes the BYOC cut and the A12 "one blessed app" framing)

Cameron, 2026-10-12: "I think it would be okay to allow any forum or WordPress or whatever software to be installed as the design keeps the IP hidden and any hacks would be contained to the docker." And: guarding owners against their own software choices is "outside of the scope" at this stage.

Adopted. The platform's promise is narrow and architectural: the IP stays hidden and a compromise stays inside the app container, because containment is a property of the WIRING (app container has no network; the Tor gateway container holds the onion key and exposes only a unix-socket HTTP path; enforced resource ceilings; gVisor boundary) — not of which software the owner runs. What an owner puts inside their container is their decision and their responsibility for its contents (the app holds whatever the owner/app stores: forum DBs, posts, member data).

Consequences:
- The dynamic tier (A12) is no longer a curated single-app tier: owners may install arbitrary PHP applications (forums, WordPress, etc.) into the app container using the same A/B socket wiring and the A12 forward-compat reservations (app-data volume class, DB-capable backup manifest, optional admin-on-separate-onion-identity WITH client authorization — offered as a platform capability, not a mandate).
- Project-packaged installs (e.g. a one-click SMF or WordPress) may exist later as a CONVENIENCE, never as a gate on what an owner may run.
- Static tiers remain the default and the v1 scope: sequencing is unchanged (dynamic/BYOC lands after the static core passes its gates). This amendment changes what is PERMITTED and promised, not the build order.
- Honest caveats that remain facts of the wiring, to be stated plainly in-product without moralizing: the app container has no outbound mail (forums cannot send email); the platform's upload-scrub guarantee covers the built-in editors, not an app's own upload handling; a hacked app can spend the container's CPU/ RAM allowance and deface its own site, but cannot reach the host, the LAN, the Tor container's key, or the network.

---

## A21 — Licence decided; dynamic-tier development STARTED (Cameron's directives, 2026-10-13)

- **Licence: Apache License 2.0** for all project code (LICENSE at repo root). Cameron's words: "give it GPLv3 — honestly whatever is the least restrictive. I don't care." GPLv3 is copyleft, NOT the least restrictive option; on Cameron's stated criterion the decision lands on a permissive licence. Apache-2.0 chosen over MIT/BSD for its explicit patent grant and its trademark clause (the licence grants no rights in the project name or marks — relevant given the open trademark question around "Onion"). This supersedes A14's "GPLv3 recommended, awaiting Cameron's OK."
- **Dynamic tier development STARTED.** A12's trigger condition (static core passes its PoC/alpha gates) is met: v1 static product is functionally complete and a prod ISO is publicly downloadable. Cameron's stated goal: reach hosting of interactive sites — a forum or a marketplace. Per A20, the tier permits arbitrary owner-installed PHP software; proving order is feasibility gates first (MariaDB + PHP-FPM under gVisor in the sealed no-network app container; SMF 2.1.7 as the reference application), then app plumbing (sockets, app-data volume, DB-capable backups), then an end-to-end interactive site.

---

## A22 — The dynamic app slot is language-neutral; Rust in scope (2026-10-13)

Cameron asked whether the platform will host Rust applications. Answer recorded as design: the app slot is defined as **app process + unix socket (or in-container loopback) + persistent data volume, inside the sealed no-network container under gVisor** — the wiring never cared what language the process is written in. PHP-FPM is runtime #1 (forums/WordPress class, per A20); **native binaries are runtime #2**, and a statically linked Rust binary is a particularly good citizen (single file, no interpreter stack; SQLite embedded removes the database-server dependency entirely). Known caveats, same family as MariaDB's: crates built on io_uring (tokio-uring) face gVisor's limited io_uring support — standard tokio/epoll is fine; apps needing outbound network remain denied regardless of language. Gate P4 added to the Slice 6 gate round to prove a Rust service over the socket path.

---

## A23 — Ship packaged default apps as convenience (Cameron's proposal, 2026-10-13)

Cameron: "Would it make sense to ship it with some default software such as a journal platform, a marketplace, a forum, etc? This keeps it easy and maybe makes it more secure." Adopted, within A20's frame (packaging = convenience, NEVER a gate; the open owner-install slot remains the foundation):

- **Packaged recipes** = pinned version + verified checksum + a sealed-world configuration overlay (the P3 findings applied: REMOTE_ADDR loopback, mail off cleanly, remote-avatar/image-proxy fetches off, phone-home neutralized) + DB seeding + nginx include, offered as wizard site-type choices. The app is present in the image, started only if chosen.
- **Security accounting, stated precisely**: packaging buys known-good configuration, verified provenance, correct permissions/quotas, and fixes delivered through the update pipeline. It does NOT buy containment — that remains a property of the wiring (A20), and a vulnerable bundled app is still a vulnerable app (its own data and defacement risk). Bundling also imports a standing maintenance duty: a CVE in a bundled app obliges the project to ship the fix via the update pipeline.
- **Bundle candidates**: Forum = SMF 2.1.7 (proven sealed in the gate round) — first recipe. WordPress — second (the app people know; covers dynamic blog/pages). Journal needs no bundle: the built-in static Journal tier already is the default journal. **Marketplace: no off-the-shelf bundle candidate fits the sealed model today** (WooCommerce-class stacks assume payments/mail egress; OpenBazaar is dead) — the marketplace recipe is Cameron's own Rust marketplace when it exists, which fits the native-binary slot directly.
- **Recipe candidate survey (2026-10-13, exploratory — not a commitment list)**: judged by the sealed test (core function must not require egress/mail/payments), maintenance weight, redistributable licence, home-hardware sanity. First wave after SMF: **WordPress** (the known app), **DokuWiki** (flat-file PHP, no database — the cheapest possible maintenance), **Gitea** (single native Go binary + SQLite — also proves the native slot for third-party software). Strong seconds: **Flarum** (modern forum), **PrivateBin** (zero-knowledge pastebin, ethos-perfect, tiny), **Vaultwarden** (Rust native binary, private vault sync — high value, high maintenance-duty stakes). Handle with care: **Nextcloud** (overlaps the Private Files v1.1 design; heavy; egress assumptions — test before promising). Fails the sealed test: Mastodon (federation IS egress), Discourse (mail-centric, heavy), FreshRSS (feed-fetching is egress), WooCommerce-class shops (payments/mail), Jellyfin (transcoding weight).
- **Piwigo DROPPED from the candidate list (2026-10-13, Cameron's challenge — sustained)**: "WordPress has many plugins including a photogallery. Does Piwigo do something so significantly better that it is justified?" Verdict: not for the common case. Piwigo's genuine edges are narrow: (1) photos are first-class — albums with per-album/per-photo privacy tiers (public/contacts/family) designed in from the start, where WordPress media is post-attachments with plugin-bolted access control; (2) photographer bulk workflow (mass upload, EXIF/IPTC preserved and searchable, batch curation). Against that: WordPress + a gallery plugin covers the casual gallery entirely, and every bundle is a standing maintenance duty + image weight + update-channel burden — a bundle must earn its keep against the generalist already in the image. DokuWiki survives the same test only because its flat-file/no-DB shape makes carrying it nearly free; Piwigo (DB, own CVE stream, heavy overlap) does not. Piwigo remains installable by any owner via the open slot (A20), and the recipe can be added later if tester demand demonstrates the photography-first audience is real.

---

## A24 — Concealing Tor use from the local network: bridges opt-in, VPS tunnels rejected (2026-10-13)

Cameron asked about hiding the host's Tor usage itself ("tor node things that SSH into it and then pop out elsewhere"). What exists, and the rulings:

- **Bridges + pluggable transports (obfs4) are the real mechanism.** Instead of connecting to a publicly listed Tor guard (an ISP can see "this household talks to Tor, persistently"), the box connects to an unlisted bridge with obfuscated traffic that doesn't fingerprint as Tor. Works for onion services (the publisher's tor uses bridges as its entry). It conceals *Tor usage from the local network observer only* — visitors and the Tor network see no difference, and the bridge learns the home IP exactly as a guard would (same trust, different hat).
- **Ruling: SUPPORT as an opt-in, default OFF, placed in Dashboard/Maintenance — not the install wizard** (concept budget stays at five). Supported form: obfs4 bridge lines from the standard pool, with a free-text "your own bridge" field covering self-run bridges. Default off because: most home users in unblocked countries gain little, pool bridges add a flakiness/downtime source for an always-on service, and censorship-blocked users are the ones who truly need it (for them it is the difference between working and not).
- **The DIY variant Cameron pictured — an SSH/VPN tunnel to a VPS, Tor inside it — is REJECTED as a product feature.** It looks like concealment but trades worse: the VPS provider becomes a single party holding a binding record (home IP ↔ onion activity) AND is linked to the owner's identity through the cloud account/payment trail. A pool bridge has neither problem. A self-run bridge on a VPS has the same identity-link issue knowingly accepted by a sophisticated owner — supported only via the bring-your-own-bridge field, never promoted.
- Sequencing: v1.1-class slice (torrc variant + per-gateway firewall profile hooks exist per A15) — after the plumbing and update-pipeline work, not before.

---

## A25 — Spare passphrase feature REMOVED: one secret, and its loss is total (owner decision, 2026-10-20)

Cameron's decision, taken in two steps the same evening. First, on
finding S13 of the fourth public-repo review — the installer and the
EXPLAINER promised the spare could be revoked, and no revocation code
existed — he chose to withdraw the promise until revocation was built.
He then went further and removed the feature itself, in his words:
no second password at all — just one single one, and if it's lost
everything is over.

**What this supersedes.** Every spare provision of the earlier design:
A3's spare keyslot, its second backup recipient, its revocation design
and revocation honesty; A19.1's three-slot layout (MAIN · SPARE ·
KEYFILE becomes TWO slots: MAIN · KEYFILE); A11's five-concept budget
(the user now holds exactly FOUR concepts: **disk phrase** ·
**generated login words** · **restart-needed card** · **Repair
button** — and A24's "concept budget stays at five" aside is
superseded with it); the WALKTHROUGH's spare items (C4, §6 item 1);
and the S13 finding itself, which this removal closes — there is no
longer a promise to keep, because there is no longer a spare.

**The product as it now stands.** The installer has no spare page and
generates no spare candidate; the phrase page states the stakes at
the moment of creation — the paper phrase is the only key, and losing
it loses the computer, the website, and the backups. The boot-key job
enrols exactly one phrase slot; the role map carries MAIN and KEYFILE
only; `backup.json` carries the main recipient only, backups are
encrypted to that one recipient, and restore derives its identity
from the main salt only. (A dual-recipient backup made before this
removal still opens with its MAIN phrase — the removal creates no
orphaned backups.) Nothing about A18 changes: while the machine is
still running, Maintenance can set a new phrase without the old one;
the total-loss rule governs the sealed machine, as it always did for
a lost paper with no one logged in.

**Why removal over repair.** A spare whose revocation is unbuilt is a
standing second owner the product could not honourably describe; a
spare with revocation built is a second credential to generate,
verify, enrol, and explain, inside a concept budget that was already
at its ceiling. One secret is the simplest true story the product can
tell a non-technical owner, and it is the story the phrase page was
already telling about the main phrase. If a second key is ever wanted
again, it starts from A3's text and must satisfy BACKUP-RESTORE-
ACCEPTANCE item 12's honesty spec before it ships — as a new
amendment, not a quiet return.

---

## A26 — Recipes are installers, not update channels: app updates are the owner's after install (owner decision, 2026-10-21)

Cameron's ruling, closing the question the LOCAL-MODS-UPDATE-POLICY
brief (2026-10-15) left open: "I think a better method is to just
install it and then let them deal with every future update."

- **The rule.** A recipe package installs an app once. After an app
  is installed on a box, no platform update run ever modifies its
  tree — no swap, no file replacement, byte-for-byte untouched.
  Because no platform app update exists, the brief's carryover
  question (plain carryover vs surgical merge vs three-way
  keep-edited-and-flag) is closed as DECIDED AGAINST: no merge or
  carryover machinery is built, and nothing an owner added to an
  app can be silently reverted by an update, because there is no
  update that touches it.
- **"Installed" is the applier's state record.** An app counts as
  installed when its recipe state record
  (/var/lib/onionhost/recipes/<id>/state.json) carries a completed
  apply — installed=True plus the applied version, written only
  when an apply completes (ruling recorded in the ISO-BUILD-LOG
  entry: the record is the ground truth; a first install that
  failed before completion leaves no such record, so the install
  path stays open for it; a rollback rewrites the record with the
  restored version — still installed). The dpkg state of the
  recipe PACKAGE is not the judge: factory images register every
  recipe package on every box, selected or not.
- **The update path is gated at both locks.** The updater's
  managed set is the platform package alone: it never installs,
  upgrades, rolls back, refuses, or judges a recipe package
  (standing high-water marks and floors recorded for recipe
  packages by earlier updaters are inert, and the fail-closed
  marker records the platform only). Recipe packages are still
  held across the updater's Debian phase so the generic upgrade
  cannot fire a recipe postinst behind its back — and the
  postinst itself is the second lock: it applies only when the
  app is not installed yet (the applier's new `is-installed`
  query), so even a hand-run package upgrade updates the payload
  on disk and leaves the installed app exactly as it was.
- **Reporting.** An installed app with a newer recipe package in
  the repository is a normal, healthy state — never an error,
  never a rollback or fail-closed trigger. The updater reports it
  in status.json (owner_maintained: app, installed version,
  available version) and the Dashboard words it as information:
  a newer package exists, the installed copy is the owner's to
  update. The wizard says the same thing plainly at the moment of
  choosing an app — we install it; updating it afterwards is
  yours — and Owner Guide §4 (the section the brief left PENDING)
  now states the policy and how an owner actually updates each
  app inside the sealed box.
- **Floors gate install time only.** A recipe's security floor
  may refuse a FIRST install (the applier refuses a payload whose
  version is below the floor its own package declares, before
  the app is placed); it can never strand, judge, or fail-close
  an app that is already installed. Platform package floors and
  the updater's fail-closed semantics are unchanged. This
  narrows A23's security accounting: packaging still buys
  known-good configuration and verified provenance **of the
  first install**, but a CVE in a bundled app no longer obliges
  the project to deliver the fix into installed apps — the fix
  ships as a new recipe package for fresh installs, the Dashboard
  notes its existence, and applying it is the owner's act. The
  maintenance duty A23 described survives as prompt packaging
  and honest reporting, not as a channel into running apps.
- **Scope kept.** Fresh installs get the current recipe version:
  a box installing an app takes the payload it carries (the
  factory set), which is the version current for that box; the
  updater does not refresh unused payloads either — a recipe
  package is entirely outside the update channel. How the first
  install works is unchanged (publish → apply → hook), and an
  owner pressing Go Live re-applies the installer as publish has
  always done: deliberate, local, owner-initiated — not an update
  run. Owner-installed (non-recipe) apps were already
  owner-maintained under A20 and are untouched, as is the
  marketplace recipe's shipping posture (still excluded from
  SHIPPING).

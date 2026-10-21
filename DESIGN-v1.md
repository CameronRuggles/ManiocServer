# OnionHost OS — Design v1 (working name)

## 1. Vision

**Any ordinary home desktop can become a private website that nobody can locate —
installed by someone with no technical training, in one sitting, by clicking through
a wizard.**

The user never sees a terminal, never edits a config file, never forwards a port on
their router, and never invents a password. The system generates every credential,
proves to the user with plain-language checks that the site is live and that its
real location is hidden, and keeps the website in a sealed box so that even a fully
hacked website reveals nothing about the machine it runs on.

### The promise (what the box on the shelf would say)

1. Download. 2. Boot from USB and click through the install.
3. Write down the passwords it gives you. 4. Name your site, click **Go Live**.
You get a `.onion` address and a QR code. That's the whole skill requirement.

### Non-goals / honest limits

- It protects the server's *location and identity*. It does not protect the user
  from what they themselves publish (a photo with EXIF GPS, their real name in a
  post, is still a leak — the wizard strips EXIF and warns, it cannot read minds).
- It does not defeat a global traffic-correlation adversary (Tor's own limit).
- If an attacker gets the admin or disk password, or physical access to the
  *running* machine, the game is over. Encryption protects a powered-off machine.
- Docker alone is not a VM. This design therefore layers rootless/user-namespace
  isolation, dropped capabilities, seccomp/AppArmor, and an optional gVisor
  runtime (§5) so "escaped the website" ≠ "escaped the box."

## 2. Target user & capability ceiling

Design ceiling: a motivated 12-year-old. That means:

- Reading level ~grade 6. No jargon without a one-line plain explanation.
- Every screen has ONE decision. Sensible defaults pre-selected.
- No typing long random strings. Passwords are generated *word phrases* (§4).
- No question whose wrong answer breaks the install. Dangerous options are
  absent, not warned about.
- Success is shown, not asserted: green check cards, a QR code that works,
  a "visit my site" test button.

## 3. The journey

### Stage A — Get it (off-machine)
- Download ISO (~2–3 GB) + a one-page "make a USB stick" guide pointing at
  balenaEtcher (3 clicks, same on Windows/Mac/Linux).

### Stage B — Install (Calamares graphical installer, ~7 screens)
1. **Language** (auto-detected, changeable)
2. **Where are you** — timezone from a map; keyboard auto-matched.
3. **Internet** — Ethernet just works; Wi-Fi is a network list + password.
   (Internet is needed for Tor, NOT for installing — the ISO installs offline.)
4. **Disk** — one big friendly option: *"Use the whole disk — this erases
   everything on this computer"* with the disk named in plain words
   ("Samsung SSD, 500 GB"). Manual partitioning exists behind an "Advanced"
   door the target user never opens. Full-disk LUKS2 encryption is NOT optional.
5. **Your disk password** — generated word phrase, §4. User writes it down and
   proves it by re-typing two of the words.
6. **Your name & computer login** — user picks a username; login password is a
   second generated word phrase (not the disk one — see §4).
7. **Install** — progress bar, 10–20 min. Then: *"Remove the USB stick and press
   Restart."*

Boot behaviour (SETTLED by Cameron 2026-10-10 — not a choice): the disk
password is typed at **every** boot. No TPM/auto-unlock is offered. If the
machine is unplugged or loses power, it comes back locked and stays locked —
site down, data unreadable — until the admin physically types the disk
phrase. Screen 5 says exactly that in plain words, so the user trades
power-cut uptime for seizure safety knowingly.

### Stage C — First-boot setup wizard ("OOBE", ~5 screens)
Runs automatically on first login. The desktop before this is finished shows
nothing but the wizard.

1. **Name your site** — a title and one sentence. (Not the address — the
   `.onion` address is cryptographic and cannot be chosen; vanity addresses are
   a documented non-feature: they teach users to expect meaning in the address.)
2. **What kind of site** — risk-tiered cards, safest first:
   - *Simple pages* (default): text/photos, built from a form. Static. Tiny risk.
   - *Blog*: adds a database container (§5). Medium risk, still sealed.
   - *Files*: a private drop/download page.
   - *Bring your own Docker container* (Advanced door): user's image, same
     sealed network rules enforced — it physically cannot get internet access.
3. **Your website password** — generated word phrase, §4 (only for site types
   with a login). Stored in the OS keyring; shown on the Recovery Sheet.
4. **Help the Tor network? (optional)** — the relay question, off by default, §7.
5. **Go Live** — the machine builds the containers, starts Tor, waits for the
   onion service to be reachable, and runs the self-check battery (§6). Ends on:
   the `.onion` address in large type, a QR code, **[Print my Recovery Sheet]**,
   **[Visit my site]** (opens Tor Browser, pre-installed, to the new address).

### Stage D — Daily life (desktop, 4 big icons)
- **My Site** — edit pages/files (a local-only editor; publishes into the
  read-only web volume through a publisher service, §5).
- **Dashboard** — green/amber cards only: Site is live · Location hidden test:
  passed (today 06:00) · Backups · Updates. Plus one red **Site OFF** button:
  stops Tor, site unreachable within seconds. (Key-shredding "panic wipe" is
  behind a hold-to-confirm door — destroying the onion key is irreversible.)
- **Backup** — one button: encrypted backup to a USB stick (§8).
- **Settings** — updates (automatic by default), relay toggle, passwords.

No other inbound service exists. SSH is OFF and absent from the UI.
The dashboard binds to 127.0.0.1 only. Remote admin, if it ever ships, is a
*separate* admin onion service with Tor client-authorization (a key the owner
carries), never the public site's login page.

## 4. Generated passwords — the design that makes or breaks it

Random strings (`xK9$mQ2!`) fail this user: untypeable, unwritable, lost.
Instead, every generated credential is a **Diceware-style word phrase**:

- Disk passphrase: 6 words + a digit, e.g. `cleft apricot 7 banjo tundra velvet moss`
  (~77 bits — strong, writable, typeable at a boot prompt, memorable with use).
- Login password: 5 words, different set.
- Website admin password: 5 words, different again.
- Database / internal secrets: machine-only, 256-bit, never shown, stored as
  Docker secret files — the user never meets them.

Rules:
- **Never reuse** one phrase for two jobs (disk ≠ login ≠ website). The wizard
  says why in one line: *"If someone finds one paper, they shouldn't get everything."*
- **Prove possession, gently:** after showing a phrase, the screen hides it and
  asks for word #2 and word #5. Can't do it → show it again. This catches
  "didn't actually write it down" without a scolding tone.
- **Recovery Sheet** (the centrepiece): one printable page — site `.onion`
  address + QR, all three phrases labelled in plain words ("Disk password —
  you type this when the computer starts"), date, and *"Keep this paper
  somewhere private. Anyone with this paper controls your site."*
  Also offered as an encrypted file on a USB stick (encrypted under the disk
  phrase). Printing is nudged hard; a screenshot/photo warning is shown
  ("a photo of this in cloud photos is a copy of your keys").
- Passwords also live in the local OS keyring so Dashboard can show them to a
  logged-in admin behind the login password — the paper is backup, not the
  only copy. (Trade-off accepted and documented: convenience for the target
  user beats the marginal risk, because the disk itself is encrypted.)

## 5. Architecture — your two-container instinct, corrected and hardened

### The correction
An onion service never uses an "exit". Exit relays are only for visiting the
*ordinary* internet through Tor. Visitor and server meet *inside* the Tor
network at a rendezvous point: the visitor never leaves Tor, the server never
leaves Tor, and neither learns the other's IP address. So the second container
is not an exit — it's a **Tor gateway**: the only box allowed to talk to the
internet, and all it speaks is Tor.

This is the Whonix gateway/workstation pattern, inverted for inbound hosting.

### Compartments

```
  Visitor's Tor Browser
          │
   ┌──────▼───────┐        Tor network (guard → rendezvous)
   │  Tor relays  │  ← the server connects OUT to its guard; no inbound
   └──────┬───────┘    ports, no router changes, works behind NAT/CGNAT
          │  outbound only, Tor protocol only
   ┌──────▼──────────────────────────────┐
   │ HOST OS (Debian 12, LUKS, minimal)  │  no website code, no inbound ports,
   │  nftables: default-drop in AND out, │  AppArmor, unattended security
   │  exceptions listed below only       │  updates, dashboard on 127.0.0.1
   │                                     │
   │  ┌───────────────────────────────┐  │
   │  │ CONTAINER A — TOR GATEWAY     │  │  holds the onion private key
   │  │ tor daemon only, no shell     │  │  (the site's identity) in its own
   │  │ tools, no web code            │  │  volume, 0700. SocksPort OFF,
   │  │                               │  │  ControlPort = unix socket,
   │  └──────┬───────────────▲────────┘  │  never shared with Container B.
   │         │ HiddenServicePort 80 → B:80
   │         │               │ established-only return traffic;
   │         │               │ B may initiate NOTHING to A or anywhere
   │  ┌──────▼───────────────┴────────┐  │
   │  │ CONTAINER B — WEBSITE         │  │  nginx-unprivileged (uid 101) +
   │  │ read-only FS, all caps dropped│  │  static files (default tier).
   │  │ no internet route, no DNS,    │  │  Knows NO keys, NO credentials
   │  │ no docker socket, gVisor      │  │  except (blog tier) a DB secret.
   │  └──────────────┬────────────────┘  │
   │                 │ backend net only  │
   │  ┌──────────────▼────────────────┐  │
   │  │ CONTAINER C — DATABASE (opt.) │  │  blog tier only; reachable only
   │  │ own volume, no other network  │  │  from B, reachable from nothing else
   │  └───────────────────────────────┘  │
   └─────────────────────────────────────┘
```

### Networks (Docker)

| Network | Members | `internal` | Gateway/DNS | Purpose |
|---|---|---|---|---|
| `tor-egress` | Tor gateway only | no | host NAT, egress-filtered | Tor gateway ↔ internet, Tor ports only |
| `onion-front` | Tor gateway + Website | **yes** | none / none | gateway forwards visitor requests to web:80 |
| `site-back` | Website + Database | **yes** | none / none | web ↔ DB, nothing else |

Website container is attached to NO network that has a gateway. Its routing
table can reach exactly two things: the Tor gateway's front-network address
(only on already-established connections) and the database. It has no DNS
server configured — names are meaningless inside the box by design.

### Host firewall (nftables) — the part that makes the containers' rules real
Docker can be misconfigured; the host firewall is the second, independent wall:
- INPUT default drop. From `onion-front`/`site-back` subnets: drop everything
  toward the host except the single forwarded web port path.
- OUTPUT/FORWARD default drop for container subnets, except: Tor gateway
  subnet → internet on Tor-usable ports (443/9001 etc.), via IPv4 NAT.
- **IPv6 from all container networks: dropped.** (The classic silent leak.)
- Host's own egress (updates) is a separate, host-only rule the containers
  cannot use; OS updates are additionally fetched over Tor where the package
  source supports it (apt-over-Tor as a hardening option, default on for Tor
  itself).

### Why the onion key lives in Container A, not B
The `.onion` address *is* its private key. The website is the component most
likely to be compromised (it parses untrusted input all day). Therefore the
website must never hold the identity it serves: a hacked site can be deleted
and rebuilt in minutes and the address survives; a stolen key means the
attacker *becomes* the site, forever, from anywhere. Key isolation is the
single most important decision in this design.

### Container hardening (B, and A where applicable)
- Rootless Docker / userns-remap: root inside = unprivileged nobody outside.
- `read_only: true` rootfs; only writable mounts: site content **read-only**
  for B (a host-side publisher service, not reachable from any network, is the
  only writer), one small tmpfs `/tmp`, and (blog tier) the DB volume in C.
- `cap_drop: ALL`, `no-new-privileges`, default seccomp + AppArmor profiles.
- Runtime: **gVisor (`runsc`) default** for the website container — a userspace
  kernel intercepts syscalls, so a container escape still isn't the host
  kernel. Fallback to `runc` only if the hardware can't, and Dashboard shows
  an amber card if so — the user sees the downgrade.
- Resource ceilings (CPU/RAM/PIDs) on B and C: a fork-bomb or miner tops out
  in its box and trips a Dashboard warning.
- Images are pinned by digest, signature-checked (cosign) at build/first-run;
  the website image contains no package manager, no shell tools beyond the
  server itself where the base allows it.

## 6. If the website is fully hacked — walk the attack

Attacker gets remote code execution in the website, then root in the container:

1. **"What's my IP?"** — There isn't one in the box. No default route, no DNS,
   outbound SYNs die at the internal network; `curl` to any IP-check site
   fails. Environment, hostname (`onionhost`), and `/etc/hosts` contain only
   generic/container values. The Docker gateway address visible on
   `onion-front` is a private bridge IP that identifies nothing.
2. **"Scan the house LAN / attack the router"** — No route exists; host
   firewall independently drops container→LAN traffic.
3. **"Steal the .onion identity"** — Key is in Container A. B has no socket,
   port, or mount that reaches it. Tor's control socket is not shared.
4. **"Persist / become a botnet node / mine"** — Read-only rootfs; a restart
   (nightly, automatic) returns a pristine image. No egress = useless as a
   botnet node or spam source even while compromised. PID/RAM ceilings cap mining.
5. **"Attack Tor itself"** — B can initiate nothing to A; A's front-network
   side listens on no port. The only flow is A's forwarded HTTP to B:80,
   with replies on established connections.
6. **"Read other data on the PC"** — B's mounts: site content (ro) and
   nothing else. No home directory, no docker.sock, no host /proc (gVisor +
   masked paths).
7. **Detection** — Egress attempts, ceiling hits, and file-integrity drift in
   the (read-only) image are logged host-side; Dashboard turns the
   "Location hidden" card amber and the daily self-check (§6 battery) fails
   loudly instead of silently.

What still works for the attacker: defacing or deleting the *public site
content* (it's the thing they compromised — backups in §8 are the answer),
and reading data the site itself can read (blog DB contents in tier 2 — which
is why the default tier is static and holds no secrets).

### Go-live & daily self-check battery (shown as plain cards)
From inside Container B, the checker attempts and must FAIL at: reaching the
internet by IP, resolving a DNS name, reaching the host, reaching the LAN
router, reaching Container A's control port, reading the onion key.
From the host it verifies: no router/inbound ports listening, Tor says the
onion service is published, firewall rules match the golden config.
Any pass-where-it-should-fail = site does not go live / Dashboard goes red.

## 7. The relay question — separate feature, default OFF

Hosting needs **no relay at all** (§5). A relay donates bandwidth to carry
*strangers'* Tor circuits:

- **Bridge** (unlisted, helps censored users connect): low bandwidth, no
  public port listing, low risk. Offered in the wizard as the one friendly
  option, still default-off, with a monthly bandwidth cap slider.
- **Middle/guard relay**: needs a publicly reachable port (fails on CGNAT,
  some home connections), more bandwidth, more attention. Advanced door only.
- **Exit relay**: **not offered.** Running an exit from a home IP invites
  abuse complaints and law-enforcement visits for strangers' traffic; a
  consumer product must never put a 12-year-old's household in that position.

The Tor gateway container for the user's *own* site is not a relay in this
sense — it carries only the site's own onion-service circuits.

## 8. Backup, restore, updates, off-switch

- **Backup**: one button → encrypted archive (age/LUKS-encrypted under the
  disk phrase) of: site content, DB dump, onion key, config. Restore onto a
  fresh install reproduces the *same* `.onion` address. The wizard explains:
  *"This backup IS your website. Guard it like the Recovery Sheet."*
- **Updates**: host + Tor automatic (security). Container images update with
  a Dashboard approval card and one-click rollback — a bad website update
  must never brick a novice's site at 2 a.m. unattended.
- **Off**: **Site OFF** stops Container A; the address stops resolving as
  reachable almost immediately. Disk stays encrypted at rest.

## 9. Settled defaults (decided in this design, not left as options)

| Question | Default | Why |
|---|---|---|
| Base OS | Debian 12 | stability, small, Tor packaging quality |
| Installer | Calamares | the click-through standard for custom distros |
| Desktop | Xfce, heavily stripped | runs on any old desktop; 4 icons only |
| Encryption | LUKS2, mandatory | a stolen powered-off PC is the realistic threat |
| Passwords | generated Diceware phrases, 3 separate | §4 |
| Boot unlock | ask every boot; no auto-unlock offered (Cameron, 2026-10-10) | §3B |
| Site tier | static | smallest attack surface that still delights |
| Runtime | Docker + gVisor for website | §5 |
| Tor placement | own container, holds the key | §5 |
| Relay | off; bridge opt-in | §7 |
| SSH | off, not in UI | no inbound surface at all |
| Admin | local desktop only | §3D |
| IPv6 (containers) | blocked | classic leak vector |

## 10. What "best" still cannot do (stated so the product never over-promises)

- A sufficiently resourced adversary correlating timing/volume at both ends
  of Tor can de-anonymise; this design inherits Tor's threat model.
- gVisor reduces, does not eliminate, kernel/host risk. A future v2 could run
  the website in a microVM (Kata/Firecracker) under the same wizard; the
  compartment boundaries in §5 are drawn so that swap changes nothing else.
- The human is the softest part: the Recovery Sheet in a desk drawer is the
  design's answer; there is no better one for this user.

---
*Design v1 — vision & architecture only. No code or ISO exists yet.*

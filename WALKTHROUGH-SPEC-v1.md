# OnionHost OS — Walkthrough Spec v1 (screen-by-screen)

Frozen 2026-10-11 from DESIGN-v2.md + DESIGN-v3-amendments.md (incl. A17/A17.1
disclosure adoption and the A18 Gate R ruling, confirmed by Cameron 2026-10-11).
Where v2 and v3 conflict, v3 governs and the conflict is flagged in §6.
Status: blueprint freeze for the alpha installer/wizard build — final marketing
copy still passes the same fact-check as all wizard copy.

The user journey is THREE walks, not one: (A) the USB installer, (B) the
first-boot wizard, (C) normal life + Maintenance. Hard budget throughout:
the user holds exactly FOUR concepts (A11, as amended by A25) — disk phrase ·
generated login words · restart-needed card · Repair button. No screen may
invent a password, an account, an email, or a cloud login. The user never
types a secret they invented; every secret is generated and hand-copied.

---

## Walk A — Booting the USB / Calamares installer

### A1. Welcome / claim page
- **User sees:** the one permitted claim, verbatim in spirit: "OnionHost
  publishes your website as a Tor onion service, which hides your computer's
  network address from visitors and from the website software itself."
  Adults-only positioning ("No technical skills needed. For adults (18+).")
- **User does:** reads, continues. No input.
- **Machine does:** nothing network-facing yet.
- **Can go wrong:** user expects "untraceable" — this page is where that
  expectation is set correctly, before any commitment.

### A2. Disclosure / residual-risk page
- **User sees:** the A17.1-adopted disclosure paragraph (Review 2's §D text,
  TIMING-REVIEW-2-2026-10-11.md), covering: uptime is NOT hidden; outage
  correlation can narrow a region over time; ride-through/mirrors slow it but
  don't prevent it; Tor-network-scale adversaries are out of scope; closing
  line — "If being physically located would put you in danger, do not rely on
  hosting from your home." Plus the v2 §1 plain statements: ISP can see Tor
  use around the clock; encryption protects only when fully shut down; not
  for use where Tor is blocked or illegal.
- **User does:** acknowledges to continue.
- **Can go wrong:** skipping/shrinking this text — it is a release gate, not
  decoration. No numerical time-to-identification may appear anywhere (A17).

### A3. Language + keyboard layout, with test field
- **User does:** picks language and layout, types test characters in a test
  box (this layout is what the disk phrase must survive at every boot).
- **Machine does:** records the layout; the initramfs will carry the matching
  console keymap (KEYMAP=y) so the phrase verified here works at the boot
  prompt on AZERTY/QWERTZ/etc. (M4/N2).
- **Can go wrong:** layout mismatch = locked out at first reboot. The test
  field is mandatory, not optional polish.

### A4. Network check — WIRED ONLY
- **User sees:** "Plug this computer into your router with a cable."
- **CORRECTION to the 2026-10-11 chat summary:** there is NO Wi-Fi password
  step. The hardware spec disqualifies Wi-Fi for the server (wired Ethernet
  only, DESIGN-v3 hardware section). The installer must not offer Wi-Fi setup.
- **Machine does:** verifies link + internet reachability.
- **Can go wrong:** no cable/no internet → install may proceed to disk setup,
  but Go Live (Walk B) will block until wired networking works; the wizard is
  re-enterable and resumable, never a dead end.

### A5. Disk choice + erase warning (M10)
- **User sees:** detected existing OSes/data NAMED ("Windows 11 — about
  412 GB of files, including Photos and Documents, will be erased") and the
  standing guidance: "This computer will only run your website. Use a spare
  one."
- **User does:** selects the disk and TYPES a confirmation word — a click is
  not enough.
- **Machine does:** nothing destructive until the typed confirmation.

### A6. The disk phrase is generated (the one paper secret)
- **Machine does:** generates a 7-word Diceware-style phrase (EFF large list,
  ASCII-only, ~90 bits, NO digit — digits are a keymap/shift trap) in-process
  in the custom Calamares page; feeds it to cryptsetup on stdin, never argv;
  nothing in process lists, logs, or Calamares globalstorage (swept at build
  time). LUKS2 + argon2id mandatory (≥1 GiB memory cost, ~2 s unlock target).
  At this same moment the system derives the backup age X25519 recipient from
  the phrase (argon2id, per-install salt); only the public recipient is
  stored — this is why backups later need no phrase to create (A3).
- **User does:** hand-copies the phrase to paper. NO printer flow is offered
  for the phrase (spool files / printer logs, Q8). Then proves the copy by
  re-typing words at RANDOMISED positions (never a fixed pair — v1's
  predictable #2/#5 taught users to memorise two words).
- **Can go wrong:** phrase leaks into a log = build failure (leak sweep is an
  alpha test, ISO-BUILD-PLAN).

### A7. Summary + install + USB removal watch
- **User sees:** plain summary; install runs; final screen says "Remove the
  USB now" and WAITS until the stick is actually gone (udev) before
  finishing; disk-first boot order set where the platform allows.
- **Why:** a forgotten stick would boot the live system at the next power cut.

---

## Walk B — First boot wizard (state machine S0 → S1 → S2, A10)

### B0. First real unlock + confidence screen
- **User does:** types the disk phrase at the real initramfs boot prompt
  (console prompt, not Plymouth, until keyboard tests pass in alpha).
- **User sees, on success:** "You just typed your disk password at the real
  boot prompt — it works. Keep the paper safe." The scariest failure (locked
  out at first reboot) is converted into a verified success before setup
  begins. Production opens the volume with the keyring DISABLED (A18,
  Cameron-confirmed) — invisible to the user; it exists so Walk C's
  lost-paper recovery works.

### B1. S0 — kiosk wizard, FIRST step: login words
- **State:** LightDM autologins into a kiosk session running ONLY the wizard
  — no desktop exists yet. Below S2 the Dashboard shows only "Finish setup."
  The wizard is always re-enterable; it can never strand the user.
- **Machine does:** generates the 3-word login phrase (~39 bits,
  pam_faillock-protected: deny=5, unlock 900 s). Shown and verified like the
  disk phrase (hand-copy, randomised-position re-type).
- **Atomic transition S0→S1:** chpasswd → remove autologin drop-in → fsync →
  write state=1. Power loss before the final write simply repeats S0;
  nothing can be half-set. Power-pull tests at S0/S1/S2 are alpha gates.
- **User is NOT in sudo.** All privileged Dashboard actions go through
  polkit. There is NO website admin password anywhere in v1 (deleted in
  v3/A2 — editing is local; do not resurrect the v2 generated-at-Go-Live
  password or its reset flow).

### B2. Site type — Pages or Journal (the only v1 tiers)
- **Simple Pages (default):** form-built static site.
- **Journal:** static generator + owner-only local editor. No comments in v1,
  no database.
- Private Files is v1.1 (client-authorised) and must NOT appear as a v1
  choice; the tier screen MAY say truthfully that a private site is also the
  hardest to probe for uptime (A17.1).
- BYOC/WordPress: cut, never offered.

### B3. Starter content
- **User does:** site title, starter page/text, photos if wanted.
- **Machine does, silently:** the publisher is the ONLY writer of the content
  volume and scrubs every upload on ingest — EXIF/metadata across images
  (incl. PNG text chunks, HEIC/AVIF), media and documents; files renamed
  randomly; quotas enforced (A17.1/D8: EXIF capture time/GPS would defeat the
  timing hygiene from inside the content). Feed/file timestamps are
  content-derived or build-fixed; no local-time strings are emitted anywhere.
- **OPEN:** editor screen detail for Pages/Journal is the least-frozen part
  of this spec — fields and flow need one design pass before build.

### B4. Self-checks (honestly scoped, M9)
- **Machine does:** probe workload runs with B's exact unit/runtime policy:
  no network route exists for the web container, socket perms correct, onion
  key unreadable from B's view, live nftables table hash matches the golden
  hash, Tor reports the service published, no host port listening. Checks run
  at Go Live, every boot, on trigger events, and hourly.
- **User sees:** plain pass/fail per check — cards say exactly what they
  test ("Website sealed off: passed"), never "Location hidden."

### B5. Go Live → S2
- **User does:** presses Go Live. Any failing check REFUSES Go Live.
- **Machine does:** on success, S1→S2. The site is live.
- **User sees:** the .onion address + QR on a SEPARATE, non-secret page
  (nothing secret shares the page, so no single artefact links owner →
  address → keys). The page carries TWO QRs: the address, and the Tor
  download page — plus the line "Open with Tor Browser (Android) or Onion
  Browser (iPhone)" (a QR opened in a phone's stock browser "fails" and
  convinces users the site is broken).
- **Status, not browsing:** there is NO Tor Browser on the box (v3/A1
  replaced v2's locked-down browser). The Dashboard status card is fed by
  the client-only probe container U fetching the site through Tor and shows
  a fixed golden string — "Your site answered over Tor at HH:MM UTC" — with
  no HTML ever rendered on the box. The phone QR is the owner's real
  external test.

---

## Walk C — Normal life

### C1. Every boot
- Power on → type disk phrase → site comes back by itself; all services run
  with nobody logged in. Login words are only for the desktop/Dashboard.
  Sleep/suspend/hibernate are masked — the machine never sleeps.

### C2. Dashboard (native GTK, polkit helper, NO TCP listener)
Cards/actions only:
- Site status (probe-fed, B5) · backups · bridge/relay opt-in (default OFF;
  exit relay never) · restart-needed card ("Restart needed for a security
  fix — have your disk password ready"; amber 7 days, red 30) · Repair
  button (firewall/golden-config mismatch shows red: "Safety settings
  changed — click Repair"; de-hardening fails closed — A stops, nothing is
  exposed) · "Restart into Maintenance (site offline ~5 min)" ·
  **"Shut down now"** (the honest panic action: stops the site, powers off).
- Tor state — especially guard state — is preserved across gateway rebuilds;
  rotation never mints fresh guard state (A17).
- If the project goes unmaintained: stale-repo amber/red cards per §7 of
  DESIGN-v2 (site keeps Debian security fixes regardless).

### C3. Backups
- **Create:** NO phrase needed — anyone in a normal session can export a
  backup; it is age-encrypted to the install-derived recipient
  and useless to whoever holds the file alone. Copy line: "Don't keep the backup stick in the same drawer
  as the paper."
- **Restore:** only in Maintenance, phrase typed at a console; identity
  re-derived, backup opened.
- **OPEN (needs Cameron's/design call, raised in chat 2026-10-11 and still
  unresolved):** is backup-destination setup a required installer/wizard
  step, or a strong first-Dashboard prompt? Not decided in any design file.

### C4. Maintenance target (pre-login, after LUKS unlock; starts no site
### services and no networking; every use is logged to the Dashboard)
- **Lost paper, machine still running** (the A18 promise): make a NEW disk
  phrase — root helper adds a new keyslot from the live volume key
  (`luksAddKey --volume-key-file`; rig-verified, incl. the positional-arg
  pitfall in A18) and kills the old slot. User hand-copies the new phrase;
  old paper becomes waste.
- **Lost login words:** regenerate them here — a non-event by design.
- **Spare key:** REMOVED (A25, owner decision 2026-10-20). There is no
  spare: one disk phrase only, and its loss is total. The create/revoke
  design that stood here — and its revocation-honesty requirements — is
  superseded by A25 and retained in git history only.
- **"Change the lock completely"** (`cryptsetup reencrypt`, takes hours,
  site stays up): the only true revocation, and the documented response to
  any suspected compromise — under A18 a passphrase change alone does NOT
  cure a running-box root compromise.
- **Restore** from backup (C3) lives here too.

### C5. Optional ride-through guidance (D1, v1 opt-in — docs/Dashboard, not
### configuration screens)
- "Backup power" (UPS sized to the WHOLE chain: host + router + modem/ONT)
  and "backup connection" presented in those words only. Strongest
  single-host defence in both timing reviews because it removes outage
  events instead of hiding them.
- **OPEN:** exact placement — a wizard page, or docs + a Dashboard card?

---

## §6. Conflicts & open decisions this freeze surfaces

1. **Spare-key creation location — v2 vs v3 conflict.** DESIGN-v2 §3 makes
   the spare an optional INSTALLER wizard step; DESIGN-v3 A3 moves re-key
   and spare creation into Maintenance. This spec follows v3 (Maintenance),
   with Walk A/B saying only that a spare exists as an option — but A3's own
   spare-step copy ("this is your only insurance if you lose the main
   paper") predates Gate R and is now WRONG under A18 (running-machine
   re-key is the primary recovery; spare covers the powered-off case). Copy
   must be rewritten before build; placement needs one confirming call.
   **Superseded (2026-10-20):** the spare itself was removed by owner
   decision (A25) — no spare exists to place anywhere, and this conflict
   is moot.
2. **Backup-destination step** — required in wizard vs first-Dashboard
   prompt: unresolved (C3).
3. **D1 guidance placement** — wizard page vs docs/Dashboard card: open (C5).
4. **Desktop environment** — XFCE (default, hardware floor) vs GNOME still
   marked DECISION PENDING in ISO-BUILD-PLAN; does not change this spec.
5. **Editor detail** for Pages/Journal content screens: one design pass
   still needed (B3).
6. **Name/branding:** Cameron's alone; gates nothing in this spec.
7. **Chat-summary corrections baked in above:** no Wi-Fi step (wired only,
   A4); no website admin password (B1); no Tor Browser on the box (B5);
   login words are generated in the first-boot wizard's first step, not
   chosen by the user and not created in the installer (B1).

## Sources
- DESIGN-v2.md §§1–3, 5–8 (claims, install, credentials, tiers, dashboard,
  gate/self-checks, updates, USB watch)
- DESIGN-v3-amendments.md A1 (no browser on box, probe card), A2 (generated
  login, admin password deleted), A3 (Maintenance, backup derivation),
  A10/A16 autologin state machine, A11 concept budget (five; four since
  A25), A17+A17.1
  (disclosure text, EXIF scrubbing, guard-state preservation, D1 opt-in,
  D2 rejected), A18 (Gate R ruling, Cameron-confirmed 2026-10-11)
- TIMING-REVIEW-2-2026-10-11.md §D (adopted disclosure paragraph)
- ISO-BUILD-PLAN.md (Calamares module order, alpha test list, XFCE pending)

# OnionHost — Maintainer Runbook

Consolidated 2026-10-15 from Cameron's maintainer-responsibility questions,
checked against ISO-BUILD-LOG.md (Gate 4 section), DESIGN-v2 §7 / DESIGN-v3
A6/A14, and ~/workspace/onionhost-maintainer/README.md. This is the
maintainer's side of the contract: owners do almost nothing because these
duties sit here.

## Standing duties

### 1. Guard the signing key — it is the fleet's trust root
- Current key: software ed25519, fingerprint
  38AA06376F68206F072939DE82610F8D4BEF9565, uid "OnionHost Release Signing
  (software key - PRE-RELEASE) <release-signing@onionhost.invalid>",
  expires 2028-10-12.
- Held OUTSIDE the product tree in `~/workspace/onionhost-maintainer/gnupg/`
  (0700). Private material never enters the tree, the ISO, or any package —
  images carry only the 300 B public keyring.
- Lose the private key → the fleet can never be updated again (new key =
  new ISO + reinstalls). Stolen → an attacker can sign "updates" to every
  box. Backups of the maintainer folder, stored safely, are a real duty.

### 2. RELEASE GATE A14 — before any public ISO advertises updates
- Generate the release key on a hardware token (~$50 class device).
- Re-export the public keyring into the overlay
  (`onionhost/rootfs-overlay/usr/share/keyrings/onionhost-archive-keyring.gpg`),
  re-sign the repository, and destroy the software key.
- Do NOT let installs in the wild accumulate trust in the software key.

### 3. Re-sign the repository monthly, even when nothing changed
- Repo metadata Valid-Until = Release Date + 45 days (injected by
  `build/make-onionhost-repo.sh` before signing; InRelease clearsigned +
  Release.gpg detached).
- Monthly cadence leaves ~2 weeks of slack. Lapse consequences are by
  design: fleet Dashboards go amber at expiry, "project may be
  unmaintained" at +90 days (DESIGN-v2 §7).
- A frozen mirror freezes only the small `onionhost` package — Debian/Tor
  security updates flow to boxes independently.
- NOTE (2026-10-15): this cadence becomes load-bearing only once a public
  ISO advertising updates exists. No reminder schedule is running yet;
  start one at publish time, not before.

### 4. Keep the repository service alive — it needs a permanent home
- Repo onion: tpt6oez5hqsmeifbd3ltjb7d4nnfys4dqyyu2mukh2v53eh5nd7fbfyd.onion
  (identity in `~/workspace/onionhost-maintainer/repo-service/`; the
  address is a public constant baked into the golden apt sources template,
  the key is never public).
- During Gate 4 proof it was served from Muse's VM / test rigs. Before
  real users exist it needs a real home machine, powered and online.

### 5. Watch upstream; packaging/testing is Muse's, judgment is Cameron's
- Debian takes care of itself (security updates flow independently).
- Maintainer watch list: the four packaged apps (SMF, WordPress, DokuWiki,
  Gitea), gVisor (pinned, checksum-verified copy rides inside the platform
  package — it never phones Google), and the platform itself.

## Worked example: a WordPress security patch lands

1. Nothing reaches any box on its own — apps cannot self-update inside the
   sealed container, by design. The recipe channel is the only path.
2. Fetch the new release; verify against WordPress's official checksums
   (the current recipe's 3,782 files were verified this way at build).
3. Rebuild the recipe package with the new version stamped in.
4. **Floor decision (maintainer's call, every security release):** raise
   the recipe's anti-rollback floor to the new version. Effect: a box that
   fails its health check on the patched version takes the site DOWN
   rather than roll back to the vulnerable one, and heals when a corrected
   update lands.
5. Test before shipping — there is NO staged rollout. Boxes check in
   within ~a day on randomized schedules, so the pre-push test (sandbox
   suites + a real install/update run) is the only gate before the fleet.
6. Sign and publish: re-run the repo script (fresh 45-day clock), publish
   to the repo onion. Post-A14, signing is a physical act (token present).
7. Fleet side is automatic: fetch over Tor, verify signature + floor,
   back up, apply, restart, health-check through the real onion path;
   rollback or fail-closed per the floor.
- Patch latency to the fleet ≈ maintainer response time + up to a day of
  randomized check-in. Context for urgency: even a fully exploited
  unpatched app on this design cannot leak its owner's IP — the worst case
  is the website, not the person. Test properly; don't sit on it either.

## Explicit non-duties
- No box ever reboots itself for updates; kernel updates take effect at
  the owner's next restart — not a maintainer action.
- A major Debian jump (13 → 14) is not a background update; it ships as a
  guided project migration when the time comes.
- Owners who installed their own software in the app slot own its updates
  (A20: containment is a property of the wiring, not curation).

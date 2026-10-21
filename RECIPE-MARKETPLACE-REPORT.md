# Marketplace recipe for OnionHost OS — build report

**Date:** 2026-10-17
**Scope:** Package Cameron's Monero marketplace (frozen Stage 10 tree at
`~/workspace/monero-marketplace-v2/marketplace/`) as a signed A23 app
recipe for OnionHost OS, following the established recipe pattern.
**Status:** Built and sandbox-proven. **Nothing published** (publish
waits on the outstanding rig regression checklist). The GCP rig was not
used. The marketplace source tree was not modified.

Full build record: `ISO-BUILD-LOG.md`, section "MARKETPLACE RECIPE —
A23 RECIPE 5 (2026-10-17)". Working files: `poc/recipes-marketplace/`.

## Deliverables

- Recipe source: `onionhost/recipes/marketplace/` — builds
  `onionhost-recipe-marketplace_0.1.0+oh.1_amd64.deb` (3,282,356 B) and
  `+oh.2` (2,930,466 B) with the existing tooling and the Gate 4
  pre-release signing key (held outside the tree, as for the other
  recipes; no key material in the tree or in this report).
- Platform generalisations in the tree (each forced by this recipe,
  each documented in `onionhost/APP-SITES.md`):
  - `db.engine: "postgres"` — PostgreSQL runs inside the app slot.
  - `native_serve: {type: "tcp", port}` — TCP-loopback native apps.
  - `native/migrate.sh` — a recipe migration step at every start.
  - Per-install `app.env` rendering + parse-as-data in app-init.
  - Backup/restore PostgreSQL leg (live pg_dump → staged import).
  - App image gains postgresql, curl, libnettle8t64, libhogweed6t64.
- Proofs: unit **31/31**; sandbox acceptance drive, update, sabotage
  rollback, backup/restore — itemised below.

## How the marketplace runs in the slot

One gVisor sandbox, no network, as for every app. Inside it, under the
golden `app-init.sh`: PostgreSQL (datadir `appdata/pgdb`, superuser
password = the per-install credentials record's root password — never
peer auth), the marketplace binary (binds 127.0.0.1:8080), the
media-worker binary beside it, and nginx proxying the edge socket to
the app's TCP port via the new golden TCP template. The Tor gateway
reaches it exactly as it reaches every app; the container gains no
network.

Per-install state, never in the package: DB credentials (platform
record at `/etc/onionhost/app-db.env`), the rendered `native/app.env`
(site name from the wizard; profile **demo** and network **stagenet**
locked — the recipe does not bypass the marketplace's production-profile
acceptance sentence; `PAYMENTS_*`/retention at the owner-accepted
pre-mainnet defaults), the app-generated master key, media/blobs, and
the PostgreSQL datadir.

Owner wizard choices: marketplace display name, and the instance's
first **admin** account. The bare marketplace has no admin bootstrap
(registration creates a buyer — the GCP demo needed a manual DB
promotion); the recipe's first-boot closes the gap by registering the
staged admin through the app's own /register form, promoting it,
proving it via a login + /moderation read, and shredding the staged
credentials on both sides (volume copy by the first-boot step, host
copy by publish's await).

Migrations 0001–0009 ship as recipe files and are applied by the
recipe's `migrate.sh` at every container start (marker ledger, glob
order — the marketplace's own deploy contract, since the app never
migrates itself). A migrate failure keeps the app down so an update's
health check fails and rolls back.

## Defects found and fixed (platform + recipe)

1. **start_pg pwfile ownership** — initdb (as postgres) could not read
   the root-owned 0600 superuser pwfile. Fixed (chown to postgres);
   companion fix: the server log is postgres-owned from the start.
   Venue-independent; production would have hit it identically.
2. **start_pg postmaster restart race** — pg_ctl refuses to start
   while the previous postmaster is shutting down (or still running);
   the database was judged dead, and the first oh.2 update rolled back
   and failed closed on exactly this. Fixed: wait bounded for a live
   postmaster, adopt a still-running one, clear a stale lock.
3. **Recipe selection written too late (publish) / never (restore)** —
   generate-configs renders the TCP nginx variant from the selection;
   publish wrote it after provisioning rendered, and backups never
   captured it. Invisible for all four unix-serve recipes; the first
   TCP-serve recipe exposed it as 502s behind a healthy app. Fixed in
   publish (selection before provisioning) and restore (reinstated
   from the restored site model). APP-SITES.md records the rule.
4. **TCP nginx template** — first cut was malformed (no load_module /
   http block); rewritten as a faithful variant of the native
   template.
5. **Helper executables vs the normaliser** — the app-init's uniform
   0664 pass strips exec bits the manifest granted; only `native/app`
   is re-chmod'ed by the platform. The media-worker died on first use
   ("Media worker error"). Fixed in oh.2 via the recipe's
   normalize-exceptions pins (0755 ×3). APP-SITES.md records the rule
   for future recipes.

## A defect in the marketplace itself — reported, not fixed

`crates/app/src/web.rs`, `media_serve` (~line 1282): the stored-ref
validation applies a hex-digit check to the whole ref **including the
file extension** (`ref.chars().all(|c| c.is_ascii_hexdigit() ||
c == '.')`). The letters of `.png` / `.jpg` are not hex digits, so the
check can never pass and `GET /media/<ref>` returns 404 for every
legitimately stored image — on any platform, including the GCP demo
shape. Proven with a diagnostic build of a scratch copy (the frozen
tree was never touched): the handler extracts the correct ref and
computes `ok=false`. Image upload, sanitize (media-worker), storage,
the DB row, and the listing-page `<img>` link all work; only serving
is dead. No test in the tree requests `/media/...`, which is why no
gate caught it; this recipe's full-stack drive is the first exercise
of the route. The fix is one line and belongs to the marketplace's own
gate process (validate the stem, or exclude the extension). The
sibling check at `messages.rs:184` is correct (extensionless refs).

## Proof summary (sandbox venue, poc/recipes-marketplace/)

- **Clean provision from the .deb** in a single publish:
  `APP_PROVISION_OK db=created` → `RECIPE_APPLY_OK first_install=yes`
  → `FIRST_BOOT_OK` → `PUBLISH_OK` (rc=0). Nine migrations in the
  ledger; admin row `marketboss|admin`; host staged env shredded.
- **Acceptance drive over the gateway path:** front page carries the
  wizard's title; /limitations shows stagenet + demo; wizard admin
  logs in, /moderation 200. Full commerce smoke: seller registered →
  applied → admin-approved at /moderation/sellers → payment identity
  → pool batch accepted (4 subaddresses) → PGP key registered →
  listing published → buyer order created **with a pool subaddress
  assigned** → accept → mark-paid → fulfil → complete; order reads
  **Completed**. Media upload sanitized + stored by the media-worker
  (serving blocked only by the marketplace defect above).
- **Restart persistence:** migrate no-ops on the ledger, first-boot
  skipped, site answers.
- **Update oh.1 → oh.2** through the signed repo over Tor:
  `updated to 0.1.0+oh.2 and healthy`, high-water advanced, data and
  app.env preserved — and the same run first recovered the machine
  from the fail-closed state defect 2 had caused (`recovery healthy -
  site is back`).
- **Sabotage rollback:** oh.3 (scrambled ELF, re-sealed hash) failed
  its health check; the updater rolled back to oh.2 automatically;
  site healthy, Completed order intact.
- **Backup/restore:** live backup (8,601,600 B, encrypted) → wipe →
  restore (decrypt + manifest verified) → boot-time dump import →
  front 200, Completed order present, admin + /moderation working.
- **D8 controls:** native root and create-path dirs at mapped
  uid:owner gid 02775 setgid after apply, after update, and after
  rollback (in-machine sweeps); named-user ACL leg asserted by the
  unit harness (the venue's gofer has no ACL xattrs — same posture as
  the D8 slice).
- **Regressions:** SMF unit 32/32, Gitea unit 27/27 against the
  current tree; all touched tools pass syntax checks.

Venue-only notes (not product behaviour): the staged rootfs carries
`/var/lib/onionhost` at 0770, which the venue's shared filesystem
forces PostgreSQL (first genuinely unprivileged slot daemon) to
traverse — production bind-mounts the volume at /srv/appdata and never
traverses it; prep records the chmod. The runsc overlay hides
host-created files from a booted sandbox unreliably, and the venue
PID 1 does not reap zombies (pid-file checks can lie). Two early
publish captures were garbled in delivery; every verdict was
re-established from files and database state.

## Rig-deferred

Production-engine app-row behaviour for PostgreSQL + the marketplace,
restart persistence under the real engine, the owner ACL's desktop
effect, and a Part-3-style rig re-run — same posture as the earlier
recipe slices. Nothing is published; the marketplace recipe joins the
catalogue in the tree and ships when the outstanding regression
checklist passes on the rig.

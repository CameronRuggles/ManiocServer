# Dynamic (PHP/forum) tier — site-type choice draft (2026-10-12)

Status: DRAFT for Cameron's decision. Not adopted design, not a build brief.
Prepared after Cameron's 2026-10-12 proposal: "an interactive website is
vastly more useful — perhaps we could toggle something where we ask the
user if they want to do such a thing or not?"

Sources: DESIGN-v3-amendments.md A12 (dynamic tier deferred, with its
forward-compatibility reservations and trigger), A13 (forum-scale hardware
guidance), chat 2026-10-12 (SMF delta analysis and the site-type counter-
proposal Muse put to Cameron).

## 1. The trigger check — A12's deferral condition is now met on paper

A12 said: design the tier when "the static core passes the PoC gates (A9)
and installs end-to-end as an alpha ISO."

- PoC gates passed; prod-flavour ISO built, delivered to Drive and
  verified bit-identical (2026-10-12).
- Simple Pages and Journal editors (slice 4) completed and passed their
  full test battery 2026-10-12; demo Journal live over Tor.
- Still outstanding before any dynamic-tier *build*: the slice 5A fix
  build (forced encryption + admin fixes) and slice 5B backup/restore —
  backup/restore matters doubly here, because A12.4 already requires the
  backup manifest to handle DB dumps, and a forum is the first tier that
  actually has a database to lose.

So: the tier can be *designed* now without breaking A12's discipline.
Building it still queues behind backup/restore and Stage 2.

## 2. The decision Cameron is actually being asked to make

Not "toggle: yes/no." The proposal on the table (Muse's, in chat
2026-10-12, awaiting Cameron's call) is:

**Interactive is a site type, chosen the same way Pages and Journal are
chosen — not a setting inside a static site.**

Draft choice-screen copy (for Cameron to edit, not final):

> **Journal / Pages** — publishes your writing. Nothing to hack, nothing
> to steal: even if someone broke in, there is no member information on
> this computer.
>
> **Forum** — hosts conversations and members. It keeps your members'
> messages, email addresses and password hashes on this computer, has a
> login page strangers can attack, sends no email (registration works
> without it), and needs regular care. It can be added later — you do
> not have to decide today.

Rules that come with that framing:
- Static stays the default; choosing Forum is a deliberate act with the
  costs stated at the moment of choosing.
- Forum can be added later to a running box as its own site — no
  reinstall, no install-time prediction of the owner's future.
- One blessed app first: SMF (Simple Machines Forum), packaged and
  updated through the normal signed-image pipeline. "Upload any PHP"
  stays cut — a curated app is the only version supportable for a
  non-technical owner.
- Forum admin paths live on a second, separate onion address gated by
  Tor client authorization (A12.5 precedent), never on the public
  address. Member logins stay public, rate-limited at the gateway.
- The core promise is unchanged and must be stated as unchanged: the
  site container still has no network, so even a fully compromised
  forum cannot learn or leak the server's IP. What changes is the
  *data* at risk (member DB), not the network-address protection.

## 3. The one spike that must pass before SMF is promised

MariaDB under gVisor is the genuine unknown identified 2026-10-12 —
databases stress exactly the syscall paths runsc taxes hardest, and
io_uring may need disabling. Spike plan (rig, no user hardware needed):

1. MariaDB in a runsc container, socket-only, no network namespace —
   same wiring pattern as the existing stack.
2. Create an SMF-schema-sized database; run insert/select/update load
   approximating A13's forum case (~15–20 dynamic req/s peak).
3. Test with io_uring on and off; record which is required and the
   performance delta.
4. Kill -9 the DB mid-write; verify clean recovery (this is also the
   backup-consistency rehearsal).
5. Measure sustained PHP-FPM + MariaDB throughput end-to-end through
   the Tor gateway, against A13's hardware floor.
Pass/fail: if MariaDB under runsc cannot sustain the A13 floor case
with clean crash recovery, the forum tier waits or the DB placement
gets its own design pass — SMF is not promised on hope.

## 4. What a forum tier also forces, honestly listed

- Persistent writable, quota'd app-data volume (A12.3 reservation
  already names this class) — the read-only symlink-swap publishing
  model does not apply to the forum's live data.
- Backups become DB-dump + attachments taken consistently together
  (A12.4 manifest extensibility — already required of slice 5B).
- Upload pipeline: attachments are stranger-supplied files — scrub /
  re-encode, serve as inert downloads, upload dir never executable.
- No email: registration and password resets must work without email
  verification. This is a product consequence to state in the choice
  copy, not a bug to fix later.
- Wall-clock/timing discipline from the static tier mostly does not
  carry over; sessions are stateful by nature.
- A new secret enters the owner's life (SMF admin password) — the
  five-concept budget bends for this tier, which is part of why it is
  a separate site type and not the default.

## 5. Open calls for Cameron (only these need him)

1. Adopt the site-type framing above, or insist on a literal toggle?
2. SMF as the one blessed first app — yes/no?
3. Sequence confirmation: design pass (plus its own external delta
   review, per A12) after backup/restore lands, build after Stage 2 —
   or pull the MariaDB/gVisor spike forward to run in parallel with
   slice 5B on the rig?

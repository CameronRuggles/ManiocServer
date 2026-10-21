# OnionHost OS — Timing / Availability Analysis: Problem Brief + Mitigation Review Request
## For: Claude Opus 5.5 · From: the OnionHost design team · 2026-10-11
## Status: this is a FOCUSED follow-up to the v2 design review and the v2 delta review (both completed). Do not relitigate those. This pack covers ONE issue family only.

---

# Part 0 — Your brief

In your first review you killed our original tagline ("a private website
that nobody can locate") on the strength of timing/availability
correlation (finding M1). We accepted that and narrowed the claim. The
project owner has now independently arrived at the same attack from
first principles, proposed a mitigation of his own, and asked the
question this pack exists to answer:

**Beyond the owner's proposal, what else — if anything — can actually
mitigate availability/timing correlation for a home-hosted onion
service, at what cost, and what residual risk honestly remains?**

We want: (1) a precise, channel-by-channel statement of the problem (so
the document doubles as our own disclosure text), (2) a steelman then a
red-team of the owner's proposal (Part 2), (3) your own mitigation
candidates, including ones we haven't thought of, each graded, and
(4) a hard statement of what cannot be fixed at any reasonable cost.

Context you need is in Part 1. The design constraints that any
mitigation must fit are in Part 4 — a mitigation that breaks them is a
finding, not a proposal.

---

# Part 1 — The system, in one page (recap, skip if fresh in mind)

OnionHost OS is a Debian 13 ISO that turns a spare home desktop into a
Tor onion-service host for non-technical owners. Settled architecture
(post two reviews, PoC under way and passing):

- LUKS2 full-disk encryption, passphrase typed at every boot; powered
  off = sealed. One human secret (generated 7-word disk phrase).
- The onion private key lives ONLY in a hardened Tor gateway container
  (gVisor/runsc). The website runs in a separate container with NO
  network at all — Tor reaches it over a unix socket. A fully
  compromised website cannot learn the host IP, reach the LAN, or steal
  the identity. The identity survives website rebuilds.
- Host firewall: default-drop, no inbound ports, only the Tor container
  has egress. No browser on the box. Native dashboard, no web UI.
- v1 content tiers are STATIC ONLY (simple pages, a static journal).
  Dynamic (PHP/database) hosting is a declared future goal, currently
  undesigned. v1 ships as a single machine in a single home.
- User-facing concept budget is FIVE concepts, hard. Our only permitted
  marketing claim is the narrow one: the product "hides your computer's
  network address from visitors and from the website software itself."
  Availability correlation is disclosed to the owner in the setup
  wizard as a residual risk — currently with no mitigation offered.

Two PoC facts that bound this discussion: a Tor container restart takes
~37 s to become reachable again (inside our accepted 30–120 s window),
and HTTP response headers already carry no wall-clock information
(`Date` stripped; ETag/Last-Modified are content-derived).

---

# Part 2 — The problem, as we currently understand it (correct us)

Tor hides WHERE the server is at the network layer. It does not hide
WHEN the server is. We believe the correlation channels are:

- **C1 — Public outage-data matching (the owner's scenario).** The site
  is one machine in one home. Its downtime pattern is that home's
  downtime pattern. Power utilities and ISPs publish (or leak, or sell)
  outage data with region + provider + timestamps. An attacker who
  records the site's uptime over weeks-to-months can intersect: site
  dark exactly during {storm outage in region X on ISP Y}, repeatedly.
  Each intersection shrinks the candidate set. The data to do this is
  cheap and the observation is free and passive.
- **C2 — Suspect-line observation.** A stronger, targeted adversary
  (ISP-level cooperation, or access to flow records) doesn't need the
  site to go down at all: they watch a *specific suspect home's* Tor
  traffic fall silent and resume, and match that rhythm to the site's.
  This presumes a suspect already exists; it confirms rather than
  discovers. We believe no hosting-side measure fully addresses C2
  short of the home's Tor traffic never reflecting the site (e.g. the
  home also runs unrelated 24/7 Tor traffic — which changes little, as
  the aggregate still stops at a power cut).
- **C3 — Induced events.** An active attacker can *cause* observable
  events: flood the site and watch a candidate's uplink saturate;
  cut or wait for cuts. Also: the owner's own behaviour (site goes
  down every night at 01:00 local = reboot habit, timezone leak via
  maintenance windows). We mitigate the update-timing version already
  (updates randomised in UTC).
- **C4 — Blurring that already exists (quantify it, please).** v3
  descriptors are cached by clients and directories; a host that dies
  keeps "existing" for some visitors for minutes; introduction points
  persist independently. Our belief: outages of seconds are invisible,
  minutes are smeared, and the harvestable signal is sustained outages
  (tens of minutes and up) repeated over time. Tell us if that
  quantification is wrong.

A note on mechanism, because it shapes Part 3: an onion ADDRESS is the
service's public key. A visitor verifies the signed descriptor against
the address itself; there is no "resolution" a third party can win.
Whoever holds the private key IS the site. Two holders publishing at
once produce two valid descriptors and the directories keep the
freshest per replica — visitors split between them.

---

# Part 3 — The owner's proposal (steelman it, then attack it)

**Proposal P1 — Multi-host same-key mirroring.** The owner installs the
system on SEVERAL machines in different locations (different homes,
ideally different towns), all holding the SAME onion private key and
the SAME static content, synced. If one home's power/ISP fails, that
host stops publishing; the others' descriptors take over; the site —
from any visitor's perspective — effectively never goes down. The
outage-correlation signal (C1) collapses from "this home's downtime" to
"the rare moments ALL locations are down together," which points
nowhere in particular.

Our own initial analysis, for you to check and extend:

- P1 works mechanically for STATIC content, with minutes-scale (not
  instant) failover due to descriptor caching, and with descriptor
  racing while multiple hosts publish. Identical content makes the
  racing harmless to visitors.
- P1 does nothing for C2 (each home's own Tor traffic still stops at
  its own power cut, visible to anyone watching that line) and little
  for C3.
- Costs we see: the private key now exists in N locations (N physical
  theft/seizure targets, possibly in other people's houses, each
  needing a human at boot for the LUKS phrase); content sync must
  travel over Tor and be timing-randomised, or simultaneous visible
  updates become a NEW correlation signal (P1 leaking through its own
  update channel); +1 or more user concepts (pairing, sync) against a
  hard budget of five.
- The "proper" form of P1 is OnionBalance: backends hold DISTINCT
  keys, a single frontend descriptor aggregates all their introduction
  points, no descriptor racing. We judged it operator-grade and
  novice-incompatible. Grade that judgement too — is a simplified,
  two-node, static-only OnionBalance actually buildable inside our
  constraints, or is raw same-key mirroring the pragmatic version?

**Questions on P1:**
- Q1. Descriptor racing with 2–3 same-key hosts: in practice, how bad
  is visitor-visible flakiness (failed rendezvous, stale intro points)?
  Does Tor's descriptor replication actually smooth this, or is P1
  flakier than our analysis admits?
- Q2. Failover honesty: when one of N hosts dies, what does the
  visitor-experienced availability curve actually look like over the
  following hour? Is "effectively never goes down" defensible language
  for owner-facing copy, and if not, what is?
- Q3. Does P1 meaningfully raise the cost of C1 for a *patient* attacker
  (months of observation)? Consider: partial correlations (site's
  responsiveness degrades when its busiest host dies), update events,
  and the intersection attack run in reverse (watch for when the site
  is served "differently").

---

# Part 4 — Design constraints any mitigation must fit

1. **Novice ceiling.** The owner is a non-technical user; the whole
   product has a hard budget of five user-facing concepts. A mitigation
   requiring the owner to understand it is a mitigation that won't be
   used. Prefer mitigations that are invisible, or expressible in one
   plain sentence.
2. **Single-home default.** v1 ships one machine, one home. A
   mitigation may be (a) built into the single-host default, (b) an
   opt-in mode, or (c) future work — say which, and don't silently
   assume multi-home for a v1 recommendation.
3. **Key custody is sacred.** Any scheme that copies the identity key
   must say so and price it. Schemes that avoid copying it score
   higher.
4. **Static now, dynamic later.** Grade mitigations for static content;
   note separately whether they survive the future PHP/database tier
   (single-writer problem).
5. **No lies in copy.** Owner-facing language must be literally true.
   If a mitigation reduces a channel from "identifying" to "expensive
   and noisy," the copy must say that, not "fixed."
6. **Cost realism.** This is a free, open-source product for home users.
   Mitigations costing real money (extra hardware, a second internet
   connection, a UPS) may be recommended to owners as options, but the
   product cannot require them.

---

# Part 5 — What we want from you

**A. Corrections to Part 2.** Anything wrong, overstated, or missing in
our channel list — especially the C4 quantification, and any channel we
haven't named (for example: does the site's *guard connection* behaviour
during partial outages leak more than the binary up/down signal?).

**B. P1 verdicts.** Steelman P1, red-team it, answer Q1–Q3, and give a
placement: v1 opt-in / future feature / reject. Include the OnionBalance
comparison (Q-grade) — if you recommend a form, specify the minimum
viable version that fits Part 4.

**C. Other mitigations — the main event.** Generate candidates we have
not proposed. Seed list to grade (do not limit yourself to it):

- S1. **Ride-through instead of distribution**: a UPS plus an automatic
  failover to a dissimilar backup connection (e.g. cellular) keeps ONE
  host up through power/ISP outages. Does this defeat C1 as effectively
  as P1 for the common outage durations, at lower complexity? Where
  does it break (long outages, tower also down, failover visible how)?
- S2. **Noise**: deliberate, randomly scheduled brief downtimes
  (minutes, randomised in UTC) so the site's uptime record contains
  many owner-generated events that match NO real-world outage, diluting
  C1's intersections. How much noise is enough to matter, what does it
  cost in real availability, and can a patient attacker filter it (e.g.
  noise is down-only, while real outages also show in… what)?
- S3. **Decoy significance**: the host deliberately does NOT come back
  immediately when power returns, but at a randomised delay (minutes to
  an hour), smearing the "restored" timestamp the way the "down"
  timestamp is already smeared by descriptor caching. Does symmetric
  smearing materially raise C1's cost?
- S4. **Always-on cover**: the box maintains its Tor presence and
  traffic shape 24/7 regardless of whether the site is being served
  (e.g. during owner-chosen site-off periods), aimed at C2. Grade
  honestly — we suspect this is weak.
- S5. Anything in Tor itself we've under-used: descriptor/introduction
  configuration, multiple services per tor instance, guard behaviour,
  or protocol features that change the availability signal.
- S6. Anything at the CONTENT layer: e.g. mirrors under SEPARATE onion
  addresses cross-linked from the site (accepting linkability to gain
  independent uptime per address?) — or does that just move the signal?

For EVERY candidate (yours included): channel(s) addressed (C1/C2/C3),
mechanism, expected effect size in plain terms, what it costs (money,
complexity, concepts, availability), what new signal it creates, and a
placement (v1 default / v1 opt-in / future / reject).

**D. The residual-risk paragraph.** Write the honest paragraph we
should show owners after all worthwhile mitigations are in: what a
patient, well-resourced observer can still learn, and how long it
takes them. One paragraph, plain language, literally true. We will
ship your paragraph nearly verbatim if it survives our fact-check.

**E. Ranking.** A single table: mitigation × channels × effect × cost ×
placement — ending with the ONE combination you would actually ship for
v1 if it were your product, and the one you would explicitly refuse to
ship even if asked.

Response format: mirror the sections (A–E). Verdicts before reasoning
in B. No mitigation gets described without its new-signal cost named.

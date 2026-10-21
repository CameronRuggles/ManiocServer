# Defensive Threat-Model Review — Availability Correlation in a Home-Hosted Onion Service
## A security-engineering review request · OnionHost OS design team · 2026-10-11
## This is a follow-up to two completed design reviews of the same project. Scope: one threat-model question only.

---

# 0. What this document is (please read first)

OnionHost OS is an open-source, Debian-based system that lets a
non-technical home user host a small personal website as a Tor onion
service from a spare computer, with the website software strongly
sandboxed. It belongs to the same legitimate privacy-tool family as
OnionShare and the Tor Project's own onion-service documentation, both
of which discuss traffic-correlation research openly: our goal is
standard defensive security engineering — understand the known
limitations of the design, reduce metadata exposure where practical,
and **disclose the residual limitations accurately to users** instead of
overclaiming. An earlier review of this project already established
that availability correlation is real, and our product copy was
narrowed accordingly. This review asks how far defensive design can
responsibly go, and asks for precise language for the user disclosure.

Nothing in this document involves accessing any system, any third
party, or any live service. It is protocol- and architecture-level
analysis of our own design, of the kind published in the Tor research
literature for two decades.

---

# 1. The system in brief

- Debian 13, full-disk encryption (passphrase at boot). A Tor gateway
  container (sandboxed with gVisor) holds the service's private key.
  The website container has no network access at all; the gateway
  reaches it over a local unix socket, so compromised website software
  cannot learn the host's network address or reach the local network.
- No inbound ports; only the gateway container has outbound access.
- Version 1 hosts STATIC content only (simple pages, a static
  journal), on a single machine in a single home. Dynamic hosting is a
  future, currently undesigned, goal.
- The product makes one narrow claim — it hides the computer's network
  address from visitors and from the website software itself — and the
  setup flow discloses availability correlation (below) as a known
  residual limitation. This review exists to make that disclosure
  precise and to check whether any reasonable defensive measure is
  being missed.
- Established measurements: a gateway restart returns to reachable in
  ~37 s; HTTP responses carry no wall-clock metadata (no `Date` header;
  cache validators are content-derived).

Protocol facts needed below: a v3 onion address is the service's
public key, encoded. Visitors verify the service's signed descriptor
against that key; there is no third-party registry. Whoever holds the
private key can operate the service. If two machines hold the same key
and both publish descriptors, directory relays keep the freshest per
replica and visitors may reach either machine.

---

# 2. The threat model under review (correct or extend)

The network layer hides the server's address. It does not hide the
server's *schedule*. We model three observers:

- **O1 — Public-data correlation.** Utilities and ISPs publish outage
  information (region, provider, start/end). A passive observer who
  logs our example service's uptime over weeks can intersect those
  windows: the service was unreachable exactly during a set of outages
  that only overlap in one region on one provider. Over time this can
  narrow where a pseudonymous home server plausibly sits — a
  doxxing-style risk for ordinary users, and the scenario our project
  owner raised. Observation is passive and the datasets are public.
- **O2 — Single-connection observation.** An observer already able to
  see one specific household's network traffic (e.g. at that
  household's provider) can compare that connection's quiet/active
  rhythm with the service's uptime. This confirms a suspicion rather
  than discovering a location. We believe hosting-side measures
  address O2 weakly at best; tell us if we're wrong.
- **O3 — Active probing.** An observer can generate load against the
  service and look for corresponding effects, or exploit predictable
  behaviour (e.g. maintenance at a fixed local time leaking a
  timezone). Predictable-schedule leaks are already designed out
  (maintenance is randomised in UTC).

**Built-in blurring (quantify, please):** onion-service descriptors
are cached by clients and directories, so very short outages may never
register as downtime for visitors, and brief events are temporally
smeared. Our working estimate: seconds are invisible, minutes are
smeared, and the usable signal for O1 is sustained outages repeated
over time. Confirm or correct.

---

# 3. Proposal P1 — redundant home hosts (evaluate)

**P1:** the owner runs the system on two or three machines in
*different* homes (different power grids and different ISPs), all
holding the same service key and serving identical static content,
kept in sync over Tor. When one home has an outage, that machine stops
publishing descriptors; the others continue, so the service stays
available and its public uptime record no longer matches any single
home's outage record.

Our preliminary assessment for you to check: mechanically workable
for static content; failover is minutes-scale (descriptor caching),
not instant; while several machines publish, visitors split between
them (harmless for identical content); key custody spreads to N
locations (N physical-security targets, each needing a person at boot
for the disk passphrase); synchronisation must be timing-randomised or
simultaneous updates become a correlation signal of their own. The
established alternative, OnionBalance (distinct backend keys under one
aggregated descriptor), avoids descriptor racing but looks too
complex for non-technical owners.

**Questions:**
- Q1. With 2–3 same-key publishers, how much visitor-visible
  unreliability (stale introduction points, failed first attempts)
  should we honestly expect?
- Q2. When one host of N fails, what does visitor-experienced
  availability look like over the following hour? Is "the site stays
  up when one home has an outage" defensible user-facing language?
- Q3. How much does P1 actually raise a patient O1 observer's cost,
  accounting for partial signals (performance changes when a host
  drops, update events, reverse intersections)?
- Q4. Is a simplified, static-only, two-node OnionBalance realistic
  within our constraints (Section 4), or is plain same-key mirroring
  the pragmatic form?

---

# 4. Constraints for any recommendation

1. **Non-technical owners.** The product's entire user-facing model is
   five simple concepts. A defence the owner must understand to
   operate will not be operated.
2. **Single home is the default.** Classify each defence as: default
   for the single-host product / opt-in / future work.
3. **Key custody matters.** Defences that avoid copying the private
   key score higher; any that copy it must price that.
4. **Static now.** Grade for static content; note whether the defence
   survives a future database-backed tier (single-writer problem).
5. **Honest copy only.** If a defence changes "identifying" to
   "slower and noisier," the wording must say exactly that.
6. **Home-user economics.** Extra hardware/connections may be offered
   as options, never required.

---

# 5. What we are asking for

**A. Threat-model corrections.** Anything in Section 2 that is wrong,
overstated, or missing — including the blurring estimate, and any
availability/timing exposure we have not named.

**B. P1 evaluation.** Steelman, then critique, then placement
(v1 opt-in / future / reject), answering Q1–Q4. If you recommend a
form of it, specify the minimum viable version within Section 4.

**C. Other defences.** Propose and grade candidates beyond P1. Seed
list (extend freely):
- D1. **Ride-through**: battery backup (UPS) plus automatic failover
  to a dissimilar second connection (e.g. cellular) keeps one host
  available through typical power/ISP outages. Comparable to P1 for
  O1 at typical outage durations? Failure modes?
- D2. **Decoy downtime**: brief, randomly scheduled unavailability
  (randomised in UTC) adds owner-generated events that match no real
  outage, diluting O1's intersections. How much noise helps measurably,
  what does it cost in real availability, and can a patient observer
  filter it?
- D3. **Restore-delay smearing**: after an outage, the host waits a
  randomised interval before resuming service, smearing the "back up"
  edge as descriptor caching smears the "went down" edge. Material?
- D4. **Constant presence**: the host keeps a steady network presence
  whether or not the site is being served, aimed at O2. We suspect
  weak; grade it.
- D5. **Protocol-level options** in Tor's onion-service configuration
  we may be under-using.
- D6. **Content-layer options** (e.g. independent mirror addresses),
  including whether they merely relocate the signal.

For each candidate: observer(s) addressed (O1/O2/O3), mechanism,
effect in plain terms, costs (money, complexity, user concepts,
availability), any NEW exposure it introduces, and placement
(default / opt-in / future / reject).

**D. The disclosure paragraph.** Write the one-paragraph plain-language
summary we should show owners after all worthwhile defences are
applied: what a patient observer with public data could still infer,
and roughly how long it would take. We intend to ship it nearly
verbatim after fact-checking.

**E. Ranking.** One table (defence × observers × effect × cost ×
placement), ending with: the combination you would ship for v1 in our
position, and one candidate you would refuse to ship even if asked.

Format: mirror sections A–E; verdict before reasoning in B; every
defence named with the new exposure it creates, or an explicit "none
identified."

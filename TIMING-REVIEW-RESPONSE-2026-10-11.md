# Timing / Availability Analysis — External Review Response
## Received from Cameron 2026-10-11 (pasted in chat; reviewing TIMING-ANALYSIS-PACK v2)
## Provenance: Cameron routed the pack to another frontier model after Claude's safeguards downgraded the session to Opus 4.8 ([cyber] flag on both pack versions). Model identity as pasted is not independently verified here.
## NOTE: the pasted text arrived partially mangled in Section A (a sampling-formula passage is truncated mid-sentence and splices into a P1 sentence). The substance below is unaffected; do not quote that passage.

---

## A. Threat-model corrections

The residual risk is real, but two premises need correction: descriptor caching does not hide a physical outage, and independent same-key publishers do not provide reliable minutes-scale failover. Also, there is no defensible universal estimate for how many weeks location inference takes.

### 1. Separate three observable states

1. **Descriptor availability**: Tor directories still have contact information for the service.
2. **Tor-service reachability**: a client can complete a connection to the service.
3. **Website availability**: the connection returns the expected content.

These states can diverge. A descriptor can remain available after its host has lost power; Tor can remain reachable while the website process is unavailable. Tor directories cache contact information, not website responses. Consequently, cached descriptors cannot keep an unavailable machine serving visitors. Tor's protocol explicitly requires services to keep advertised introduction circuits alive while their descriptors remain valid — something a powered-off host cannot do.

### 2. Correct the "built-in blurring" estimate

Replace "Seconds are invisible, minutes are smeared" with: "Short interruptions may be missed or obscured by sampling, connection timeouts, retries, and ordinary Tor variability. Descriptor caching can prolong stale contact information, but does not guarantee that an interruption is invisible."

- A visitor already transferring data can notice a seconds-long interruption.
- A new connection attempted during an interruption can fail, even with a valid cached descriptor.
- A brief network interruption that preserves existing connections can be experienced differently from a gateway restart that destroys circuits.
- Cached browser content can conceal an interruption from an ordinary reader, but is not a property of onion-service availability.

[A sampling-probability illustration followed in the original; the pasted copy is truncated at this point.]

For tested OnionBalance, defensible copy would be: "A working copy can remain reachable when one host fails, although some connections may fail or need a retry during the transition."

### Q3: How much does P1 increase O1's cost?

Potentially materially, but not by a defensible universal factor — and less than ideal redundancy suggests. For an observer restricted to a single binary "some copy answered" record, healthy redundancy removes many individual-home outage events; that changes the inference problem substantially.

Residual information includes: failures associated with the currently dominant publisher; disappearance of a distinguishable serving instance; performance/capacity changes; content-version transitions; common failures from coordinated updates or shared infrastructure; uptime during candidate outages that constrains possible replica arrangements.

Randomizing synchronization helps avoid lockstep transitions, but is not sufficient or always necessary: byte-identical replicas under one address do not expose a separate public "synchronization event"; random publication delays can themselves create distinguishable old/new versions; publication of new content still reveals an event on the main site. Use independent synchronization scheduling, atomic local installation, bounded version skew, and no instance identifiers. Do not claim that random timing makes updates uncorrelatable.

Net assessment: properly engineered redundancy makes O1 slower and noisier by suppressing events. Same-key descriptor competition can reintroduce enough partial downtime that the improvement is uncertain.

### Q4: Is simplified OnionBalance realistic?

Yes as product engineering; no as an owner-operated recipe. Debian 13 packages OnionBalance; Tor documents its distinct-backend-key architecture.

Minimum viable supported design: two independently powered/networked static backends; distinct backend onion keys; automatic pairing and authenticated snapshot synchronization over Tor; identical serving configuration, no node identifiers; isolated publisher processes and authenticated local Tor control sockets; automatic health/recovery handling, local-only diagnostic records; independent maintenance and tested cached-client behaviour.

Publisher placement is the crucial constraint:
- **One publisher, master key in one home**: avoids distributing the master key, but that home remains a publication failure domain. Existing descriptors provide a grace period, not indefinite independence.
- **Publishers in both homes**: publisher redundancy, but the master key lives in both homes. Isolation reduces software exposure, not the number of physical key-custody locations.
- **Separate reliable publisher**: preserves separation from backends, adds a machine/operator or provider relationship, and does not by itself make publication redundant.

OnionBalance health detection is not instantaneous: source defaults include backend-descriptor fetching every ten minutes and publication checks every five minutes; neither timer is a guaranteed dead-backend-removal bound. Cached backend descriptors are not proof of backend health. The current Tor-hosted OnionBalance manual also lists **C Tor only** and **no compatibility with onion-service PoW defence** as limitations — recheck the exact release integrated rather than assuming both features combine.

**New exposure — same-key P1**: additional master-key custody locations, hosts/guards, synchronization relationships, potentially distinguishable instances. A stolen master key cannot be revoked while retaining the address.
**New exposure — OnionBalance**: publisher/control-plane attack surface, backend membership relationships, distinguishable backend availability, possibly duplicated master-key custody for publisher redundancy.
**Dynamic future**: neither form solves single-writer availability. Replicas can serve static snapshots or stale reads; write availability requires a separate database/consistency design.

---

## C. Other defences

**D1. Ride-through (UPS + dissimilar access failover)** — O1 primarily; limited O2 availability benefit; little O3. Preventing outages from becoming service outages removes observations rather than adding noise: one of the strongest practical single-host options. Comparable to redundancy for outages within its tested coverage, but not for host failure, owner shutdown, or prolonged regional disruption. Failure modes: UPS not powering router/modem/ONT/cellular gear; cellular congestion, tower power failure, shared backhaul, regional shutdown; failover breaks Tor connections/circuits; battery exhaustion → shutdown + passphrase-dependent recovery; flapping between connections. Size runtime from usable battery energy ÷ total backed-up load (illustration: 60 Wh at 30 W ≈ 2 h — not a generic claim). Costs: hardware, battery replacement, optional cellular subscription; present as "backup power"/"backup connection". New exposure: another provider/subscriber relationship, cellular location records, failover traffic transitions. **Placement: v1 opt-in (UPS and automatic connection failover offered independently). Dynamic: survives.**

**D2. Decoy downtime** — O1 weakly; not dependable for O3. Adds unrelated unavailability; contaminates a naive event list but does not remove true matches. No established protective noise budget; a patient observer can model downtime as a mixture. Brief decoys are poor cover for long outages. Arithmetic: 5 min/day ≈ 0.35% availability ≈ 2.5 h per 30 days; 30 min/day ≈ 2.1% ≈ 15 h per 30 days — imposed costs, not measured privacy benefits. Website-only decoys are distinguishable from power loss (Tor may continue); stopping Tor adds circuit disruption signatures. **Placement: reject for v1; research-only. (Also the reviewer's refused-to-ship pick, Section E.)**

**D3. Restore-delay smearing** — O1's restoration edge only; does not conceal onset. Uniform 0–W delay adds W/2 expected downtime (0–30 min → +15 min avg per recovery); repeated observations can still estimate the relationship. Only valuable if restoration timing is unusually informative; the boot passphrase already adds uncontrolled human delay. New exposure: characteristic recovery-delay distribution; Tor-before-HTTP intermediate state. **Placement: future measurement work, not default.**

**D4. Constant presence** — O2, coarse records. Keep Tor operating while the website restarts/isn't serving: separates application availability from network silence. A connected Tor process is not constant-rate traffic; stock connection padding reduces flow-record precision, does not conceal all volume variation, and cannot survive power/connectivity loss. **Placement: default architectural separation + stock padding; custom constant-rate cover traffic = future research, not a v1 promise.**

**D5. Tor protocol/configuration** — O3 primarily. Defaults: maintained v3 Tor; **preserve Tor state (esp. guard state) across gateway restarts** rather than fresh state each time; normal padding behaviour; validate intro-DoS and PoW in the shipped build; tested stream/resource limits; never enable non-anonymous/single-hop modes. More introduction points ≠ more hosts. Costs: compatibility testing; possible false rejection of bursts. New exposure: observable limit/PoW behaviour; extra intro points = extra relay relationships. **Placement: default tested protections.**

**D6. Independent mirror addresses / external static replicas** — each host keeps its own key: good custody/availability, but the original home address still exposes its original schedule; publishing the association links the services explicitly. A complete independent static copy can serve while home is offline, provided no cache-miss dependence on home; updates still carry timing; a clearnet host adds a different trust relationship. Use a dedicated content-signing credential, not the onion identity key. **Placement: v1 opt-in automatic static export/mirror if affordable; external canonical hosting future. Dynamic: snapshots/read-only only.**

**D7. Lifecycle/schedule hygiene** — O1, weak O2, O3's schedule component. No idle suspend/hibernation; no daily shutdown; independent randomized maintenance per replica; website reloads must not restart Tor unnecessarily; no simultaneous replica maintenance. The *distribution* of times matters more than the UTC label (randomization confined to the owner's evenings still leaks "evenings"). Zero added owner concepts. **Placement: default. Dynamic: survives (DB maintenance separate).**

**D8. Static-serving/publication hygiene** — bounded request/response resources, efficient static serving, atomic content replacement, uniform error behaviour, no public uptime/version/node identifiers, strip unintended file/build timestamps. Optional publication batching reduces immediate timing but not the eventual update event. **Placement: default; publication-delay features future/opt-in.**

**D9. Restricted discovery / client authorization** — limits unauthorized O1/O3 observation by changing the threat model (only authorized readers can connect), but outer descriptor presence remains examinable and authorized observers retain access. Costs: enrollment/revocation concepts, loss of public accessibility. **Placement: future opt-in "private site" mode.**

---

## D. Disclosure paragraph (reviewer's draft, for owner-facing use)

> OnionHost uses Tor to hide your computer's network address from visitors, but it cannot hide every clue about where your site is hosted. Someone who repeatedly checks when your site works could compare interruptions with publicly reported power or internet outages and narrow down possible regions or providers. Repeated matches over weeks or months may strengthen a guess, but an unusually distinctive outage could provide a clue sooner, and some patterns may never identify a location. Backup power, a backup connection, or independent hosting copies can reduce these clues, but do not guarantee location privacy. Someone who can already observe your home internet connection may also use traffic timing to help link it to your site.

Reviewer's fact-check note: "weeks or months" is an illustrative observation horizon, not an experimentally established attack duration; the sooner/never qualifications are necessary; do not ship a numerical minimum time-to-identification.

---

## E. Ranking (reviewer's table, condensed)

| Defence | O1 | O2 | O3 | Placement |
|---|---|---|---|---|
| D7 lifecycle/schedule hygiene | Useful | Weak | Useful (schedules) | **Default** |
| D8 static/resource/publication hygiene | Limited | Limited | Useful | **Default** (batching later) |
| D5 tested Tor protections | Little | Limited | Useful | **Default** |
| D4 persistent Tor + stock padding | Little | Limited (coarse) | Little | **Default** (custom cover later) |
| D1 UPS + dissimilar failover | Strong within coverage | Limited | Little | **v1 opt-in** |
| D6 independent static mirrors | Weak if home public; stronger decoupled | Limited | Some resilience | **v1 opt-in export**; broader future |
| OnionBalance multi-home | Potentially substantial | Limited | Resilience, PoW caveat | **Future — preferred multi-host form** |
| P1 same-key publishers | Uncertain/moderate | Limited | Extra capacity | **Future experimental — not a v1 claim** |
| D9 client authorization | Substantial access restriction | Little | Substantial | **Future opt-in private mode** |
| D3 restore delay | Weak | Weak | Little | Future evaluation |
| D2 decoy downtime | Unproven/weak | Weak | Little | **Reject for v1** |

**Reviewer's v1 ship combination**: defaults D7 + D8 + D5 + D4, plus the Section D disclosure; optional D1 and D6 (where operationally invisible to owners); defer single-address multi-host until OnionBalance integration + failure testing are complete (test fresh/cached clients, host failure, publisher failure, partition, restoration, independent maintenance; measure first-attempt success separately from time-to-success).

**Refused to ship**: D2 decoy downtime as an advertised privacy defence — certain availability loss, no demonstrated protection, preserves real evidence, risks misleading owners.

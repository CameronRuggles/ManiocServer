# OnionHost OS — Availability Correlation Threat-Model Review

Oct 11, 2026 · @Cameron

The honest headline: most of the anti-correlation tricks in the seed list do little against a patient observer. The two measures that actually move the needle are making the service non-public (so observers cannot probe it) and disclosing the residual risk accurately. This review recommends resilience plus honest copy over obfuscation theater, and follows the requested A–E structure.

## A. Threat-model corrections

The O1/O2/O3 split is sound. Corrections and additions:

**The blurring estimate is directionally right but under-specified.** "Seconds invisible, minutes smeared, sustained outages are the signal" holds for a *passive visitor* logging reachability. It does not hold against an observer who actively probes reachability on a fine interval — and a patient O1 observer with public data will almost certainly probe. So O1 and O3 overlap more than the document implies: the intersection attack is fed by active probing. Smearing is not a fixed "minutes" window; it is a function of descriptor republish interval, intro-point circuit lifetime, and whether live traffic is forcing circuit rebuilds during the outage. Treat the protection as real against passive visitors, weak against an active prober, and write copy to the weaker case.

**Exposures not yet named:**

- **Application-layer timestamp leaks.** A static journal is full of them: feed/RSS `pubDate`, `Last-Modified`, visible post dates, and especially EXIF in uploaded images (capture time, sometimes GPS). These leak timezone and schedule directly and defeat the UTC-maintenance randomization. Cheap to fix; belongs in the default set.
- **Performance fingerprint.** Not just up/down — response-latency distribution shifts with household load (evenings, when the home connection is also streaming), with the number of live replicas, and so on. A continuous side-channel the binary-uptime model misses.
- **Reverse-intersection / "too reliable" anomaly.** Reverse intersection is correctly flagged in Q3. Its mirror image: a home server that is *never* down during any single local outage looks like it has redundancy, which itself narrows the observer's model of the operator. Defenses can create signal.
- **The out-of-scope elephant.** Availability correlation is a minor deanonymization vector compared to guard-relay / netflow correlation by an adversary who can see large parts of the Tor network. Solving O1 perfectly, if users read it as "I am location-safe," makes them less safe. The disclosure must say O1 is not the main risk.

## B. P1 evaluation

**Verdict:** Not a v1 default. At most a documented opt-in — and if offered, document OnionBalance, not naive same-key mirroring. For the single-home product, P1 is over-engineered relative to D1 (ride-through), which gets most of the O1 benefit with none of the key-custody blowup. Same-key multi-home mirroring can lower location-correlation risk while raising catastrophic key-compromise risk — a bad trade for this user base.

**Q1 — visitor-visible unreliability.** Expect noticeable-but-minor degradation versus single-host steady state. Same-key replicas publishing to the same HSDirs cause descriptor racing: clients may hold a descriptor pointing at a replica's intro points that just died, producing failed first attempts and retries until refetch. Worse at failover windows, better than a single host *during* an outage. OnionBalance exists specifically to kill the racing by aggregating intro points under one descriptor.

**Q2 — one-of-N fails.** Failover is descriptor-republish-scale — minutes, not instant. For up to roughly a republish interval, some clients get failures/retries; then descriptors refresh and surviving replicas carry the service. So "stays up when one home has an outage" is only defensible as *usually reachable again within a few minutes*. Under the honest-copy constraint (4.5), "stays up" overclaims. Say "recovers within minutes."

**Q3 — cost to a patient O1.** Removes the clean single-home intersection — a real gain against a casual observer. Residual signals remain: latency change when a replica drops, the "never down during local outages" anomaly, sync/update events, and reverse intersection. Net: meaningful cost increase against casual O1, modest against an O1 who models multi-home. It converts "identifying" into "requires correlating several regions plus performance side-channels" — real, not infinite. And it multiplies key custody by N: each node is a physical-seizure target, and seizing any one yields the private key (impersonation / takeover) plus a confirmed location. A strictly worse risk class than the one being mitigated.

**Q4 — is a 2-node static OnionBalance realistic?** Mechanically yes — OnionBalance v3 is static-friendly and avoids racing. But it adds a management / frontend host and still uses key material, which blows the "five simple concepts" budget as a default. As a power-user opt-in it is the better-engineered choice than same-key racing. Pragmatic form for v1: offer neither by default; if an opt-in ships, ship OnionBalance.

## C. Other defences

**D1 — Ride-through (UPS + dissimilar failover).** Observers: O1. Mechanism: survive the common short/medium outage so uptime stops matching local outage records. Plain terms: most home outages are brief, so batteries plus an LTE/5G failover ride through them and your downtime stops lining up with the public outage feed. Cost: hardware money, trivial user concepts. Key custody: single machine, no key copying — best score. Survives the future DB tier (single writer, no sync problem). Failure modes: multi-hour outages still correlate; failover activation is a brief observable blip; cellular has its own caps/outages and ties to a billing identity (not O1-visible, but worth noting). New exposure: the failover-transition event is a small timing signal — noted, minor. **Placement: recommended opt-in hardware — the one I would actually push.**

**D2 — Decoy downtime.** Observers: O1 (claimed). A patient observer filters it trivially: real outages correlate with external public power/ISP data, decoys do not, so the analyst keeps only events matching known outages and discards the noise. Decoys coinciding with a real regional outage are rare and do not help. Meanwhile it directly costs real availability for zero user benefit, and it tempts dishonest "we hide your location" copy. New exposure: the decoy schedule is itself a fingerprint, and "this operator actively injects fake downtime" is itself information. **Placement: reject — my candidate for "refuse to ship."**

**D3 — Restore-delay smearing.** Observers: O1. Caching already smears the down-edge; a randomized up-edge delay just shifts a transition a fine-grained prober still catches, while costing real extra downtime. The signal O1 uses is the set of windows, not the exact edges. New exposure: none identified. **Placement: future/experimental, not v1.**

**D4 — Constant presence (vs O2).** Observers: O2. O2 compares the household's online/active rhythm with the service's reachability. Constant presence does not change when the service is reachable, so it addresses the wrong variable; Tor already does circuit padding as a baseline. New exposure: self-rolled cover traffic is a fingerprint and burns bandwidth. **Placement: reject — do not roll your own padding.**

**D5 — Protocol-level options (the biggest under-use).** Observers: O1 and O3. The high-value one is v3 client authorization. For a *personal* site you do not need to be publicly reachable — require a client key, and an unauthorized observer cannot fetch the descriptor or probe reachability at all, which collapses most of O1 and O3. Also onion-service PoW defense and intro-point DoS defense blunt O3 active-load probing by making flooding expensive. Cost: client auth changes the product (visitors need a key) — fine for personal, wrong for public. New exposure: none identified (do not touch single-hop / non-anonymous modes — those deanonymize). **Placement: client auth = default-offer for personal sites; PoW + intro-DoS = default-on. Verify current parameter names/status against the live Tor onion-service man page before shipping.**

**D6 — Content-layer / independent mirror addresses.** Observers: O1. Each address keeps its own uptime unless aggregated (which is OnionBalance again), and it doubles attack surface and fragments the audience. New exposure: a second address is a second correlation target. **Placement: reject as a privacy measure; fine as a plainly-labeled redundancy convenience.**

**Addition — strip application-layer time metadata.** Observers: O3 (timezone). Default, cheap, genuinely effective: scrub EXIF on upload, use content-derived or build-fixed timestamps on feeds and `Last-Modified`, no local-time strings. New exposure: none. **Placement: default.**

## D. Disclosure paragraph (draft, for fact-check)

> OnionHost hides your computer's internet address from visitors and from the website software itself. It does **not** hide *when* your site is online. A determined observer who records your site's availability over weeks and compares it against publicly available power and internet-outage records for different areas may, over time, narrow down the general region where your computer sits. Measures like a battery backup, a backup internet connection, and running from more than one location make this slower and noisier, but they do not make it impossible, and some add risks of their own. Separately — and more importantly — hiding your uptime does **not** protect you from powerful adversaries who can monitor large portions of the Tor network; that is a different and harder problem this product does not solve. If being physically located would put you in danger, do not rely on hosting from your home.

## E. Ranking

| Defence | Observers | Effect (plain) | Cost | New exposure | Placement |
| --- | --- | --- | --- | --- | --- |
| Client authorization | O1, O3 | Observers cannot probe/fetch at all | Visitors need a key (personal only) | none | Default-offer (personal) |
| PoW + intro-DoS defense | O3 | Makes active flooding expensive | config only | none | Default-on |
| Strip timestamp/EXIF | O3 | Removes timezone/schedule leaks | trivial | none | Default |
| Honest disclosure | — | User decides with real info | none | none | Default |
| D1 ride-through (UPS+LTE) | O1 | Survives common outages | hardware $ | tiny failover blip | Recommended opt-in |
| OnionBalance (2-node) | O1 | Breaks single-home intersection | host + concepts + key use | key custody ×N | Power-user opt-in |
| P1 same-key mirror | O1 | Same, but racing | descriptor racing | key custody ×N, racing | Discouraged |
| D3 restore-delay | O1 | Smears up-edge marginally | real downtime | none | Future only |
| D6 mirror addresses | O1 | Relocates signal | 2× surface | 2nd target | Reject (as privacy) |
| D4 constant presence | O2 | Wrong variable | bandwidth | padding fingerprint | Reject |
| D2 decoy downtime | O1 | Filtered out by observer | real downtime | decoy fingerprint | Refuse |

**Ship for v1 in your position:** client authorization (default-offered for personal sites) + PoW/intro-DoS defenses (default) + timestamp/EXIF scrubbing (default) + the honest disclosure paragraph (default) + D1 as recommended opt-in hardware. That stack is reliability and honesty, plus the one measure (client auth) that works by not being observable rather than by fooling an observer.

**Refuse to ship even if asked:** D2, decoy downtime. It degrades real availability to produce an anti-forensic effect a patient observer simply filters out, and its main practical function would be to justify "we hide your location" copy you have correctly committed to avoiding.

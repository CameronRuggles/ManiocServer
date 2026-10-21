# Legal intake drafts — OnionHost OS (working title)

Prepared 2026-10-11. NOT sent. Both drafts are send-ready except the
`[PROJECT NAME]` placeholder — the name is Cameron's call and also the
subject of the trademark question, so it goes in last.

Contacts verified 2026-10-11:
- SFLC: help@softwarefreedom.org — their contact page directs FLOSS
  projects needing legal advice to this address
  (https://Softwarefreedom.org/about/contact/).
- EFF: info@eff.org — the EFF Tor Legal FAQ invites contact "if you face
  a specific legal issue" and says they try to assist but cannot
  guarantee help (https://community.torproject.org/relay/community-resources/eff-tor-legal-faq/).

Caveats to keep in mind before sending:
- SFLC's published material frames its clients as FLOSS projects, often
  not-for-profit ones. This project is currently a solo, pre-release
  effort planning an open-source (likely GPLv3) release. The draft below
  states that plainly and asks about eligibility/referral rather than
  assuming it.
- EFF's FAQ language is about facing a *specific* issue. The draft
  therefore names two specific questions (publisher posture for
  onion-hosting software; marketing-claim exposure) instead of asking
  for a general review.

---

## Draft 1 — SFLC (licensing + trademark half)

Subject: New open-source project seeking licensing and trademark guidance — self-hosted onion-service OS

Hello,

I'm developing an open-source tool (working title "[PROJECT NAME]",
final name still being chosen) that turns a home computer into a
self-hosted Tor onion-service web server through a click-through
installer: a Debian-based image with the website isolated in sandboxed
containers, a separate gateway container holding the onion key, and
full-disk encryption. I'm a solo developer; the project is pre-release,
not yet incorporated, and I plan to release the code under GPLv3 with
reproducible, independently verifiable builds.

Before any public release, I'd like guidance on:

1. Licence compliance for shipping a Debian-based ISO (licence texts,
   source-availability obligations for the binaries distributed).
2. Whether GPLv3 is the right licence choice for the parts that are
   ours (installer, dashboard, configuration tooling).
3. A trademark clearance check on the final product name, specifically
   around the Tor Project's "Onion" marks — the working title may be
   too close, and I'd rather rename now than after release.

Is this the kind of project SFLC can advise, and if the project's
structure (solo, not a nonprofit) makes it ineligible, could you point
me to counsel who handles this kind of work? I'm in Utah; the release
is months away, so there's no deadline pressure — I'm asking early
because I understand intake can take time.

Thank you,
Cameron

---

## Draft 2 — EFF (publisher-posture half)

Subject: Legal questions from a developer publishing onion-service hosting software

Hello,

I'm building open-source software (working title "[PROJECT NAME]")
that lets a non-technical person host a website as a Tor onion service
from a computer in their home: one-click install, the site sandboxed in
containers, and the publisher (me) operates nothing — I host no one's
site, keep no directory of users' sites, and collect no telemetry.
Release is still months away; I'm asking before publishing, not in
response to any dispute.

Two specific questions:

1. Publisher posture: is the "software publisher, not operator"
   framing above the right one for this kind of tool, and is there
   anything about how the project presents itself publicly that I
   should set up from the start to stay clearly in that posture?
2. Marketing claims: the product's honest claim is narrow — it hides
   the hosting computer's network address, with stated limits. What
   wording risks should I avoid so users can't reasonably claim they
   were promised more anonymity than the tool provides?

Your Tor Legal FAQ was my starting point; if EFF can't take this on,
a referral to a cooperating attorney who knows this area would be
just as valuable.

Thank you,
Cameron

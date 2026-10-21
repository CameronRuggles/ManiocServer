# Legal intake drafts — Manioc Server (v2, reworked 2026-10-17)

Supersedes LEGAL-INTAKE-DRAFTS.md (2026-10-11). NOT sent.
Reworked because the v1 drafts were stale on three premises:

1. **Name:** v1 carried a `[PROJECT NAME]` placeholder and framed the
   trademark question around the "OnionHost" working title's closeness
   to the Tor Project's "Onion" marks. The name was DECIDED by Cameron
   2026-10-17: **Manioc Server**. The internal working identifier
   "OnionHost" is not the public name.
2. **Licence:** v1 said "likely GPLv3" and asked whether GPLv3 is the
   right choice. The licence was DECIDED 2026-10-13: **Apache 2.0**
   for the project's own code. The live question is compliance for
   distributing a Debian-based ISO whose components carry their own
   licences, not licence selection.
3. **Release status:** v1 said "pre-release" / "release is months
   away." An alpha ISO (Prod Rebuild 2) is already publicly
   downloadable at maniocserver.org with its SHA-256 posted.
   The drafts now say so plainly — asking counsel while describing
   the project as unreleased would misstate the facts.

Contacts (verified 2026-10-11; re-verify before any send):
- SFLC: help@softwarefreedom.org — their contact page directs FLOSS
  projects needing legal advice to this address
  (https://Softwarefreedom.org/about/contact/).
- EFF: info@eff.org — the EFF Tor Legal FAQ invites contact "if you face
  a specific legal issue" and says they try to assist but cannot
  guarantee help (https://community.torproject.org/relay/community-resources/eff-tor-legal-faq/).

Caveats unchanged from v1:
- SFLC's published material frames its clients as FLOSS projects, often
  not-for-profit ones. This project is a solo effort; the draft states
  that plainly and asks about eligibility/referral rather than
  assuming it.
- EFF's FAQ language is about facing a *specific* issue. The draft
  names two specific questions (publisher posture for onion-hosting
  software; marketing-claim exposure) instead of asking for a general
  review.
- Scope note: these drafts cover Manioc Server (the OS) only.
  Polyculture Markets (the marketplace software) has its own separate
  pre-launch legal review item; do not treat a reply to these drafts
  as covering it.

---

## Draft 1 — SFLC (licensing + trademark half)

Subject: Open-source project seeking licensing and trademark guidance — self-hosted onion-service OS

Hello,

I'm developing an open-source tool, **Manioc Server**, that turns a
home computer into a self-hosted Tor onion-service web server through
a click-through installer: a Debian-based image with the website
isolated in sandboxed containers, a separate gateway container holding
the onion key, and full-disk encryption. I'm a solo developer, not yet
incorporated. An alpha build is already publicly downloadable, and I
plan to publish the project's own code under Apache 2.0.
Reproducible, independently verifiable builds are a goal and a
release gate I am working towards; they are not yet established.

Before the first non-alpha release, I'd like guidance on:

1. Licence compliance for shipping a Debian-based ISO (licence texts,
   source-availability obligations for the binaries distributed,
   given the mix of licences in the components).
2. Whether Apache 2.0 for our own parts (installer, dashboard,
   configuration tooling) creates any friction with the copyleft
   components the image ships.
3. A trademark clearance check on the name "Manioc Server." (An
   earlier working title, "OnionHost," was dropped before any public
   branding under the new name; if its earlier use on a download page
   matters, I'd like to know. For completeness: the old name still
   persists in package metadata and other internal identifiers —
   I am telling you that as a fact for counsel, not asking to
   rename those identifiers.)

Is this the kind of project SFLC can advise, and if the project's
structure (solo, not a nonprofit) makes it ineligible, could you point
me to counsel who handles this kind of work? I'm in Utah; I'm asking
early because I understand intake can take time.

Thank you,
Cameron

---

## Draft 2 — EFF (publisher-posture half)

Subject: Legal questions from a developer publishing onion-service hosting software

Hello,

I'm building open-source software, **Manioc Server**, that lets a
non-technical person host a website as a Tor onion service from a
computer in their home: one-click install, and the site sandboxed
in containers. I host no one's site, keep no directory of users'
sites, and collect no telemetry — but that is not the whole
picture: the maintainer (me) operates the project's update-repository
onion service, which every installed box contacts roughly daily
to check for signed updates.
An alpha build is already publicly downloadable; I'm asking before
any wider launch, not in response to any dispute.

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

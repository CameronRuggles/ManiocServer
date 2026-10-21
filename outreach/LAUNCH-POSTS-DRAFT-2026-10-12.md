# OnionHost — launch / recruiting post drafts
Drafted 2026-10-12 (Mon evening, America/Denver) for Cameron's approval. NOTHING is posted.
Target page: vespiary.org/onionhost/ — VERIFIED LIVE 2026-10-13 (re-fetched in the 2026-10-12 evening proactivity run; page lists @CameronRuggles + the Vespiary forum, no WorldExpanders references).
UPDATED 2026-10-12 evening: Cameron directed the page NOT be associated with WorldExpanders. It was moved to vespiary.org/onionhost/, the WorldExpanders copy was deleted and verified 404, and Cameron confirmed @CameronRuggles on Twitter as the contact for the time being. Earlier text in this file pointing to worldexpanders.com/onionhost/ as canonical was stale and has been corrected throughout.
Download timing — DECIDED 2026-10-13: no download link until a prod ISO ready for others'/Cameron's own testing is built — i.e. after backup/restore (Slice 5B) lands, test scaffolding stripped and verified absent, SHA-256 posted on the page and a Drive copy refreshed. The newest Slice 5A ISO is test-flavour (known test account/SSH) and must NOT be published.
SUPERSEDED 2026-10-13 afternoon (proactivity pass): that condition has now been MET — prod rebuild 2 is publicly downloadable at vespiary.org/onionhost/onionhost-amd64.iso with its SHA-256 on the page (see STAGE2-RUNBOOK.md for the current hash), and the licence was DECIDED 2026-10-13 as Apache 2.0 (LICENSE filed in the project tree). Every "no public download yet" and "licence undecided / GPLv3 recommended" line in the posts below was stale and has been corrected in place. What remains true: no public repo yet, and a formal release still waits on the reproducible-build gate — the download is an alpha/testing ISO, not the release.

## Read first — the four decisions/risks baked into every post

1. **Name/URL lock-in.** Every post bakes in the working title "OnionHost OS" and a
   vespiary.org subfolder URL, both of which will change when Cameron picks the real name.
   Reddit *titles* cannot be edited after posting. X and r/opensource are the lowest-stakes
   first moves; the subreddit posts below are ready whenever he accepts the lock-in or picks
   a name first.
2. **No repo yet — on purpose; a testing download IS live.** The posts recruit people
   (testers / reviewers / builders) first, and say so plainly; the alpha ISO (prod
   rebuild 2) is downloadable from the project page for testers. Several communities
   normally expect a source link; expect "repo or it didn't happen" comments and answer
   them with the release rule (public repo + reproducible, independently verified build
   come before any formal release), exactly as the site's footer states it.
3. **Do not blast all communities the same day.** Same link across several subreddits in a
   short window reads as spam and can trip filters. Suggested order, spaced at least a day
   apart: X → r/opensource (Promotional flair) → r/selfhosted (megathread route, see below)
   → r/TOR (modmail first). One tailored post per community; Cameron approves and sends each.
4. **Screenshots exist.** ~/workspace/onion-host-os/demo-shots/ has dashboard, editor, and
   published-site shots — attach 1–2 to the r/selfhosted / r/opensource posts; those
   communities are visual and screenshot-first.

## Community rules — what was checked (2026-10-12/13)

Direct reads of the Reddit rule wikis were blocked in the text fetcher (reddit.com blocked);
a live-browser read of all three rule pages is in flight and must confirm the notes below
before anything posts. Secondary sources checked 2026-10-13:

- **r/selfhosted** — self-promo-friendly IF the project is genuinely self-hostable and the
  post carries substance (what it does, tech stack, screenshots, honest stage). One current
  listing of subreddit rules says projects younger than three months (from first public
  commit/post) belong ONLY in the current New Project Megathread, and Wednesday posts get
  the showcase slot. OnionHost has no public commit yet — safest read: use the megathread,
  or message mods before a standalone post. Flair the post correctly.
- **r/TOR** — strict about self-promotion; practitioner notes say check recent "I built X
  that uses Tor" posts first and expect to modmail the mods before posting a project.
  Draft below is written as a design-review request, not an ad; modmail draft included.
- **r/privacy** — NOT recommended for a launch announcement post. Use participation and,
  if anything, a mod-approved discussion question (variant included below). Posting the
  recruiting pitch there cold is the likeliest removal of the set.
- **r/opensource** — project posts allowed with the **Promotional** flair; keep own-content
  share low and engage in comments.

---

## 1. X / Twitter (ready first — lowest stakes)

Post 1:
> I'm building OnionHost OS — a free, open-source OS that turns a spare home computer into
> a Tor .onion website. No hosting account, no domain, no port forwarding, no monthly bill.

Post 2 (thread):
> The one claim: it hides your computer's network address — even from the website software
> itself, which runs in a sandbox with no network at all. If the site is hacked, the
> attacker still doesn't get your home IP. The limits are on the page too — uptime can leak
> what Tor hides, and we say so.

Post 3 (thread):
> It's in alpha — a testing ISO is downloadable from the project page, with its SHA-256
> posted. What I need is people: testers with a spare PC, security reviewers, and builders
> who'll rebuild the ISO and check it matches. Adults only. vespiary.org/onionhost/

## 2. r/opensource — Promotional flair

**Title:** OnionHost OS (alpha) — a Debian-based OS that hosts a Tor onion site from a spare
home computer; the web server runs in a sandbox with no network at all. Recruiting testers,
reviewers, and rebuilders

**Body:**
I'm the builder. OnionHost OS is a free, open-source (Apache 2.0) Debian 13
derivative that turns a spare home computer into a website reachable only as a Tor .onion
address: no hosting account, no domain, no port forwarding, no monthly bill, because onion
services connect outward to Tor.

The design makes exactly one claim: it hides the computer's network address — from visitors,
and from the website software itself. Three sandboxed containers (Podman + gVisor) each do
one job:

- The website container has **no network at all** and never holds the onion key. A fully
  compromised site can be defaced, but it can't phone home, scan the LAN, or leak an address
  it has never seen.
- The Tor gateway is the only part online; it speaks only Tor and reaches the site over a
  unix socket — a channel that carries no IP address to leak.
- A client-only helper checks "is my site reachable?" and fetches signed updates, so
  maintenance never reveals the server's own Tor identity.

Around that: full-disk encryption with a generated 7-word phrase typed at every boot (unplug
it and it's a brick), a firewall that compares itself against a golden config and fails
closed, EXIF/GPS stripped from photos published through the built-in editors, and no web
admin panel at all — editing happens in a local app on the machine.

What we don't claim is also on the project page: Tor hides where a server is, not when it's
online, so a patient observer correlating uptime with outage reports can narrow things down
over time. If being located would put you in danger, don't host from home.

Status, honestly: design went through two rounds of external security review (the reviews
that corrected us were adopted); installer, encrypted boot, container stack, dashboard and
page/journal editors are built and passing end-to-end install tests. A **testing ISO is
downloadable from the project page** (prod rebuild 2, SHA-256 posted), but there is no
public repo yet, deliberately — a formal release counts only when independent rebuilders
produce a bit-identical ISO, and that gate comes first.

What I'm recruiting for: (1) testers with a spare computer they can erase — non-technical
is the point; "I got stuck here" is the report we need; (2) security reviewers to read the
design record adversarially; (3) builders/rebuilders. Adults only. Details and contact:
vespiary.org/onionhost/

Happy to answer anything about the wiring — that's the part worth arguing with.

## 3. r/selfhosted — use the New Project Megathread (or modmail for a standalone post)

**Megathread comment version (short):**
I'm building **OnionHost OS** — a Debian-based OS that turns a spare PC into a self-hosted
website reachable only as a Tor .onion address (no port forwarding, no public IP, no domain,
no VPS bill). The twist is the wiring: the web server (Podman + gVisor) runs with **no
network interface at all** and never holds the onion key; a separate Tor gateway container
passes requests over a unix socket, so a hacked site has no home IP to give away — it has
never seen it, and that holds as long as the sandbox wiring does. The honest limit, same as
on the project page: this is about the network address only. Tor hides where a server is,
not when it is online, so a patient observer matching uptime against public outage reports
can still narrow things down over time. Full-disk encryption with a generated paper
phrase, golden-config firewall that fails closed, EXIF stripping on publish through the
built-in editors, local-only editing (no web admin panel).
Alpha: installers/editors built and passing end-to-end tests; a testing ISO is
downloadable from the project page — the formal release still waits on reproducible-build
verification. Recruiting spare-PC testers, security
reviewers, and rebuilders: vespiary.org/onionhost/ (working title/URL — name is
still being chosen). Screenshots in my reply below. Ask me anything about the stack.

**Standalone-post title (only if mods clear it):**
I built an OS that self-hosts a website as a Tor onion service — and gave the web server
no network at all

(Standalone body = the r/opensource body above, plus the demo-shots screenshots and one
added line at the top: "Mods cleared this post — the project is pre-repo, so it didn't fit
the megathread's link format." Only use that line if it's true.)

## 4. r/TOR — modmail FIRST, post only on a yes

**Modmail draft:**
> Hi mods — I'm building an open-source OS that hosts a site as a v3 onion service from a
> home computer (site software sandboxed with no network; gateway holds the key; socket
> between them). It's in alpha (a testing ISO is on the project page), and I'm recruiting testers/reviewers. May I
> post a short design-summary + recruiting post? Happy to use a specific thread/format if
> you'd prefer, and to keep the only link to the project page at the end.

**Post (if approved) — Title:** Hosting an onion service from home without the site software
ever seeing an IP address — design summary and a request for hostile review

**Body (condensed from the site; claims and limits verbatim in substance):**
Disclosure: it's my project. The one claim is narrow — the server's network address stays
hidden from visitors AND from the website software. Architecture: website container with no
network (Podman + gVisor), Tor gateway as the only online component holding the onion key,
requests passed over a unix socket, client-only helper for reachability checks and signed
updates so maintenance doesn't expose the server's Tor identity. Tor PoW + intro-point rate
limits on by default. Disk encrypted, phrase typed at every boot; firewall self-checks
against a golden table and fails closed.

Limits, stated on our own front page: uptime correlation against public outage reports can
narrow a server's region over time; no defence against an adversary watching large parts of
the Tor network; a running, seized machine is not the ironclad state — powered off is.

The design has had two external review rounds and we adopted the corrections. What I want
from this sub is the third: where does the wiring leak? Testers with spare hardware and
rebuilders also welcome. Project page (working title; testing ISO + SHA-256 there):
vespiary.org/onionhost/

## 5. r/privacy — do NOT post the pitch; discussion variant only, ideally mod-approved

**Title:** What would a home onion-hosting tool have to prove before you'd trust its
"your address stays hidden" claim?

**Body sketch:** No link in the opening post. Frame it as the question the project is
built around: one narrow claim, published limits (uptime correlation, global adversary,
seized-while-running), no telemetry, no directory of users' sites. Disclose in the first
comment that Cameron is building a tool on exactly these lines and link the project page
there only if the sub's rules/mods allow it. If mods say no, the honest move is to just
participate in the thread — the answers are the market research either way.

## Pre-post checklist (Cameron, ~5 minutes total across all posts)

- [x] Live check confirms vespiary.org/onionhost/ loads (verified live 2026-10-13; WorldExpanders copy deleted/404).
- [ ] Decide: post under the working title now, or pick the real name first (Reddit titles
      can't be edited; X posts can be redone).
- [x] Contact DECIDED: X (@CameronRuggles) for the time being + the Vespiary forum — live on the page.
- [ ] Attach demo-shots 1-dashboard.png + 4-published.png to the r/selfhosted /
      r/opensource posts.
- [ ] Stagger: one community per day at most, in the order above; reply to comments the
      same day each post goes up.

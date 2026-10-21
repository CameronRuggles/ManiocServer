# Manioc Server — Public Repo Review Pack

Prepared 2026-10-20 for an external reviewer (Claude). This is a read-only
review request. The owner will verify every load-bearing claim against the
code before acting on it, so evidence matters more than coverage: cite
`file:line` for every finding, and separate what you verified from what you
suspect.

## The target

- Repository: https://github.com/CameronRuggles/ManiocServer (public)
- Review commit: `<pre-rewrite commit SHA withheld — see maintainer record>`
  It is the repo's initial commit and, at the time of writing, its only one.
- Companion repo (source of the marketplace app that ships as a recipe):
  https://github.com/CameronRuggles/polyculture-markets
- Project site: https://maniocserver.org

## What this project is

Manioc Server is free, open-source software (Apache 2.0) that turns a home
desktop into a Tor onion hosting server for non-technical users. It ships as
a Debian 13 live/install ISO: Calamares installer, mandatory LUKS2 disk
encryption with a 7-word phrase typed at every boot, and a sealed
architecture in which the website container has **no network at all** — a
separate Tor gateway container reaches it over a unix socket, and the Tor
container alone holds the onion key. Containers are rootful Podman/Quadlet
with gVisor (runsc) mandatory. Owners can install packaged apps ("recipes":
SMF, WordPress, DokuWiki, Gitea, and the Polyculture Markets marketplace)
into a language-neutral app slot, or their own software — containment is a
property of the wiring, not of curation. Updates arrive in place over Tor
from a signed package repo, with health checks and automatic rollback.

Status: alpha. The currently downloadable ISO ("Prod Rebuild 2", built
2026-10-13) is offered for testers, with a published SHA-256. Nothing about
this project is mainnet-of-anything; there are no funds and no users' data
at stake yet. The owner is one person. The project's public claims are
deliberately narrow: for example, the boot chain is **not** claimed to be
evil-maid-proof, and copy must never say it is.

### Names and identifiers — read this before flagging them

The OS was developed under the working title "OnionHost", renamed Manioc
Server on 2026-10-17. Internal identifiers deliberately did **not** change:
package names (`onionhost`, `onionhost-recipe-*`), paths (`/etc/onionhost`,
`/usr/lib/onionhost`, `/var/lib/onionhost`), systemd/Quadlet unit names, and
`ONIONHOST_*` environment variables. This is a decision, not an oversight —
do not report it as an inconsistency. The marketplace's `marketplace_id`
(`vespiary-market`) likewise stays: it is baked into a signed
payment-statement format.

### Tree map (263 files, ~3.6 MB at the review commit)

- `onionhost/` — the OS source: rootfs overlay, Calamares configuration and
  plugin sources, the wizard, and `recipes/` (per-app recipe definitions:
  `recipe.json`, overlay, seed, files — the vendored app archives themselves
  are **not** in the repo; see exclusions).
- `build/` — the build scripts, including `build-iso.sh` (the automated ISO
  build), `build-onionhost-deb.sh`, `build-recipe-deb.sh`,
  `make-onionhost-repo.sh`, and the VM test drivers.
- Top-level `*.md` — design documents (DESIGN-v2, DESIGN-v3-amendments),
  acceptance reports, runbooks, the full ISO build log, naming/legal
  working papers. This repo is intentionally the project's public record,
  not a bare source drop.
- `audit/` — reports only from an in-progress security audit
  (`INTERIM-SUMMARY.md`, `tools.txt`). Its raw working bulk is excluded.
- `poc/` — only `POC-RESULTS.md` and `scripts/`; the PoC laboratory itself
  is excluded (see below).
- `stage1/` — GCP rig bootstrap/test scripts. `site/` — the source of the
  older recruiting page. `outreach/` — tester-kit and launch drafts.
  `demo-shots/` — screenshots.

### Deliberately excluded from the repo (do not report these as missing)

Excluded by the `.gitignore` at the repo root, and still present in the
owner's local tree: release ISOs (`releases/`), recipe vendored archives
(`onionhost/recipes/*/archive/` — upstream binaries/zips the recipes pin by
SHA-256, plus one locally built app binary), the entire `poc/` laboratory
(extracted app installs, container stores, extracted root filesystems, Tor
test data — including two proof-of-concept onion service keys),
`audit/` raw extractions and scan output, and all `*-evidence/`
screenshot/log directories. The scrub that produced this set is itself one
of the things you are asked to review (Scope 1).

### The repo is not the shipped ISO

The downloadable ISO was built 2026-10-13 from an earlier tree state. The
repo tree is newer (it contains a permissions fix known as "D8" and the
Manioc rebrand). Review the repo as the repo. Where a mechanism in the tree
mitigates something observed in the ISO, say so; do not clear the ISO with
the tree or indict the tree with the ISO.

## Scope 1 — Publication audit (what did we just make public?)

This repo went public on 2026-10-20 after one scrub pass by the owner's
agent. Audit that scrub. The question is whether anything in the public
tree should not be public, and whether the `.gitignore` will keep it that
way as commits accumulate.

1. Sweep the full tree at the review commit for: key material of any kind
   (private keys, key fragments, seeds, passphrases), credentials and
   tokens, personal data (names, emails, addresses beyond what the owner
   publishes deliberately), test data that is actually real data, and
   infrastructure details that go beyond labels (host addresses, internal
   addressing, account identifiers). Distinguish "label" (a cloud project
   or VM name — the owner has knowingly published these before) from
   "lever" (anything that grants or eases access).
2. Audit `.gitignore` as a control, not a formality: which realistic future
   files would slip past it? Consider new evidence/screenshot directories
   that don't match `*-evidence/`, new archive locations outside
   `recipes/*/archive/`, VM disk images with other extensions, packet
   captures, database dumps, editor/OS litter, and anything a build script
   writes into the tree. Check whether the build scripts themselves emit
   files the ignore rules don't cover.
3. Check the committed documents for statements the owner would not want
   quoted back: drafts that read as commitments, legal working papers
   (the LEGAL-INTAKE files are drafts to counsel — flag anything in them
   that is inaccurate about the project as it now stands), and the GCP
   appeal draft.
4. Sanity-check the licence posture: `LICENSE` (Apache 2.0) at the root,
   any third-party code vendored into the tree (wordlists, JS, fonts,
   copied snippets in the overlay or wizard), and whether attribution or
   licence texts that should travel with them are present.

Severity for this scope: **Critical** = live credential, key material, or
data that endangers a person, public in the tree. **High** = material that
materially eases attacking the owner or the project's infrastructure.
**Medium/Low** = hygiene, future-slip risk in the ignore rules, statements
that misdescribe the project.

## Scope 2 — Build-from-repo review (could a stranger build this?)

The project's claim, as of publication, is: a competent Linux developer
could build a working Manioc Server from this repo plus the companion
marketplace repo, using only public sources. Test that claim statically —
do not attempt the build; trace it.

1. Follow `build/build-iso.sh` end to end from a cold clone. List every
   prerequisite it assumes: host tools and versions, network access,
   local paths, files expected to exist outside the repo, environment
   variables, and any step that is manual, undocumented, or dependent on
   the maintainer's machine. The build's own stated rule is "a release
   build has no manual steps and no binaries out of a developer's home
   directory" — check the script against its own rule.
2. Check the pinned-input story for completeness: the Debian snapshot pin
   and `SOURCE_DATE_EPOCH` in `build-iso.sh`; the Calamares source hash;
   and for each of the five recipes (SMF, WordPress, DokuWiki, Gitea,
   marketplace), whether `recipe.json` records enough to re-fetch the exact
   archive the recipe expects (upstream source + SHA-256), and whether
   `build/build-recipe-deb.sh` verifies what it is given. The marketplace
   recipe is the special case: its app binary is built from the companion
   repo — is that relationship documented anywhere a rebuilder would find
   it, and is the version pinned?
3. Follow `build/make-onionhost-repo.sh` and the update path: where does
   the signing key come from, what must a rebuilder generate for
   themselves, and is any of it under-documented in a way that would strand
   them — or, worse, tempt them to disable signature verification?
4. Report the gap list as a rebuilder would experience it: ordered,
   concrete, each item citing the script and line that creates the gap.

## Scope 3 — Design-level security pass over the wiring

A second, independent read of the security architecture **as implemented in
this tree** (not as described in the design docs — where they differ, the
code is the finding). An automated audit of the source and the shipped ISO
is already underway by another route (see "Already covered" below); your
value here is a fresh read of the mechanisms, not tool output.

Test these settled invariants against the implementation:

1. The website/app container has no network. All reachability flows
   through the Tor gateway container over a unix socket. The onion private
   key exists only in the Tor container.
2. gVisor (runsc) is mandatory for the app slot, not optional or
   best-effort, and the engine configuration can't silently fall back to
   plain runc.
3. Disk encryption: LUKS2 with PBKDF2-only key slots for the phrase;
   the phrase is typed at every boot; an unplugged machine is a brick;
   any spare keyslot is generated, revocable, and owner-held. /boot is
   encrypted; an initramfs keyfile slot exists. (Known and accepted: this
   is **not** authenticated boot and not evil-maid-proof — do not report
   the absence of secure boot as a finding; do report any place the code
   or copy overclaims it.)
4. Updates: packages are signed; the client verifies before applying;
   replayed/old packages are refused; a failed health check rolls back;
   a security-floor conflict fails closed. Stock Debian apt silently
   ignores a unix-socket Tor proxy — the pipeline therefore ships its own
   fetch method with no clearnet code path. Verify there is genuinely no
   clearnet path (including error, retry, and fallback paths).
5. Recipes: the applier verifies the pinned archive SHA-256 before
   swapping; the swap is atomic; per-install database credentials are
   substituted at provision time from `/etc/onionhost/app-db.env` and never
   shipped inside a recipe package; a failed migration at start keeps the
   app down so update health checks fail and roll back.
6. First-boot wizard: account creation, the generated login secret, and
   any staged credentials (the marketplace recipe stages a first admin
   registration) are handled and destroyed as the docs claim.
7. The app slot is language-neutral and owners may install arbitrary
   software into it (a deliberate owner ruling). Containment must therefore
   come from the wiring. Judge the wiring, not the policy.

## Already covered — don't duplicate

- An automated security audit of this tree and the shipped ISO is in
  progress under a separate 9-phase runbook. Phases 0–2 (tool setup,
  source static analysis, ISO forensics) are complete; the interim summary
  is in the repo at `audit/INTERIM-SUMMARY.md`. Its provisional findings
  are Low-grade only so far — e.g. **F-P2-1**: the shipped ISO's
  `/etc/resolv.conf` carries the build rig's cloud DNS search domains
  (an ISO-side observation; if you can find the mechanism in the tree's
  build scripts, that is in scope and valuable). Phases 3–9 — install
  under packet capture, leak analysis, sandbox/systemd review,
  reproducibility (a second build compared byte-for-byte), and the final
  report — are dynamic or build-execution work and are **out of scope**
  for this review.
- The companion marketplace repo has been through five external audits
  (payments, account security, messaging, media/disputes, deployment) and
  three fix verifications in October 2026. Do not re-audit the marketplace
  application itself; the marketplace **recipe** in this tree (packaging,
  provisioning, wizard flow) is in scope.
- Settled decisions that are not findings: Apache 2.0 licence; the
  internal "onionhost" identifiers (above); owners may install arbitrary
  software in the app slot; one app slot per box (multi-app is a possible
  future extension); no exit relay, ever; bridge support opt-in and off by
  default; Tor Browser is not installed on the box.

## Seeded leads — unverified, check or discard

These are suspicions from the owner's side, offered as starting points,
not findings. Report each as confirmed, refuted, or not determinable.

1. The build rig's network identity may leak into built artifacts through
   more paths than the ISO's resolv.conf (F-P2-1) — build-info files,
   logs, cached chroots, stamped metadata.
2. The five recipes' re-fetch story may be uneven: some `recipe.json`
   files document provenance thoroughly (Gitea's is the model), others may
   pin a hash without naming a source a stranger could fetch from.
3. Recipe definitions in this tree were built against the marketplace app
   as of mid-October 2026; the companion repo has moved since. Version
   skew between the recipe's expectations and the current companion source
   may strand a rebuilder even if every pin verifies.
4. `build/` contains several generations of test-driver scripts
   (`dbg-run*.py`, `boottest*.py`, `gssh*.sh`…). Some may contain rig
   addresses or assume credentials in ways the Scope 1 sweep should catch
   if present — or cruft that merely embarrasses. Either is worth a line.
5. The wizard's handling of the generated 3-word login and the optional
   spare keyslot is security-critical and mostly implemented in one file;
   a careful read may find edge cases the acceptance tests didn't cover
   (interrupted first boot, re-run wizard, entropy source).

## Rules for this review

- Read-only. Do not propose yourself as able to run the build or the
  dynamic tests; where a question can only be settled dynamically, put it
  in a "not determinable from the tree" list rather than guessing.
- Every finding carries `file:line` evidence (or, for documents, the file
  and the quoted line). A finding without evidence will be treated as a
  lead, not a finding.
- Mark each finding **verified** (you traced the mechanism in the code) or
  **suspected** (pattern-matched, not traced). The owner verifies before
  acting; overstated certainty wastes that pass.
- Severity rubric for Scopes 2–3: **Critical** = reveals an operator's IP,
  location, or identity, or yields remote code execution on a user box.
  **High** = DNS or metadata leakage, unsigned or unverifiable updates,
  escape from the app slot to the host or the Tor container.
  **Medium** = clearnet contact on any path, unsafe systemd/container
  ratings, rollback or floor failures. **Low** = hygiene and hardening
  gaps. (Scope 1 has its own rubric above.)

## Deliverable

One report, in this shape:

1. **Verdict** — three to five sentences per scope: is the publication
   clean; could a stranger build it; does the wiring implement the
   invariants.
2. **Findings** — numbered per scope (P1…, B1…, S1…), each with severity,
   verified/suspected, evidence, and impact stated in terms of a real
   operator or rebuilder, not abstractions.
3. **A fix brief** — numbered tasks a developer can execute without
   re-deriving your reasoning, grouped so that all tasks touching the same
   file land together, each with an acceptance test or check.
4. **Owner questions** — at most five, and only decisions the owner can
   make (risk acceptance, naming, publication posture). Not questions the
   code can answer.
5. **Not reviewed / not determinable** — an explicit list. An honest gap
   list is worth more than silent non-coverage.

The owner's workflow on receiving it: every load-bearing claim gets
verified against the code, confirmed findings become gated fix batches
(fix the code, never the tests), and the fixes ship in the next ISO and
repo push — with credit to the review in the project record.

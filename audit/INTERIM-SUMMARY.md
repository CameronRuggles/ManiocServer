# Manioc Server Security Audit — Interim Summary (Phases 0–2)

Date: 2026-10-18. Auditor: Muse (automated, per the runbook's rules of
engagement: audit only, nothing fixed, everything local, no uploads;
Semgrep `--metrics=off`, TruffleHog `--no-verification`).
Scope of this interim report: Phase 0 (tool setup), Phase 1 (source
static analysis), Phase 2 (ISO forensics). Phases 3–9 not started.

## Targets audited (two separate targets, as instructed)

1. **Source tree, as-is on 2026-10-18** — `onionhost/` + `build/`
   copied to `audit/repo/` (219 files; identity = SHA-256 manifest
   `raw/p1/tree-manifest.sha256`, see `raw/p1/commit.txt`). This tree
   contains the D8 fix and the Manioc rebrand work.
2. **The shipped ISO** — `releases/onionhost-amd64.iso`, SHA-256
   `080e45ac048e9999d2de57f199d5411c53a442f4a7a7daaa49a92c0e4cb2b1c1`
   (verified before extraction), Prod Rebuild 2, built 2026-10-13
   from Debian snapshot `20251011T143150Z`, `flavour=prod`.

**Known divergence, stated plainly:** the ISO predates the current
tree. Findings are reported against the target they were found in;
the tree's newer code does not clear the ISO, and the ISO's state
does not indict the tree. Where a tree-side mechanism mitigates an
ISO-side observation (e.g. installer cleanup), that is said.

## Candidate findings (provisional, runbook rubric)

No Critical and no High candidates emerged from Phases 1–2.

### F-P2-1 — Low — Build rig's DNS search domains baked into every ISO (ISO)
`/etc/resolv.conf` in the shipped image is a regular file containing
`search us-west3-a.c.onion-rig.internal c.onion-rig.internal google.internal`
— the GCP build rig's project name and region, in every copy of the
public ISO (evidence: `raw/p2/p2-network-config.txt`). It fails the
Phase 2 "no build-host network config" row. It does not expose any
*operator* (the operator's own network config is created at install),
and the nameserver is only the systemd stub; it does disclose the
project's build infrastructure and leaves wrong search domains in
the live/installer environment. `/etc/onionhost-build-info`'s
`builder_host=Linux 7.0.0-1011-gcp` is the same family, smaller.
Phase 3/4 should check whether the search domains survive onto an
*installed* disk (if they do, raise severity).

### F-P1-1 — Low — Root updater executes an env-overridable command via `shell=True` (tree)
`onionhost-update:98-99,314`: `HEALTH_CMD` comes from
`ONIONHOST_HEALTH_CMD` (default: a fixed path) and runs with
`shell=True`. No shipped unit sets the variable, and influencing a
root service's environment already implies control of the unit, so
this is hygiene, not a vulnerability: argv-form exec would remove the
shell from a root updater entirely. (Evidence: `raw/p1/semgrep.sarif`,
analysis in `raw/p1/p1-notes.md`.)

### F-P1-2 — Low/Info — Installer diagnostic writes a predictable `/tmp` path (tree)
`calamares/modules/onionhostprobe/main.py:58` writes
`/tmp/gsprobe.txt` (fixed name) containing Calamares GlobalStorage
probe values. Live-installer session only, root-run, non-secret
content; a pre-planted symlink in the live session is the worst case.
Everything else in the tree uses `mkdtemp`/`mkstemp` correctly,
including 0700 tmpfs dirs for LUKS phrases and age identities.

### F-P2-2 — Info — Project bytecode (`__pycache__`) shipped in tree and ISO (both)
Build-time `.pyc` files for the project's own code sit in
`rootfs-overlay` in the tree and shipped in the ISO rootfs
(`usr/lib/onionhost/__pycache__/`, `usr/local/bin/__pycache__/`,
Calamares module cache). No build-user paths were found inside them;
the practical effect is scanner noise (the embedded self-test
constant is what tripped Gitleaks — see below) and build residue in
a privacy image.

### F-P2-3 — Medium (provisional) — Shipped snapshot carries a year of fixable CVEs, including in Tor and OpenSSL (ISO)
The ISO pins Debian snapshot 2025-10-11. Against the 2026-10-18
Grype DB (`raw/p2/grype-fixable.txt`): 3,490 fixable matches, of
which 2,584 are the `linux-kernel` pseudo-package (NVD version-range
matching that ignores Debian backports — treat as noise). The
remaining **906 fixable matches (≈79 Critical, ≈425 High)** include
network-facing packages:

* **tor 0.4.8.16-1** — 9 fixable Critical/High (fixed in
  0.4.9.8/0.4.9.11 `deb13u1`); 15 rows total.
* **openssl / libssl3 3.5.1** — incl. CVE-2025-15467 (Critical,
  EPSS 52%) fixed in 3.5.4 `deb13u2`, CVE-2026-63073.
* Go `stdlib` in shipped binaries (≈36 Critical/High, module-level
  matching — approximate), rsync 28, X.org 17.
* **nginx and PHP: zero fixable rows** — clean at DB date.

This is the expected consequence of a pinned snapshot + elapsed
time, and the platform's signed, Tor-only update channel exists
precisely to close it (verified in the tree, Phase 1). Severity
stays Medium **only if** Phase 4 confirms installed systems actually
receive current packages promptly; the exposure window between ISO
install and first successful update, and users who never update, are
the real risk. If Phase 4 finds the channel does not deliver these
fixes, this becomes High.

### Observations recorded as deliberate design (not findings)
* nginx PHP template pins `REMOTE_ADDR 127.0.0.1` with an explanatory
  comment (`golden/nginx-app-php.conf.tmpl:13-15,50`) — the platform
  knowingly fabricates it because the edge is a unix socket. The
  Phase 7 loopback-trust question therefore applies to the
  *packaged apps'* use of it, not to first-party code (no first-party
  code makes a REMOTE_ADDR decision — Phase 1 Q4).
* Live image: LightDM autologin + a live-user password hash are
  present, but prod builds set a **per-build random, unrecorded**
  password (`build/build-iso.sh:391-395`; verified the shipped hash
  is not the test flavour's `onion` or other common values), and the
  install/setup path removes the live user and the autologin drop-in
  (Phase 1 code evidence). Phase 3/4 must confirm on a real install.
* The helper's `cmd_app_info` prints the app DB password to the
  owner's own authenticated session by design (dashboard feature,
  sudo-gated). Recorded in `raw/p1/p1-notes.md` Q2.
* Setgid 0o2775 app directories (D8 design: mapped gid + owner ACL —
  required for creates through gVisor) and the WordPress/DokuWiki
  sealed-posture config files are deliberate and documented in-tree.

## Phase results in brief

**Phase 1** (`raw/p1/p1-notes.md` has the full analysis):
ShellCheck clean (6 minor warnings / 23 files). Semgrep: 16
findings, all triaged — false positives or the Low above. Bandit: 93
results, shipped-code items all false positives (secure `mkdtemp`
pattern flagged as B108; self-test asserts; a `random.sample` that
chooses re-type prompts, not secrets). Gitleaks: 2 hits, one false
positive (the `backupkeys` **self-test** age identity for the public
seed `bytes(range(32))`, cross-checked against age 1.2.1 + RFC 7748
vectors — it protects nothing). TruffleHog: 49 hits, all inside
vendored upstream app archives/binaries, none in first-party code.
OSV-Scanner: no lockfiles exist in scope — nothing to scan.
PHPStan level 6 + Psalm taint analysis on the 3 first-party PHP
files (165 lines of configuration): no security findings; Psalm "No
errors found". Lintian on 22 project-built .debs: 561 tag lines,
all packaging-style (deliberate `/usr/local` + `/etc/systemd/system`
layout, files in /etc not marked as conffiles, missing
changelog/copyright files) — no security defects; full output in
`raw/p1/lintian.txt`. Anti-pattern grep: zero hits for every
dangerous class (`curl|sh`, `chmod 777`, `--insecure`,
`trusted=yes`, `StrictHostKeyChecking no`, `SingleHopMode`, …).

The five manual-review answers (detail + citations in p1-notes):
**(1)** No input reaches a shell — argv-only subprocess everywhere;
secrets and recipe inputs travel on stdin; the staged
`recipe-admin.env` (0400, root) is parsed as data, *never sourced*
(explicit comment in both shell consumers). **(2)** No password or
key is ever an argv value or logged — LUKS phrases move as key
files in a 0700 tmpfs dir, age identities as 0600 files.
**(3)** Temp files: `mkdtemp`/`mkstemp` throughout (one exception,
F-P1-2). **(4)** No REMOTE_ADDR trust decisions in first-party code.
**(5)** No non-Tor fetch path exists: apt is hard-wired to a custom
`tor+http` method speaking SOCKS5 over a unix socket to a
client-only Tor container, the stock http/https apt methods are
*disabled* so misconfiguration fails closed, the wizard has no URL
input at all, and recipe archives are vendored + SHA-256-pinned.

**Phase 2** (`raw/p2/p2-checks.md` — every table row completed):
PASS on SSH host keys (none baked in), machine-id (empty),
Tor state (`/var/lib/tor` empty), hostname (`onionhost-live`,
generic), timezone (UTC), SUID/SGID (exactly the stock Debian 13
set of 17), world-writable files (zero), apt sources (single
signed-by pinned snapshot over HTTPS), and rootfs secrets scans
(827 TruffleHog + 22 Gitleaks hits — every one a documented false
positive: Debian package-index/changelog format matches, the stock
commented torrc example hash, the self-test constant). FAIL on
build-host network config (F-P2-1). SBOM produced: syft SPDX-JSON,
5,529 packages (`raw/p2/sbom.spdx.json`); Grype outputs in
`raw/p2/grype-all.txt` / `grype-fixable.txt` (see F-P2-3).

## Adaptations made (all logged per the rules of engagement)

1. **Tree is not a git repo** → SHA-256 manifest instead of a commit
   hash; Gitleaks/TruffleHog in directory/filesystem mode instead of
   git-history mode; `grep -rnIE` instead of `git grep`.
2. **Phase 1 scope** = `onionhost/` + `build/`. The project's
   `poc/`, `stage1/`, `*-evidence/` are test rigs/evidence, not
   source (their .debs were still lintian-checked).
3. **TruffleHog `--no-verification`** on both scans — default
   verification phones third-party APIs, violating keep-it-local.
   Findings triaged by location/context instead.
4. **Lintian deduplication**: ~130 .deb copies exist under `poc/`
   (stage dirs, repos, rootfs copies); lintian ran on the 22 unique
   filenames (one copy each), kept in `raw/p1/debs/`.
5. **VM replacement mid-session**: the audit host was replaced
   once; apt tools vanished and were restored by the runtime's
   package replay (~25 min of dpkg-lock contention). During the
   window, unsquashfs/xorriso were used from Ubuntu .debs extracted
   into `~/audit-tools/root/` (same versions). Full note in
   `tools.txt`. No evidence was lost (all outputs live under `~/`).
6. **Psalm 5.26.1 substituted for 6.20.0** (PHP patch-version
   floor; see Not tested).
7. Sharpened-tool substitutions per runbook Phase 0: none needed —
   every mandated tool was obtained from its official source.

## Not tested (with reasons — nothing silently skipped)

* **Git-history secrets scan** — no git history exists (tree is not
  a repository). Working-tree scans ran instead.
* **OSV-Scanner dependency scan** — ran, but the tree contains no
  lockfiles/manifests it can consume ("No package sources found").
  Dependency CVE coverage for the *shipped system* comes from the
  Phase 2 SBOM/Grype instead.
* **Psalm 6.20 taint analysis** — the 6.20 phar refuses the host's
  PHP 8.3.6 (requires ~8.3.16+). Psalm **5.26.1** taint analysis ran
  clean on the same files, so coverage exists; the version delta is
  the only gap.
* **TruffleHog verification** — deliberately off (would transmit
  candidate secrets to third-party APIs). All hits triaged manually.
* **TruffleHog cosign signature** — not verified (cosign absent);
  release checksums verified instead.
* **Calamares C++ plugin sources** (`plugin-src`, 3 files) — no
  dedicated C++ analyzer in the Phase 0 toolset; covered only by
  Semgrep's generic rules (0 findings) and the shell/Python review
  around them. Flagged for the final report's completeness section.
* **Container image contents** (`onionhost-tor.tar`,
  `onionhost-web.tar` in the ISO) — catalogued in the SBOM and
  included in Grype matching, but not unpacked/reviewed as code;
  they are Phase 6 scope.
* **Vendored app archives** (Gitea binary, WordPress/SMF/DokuWiki/
  marketplace in the tree's recipes) — upstream artifacts, Phase 6
  scope; Phase 1 verified only their hash-pinning and the
  first-party code around them.
* **Installed-system state** — everything post-install (shadow,
  autologin removal, nftables, services) is Phase 3/4 by design.

## What Phase 3 will need

* **VM resources**: this host has 2 cores / 7 GB and **no KVM** —
  QEMU runs emulated (as in the project's prior install proofs);
  install testing will be slow but workable. Install qemu +
  libguestfs then (deferred in Phase 0 by scope).
* **Snapshot discipline** per the runbook (pre-first-boot snapshot
  is the master; clone per scenario) — emulated QEMU makes snapshot
  hygiene more important, not less.
* **Specific verifications queued by Phases 1–2**: (a) installed
  disk's `/etc/resolv.conf` — do the rig search domains (F-P2-1)
  survive installation? (b) installed `/etc/shadow` + LightDM
  config — live user gone, autologin gone, owner account as
  designed; (c) first-boot → S0 wizard flow end-to-end, confirming
  the stdin-secret handling observed in code; (d) an early
  `onionhost-update` run to start closing F-P2-3, with Phase 4
  verifying the delivered package set against `grype-fixable.txt`.
* The two shipped container image tarballs and their build-info
  hashes (`raw/p2/p2-checks.md`) for Phase 6 provenance checks.
* Prod Rebuild 2 is `flavour=prod`: the live session cannot be
  driven with the test flavour's known password — plan Phase 3
  interaction through the graphical installer as a user would.

## Deliverables index

* `tools.txt` — every tool, version, source, verification, deferrals.
* `raw/p1/` — shellcheck.txt, semgrep.sarif (+log), gitleaks.json,
  trufflehog.json (+err), osv.txt, bandit.json, antipatterns.txt,
  lintian.txt (+debs/), phpstan.txt, psalm.txt, shell-files.txt,
  tree-manifest.sha256, commit.txt, p1-notes.md. (apt/pipx install
  logs are at `raw/` root.)
* `raw/p2/` — iso.sha256, xorriso.log, unsquashfs.log,
  p2-checks.md (the completed table), p2-*.txt evidence files,
  sbom.spdx.json, grype-all.txt, grype-fixable.txt,
  trufflehog-rootfs.json, gitleaks-rootfs.json.
* Working artifacts: `iso/` (extracted ISO), `rootfs/` (unsquashed
  live rootfs), `repo/` (audited source copy) — retained for
  Phases 3–9.

#!/bin/sh
# ci-scan.sh — publication guard for the Manioc Server repo (Review 2, task 2).
#
# Fails (exit 1) if any file that would enter the public repo contains:
#   * private-key headers: PEM ("BEGIN ... PRIVATE KEY"), OpenSSH
#     ("BEGIN OPENSSH PRIVATE KEY" / the openssh-key-v1 binary magic), or
#     Tor ("ed25519v1-secret" key-file header);
#   * a globally-routable IPv4 address that is not on the allowlist below
#     (private / reserved / multicast / shared / CIDR-network addresses
#     such as the nft bogon set are not findings);
#   * a /home/<user>/ path that is not on the allowlist below;
#   * an ELF binary outside an archive/ directory;
#   * secret key material in a tracked *.gpg file: every such file must
#     list as public-only under `gpg --show-keys --with-colons` (no
#     sec/ssb records) — a binary secret-key export has no header for
#     the patterns above to catch (Review 3, P11). The same public-only
#     check also runs on any other committable file whose first byte
#     is an OpenPGP secret-key packet header (packet tag 5: old-format
#     0x94-0x97, new-format 0xC5), so a binary export saved under
#     another name (e.g. .pgp/.kbx/.sec) cannot slip past (Review 4,
#     P15);
#   * an age secret identity: the literal prefix AGE-SECRET-KEY-1
#     followed by a long contiguous bech32 run (a complete identity
#     carries 58 such characters after the prefix; the rule fires at
#     44+, and the in-tree regression vector in backupkeys.py is
#     split across adjacent string literals so no contiguous run in
#     that file reaches the threshold) (Review 4, P15);
#   * a passphrase-like run: five or more consecutive words from the
#     EFF large wordlist within a line pair (a line plus the next),
#     allowlistable only as an exact (file, run) pair in PHRASE_ALLOW
#     below (Review 3, P10);
#   * a three-word passphrase-like run in secret context (Review 4,
#     P15): login phrases are three words, so the five-word rule can
#     never see one. A run of three consecutive EFF-wordlist words is
#     a finding when it immediately follows a trigger word (login,
#     spare, disk, phrase) on the same line, or when it is the entire
#     word content of a short quoted/bracketed segment on one line.
#     Allowlistable only as an exact (file, run) pair in PHRASE_ALLOW,
#     same mechanism as the five-word rule.
#
# Prerequisites are not optional: if `gpg` is not on PATH, or the EFF
# wordlist is missing/empty, the scan FAILS instead of silently
# skipping those rules and printing PASS (Review 4, P15).
#
# Usage: build/ci-scan.sh [ROOT]     (default ROOT: the repo this script
# lives in). Usable from CI (see .github/workflows/ci-scan.yml) or as a
# pre-push hook:  ln -s ../../build/ci-scan.sh .git/hooks/pre-push
#
# File set: with a .git directory, `git ls-files -co --exclude-standard`
# (tracked + untracked-but-not-ignored — exactly what could be committed
# next); without one, every file under ROOT except .git itself.
# This script is excluded from its own scan: its pattern and allowlist
# literals would otherwise be findings about themselves.
#
# ALLOWLIST — every entry is an exact (file, literal) pair with a reason.
# An allowlisted literal in any OTHER file is still a finding. Shrink
# this list as the cited clean-ups land; do not grow it silently.
#   IPv4:
#     192.71.80.206  public Netnod NTS server, observed endpoint in a
#                    packet-capture log entry (ISO-BUILD-LOG.md) — public
#                    infrastructure, not operated by this project
#     (The build-rig addresses that Review 2 P1 cited were redacted
#     by task 23; their allowlist pairs were removed 2026-10-20 when
#     the redaction landed, so the addresses appear nowhere in the
#     tree, this script included.)
#   /home/<user>/:
#     hatch    builder username (ISO-BUILD-LOG.md, stage1/logs/, and
#              embedded in the media-worker binary, itself PENDING
#              the owner's task 12 / P4 posture decision; the gssh
#              scripts' instances were removed by task 23)
#     user     the live system's own generic account, created by the build
#              (build/build-iso.sh: /home/user/.ssh/authorized_keys)
#     testuser throwaway guest account in the test drivers (build/*.py,
#              build/calamares-session-clean-install.log)
#     rig      guest account on the build rig in the prod drivers
#              (build/prod-*.py, build/s2con.py)
#   ELF:
#     onionhost/recipes/marketplace/files/media-worker — PENDING Review 2
#     task 12 / P4: prebuilt binary to be moved under archive/ or built
#     from a pinned source; allowlisted here only until that lands.
set -eu
ROOT=${1:-$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)}
exec python3 - "$ROOT" "$0" <<'PYEOF'
import ipaddress, os, re, shutil, subprocess, sys, tempfile

root = os.path.abspath(sys.argv[1])
self_path = os.path.abspath(sys.argv[2])

# (relative file glob, literal) allowlists — see header for reasons.
IP_ALLOW = [
    ("ISO-BUILD-LOG.md", "192.71.80.206"),
]
HOME_ALLOW = [
    ("ISO-BUILD-LOG.md", "hatch"),
    ("stage1/logs/*", "hatch"),
    ("onionhost/recipes/marketplace/files/media-worker", "hatch"),
    ("build/build-iso.sh", "user"),
    ("build/*.py", "testuser"),
    ("build/calamares-session-clean-install.log", "testuser"),
    ("build/prod-*.py", "rig"), ("build/s2con.py", "rig"),
]
ELF_ALLOW = {"onionhost/recipes/marketplace/files/media-worker"}
# Exact (file glob, space-joined lower-case run) pairs for the EFF
# phrase rule — same exact-pair mechanism as IP_ALLOW / HOME_ALLOW:
# an allowlisted run in any OTHER file is still a finding. Starts
# empty: every run of >= 5 wordlist words in a line pair is reported.
# Adjudicated 2026-10-20 (Repo Review 3 fix batch): the 53 pairs
# below are the detector's full first-run output on this tree.
# Each was read in context and is ordinary prose, source-code
# identifier chains (e.g. wizard.py's HTML attribute words), or
# a library string table inside the media-worker binary - none
# is a generated passphrase. A real phrase set anywhere else
# (or any new run in these files) still trips the rule.
PHRASE_ALLOW = [
    ("DESIGN-v3-amendments.md", "clean active active shape operator"),
    ("DESIGN-v3-amendments.md", "onion service client only posture outbound"),
    ("DESIGN-v3-amendments.md", "only clean active active shape operator"),
    ("FIX-BRIEF-ENCRYPTION-GUARD-2026-10-12.md", "battery stays green manual path manual"),
    ("ISO-BUILD-LOG.md", "attempt proved disk phrase throwaway"),
    ("ISO-BUILD-LOG.md", "body visible reply posted visible"),
    ("ISO-BUILD-LOG.md", "concept concept budget stays five"),
    ("ISO-BUILD-LOG.md", "never arose net user visible"),
    ("ISO-BUILD-LOG.md", "refusal path stays clean task wizard helper"),
    ("ISO-BUILD-LOG.md", "sandbox state machine proofs task"),
    ("ISO-BUILD-LOG.md", "shell false correct phrase boots"),
    ("ISO-BUILD-LOG.md", "slot reboot battery old phrase"),
    ("ISO-BUILD-LOG.md", "that fetch path external avatar"),
    ("ISO-BUILD-LOG.md", "wizard helper probe status probe onion"),
    ("REVIEW-PACK-for-claude-opus.md", "security update container image upstream"),
    ("TEST-PLAN.md", "only machine plus external security"),
    ("TIMING-REVIEW-2-2026-10-11.md", "public outage feed cost hardware"),
    ("WALKTHROUGH-SPEC-v1.md", "anywhere open editor screen detail"),
    ("build/boottest-slice2.py", "stable screen print screen stable"),
    ("build/build-iso.sh", "echo release status release status echo"),
    ("build/build-iso.sh", "probe echo release status release status"),
    ("build/qemu-drive.py", "name status print running running"),
    ("build/qemu-drive3.py", "name status print running running"),
    ("onionhost/calamares/plugin-src/onionhostphrase/OnionHostPhraseViewStep.cpp", "delete item widget delete item"),
    ("onionhost/recipes/marketplace/files/media-worker", "cannot decode bogus vertical sampling factor"),
    ("onionhost/rootfs-overlay/usr/lib/apt/methods/tor+http", "self length left self length"),
    ("onionhost/rootfs-overlay/usr/lib/onionhost/backupkeys.py", "empty phrase return hash secret"),
    ("onionhost/rootfs-overlay/usr/lib/onionhost/backupkeys.py", "identity phrase salt return identity"),
    ("onionhost/rootfs-overlay/usr/lib/onionhost/backupkeys.py", "recipient phrase salt return recipient"),
    ("onionhost/rootfs-overlay/usr/lib/onionhost/golden/app-init.sh", "data data native data native"),
    ("onionhost/rootfs-overlay/usr/lib/onionhost/sitegen.py", "return value value value replace"),
    ("onionhost/rootfs-overlay/usr/lib/onionhost/wizard.py", "delete selected self self capture"),
    ("onionhost/rootfs-overlay/usr/lib/onionhost/wizard.py", "font self body font anchor"),
    ("onionhost/rootfs-overlay/usr/lib/onionhost/wizard.py", "font self body font self"),
    ("onionhost/rootfs-overlay/usr/lib/onionhost/wizard.py", "font self body font width"),
    ("onionhost/rootfs-overlay/usr/lib/onionhost/wizard.py", "font self body font width anchor"),
    ("onionhost/rootfs-overlay/usr/lib/onionhost/wizard.py", "font self word font anchor"),
    ("onionhost/rootfs-overlay/usr/lib/onionhost/wizard.py", "item photo self pending photo"),
    ("onionhost/rootfs-overlay/usr/lib/onionhost/wizard.py", "name font self body font anchor"),
    ("onionhost/rootfs-overlay/usr/lib/onionhost/wizard.py", "photo self self pending photo"),
    ("onionhost/rootfs-overlay/usr/lib/onionhost/wizard.py", "progress self progress self clear"),
    ("onionhost/rootfs-overlay/usr/lib/onionhost/wizard.py", "return self pending photo name"),
    ("onionhost/rootfs-overlay/usr/lib/onionhost/wizard.py", "return self progress step editor"),
    ("onionhost/rootfs-overlay/usr/lib/onionhost/wizard.py", "selected delete self delete selected"),
    ("onionhost/rootfs-overlay/usr/lib/onionhost/wizard.py", "self pending photo name self update photo"),
    ("onionhost/rootfs-overlay/usr/lib/onionhost/wizard.py", "self pending photo self photo"),
    ("onionhost/rootfs-overlay/usr/local/bin/onionhost-recipe", "image proxy secret image proxy secret"),
    ("onionhost/rootfs-overlay/usr/local/bin/onionhost-recipe", "value return value replace replace"),
    ("onionhost/rootfs-overlay/usr/local/bin/onionhost-recipe", "whole state coherent written directly"),
    ("onionhost/rootfs-overlay/usr/local/bin/onionhost-restore", "target tag replace directory target"),
    ("poc/POC-RESULTS.md", "storage overlay driver unusable overlay"),
    ("stage1/run-deferred-gates.sh", "stopped disk cost only running"),
    # Adjudicated 2026-10-20 (Repo Review 4 fix batch, task 4): the
    # 29 pairs below are the 3-word secret-context rule's full first
    # run on this tree. Each was read in context. Segment-context
    # pairs are short quoted/bracketed prose or code fragments
    # (headings, a place name, shell/SQL/Python strings and call
    # sites, parenthetical asides) and trigger-context pairs are
    # ordinary sentences that happen to follow a trigger word —
    # including the build log's own redaction markers. None is a
    # generated passphrase. The one real 3-word login phrase the
    # rule was written for (ISO-BUILD-LOG.md, Part 3 section) is
    # NOT allowlisted: it was redacted under task 1 of the same
    # batch. A real phrase set anywhere else (or any new run in
    # these files) still trips the rule.
    ("ISO-BUILD-LOG.md", "concept budget stays five"),
    ("ISO-BUILD-LOG.md", "native cold copy"),
    ("ISO-BUILD-LOG.md", "phrase boots treat"),
    ("ISO-BUILD-LOG.md", "phrase phrase removed"),
    ("ISO-BUILD-LOG.md", "private halves only"),
    ("ISO-BUILD-LOG.md", "single apply path"),
    ("ISO-BUILD-LOG.md", "skeleton password onion"),
    ("LEGAL-INTAKE-DRAFTS-v2-2026-10-17.md", "publisher posture half"),
    ("LEGAL-INTAKE-DRAFTS.md", "publisher posture half"),
    ("STAGE1-RIG-SETUP.md", "salt lake city"),
    ("TEST-PLAN.md", "salt lake city"),
    ("build/boottest-slice2.py", "user phrase greeter"),
    ("build/build-iso.sh", "release status release status"),
    ("build/s5b-analyze.py", "phrase identity good"),
    ("onionhost/calamares/modules/onionhostbootkey/main.py", "copied onto paper"),
    ("onionhost/recipes/marketplace/files/migrations/0003_listing_category.sql", "operator facing browse filter"),
    ("onionhost/rootfs-overlay/usr/lib/onionhost/backupkeys.py", "alone suffice phrase"),
    ("onionhost/rootfs-overlay/usr/lib/onionhost/wizard.py", "delete self delete selected"),
    ("onionhost/rootfs-overlay/usr/lib/onionhost/wizard.py", "update status path"),
    ("onionhost/rootfs-overlay/usr/lib/onionhost/wizard.py", "widget cut false"),
    ("onionhost/rootfs-overlay/usr/local/bin/onionhost-publish", "old release untouched"),
    ("onionhost/rootfs-overlay/usr/local/bin/onionhost-recipe", "image proxy secret"),
    ("onionhost/rootfs-overlay/usr/local/bin/onionhost-restore", "setup never finished"),
    ("onionhost/rootfs-overlay/usr/local/bin/onionhost-restore", "stage filter data"),
    ("onionhost/rootfs-overlay/usr/local/bin/onionhost-restore", "stage onion name"),
    ("outreach/TESTER-SESSION-KIT-v1.md", "onto paper keep"),
    ("poc/runtime-gate/run_sim.py", "clear latch removed"),
    ("stage1/SESSION-CHECKLIST.md", "salt lake city"),
    ("stage1/run-deferred-gates.sh", "cost only running"),
    # Adjudicated 2026-10-20 (Repo Review 4 fix batch, task 4): the
    # log's Review 4 correction note (finding P10) describing the
    # new 3-word rule in its own words — ordinary prose about the
    # scanner, spanning a line break; not a generated phrase.
    ("ISO-BUILD-LOG.md", "word secret context scanner rule"),
]
WORDLIST_REL = "onionhost/rootfs-overlay/usr/share/onionhost/eff-large-wordlist.txt"

def load_eff_words():
    # Wordlist rows are "<dice-number>\t<word>"; use the word column.
    # Resolve relative to the scanned tree. If the list is absent the
    # set comes back empty and the caller turns that into a hard
    # failure (Review 4, P15): a scan that cannot run its phrase
    # rules must never report PASS.
    words = set()
    try:
        fh = open(os.path.join(root, WORDLIST_REL),
                  encoding="utf-8", errors="replace")
    except OSError:
        return words
    with fh:
        for line in fh:
            parts = line.split()
            if parts:
                words.add(parts[-1].lower().encode())
    return words

EFF_WORDS = load_eff_words()
WORD_TOKEN_RE = re.compile(rb"[A-Za-z]+")

def allowed(pairs, rel, literal):
    import fnmatch
    return any(fnmatch.fnmatch(rel, pat) and lit == literal
               for pat, lit in pairs)

def file_list():
    if os.path.isdir(os.path.join(root, ".git")):
        out = subprocess.run(
            ["git", "-C", root, "ls-files", "-co", "--exclude-standard", "-z"],
            check=True, capture_output=True).stdout
        return [p.decode("utf-8", "surrogateescape")
                for p in out.split(b"\0") if p]
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        if ".git" in dirnames:
            dirnames.remove(".git")
        for name in filenames:
            found.append(os.path.relpath(os.path.join(dirpath, name), root))
    return sorted(found)

KEY_PATTERNS = [
    ("private-key header (PEM/OpenSSH/PGP)",
     re.compile(rb"-----BEGIN [A-Z0-9 ]*PRIVATE KEY( BLOCK)?-----")),
    ("OpenSSH private-key magic (openssh-key-v1)",
     re.compile(rb"openssh-key-v1\x00")),
    ("Tor secret key header (ed25519v1-secret)",
     re.compile(rb"ed25519v1-secret")),
    # Age secret identity (Review 4, P15): literal prefix plus a long
    # contiguous run of bech32 characters. A complete identity has 58
    # characters after the prefix; 44+ also catches a near-complete
    # copy. The backupkeys.py regression vector is split across two
    # adjacent string literals, so no contiguous run in that file
    # reaches this threshold, and its docstring/startswith mentions
    # carry no run at all.
    ("age secret identity (AGE-SECRET-KEY-1...)",
     re.compile(rb"AGE-SECRET-KEY-1[A-Z0-9]{44,}")),
]
IP_RE = re.compile(rb"\b(?:\d{1,3}\.){3}\d{1,3}\b")
HOME_RE = re.compile(rb"/home/([A-Za-z0-9_.-]+)/")

findings = []
if not EFF_WORDS:
    # Missing/empty wordlist: the phrase rules below cannot run, so
    # this scan must not PASS (Review 4, P15 / task 6).
    findings.append(
        "%s: EFF wordlist missing or empty — phrase rules cannot "
        "run; refusing to PASS" % WORDLIST_REL)
scanned = 0
files = file_list()
for rel in files:
    path = os.path.join(root, rel)
    if os.path.abspath(path) == self_path or not os.path.isfile(path):
        continue
    scanned += 1
    with open(path, "rb") as fh:
        data = fh.read()
    if data[:4] == b"\x7fELF":
        parts = rel.split("/")
        if "archive" not in parts and rel not in ELF_ALLOW:
            findings.append("%s: ELF binary outside archive/" % rel)
    for label, pat in KEY_PATTERNS:
        for m in pat.finditer(data):
            line = data.count(b"\n", 0, m.start()) + 1
            findings.append("%s:%d: %s" % (rel, line, label))
    for m in IP_RE.finditer(data):
        text = m.group().decode()
        try:
            ip = ipaddress.IPv4Address(text)
        except ValueError:
            continue  # e.g. version strings with an octet > 255
        # Not a finding: non-global space (private, reserved, shared,
        # multicast, 0.0.0.0/8 version lookalikes) and CIDR network
        # addresses (immediately followed by "/prefix", e.g. the nft
        # bogon set 224.0.0.0/4).
        if not ip.is_global or ip.is_multicast or ip.is_reserved \
                or ip.is_unspecified:
            continue
        # A following "/" counts as CIDR notation only when it
        # introduces a 1-2 digit prefix length (e.g. 203.0.113.0/24)
        # AND the address is not part of a URL (not immediately
        # preceded by "://"). "http://203.0.113.9/x" and
        # "203.0.113.9/path" are findings, not networks.
        after = data[m.end():m.end() + 4]
        if after[:1] == b"/" \
                and data[max(0, m.start() - 3):m.start()] != b"://":
            if re.match(rb"/(\d{1,2})(?!\d)", after):
                continue
        if allowed(IP_ALLOW, rel, text):
            continue
        line = data.count(b"\n", 0, m.start()) + 1
        findings.append("%s:%d: non-allowlisted public IPv4 %s"
                        % (rel, line, text))
    for m in HOME_RE.finditer(data):
        user = m.group(1).decode()
        if allowed(HOME_ALLOW, rel, user):
            continue
        line = data.count(b"\n", 0, m.start()) + 1
        findings.append("%s:%d: /home/%s/ path" % (rel, line, user))
    if EFF_WORDS:
        # Passphrase rule: >= 5 consecutive EFF-wordlist words within
        # a line pair (this line plus the next). Tokens keep their
        # line numbers so a run found via two overlapping pairs is
        # reported once.
        line_tokens = [[tok.lower() for tok in WORD_TOKEN_RE.findall(ln)]
                       for ln in data.split(b"\n")]
        reported = set()
        for i in range(len(line_tokens)):
            pair = [(w, i + 1) for w in line_tokens[i]]
            if i + 1 < len(line_tokens):
                pair += [(w, i + 2) for w in line_tokens[i + 1]]
            run = []
            for word, lineno in pair + [(None, None)]:
                if word is not None and word in EFF_WORDS:
                    run.append((word, lineno))
                    continue
                if len(run) >= 5:
                    phrase = b" ".join(w for w, _ in run).decode()
                    key = (run[0][1], run[-1][1], phrase)
                    if key not in reported:
                        reported.add(key)
                        if not allowed(PHRASE_ALLOW, rel, phrase):
                            findings.append(
                                "%s:%d: EFF wordlist phrase-like run "
                                "(%d words): %s"
                                % (rel, run[0][1], len(run), phrase))
                run = []
        # 3-word rule (Review 4, P15 / task 4): login phrases are
        # three words, invisible to the >= 5 rule. A run of exactly
        # three consecutive EFF-wordlist words is a finding only in
        # secret context, per line:
        #   (a) it immediately follows a trigger word (login, spare,
        #       disk or phrase, case-insensitive), or
        #   (b) it is the entire word content of a short quoted or
        #       bracketed segment — a phrase as it is displayed or
        #       logged, set off from surrounding prose; the segment
        #       holds 3-8 words and every word is in the wordlist.
        # Same exact-pair allowlist as the 5-word rule.
        triggers = {b"login", b"spare", b"disk", b"phrase"}
        seg_re = re.compile(
            rb'"([^"\n]{1,120})"|' rb"'([^\'\n]{1,120})'"
            rb"|\(([^()\n]{1,120})\)|\[([^\[\]\n]{1,120})\]")
        reported3 = set()
        for lineno0, raw_line in enumerate(data.split(b"\n")):
            toks = [t.lower() for t in WORD_TOKEN_RE.findall(raw_line)]
            runs3 = []
            for i, tok in enumerate(toks):
                if tok in triggers:
                    nxt = toks[i + 1:i + 4]
                    if len(nxt) == 3 and \
                            all(w in EFF_WORDS for w in nxt):
                        runs3.append(b" ".join(nxt).decode())
            for m in seg_re.finditer(raw_line):
                seg = next(g for g in m.groups() if g is not None)
                stoks = [t.lower()
                         for t in WORD_TOKEN_RE.findall(seg)]
                if 3 <= len(stoks) <= 8 and \
                        all(w in EFF_WORDS for w in stoks):
                    runs3.append(b" ".join(stoks).decode())
            for run3 in runs3:
                key = (lineno0 + 1, run3)
                if key in reported3:
                    continue
                reported3.add(key)
                if not allowed(PHRASE_ALLOW, rel, run3):
                    findings.append(
                        "%s:%d: EFF wordlist 3-word phrase-like run "
                        "in secret context: %s"
                        % (rel, lineno0 + 1, run3))

# Public-only key check. Every *.gpg file in the committable set
# must be public-only key material: list it with gpg and reject any
# sec/ssb (secret key / secret subkey) record. The same check runs
# on any other committable file whose first byte is an OpenPGP
# secret-key packet header — packet tag 5 in old format (0x94-0x97,
# by length type) or new format (0xC5) — so a binary secret-key
# export renamed to e.g. .pgp, .kbx or .sec cannot slip past by
# extension alone (Review 4, P15 / task 5). A throwaway homedir
# keeps the check from touching the caller's own keyring or
# trustdb. If gpg is absent, or gpg fails on a candidate file, that
# is a finding, not a silent skip (Review 4, P15 / task 6).
SECRET_KEY_FIRST_BYTES = {b"\x94", b"\x95", b"\x96", b"\x97", b"\xc5"}
gpg_bin = shutil.which("gpg")
if not gpg_bin:
    findings.append(
        "gpg not found on PATH — public-only GPG check cannot "
        "run; refusing to PASS")
else:
    gpg_home = tempfile.mkdtemp(prefix="ci-scan-gpg-")
    try:
        for rel in files:
            path = os.path.join(root, rel)
            if os.path.abspath(path) == self_path or not os.path.isfile(path):
                continue
            is_gpg_name = rel.endswith(".gpg")
            if not is_gpg_name:
                with open(path, "rb") as fh:
                    if fh.read(1) not in SECRET_KEY_FIRST_BYTES:
                        continue
            try:
                out = subprocess.run(
                    [gpg_bin, "--batch", "--homedir", gpg_home,
                     "--show-keys", "--with-colons", path],
                    capture_output=True, timeout=60)
            except (OSError, subprocess.SubprocessError) as exc:
                findings.append(
                    "%s: gpg --show-keys could not run (%s) — "
                    "cannot verify public-only key material"
                    % (rel, exc.__class__.__name__))
                continue
            if out.returncode != 0:
                findings.append(
                    "%s: gpg --show-keys failed (exit %d) — cannot "
                    "verify public-only key material"
                    % (rel, out.returncode))
                continue
            secret_kinds = []
            for record in out.stdout.decode("utf-8", "replace").splitlines():
                kind = record.split(":", 1)[0]
                if kind in ("sec", "ssb"):
                    secret_kinds.append(kind)
                    findings.append(
                        "%s: GPG secret key material (%s record) "
                        "in key file" % (rel, kind))
            if not is_gpg_name and not secret_kinds:
                # First packet claims tag 5 (secret key) yet gpg
                # listed no secret record: the header alone fails
                # the public-only rule for a non-*.gpg name.
                findings.append(
                    "%s: OpenPGP secret-key packet header (tag 5) "
                    "in non-*.gpg file" % rel)
    finally:
        shutil.rmtree(gpg_home, ignore_errors=True)

if findings:
    print("ci-scan: FAIL (%d finding(s)):" % len(findings))
    for f in findings:
        print("  " + f)
    sys.exit(1)
print("ci-scan: PASS (%d files scanned under %s)" % (scanned, root))
PYEOF

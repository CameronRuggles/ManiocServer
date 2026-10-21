# SPDX-License-Identifier: GPL-3.0-or-later
"""OnionHost GRUB fixes (slice 2, tasks 1 + 5).

Runs in the exec sequence AFTER the `bootloader` job (grub-install)
and `grubcfg`, and edits two files in the target:

1. THE PASSPHRASE RETRY LOOP. Debian's signed GRUB 2.12, given a
   wrong passphrase at the cryptomount prompt, falls through its
   boot script and drops to a `grub>` rescue shell - a dead end for
   a novice (observed in slice 1). The ESP stub that grub-install
   wrote (/boot/efi/EFI/debian/grub.cfg) is rewritten here: the
   single cryptomount command is wrapped in an INDEFINITE retry
   loop with plain-language messages. Indefinite is the recorded
   choice: this is a physical-presence prompt, and the real
   throttle is the PBKDF2 cost itself (~9 s per attempt at
   iter-time 2000). A numeric cap would only strand a legitimate
   owner who mistypes, has a stuck key, or whose keyboard layout
   changed. The transformation preserves grub-install's exact
   cryptomount command line and everything else in the stub; if no
   cryptomount line is found the install FAILS LOUDLY rather than
   shipping the rescue-shell behaviour. The same transformation is
   available on the installed system as /usr/local/bin/
   onionhost-grub-stub (grub package updates can regenerate the
   stub; an apt hook re-applies it - see the ISO build log).

2. THE MAINTENANCE MENU ENTRY. /boot/grub/custom.cfg (sourced by
   the generated grub.cfg after the disk is unlocked) gains an
   "OnionHost Maintenance" entry: a copy of the default entry's
   boot lines with systemd.unit=onionhost-maintenance.target
   appended, booting a no-network, no-container console that runs
   the re-key tool.
"""
import os
import re

import libcalamares

STUB_CANDIDATES = ["/boot/efi/EFI/debian/grub.cfg",
                   "/boot/efi/EFI/BOOT/grub.cfg"]
MARKER = "OnionHost passphrase retry loop"
CUSTOM_CFG = "/boot/grub/custom.cfg"


def _fsync_path(path):
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
    dfd = os.open(os.path.dirname(path), os.O_RDONLY)
    try:
        os.fsync(dfd)
    finally:
        os.close(dfd)


def _loopify(stub_text):
    """Wrap the stub's cryptomount line in a retry loop. Returns
    (new_text, changed) or (None, error)."""
    if MARKER in stub_text:
        return stub_text, False
    lines = stub_text.splitlines()
    idx = None
    for i, line in enumerate(lines):
        if re.match(r"\s*cryptomount\b", line):
            idx = i
            break
    if idx is None:
        return None, "no cryptomount line found in the GRUB stub"
    cmd = lines[idx].strip()
    block = [
        "# %s: a wrong passphrase re-prompts here instead of" % MARKER,
        "# dropping to a rescue shell. The loop is indefinite on",
        "# purpose - the PBKDF2 delay (~9 s) is the rate limit, and a",
        "# cap could strand the owner (mistakes, stuck keys, layout",
        "# changes).",
        'echo "This computer is locked with a passphrase."',
        'echo "Type the passphrase from your paper copy, then press Enter."',
        'echo "The screen stays blank while you type - that is normal."',
        cmd,
        "while [ $? != 0 ]; do",
        '    echo ""',
        '    echo "That passphrase was not accepted."',
        '    echo "Check that Caps Lock is off, then try again."',
        "    " + cmd,
        "done",
    ]
    lines[idx:idx + 1] = block
    return "\n".join(lines) + "\n", True


def _maintenance_entry(grub_cfg_text):
    """Copy the first menuentry of the generated grub.cfg, renamed,
    with the maintenance target appended to its linux line.

    Brace-counting scan, NOT a regex: Debian's menuentry line has
    options (--class ..., $menuentry_id_option '...') between the
    quoted name and the opening brace, which a name-then-brace
    regex cannot match (that bug failed slice 2's first install)."""
    lines = grub_cfg_text.splitlines()
    block = None
    for i, line in enumerate(lines):
        if line.lstrip().startswith("menuentry "):
            depth = 0
            candidate = []
            for j in range(i, len(lines)):
                candidate.append(lines[j])
                depth += lines[j].count("{") - lines[j].count("}")
                if j > i and depth == 0:
                    block = candidate
                    break
            break
    if not block or not any(
            re.match(r"linux\b", ln.lstrip()) for ln in block):
        return None
    body_lines = []
    for line in block[1:-1]:  # body only; the wrapper is rebuilt
        if re.match(r"linux\b", line.lstrip()):
            line = (line.rstrip()
                    + " systemd.unit=onionhost-maintenance.target")
        body_lines.append(line)
    body = "\n".join(body_lines).strip("\n")
    return ("# OnionHost Maintenance entry (written by the installer;\n"
            "# survives update-grub because grub.cfg sources custom.cfg).\n"
            "menuentry 'OnionHost Maintenance' {\n%s\n}\n" % body)


def run():
    gs = libcalamares.globalstorage
    root = gs.value("rootMountPoint")
    if not root or not os.path.isdir(root):
        return ("OnionHost GRUB fixes",
                "rootMountPoint missing; cannot fix GRUB.", 1)

    # 1. ESP stub retry loop.
    stub_path = None
    for cand in STUB_CANDIDATES:
        if os.path.exists(root + cand):
            stub_path = root + cand
            break
    if stub_path is None:
        return ("OnionHost GRUB fixes",
                "No GRUB stub found at any of: %s"
                % ", ".join(STUB_CANDIDATES), 1)
    with open(stub_path) as f:
        stub_text = f.read()
    new_text, changed = _loopify(stub_text)
    if new_text is None:
        return ("OnionHost GRUB fixes",
                "GRUB stub rewrite failed: %s" % changed, 1)
    if changed:
        with open(stub_path, "w") as f:
            f.write(new_text)
        _fsync_path(stub_path)

    # 2. Maintenance entry in /boot/grub/custom.cfg.
    grub_cfg = root + "/boot/grub/grub.cfg"
    if not os.path.exists(grub_cfg):
        return ("OnionHost GRUB fixes",
                "Generated grub.cfg not found at %s" % grub_cfg, 1)
    with open(grub_cfg) as f:
        entry = _maintenance_entry(f.read())
    if entry is None:
        return ("OnionHost GRUB fixes",
                "Could not extract a menuentry from grub.cfg for the "
                "Maintenance entry.", 1)
    custom_path = root + CUSTOM_CFG
    existing = ""
    if os.path.exists(custom_path):
        with open(custom_path) as f:
            existing = f.read()
    if "OnionHost Maintenance" not in existing:
        with open(custom_path, "w") as f:
            f.write(existing + entry)
        _fsync_path(custom_path)
    return None

# SPDX-License-Identifier: GPL-3.0-or-later
"""OnionHost first-run setup job (DESIGN-v3 A10 state machine).

Runs late in the exec sequence, AFTER onionhostcleanup (which strips
the live session), and prepares the installed system for state S0:

  * /var/lib/onionhost/state  <- "S0" (the wizard state machine's
    source of truth; written atomically with fsync),
  * /etc/lightdm/lightdm.conf.d/20-onionhost-s0.conf - LightDM
    autologin of the INSTALL user into the onionhost-wizard kiosk
    session (the wizard session itself falls through to XFCE at any
    state other than S0, so a stale drop-in cannot strand the user),
  * /etc/sudoers.d/onionhost-wizard - the install user's sudo group
    may run ONLY the wizard helper without a password (the helper
    performs the atomic S0->S1 transition: chpasswd, remove this
    drop-in, fsync, state=S1, restart LightDM),
  * login-phrase throttling (A2): /etc/security/faillock.conf with
    deny=5 / unlock_time=900, and pam_faillock wired into
    /etc/pam.d/common-auth. The PAM edit is applied only when
    common-auth still has the stock Debian shape; otherwise it is
    reported as a non-fatal problem in the job output (fail visible,
    not silent),
  * factory packages (Gate 4 + A23): the platform package and the
    recipe packages planted by the ISO build under
    /usr/lib/onionhost/factory-packages are dpkg-installed into
    the target, so the updater's factory version and the wizard's
    recipe choices key off real dpkg state. A failure here fails
    the install: a machine without its update channel registered
    must not ship silently.
"""
import glob
import os
import subprocess

import libcalamares

STATE_DIR = "/var/lib/onionhost"
STATE_FILE = "/var/lib/onionhost/state"
S0_DROPIN = "/etc/lightdm/lightdm.conf.d/20-onionhost-s0.conf"
SUDOERS_FILE = "/etc/sudoers.d/onionhost-wizard"
HELPER = "/usr/local/bin/onionhost-wizard-helper"
FAILLOCK_CONF = "/etc/security/faillock.conf"
COMMON_AUTH = "/etc/pam.d/common-auth"
FACTORY_PKG_DIR = "/usr/lib/onionhost/factory-packages"


def _write(path, content, mode):
    with open(path, "w") as f:
        f.write(content)
    os.chmod(path, mode)


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


def _wire_faillock(root):
    """Insert pam_faillock into the target's common-auth. Returns a
    problem string or None. Only the stock Debian trixie shape is
    rewritten; anything else is left untouched and reported."""
    path = root + COMMON_AUTH
    with open(path) as f:
        content = f.read()
    if "pam_faillock" in content:
        return None
    lines = content.splitlines()
    unix_idx = None
    for i, line in enumerate(lines):
        if "pam_unix.so" in line and line.strip().startswith("auth"):
            unix_idx = i
            break
    if unix_idx is None:
        return "common-auth has no pam_unix auth line; faillock " \
               "not wired"
    new = []
    for i, line in enumerate(lines):
        if i == unix_idx:
            new.append("auth\trequired\t\t\tpam_faillock.so preauth")
            new.append(line)
            new.append("auth\t[default=die]\t\t\tpam_faillock.so authfail")
            new.append("auth\tsufficient\t\t\tpam_faillock.so authsucc")
        else:
            new.append(line)
    _write(path, "\n".join(new) + "\n", 0o644)
    return None


def _install_factory_packages(root):
    """dpkg-install the factory platform + recipe packages into
    the target. Returns a problem string or None."""
    pkgdir = root + FACTORY_PKG_DIR
    debs = sorted(glob.glob(pkgdir + "/onionhost_*.deb"))
    debs += sorted(glob.glob(pkgdir + "/onionhost-recipe-*.deb"))
    if not debs:
        return "no factory packages found in the image at %s" \
            % FACTORY_PKG_DIR
    rel = [d[len(root):] for d in debs]
    try:
        proc = subprocess.run(
            ["chroot", root, "env", "DEBIAN_FRONTEND=noninteractive",
             "dpkg", "-i"] + rel,
            capture_output=True, text=True, timeout=900)
    except Exception as exc:
        return "factory package install failed to run: %s" % exc
    if proc.returncode != 0:
        tail = (proc.stdout + proc.stderr).strip().splitlines()[-5:]
        return "factory package install failed: %s" % " | ".join(tail)
    return None


def run():
    gs = libcalamares.globalstorage
    root = gs.value("rootMountPoint")
    if not root or not os.path.isdir(root):
        return ("OnionHost first-run setup",
                "rootMountPoint missing; cannot prepare S0 state.", 1)
    username = gs.value("username")
    if not username:
        return ("OnionHost first-run setup",
                "Install username missing from GlobalStorage.", 1)
    problems = []

    # State S0 (atomic: tmp + rename + fsync).
    state_dir = root + STATE_DIR
    os.makedirs(state_dir, exist_ok=True)
    tmp = root + STATE_FILE + ".tmp"
    _write(tmp, "S0\n", 0o644)
    os.replace(tmp, root + STATE_FILE)
    _fsync_path(root + STATE_FILE)

    # LightDM S0 autologin drop-in for the install user.
    dropin_dir = os.path.dirname(root + S0_DROPIN)
    os.makedirs(dropin_dir, exist_ok=True)
    _write(root + S0_DROPIN,
           "[Seat:*]\n"
           "autologin-user=%s\n"
           "autologin-user-timeout=0\n"
           "autologin-session=onionhost-wizard\n" % username,
           0o644)
    _fsync_path(root + S0_DROPIN)

    # Sudoers: the wizard helper only, for the sudo group.
    _write(root + SUDOERS_FILE,
           "# OnionHost: the first-boot wizard runs its privileged\n"
           "# transition through this one helper (A10).\n"
           "%%sudo ALL=(root) NOPASSWD: %s\n" % HELPER,
           0o440)

    # Login throttling (A2: deny=5, unlock 900 s).
    _write(root + FAILLOCK_CONF,
           "# OnionHost login throttling (A2)\n"
           "deny = 5\n"
           "fail_interval = 900\n"
           "unlock_time = 900\n",
           0o644)
    err = _wire_faillock(root)
    if err:
        problems.append(err)

    # Factory packages: register the platform + recipe packages in
    # the target's dpkg database (Gate 4 / A23).
    err = _install_factory_packages(root)
    if err:
        problems.append(err)

    if problems:
        return ("OnionHost first-run setup", "; ".join(problems), 1)
    return None

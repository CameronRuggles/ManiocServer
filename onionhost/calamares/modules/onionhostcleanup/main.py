# SPDX-License-Identifier: GPL-3.0-or-later
"""OnionHost cleanup jobmodule: strip live-session test scaffolding
from the INSTALLED target (ISO-BUILD-LOG step-3 blocker #2).

The live image needs a pre-created live user, LightDM autologin, and
(in the test flavour) sshd + authorized_keys + xdotool for rig
automation. Calamares copies the live filesystem to the target, so
without this job ALL of that lands in the installed system (verified
on the skeleton: the installed system autologged into the live user
account and carried the operator pubkey).

Runs late in the exec sequence (after packages, before initramfscfg)
and edits only the target (GlobalStorage rootMountPoint):
  * A19.1 keyfile relocation: Calamares' luksbootkeyfile leaves a
    random keyfile at /crypto_keyfile.bin and the fstab job points
    crypttab at it. Move it to /etc/cryptsetup-keys.d/root.key
    (dir 0700 root:root, file 0400 root:root), rewrite the crypttab
    reference to the exact new path, and set UMASK=0077 in
    initramfs.conf. Hard failure if the keyfile or the crypttab
    reference is missing - this step lives here (not in
    onionhostbootkey) because crypttab is only written by the fstab
    job, which runs after luksbootkeyfile.
  * delete the live user and its home (userdel --remove, in chroot)
  * remove the LightDM autologin drop-in and un-set autologin in
    lightdm.conf -> the installed system boots to a real login
  * remove the test sshd drop-in, mask ssh.service, and purge the
    test-only packages (openssh-server, xdotool) if present
  * remove any authorized_keys left in target homes
Idempotent and best-effort per item, but a missing rootMountPoint is
a hard failure: silently skipping cleanup would ship test access.
"""
import os
import subprocess

import libcalamares

LIVE_USER = "user"
AUTOLOGIN_DROPIN = "/etc/lightdm/lightdm.conf.d/10-onionhost-live.conf"
SSHD_DROPIN = "/etc/ssh/sshd_config.d/10-onionhost-test.conf"
TEST_PACKAGES = ["openssh-server", "xdotool"]
OLD_KEYFILE = "/crypto_keyfile.bin"
KEYFILE_DIR = "/etc/cryptsetup-keys.d"
KEYFILE_NAME = "root.key"


def _relocate_keyfile(root):
    """A19.1 keyfile hygiene. Returns an error string or None."""
    old = root + OLD_KEYFILE
    if not os.path.exists(old):
        return "Calamares keyfile %s not found in target" % OLD_KEYFILE
    newdir = root + KEYFILE_DIR
    os.makedirs(newdir, exist_ok=True)
    os.chmod(newdir, 0o700)
    os.chown(newdir, 0, 0)
    new = newdir + "/" + KEYFILE_NAME
    os.replace(old, new)
    os.chown(new, 0, 0)
    os.chmod(new, 0o400)
    crypttab = os.path.join(root, "etc/crypttab")
    with open(crypttab) as f:
        content = f.read()
    if OLD_KEYFILE not in content:
        return "crypttab does not reference %s" % OLD_KEYFILE
    content = content.replace(OLD_KEYFILE,
                               KEYFILE_DIR + "/" + KEYFILE_NAME)
    with open(crypttab, "w") as f:
        f.write(content)
    conf = os.path.join(root, "etc/initramfs-tools/initramfs.conf")
    with open(conf) as f:
        lines = f.read().splitlines()
    lines = [l for l in lines if not l.strip().startswith("UMASK=")]
    lines.append("UMASK=0077")
    with open(conf, "w") as f:
        f.write("\n".join(lines) + "\n")
    return None


def _chroot(root, args, **kw):
    return subprocess.run(["chroot", root] + args,
                          capture_output=True, text=True, **kw)


def run():
    gs = libcalamares.globalstorage
    root = gs.value("rootMountPoint")
    if not root or not os.path.isdir(root):
        return ("OnionHost cleanup",
                "rootMountPoint missing; refusing to skip target "
                "cleanup.", 1)
    problems = []

    # 0. A19.1 keyfile relocation (hard failure: see docstring).
    err = _relocate_keyfile(root)
    if err:
        return ("OnionHost cleanup", err, 1)

    # 1. Live user + home.
    proc = _chroot(root, ["userdel", "--remove", LIVE_USER])
    if proc.returncode not in (0, 6):  # 6 = user does not exist
        problems.append("userdel: %s" % proc.stderr.strip()[:200])
    home = os.path.join(root, "home", LIVE_USER)
    if os.path.isdir(home):
        subprocess.run(["rm", "-rf", home])

    # 2. LightDM autologin must not survive into the installed system.
    dropin = root + AUTOLOGIN_DROPIN
    if os.path.exists(dropin):
        os.unlink(dropin)
    conf = os.path.join(root, "etc/lightdm/lightdm.conf")
    if os.path.exists(conf):
        with open(conf) as f:
            lines = f.read().splitlines()
        out = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("autologin-user=") or \
                    stripped.startswith("autologin-user-timeout="):
                out.append("#" + line)
            else:
                out.append(line)
        with open(conf, "w") as f:
            f.write("\n".join(out) + "\n")

    # 3. Test access: sshd drop-in, service, packages, stray keys.
    sshd_dropin = root + SSHD_DROPIN
    if os.path.exists(sshd_dropin):
        os.unlink(sshd_dropin)
    _chroot(root, ["systemctl", "mask", "ssh.service"])
    homes = os.path.join(root, "home")
    if os.path.isdir(homes):
        for entry in os.listdir(homes):
            ak = os.path.join(homes, entry, ".ssh", "authorized_keys")
            if os.path.exists(ak):
                os.unlink(ak)
    installed = []
    for pkg in TEST_PACKAGES:
        chk = _chroot(root, ["dpkg-query", "-W", "-f=${Status}", pkg])
        if "install ok installed" in chk.stdout:
            installed.append(pkg)
    if installed:
        env = dict(os.environ, DEBIAN_FRONTEND="noninteractive")
        proc = _chroot(root, ["apt-get", "purge", "-y"] + installed,
                       env=env)
        if proc.returncode != 0:
            problems.append("apt purge %s: %s"
                            % (installed, proc.stderr.strip()[:200]))

    if problems:
        return ("OnionHost cleanup", "; ".join(problems), 1)
    return None

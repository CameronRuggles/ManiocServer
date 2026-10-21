# SPDX-License-Identifier: GPL-3.0-or-later
"""OnionHost backup key derivation job (DESIGN-v3 A3).

Runs LAST in the OnionHost exec sequence (after onionhostfirstrun),
while the installer still holds the generated disk phrase in
GlobalStorage:

  1. Generate a per-install random salt (16 bytes, kernel CSPRNG)
     for the main phrase.
  2. Derive the age X25519 recipients:
         seed = argon2id(phrase, salt, t=3, m=64 MiB, p=1, 32)
     via /usr/lib/onionhost/backupkeys.py (pure-Python X25519 +
     bech32 on top of argon2-cffi; RFC 7748 vectors self-tested).
  3. PROVE the chain against the real `age` binary before writing
     anything: encrypt a probe string to the recipient, decrypt
     it back with the main-derived identity and compare
     byte-for-byte. A derivation that cannot round-trip fails the
     install loudly - a system whose backups can never be opened
     must not ship silently.
  4. Write /etc/onionhost/backup.json into the target:
         {"version": 1,
          "main":  {"salt": hex, "recipient": "age1..."}}
     Public data only (recipients + salts are not secret), mode
     0644. The private identities exist only in a 0700 tmpfs
     directory during the smoke test and are shredded in a finally
     block; phrases, seeds and identities are never logged.
"""
import json
import os
import subprocess
import sys
import tempfile

import libcalamares

sys.path.insert(0, "/usr/lib/onionhost")
import backupkeys  # noqa: E402

BACKUP_JSON = "/etc/onionhost/backup.json"


def _fail(msg):
    return ("OnionHost backup keys", msg, 1)


def _unobscure(value):
    """Inverse of Calamares::String::obscure (see onionhostbootkey)."""
    return "".join(ch if ord(ch) <= 0x21 else chr(0x1001F - ord(ch))
                   for ch in value)


def _fsync_file(path):
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


def _shred(path):
    try:
        size = os.path.getsize(path)
        with open(path, "wb") as f:
            f.write(os.urandom(size))
            f.flush()
            os.fsync(f.fileno())
        os.unlink(path)
    except OSError:
        pass


def _smoke_test(items):
    """items: [(role, phrase, salt)]. Encrypt one probe payload to
    all recipients, decrypt with EACH identity, compare. Raises
    RuntimeError on any failure."""
    recipients = [backupkeys.derive_recipient(p, s)
                  for _r, p, s in items]
    tmpdir = tempfile.mkdtemp(prefix="onionhost-backupkeys-",
                              dir="/dev/shm")
    os.chmod(tmpdir, 0o700)
    secret_files = []
    try:
        probe = os.path.join(tmpdir, "probe.txt")
        with open(probe, "wb") as f:
            f.write(b"onionhost backup key derivation probe\n")
        enc = os.path.join(tmpdir, "probe.age")
        cmd = ["age"]
        for r in recipients:
            cmd += ["-r", r]
        cmd += ["-o", enc, probe]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError("age encryption failed: %s"
                               % proc.stderr.strip()[:200])
        for role, phrase, salt in items:
            ident = os.path.join(tmpdir, "identity-%s" % role)
            secret_files.append(ident)
            with open(ident, "w") as f:
                f.write(backupkeys.derive_identity(phrase, salt)
                        + "\n")
            os.chmod(ident, 0o600)
            out = os.path.join(tmpdir, "out-%s" % role)
            proc = subprocess.run(
                ["age", "-d", "-i", ident, "-o", out, enc],
                capture_output=True, text=True)
            if proc.returncode != 0:
                raise RuntimeError(
                    "age decryption with the %s-derived identity "
                    "failed: %s" % (role, proc.stderr.strip()[:200]))
            with open(out, "rb") as f:
                data = f.read()
            with open(probe, "rb") as f:
                want = f.read()
            if data != want:
                raise RuntimeError(
                    "age round-trip mismatch for the %s-derived "
                    "identity" % role)
        return recipients
    finally:
        for path in secret_files:
            _shred(path)
        for name in os.listdir(tmpdir):
            _shred(os.path.join(tmpdir, name))
        try:
            os.rmdir(tmpdir)
        except OSError:
            pass


def run():
    gs = libcalamares.globalstorage
    root = gs.value("rootMountPoint")
    if not root or not os.path.isdir(root):
        return _fail("rootMountPoint missing; cannot derive the "
                     "backup keys.")
    generated = gs.value("onionhostGeneratedPhrase")
    stored = gs.value("luksPassphrase")
    if not generated or not stored:
        return _fail("Generated-phrase record missing from "
                     "GlobalStorage; cannot derive the backup keys.")
    phrase = _unobscure(generated)
    if _unobscure(stored) != phrase:
        return _fail("The disk passphrase is not the generated "
                     "phrase; refusing to derive backup keys from "
                     "an unverified phrase.")

    items = [("main", phrase, os.urandom(backupkeys.SALT_LEN))]

    try:
        recipients = _smoke_test(items)
    except Exception as e:  # noqa: BLE001 - fail the install loudly
        return _fail("Backup key derivation failed its self-test: "
                     "%s" % e)

    record = {"version": 1, "main": None}
    for (role, _p, salt), recipient in zip(items, recipients):
        record[role] = {"salt": salt.hex(), "recipient": recipient}
    path = root + BACKUP_JSON
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        f.write(json.dumps(record, indent=2, sort_keys=True) + "\n")
    os.chmod(tmp, 0o644)
    os.replace(tmp, path)
    _fsync_file(path)
    return None

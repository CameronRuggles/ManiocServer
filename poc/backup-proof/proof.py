#!/usr/bin/env python3
"""S12 proof harness for onionhost-backup (Review 3 task 19).

Fixture style follows the poc/recipes-* unit harnesses: product
paths redirected into a scratch tree, external tools (age,
systemctl) replaced by PATH shims, product module loaded
unmodified from the tree. Cases:
  clean        - known false positives (shadow.php, index.php)
                 admitted, backup produced
  tmp-skip     - appdata/www/cache/x.tmp skipped + reported
  secret       - appdata/native/.recipe-admin.env refuses,
                 plain language, no backup written
  secret-tmp   - appdata/native/recipe-admin.env.tmp refuses
                 the same way (named secret, NOT skipped)
  shadow-guard - a file actually named "shadow" still refuses
  outer-min    - format 3 (deanonymization audit R-04): the
                 plaintext outer layer carries neither the onion
                 address nor a creation time (no meta keys, no
                 nonzero tar mtimes), while the real restore
                 module still reads the wrapper and verifies the
                 payload, taking the address from the encrypted
                 manifest
"""
import contextlib
import gzip
import importlib.util
import io
import json
import os
import pwd as pwd_mod
import shutil
import sys
import tarfile
from collections import namedtuple

TREE = os.path.expanduser("~/workspace/onion-host-os")
LIB = os.path.join(TREE, "onionhost/rootfs-overlay/usr/lib/onionhost")
sys.path.insert(0, LIB)
import sitegen  # noqa: E402

from importlib.machinery import SourceFileLoader
spec = importlib.util.spec_from_loader(
    "onionhost_backup",
    SourceFileLoader(
        "onionhost_backup",
        os.path.join(TREE, "onionhost/rootfs-overlay/usr/local/bin/"
                           "onionhost-backup")))
bk = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bk)

ROOT = "/tmp/backup-proof"
os.environ["PATH"] = os.path.join(ROOT, "bin") + ":" + os.environ["PATH"]

Pw = namedtuple("Pw", "pw_name pw_passwd pw_uid pw_gid pw_gecos "
                      "pw_dir pw_shell")
_real_getpwnam = pwd_mod.getpwnam
passed = []


def check(name, cond):
    assert cond, "FAIL: %s" % name
    passed.append(name)
    print("PASS", name)


def build_fixture(case, plants):
    base = os.path.join(ROOT, "fx-" + case)
    shutil.rmtree(base, ignore_errors=True)
    home = os.path.join(base, "home")
    cfg = os.path.join(home, ".config", "onionhost")
    os.makedirs(cfg)
    model = sitegen.starter_model("app", runtime="native")
    model["title"] = "Proof Site"
    with open(os.path.join(cfg, "site.json"), "w") as f:
        json.dump(model, f)
    appdata = os.path.join(base, "appdata")
    files = {
        "www/index.php": "<?php // index\n",
        "www/wp-includes/block-supports/shadow.php": "<?php // wp\n",
        "native/app": "binary-bytes",
    }
    files.update(plants)
    for rel, data in files.items():
        p = os.path.join(appdata, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as f:
            f.write(data)
    hs = os.path.join(base, "hs")
    os.makedirs(hs)
    for name, data in (("hostname", "p" * 52 + "d.onion\n"),
                       ("hs_ed25519_secret_key", "secret"),
                       ("hs_ed25519_public_key", "public")):
        with open(os.path.join(hs, name), "w") as f:
            f.write(data)
    keys = os.path.join(base, "backup.json")
    with open(keys, "w") as f:
        json.dump({"main": {"recipient": "age1proofrecipient",
                            "salt": "00" * 16}}, f)
    state = os.path.join(base, "state")
    with open(state, "w") as f:
        f.write("S-state proof\n")
    outdir = os.path.join(base, "out")
    os.makedirs(outdir)
    # redirect the module's product paths into the fixture
    bk.BACKUP_KEYS = keys
    bk.SITE_DIR = os.path.join(base, "site")
    bk.HS_DIR = hs
    bk.STATE_FILE = state
    bk.APPDATA = appdata
    bk.APP_DB_ENV = os.path.join(base, "no-app-db.env")
    pwd_mod.getpwnam = lambda u: Pw("proof", "x", 0, 0, "", home, "/bin/sh")
    return os.path.join(outdir, case + ".onionhost-backup")


def run_backup(dest):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), \
            contextlib.redirect_stderr(err):
        rc = bk.create_backup("proof", dest)
    return rc, out.getvalue(), err.getvalue()


def read_manifest(dest):
    with tarfile.open(dest) as tar:
        payload = tar.extractfile("payload.age").read()
    with tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz") as tar:
        names = tar.getnames()
        manifest = json.load(tar.extractfile("manifest.json"))
    return names, manifest


def main():
    # (iii) clean fixture + false-positive guards admitted
    dest = build_fixture("clean", {})
    rc, out, err = run_backup(dest)
    check("clean: backup succeeds", rc == 0 and "BACKUP_OK" in out)
    check("clean: backup file written", os.path.isfile(dest))
    names, manifest = read_manifest(dest)
    paths = [e["path"] for e in manifest["entries"]]
    check("clean: shadow.php admitted",
          "app/www/wp-includes/block-supports/shadow.php" in paths)
    check("clean: index.php admitted", "app/www/index.php" in paths)
    check("clean: payload members present",
          any(n.startswith("app/") for n in names))
    check("clean: no skipped key", "skipped" not in manifest)

    # (i) planted appdata .tmp: skipped, listed, backup succeeds
    dest = build_fixture("tmp-skip", {"www/cache/x.tmp": "partial"})
    rc, out, err = run_backup(dest)
    check("tmp: backup succeeds", rc == 0 and "BACKUP_OK" in out)
    check("tmp: completion report names the skipped file",
          "BACKUP_SKIPPED path=app/www/cache/x.tmp" in out)
    names, manifest = read_manifest(dest)
    paths = [e["path"] for e in manifest["entries"]]
    check("tmp: archive omits x.tmp",
          "app/www/cache/x.tmp" not in paths
          and not any("x.tmp" in n for n in names))
    check("tmp: manifest skipped list names x.tmp",
          [s["path"] for s in manifest.get("skipped", [])]
          == ["app/www/cache/x.tmp"])
    check("tmp: other files still backed up",
          "app/www/index.php" in paths)

    # (ii) planted named secret: plain refusal, no backup
    dest = build_fixture("secret",
                         {"native/.recipe-admin.env": "PASSWORD=x"})
    rc, out, err = run_backup(dest)
    check("secret: backup refused", rc == 1)
    check("secret: no backup written", not os.path.exists(dest))
    check("secret: message names the file",
          ".recipe-admin.env" in err)
    check("secret: message says setup/first-boot did not finish",
          "did not finish" in err)
    check("secret: message tells owner what to do",
          "Finish the setup" in err and "remove the file" in err)
    check("secret: no 'internal error' wording",
          "internal error" not in err)

    # (ii-b) the named temp form refuses too (not skipped)
    dest = build_fixture("secret-tmp",
                         {"native/recipe-admin.env.tmp": "PASSWORD=x"})
    rc, out, err = run_backup(dest)
    check("secret-tmp: backup refused, no backup written",
          rc == 1 and not os.path.exists(dest))
    check("secret-tmp: plain message, names file, no internal error",
          "recipe-admin.env.tmp" in err and "did not finish" in err
          and "internal error" not in err)

    # (iii-b) pre-existing forbidden guard still refuses
    dest = build_fixture("shadow-guard", {"www/shadow": "nope"})
    rc, out, err = run_backup(dest)
    check("guard: exact 'shadow' component still refused",
          rc == 1 and not os.path.exists(dest)
          and "forbidden path" in err)

    # (iv) format 3: the plain outer layer identifies nothing.
    # Give this fixture a CONSISTENT onion identity (real key
    # bytes + the address recomputed from them) so the real
    # restore verifier can run its three-way identity check.
    import backupkeys
    dest = build_fixture("outer-min", {})
    hs = os.path.join(ROOT, "fx-outer-min", "hs")
    key32 = bytes(range(32))
    address = backupkeys.onion_address_from_pubkey(key32)
    with open(os.path.join(hs, "hs_ed25519_public_key"), "wb") as f:
        f.write(b"\x00" * 32 + key32)
    with open(os.path.join(hs, "hostname"), "w") as f:
        f.write(address + ".onion\n")
    rc, out, err = run_backup(dest)
    check("outer: backup succeeds", rc == 0 and "BACKUP_OK" in out)
    with tarfile.open(dest) as tar:
        members = tar.getmembers()
        meta_raw = tar.extractfile("meta.json").read()
    meta = json.loads(meta_raw)
    check("outer: format is 3", meta.get("format") == 3)
    check("outer: meta carries no onion address",
          "onion" not in meta
          and (address + ".onion").encode() not in meta_raw)
    check("outer: meta carries no creation time",
          "created" not in meta)
    check("outer: every outer tar member has mtime 0",
          all(m.mtime == 0 for m in members))
    # The real restore module reads the wrapper and verifies the
    # decrypted payload (the age shim is a passthrough, so the
    # payload bytes ARE the payload tar.gz).
    rspec = importlib.util.spec_from_loader(
        "onionhost_restore",
        SourceFileLoader(
            "onionhost_restore",
            os.path.join(TREE, "onionhost/rootfs-overlay/usr/local/"
                               "bin/onionhost-restore")))
    rs = importlib.util.module_from_spec(rspec)
    rspec.loader.exec_module(rs)
    meta2, payload = rs._read_wrapper(dest)
    check("outer: restore accepts the format 3 wrapper",
          meta2.get("format") == 3)
    stage = os.path.join(ROOT, "fx-outer-min", "stage")
    os.makedirs(stage)
    payload_path = os.path.join(ROOT, "fx-outer-min",
                                "payload.tar.gz")
    with open(payload_path, "wb") as f:
        f.write(payload)
    manifest = rs._verify(payload_path, stage)
    check("outer: restore verifies the payload and recovers the "
          "address from the encrypted manifest",
          manifest.get("onion") == address + ".onion"
          and bool(manifest.get("created")))

    pwd_mod.getpwnam = _real_getpwnam
    print("ALL %d CHECKS PASS" % len(passed))
    return 0


if __name__ == "__main__":
    sys.exit(main())

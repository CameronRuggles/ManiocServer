#!/usr/bin/env python3
"""Slice-5B backup analysis (runs on the rig host).

Usage: s5b-analyze.py <backup-file> <main-phrase> <spare-phrase|->
                     <wrong-phrase> <workdir>

Verifies, from OUTSIDE the guest, using the shipped derivation
library (backupkeys.py staged next to this script):
  * wrapper listing + plain metadata,
  * the payload decrypts with an identity derived from the MAIN
    phrase + the metadata salt, and separately with the SPARE
    phrase (when given),
  * every manifest entry's sha256/size matches the payload,
  * a WRONG phrase derivation fails to decrypt,
  * no forbidden path (LUKS keyfile / initramfs / cryptsetup-keys /
    shadow / roles) appears in the wrapper or payload listings.
Prints a report; exit 0 only if every check passes.
"""
import hashlib
import io
import json
import os
import subprocess
import sys
import tarfile

sys.path.insert(0, os.path.expanduser("~/slice5b/share"))
import backupkeys  # noqa: E402

FORBIDDEN = ("cryptsetup-keys", "crypto_keyfile", "root.key",
             "initrd", "initramfs", "shadow", "luks-roles",
             "/etc/passwd", "backup.json")


def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def main():
    path, main_phrase, spare_phrase, wrong_phrase, work = sys.argv[1:6]
    os.makedirs(work, exist_ok=True)
    ok = True

    def check(name, cond, detail=""):
        nonlocal ok
        print("%-52s %s %s" % (name, "PASS" if cond else "FAIL",
                               detail))
        ok = ok and cond

    with tarfile.open(path, "r:*") as tar:
        names = tar.getnames()
        meta = json.loads(tar.extractfile("meta.json").read())
        payload_age = tar.extractfile("payload.age").read()
    print("wrapper listing:", names)
    print("meta:", json.dumps(meta, indent=1))
    check("wrapper has exactly meta.json + payload.age",
          sorted(names) == ["meta.json", "payload.age"])
    bad = [n for n in names if any(f in n.lower() for f in FORBIDDEN)]
    check("wrapper listing free of forbidden names", not bad, str(bad))

    age_file = os.path.join(work, "payload.age")
    with open(age_file, "wb") as f:
        f.write(payload_age)

    def try_open(phrase, salt_hex, tag):
        ident = backupkeys.derive_identity(
            phrase, bytes.fromhex(salt_hex))
        idf = os.path.join(work, "id-%s.txt" % tag)
        with open(idf, "w") as f:
            f.write(ident + "\n")
        os.chmod(idf, 0o600)
        out = os.path.join(work, "payload-%s.tar.gz" % tag)
        proc = sh(["age", "-d", "-i", idf, "-o", out, age_file])
        os.unlink(idf)
        return proc.returncode == 0, out

    salts = meta["salts"]
    good, out_main = try_open(main_phrase, salts["main"], "main")
    check("payload decrypts with MAIN phrase identity", good)
    if spare_phrase != "-" and salts.get("spare"):
        good_s, _o = try_open(spare_phrase, salts["spare"], "spare")
        check("payload decrypts with SPARE phrase identity", good_s)
    good_w, _o = try_open(wrong_phrase, salts["main"], "wrong")
    check("payload REFUSES wrong-phrase identity", not good_w)

    if good:
        with tarfile.open(out_main, "r:gz") as tar:
            members = tar.getnames()
            manifest = json.loads(
                tar.extractfile("manifest.json").read())
            blobs = {m.name: tar.extractfile(m).read()
                     for m in tar.getmembers()
                     if m.isfile() and m.name != "manifest.json"}
        print("payload listing:")
        for m in members:
            print("   ", m)
        bad = [m for m in members
               if any(f in m.lower() for f in FORBIDDEN)]
        check("payload listing free of forbidden names", not bad,
              str(bad))
        allok = True
        for e in manifest["entries"]:
            data = blobs.get(e["path"])
            if data is None or len(data) != e["size"] or \
                    hashlib.sha256(data).hexdigest() != e["sha256"]:
                allok = False
                print("   MISMATCH:", e["path"])
        check("all manifest sha256/size verify", allok,
              "(%d entries)" % len(manifest["entries"]))
        check("manifest onion == meta onion",
              manifest["onion"] == meta["onion"], manifest["onion"])
        host = blobs["onion/hostname"].decode().strip()
        check("hostname file == manifest onion",
              host == manifest["onion"])
        pub = blobs["onion/hs_ed25519_public_key"]
        pubkey = pub[32:64] if len(pub) >= 64 else pub
        derived = backupkeys.onion_address_from_pubkey(pubkey)
        check("onion address recomputes from public key",
              derived + ".onion" == host, derived)
        check("secret key present (96-byte tor format)",
              len(blobs["onion/hs_ed25519_secret_key"]) == 96)
    print("ANALYSIS:", "ALL PASS" if ok else "FAILURES PRESENT")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

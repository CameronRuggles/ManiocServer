#!/usr/bin/env python3
"""Host-side proof suite for versioned container-image delivery
(review 2026-10-25, finding F2).

Drives the real onionhost-import-images from the overlay against
stub podman/systemctl binaries (poc/images-delivery/bin/), via
the importer's ONIONHOST_* seams - the same stub discipline as
poc/runtime-gate. No Podman, no systemd, no root needed.

Run: python3 poc/images-delivery/run_tests.py
Exit status: number of failed assertions.

Cases:
  (a) first import loads all three tarballs and records the
      manifest's version; nothing is restarted
  (b) same version again = no-op: podman is never asked to
      import or tag, nothing is restarted
  (c) version change: running images are tagged :rollback
      BEFORE the first import, the new set loads, all four
      container units restart, and the record moves to the new
      version with the old one kept as "previous"
  (d) a tarball whose sha256 does not match the manifest fails
      closed: nonzero exit, nothing imported, nothing
      restarted, record and running images untouched
  (e) --rollback after (c): :latest points at the old set
      again, units restart, the record is restored
  (f) pre-F2 migration: the old .images-imported marker becomes
      a record at the ISO manifest's version, with no import
  (g) restart failure on a change (full-tree audit Finding 2,
      2026-11-03): the failed change is undone in the tags
      before the tool exits - record and :latest keep naming
      the old set, the rollback copy survives, and a later
      retry lands the change cleanly
  (h) an import failing midway leaves no mixed :latest: the
      recorded set is restored over the partial import
  (i) a change run killed mid-import leaves the in-progress
      marker; the next run restores the recorded set from the
      rollback tags BEFORE tagging anything, so the rollback
      copy is never the half-imported set

Paths are derived from this file's location, never a hardcoded
home directory (review 2026-10-25, finding F7).
"""
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TREE = os.path.abspath(os.path.join(HERE, "..", ".."))
IMPORTER = os.path.join(
    TREE, "onionhost/rootfs-overlay/usr/local/bin/onionhost-import-images")
TARS = ["onionhost-tor.tar", "onionhost-web.tar", "onionhost-app.tar"]
UNITS = ["onionhost-a.service", "onionhost-b.service",
         "onionhost-app.service", "onionhost-u.service"]

FAILS = []
COUNT = {"n": 0}


def check(desc, cond):
    COUNT["n"] += 1
    print("%s %s" % ("PASS" if cond else "FAIL", desc))
    if not cond:
        FAILS.append(desc)


def flat(ref):
    return ref.replace("/", "_").replace(":", "_")


class World:
    def __init__(self, name):
        self.dir = tempfile.mkdtemp(prefix="images-delivery-%s-" % name)
        self.images = os.path.join(self.dir, "images")
        self.state = os.path.join(self.dir, "state")
        self.store = os.path.join(self.dir, "store")
        self.stubbin = os.path.join(self.dir, "bin")
        for d in (self.images, self.state, self.store, self.stubbin):
            os.makedirs(d)
        for stub in os.listdir(os.path.join(HERE, "bin")):
            src = os.path.join(HERE, "bin", stub)
            dst = os.path.join(self.stubbin, stub)
            shutil.copyfile(src, dst)
            os.chmod(dst, 0o755)
        self.podman_log = os.path.join(self.dir, "podman.log")
        self.systemctl_log = os.path.join(self.dir, "systemctl.log")
        self.env = dict(os.environ)
        self.env.update({
            "PATH": "/usr/bin:/bin",
            "ONIONHOST_PODMAN": os.path.join(self.stubbin, "podman"),
            "ONIONHOST_SYSTEMCTL": os.path.join(self.stubbin, "systemctl"),
            "ONIONHOST_IMAGES_DIR": self.images,
            "ONIONHOST_IMAGES_STATE_DIR": self.state,
            "PODMAN_STUB_DIR": self.store,
            "PODMAN_LOG": self.podman_log,
            "SYSTEMCTL_LOG": self.systemctl_log,
        })

    def make_images(self, tag, corrupt=False):
        """Write a fake tarball set + a manifest in the exact
        IMAGES-VERSION format the builders produce. Returns the
        manifest's version string."""
        lines = []
        for t in TARS:
            with open(os.path.join(self.images, t), "w") as f:
                f.write("imgid-%s-%s\n" % (t, tag))
            digest = hashlib.sha256(
                open(os.path.join(self.images, t), "rb").read()).hexdigest()
            if corrupt and t == "onionhost-web.tar":
                digest = "0" * 64
            lines.append("%s: %s\n" % (t, digest))
        combined = hashlib.sha256("".join(lines).encode()).hexdigest()
        version = "img-%s" % combined[:12]
        with open(os.path.join(self.images, "IMAGES-VERSION"), "w") as f:
            f.write("version: %s\n" % version)
            f.writelines(lines)
        return version

    def run(self, *args):
        for log in (self.podman_log, self.systemctl_log):
            if os.path.exists(log):
                os.unlink(log)
        proc = subprocess.run(["sh", IMPORTER] + list(args), env=self.env,
                              capture_output=True, text=True)
        return proc

    def log_lines(self, which):
        path = self.podman_log if which == "podman" else self.systemctl_log
        if not os.path.exists(path):
            return []
        return open(path).read().splitlines()

    def record(self):
        out = {}
        path = os.path.join(self.state, "images-imported-version")
        if os.path.exists(path):
            for line in open(path):
                if ": " in line:
                    k, v = line.rstrip("\n").split(": ", 1)
                    out[k] = v
        return out

    def stored(self, ref):
        path = os.path.join(self.store, flat(ref))
        if os.path.exists(path):
            return open(path).read().strip()
        return None


def main():
    # (a) first import
    w = World("a")
    v1 = w.make_images("v1")
    p = w.run()
    imports = [l for l in w.log_lines("podman") if l.startswith("import ")]
    check("(a) first import exits 0", p.returncode == 0)
    check("(a) all three tarballs imported", len(imports) == 3)
    check("(a) record holds the manifest version",
          w.record().get("version") == v1)
    check("(a) record has no previous", w.record().get("previous") == "-")
    check("(a) nothing restarted on first import",
          w.log_lines("systemctl") == [])
    check("(a) latest tags carry the v1 ids",
          w.stored("localhost/onionhost-tor:latest") == "imgid-onionhost-tor.tar-v1")

    # (b) same version = no-op
    p = w.run()
    check("(b) re-run exits 0", p.returncode == 0)
    check("(b) podman never invoked on a no-op",
          w.log_lines("podman") == [])
    check("(b) nothing restarted on a no-op",
          w.log_lines("systemctl") == [])

    # (c) version change
    v2 = w.make_images("v2")
    p = w.run()
    plog = w.log_lines("podman")
    first_tag = next((i for i, l in enumerate(plog)
                      if l.startswith("tag ")), None)
    first_import = next((i for i, l in enumerate(plog)
                         if l.startswith("import ")), None)
    check("(c) change import exits 0", p.returncode == 0)
    check("(c) rollback tags taken before the first import",
          first_tag is not None and first_import is not None
          and first_tag < first_import)
    restarts = w.log_lines("systemctl")
    check("(c) exactly one restart, of all four units",
          len(restarts) == 1
          and all(u in restarts[0] for u in UNITS))
    check("(c) record moved to the new version",
          w.record().get("version") == v2)
    check("(c) record keeps the old version as previous",
          w.record().get("previous") == v1)
    check("(c) latest tags carry the v2 ids",
          w.stored("localhost/onionhost-app:latest") == "imgid-onionhost-app.tar-v2")
    check("(c) rollback tags keep the v1 ids",
          w.stored("localhost/onionhost-app:rollback") == "imgid-onionhost-app.tar-v1")

    # (e) --rollback (same world as (c))
    p = w.run("--rollback")
    check("(e) rollback exits 0", p.returncode == 0)
    check("(e) latest tags restored to the v1 ids",
          w.stored("localhost/onionhost-tor:latest") == "imgid-onionhost-tor.tar-v1"
          and w.stored("localhost/onionhost-web:latest") == "imgid-onionhost-web.tar-v1"
          and w.stored("localhost/onionhost-app:latest") == "imgid-onionhost-app.tar-v1")
    check("(e) units restarted on rollback",
          len(w.log_lines("systemctl")) == 1)
    check("(e) record restored to the previous version",
          w.record().get("version") == v1
          and w.record().get("previous") == "-")

    # (d) hash mismatch fails closed (fresh world at v1)
    w = World("d")
    v1 = w.make_images("v1")
    w.run()
    w.make_images("v2", corrupt=True)
    p = w.run()
    plog = w.log_lines("podman")
    check("(d) corrupted set exits nonzero", p.returncode != 0)
    check("(d) nothing imported from a corrupted set",
          not any(l.startswith("import ") for l in plog))
    check("(d) nothing restarted for a corrupted set",
          w.log_lines("systemctl") == [])
    check("(d) record unchanged after refusal",
          w.record().get("version") == v1)
    check("(d) running images untouched after refusal",
          w.stored("localhost/onionhost-web:latest") == "imgid-onionhost-web.tar-v1")

    # (f) pre-F2 marker migration
    w = World("f")
    v1 = w.make_images("v1")
    open(os.path.join(w.state, ".images-imported"), "w").close()
    p = w.run()
    check("(f) migration exits 0", p.returncode == 0)
    check("(f) record created at the ISO manifest version",
          w.record().get("version") == v1)
    check("(f) old marker retired",
          not os.path.exists(os.path.join(w.state, ".images-imported")))
    check("(f) migration imports nothing",
          not any(l.startswith("import ")
                  for l in w.log_lines("podman")))

    # (g) restart failure on a change (Finding 2)
    w = World("g")
    v1 = w.make_images("v1")
    w.run()
    v2 = w.make_images("v2")
    w.env["SYSTEMCTL_STUB_FAIL"] = "restart"
    p = w.run()
    check("(g) failed restart exits nonzero", p.returncode != 0)
    check("(g) record still names the old version",
          w.record().get("version") == v1)
    check("(g) latest tags restored to the old set",
          all(w.stored("localhost/%s:latest" % img)
              == "imgid-%s-v1" % t
              for img, t in (("onionhost-tor", "onionhost-tor.tar"),
                             ("onionhost-web", "onionhost-web.tar"),
                             ("onionhost-app", "onionhost-app.tar"))))
    check("(g) rollback tags still hold the old set",
          w.stored("localhost/onionhost-app:rollback")
          == "imgid-onionhost-app.tar-v1")
    del w.env["SYSTEMCTL_STUB_FAIL"]
    p = w.run()
    check("(g) retry with a working restart exits 0",
          p.returncode == 0)
    check("(g) record moved to the new version on retry",
          w.record().get("version") == v2
          and w.record().get("previous") == v1)
    check("(g) latest carries the new set after retry",
          w.stored("localhost/onionhost-app:latest")
          == "imgid-onionhost-app.tar-v2")
    check("(g) rollback still holds the old set after retry",
          w.stored("localhost/onionhost-app:rollback")
          == "imgid-onionhost-app.tar-v1")

    # (h) an import failing midway (second tarball)
    w = World("h")
    v1 = w.make_images("v1")
    w.run()
    v2 = w.make_images("v2")
    w.env["PODMAN_STUB_FAIL_IMPORT_ON"] = "2"
    p = w.run()
    check("(h) failed import exits nonzero", p.returncode != 0)
    check("(h) record still names the old version",
          w.record().get("version") == v1)
    check("(h) no mixed latest: the partial import is undone",
          w.stored("localhost/onionhost-tor:latest")
          == "imgid-onionhost-tor.tar-v1"
          and w.stored("localhost/onionhost-web:latest")
          == "imgid-onionhost-web.tar-v1"
          and w.stored("localhost/onionhost-app:latest")
          == "imgid-onionhost-app.tar-v1")
    check("(h) rollback tags hold the old set",
          w.stored("localhost/onionhost-tor:rollback")
          == "imgid-onionhost-tor.tar-v1")

    # (i) a change run killed mid-import (first tarball written)
    w = World("i")
    v1 = w.make_images("v1")
    w.run()
    v2 = w.make_images("v2")
    w.env["PODMAN_STUB_KILL_PARENT_ON_IMPORT"] = "1"
    p = w.run()
    marker = os.path.join(w.state, "images-import-in-progress")
    check("(i) the killed run died by the injected SIGKILL",
          p.returncode == -9)
    check("(i) the killed run left the in-progress marker",
          os.path.exists(marker))
    check("(i) the kill really landed mid-import (tor is new)",
          w.stored("localhost/onionhost-tor:latest")
          == "imgid-onionhost-tor.tar-v2")
    check("(i) record still names the old version",
          w.record().get("version") == v1)
    del w.env["PODMAN_STUB_KILL_PARENT_ON_IMPORT"]
    p = w.run()
    check("(i) the recovery run exits 0", p.returncode == 0)
    check("(i) record moved to the new version",
          w.record().get("version") == v2
          and w.record().get("previous") == v1)
    check("(i) rollback holds the pure old set, not the mix",
          w.stored("localhost/onionhost-tor:rollback")
          == "imgid-onionhost-tor.tar-v1"
          and w.stored("localhost/onionhost-web:rollback")
          == "imgid-onionhost-web.tar-v1"
          and w.stored("localhost/onionhost-app:rollback")
          == "imgid-onionhost-app.tar-v1")
    check("(i) latest carries the new set",
          w.stored("localhost/onionhost-tor:latest")
          == "imgid-onionhost-tor.tar-v2")
    check("(i) the marker is gone after the recovery run",
          not os.path.exists(marker))

    print("---")
    print("%d assertion(s) failed" % len(FAILS))
    return len(FAILS)


if __name__ == "__main__":
    sys.exit(main())

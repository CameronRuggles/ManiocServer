#!/usr/bin/env python3
"""Updater-side proof for the images phase's importer-failure
branch (full-tree audit 2026-11-03, Finding 2).

The importer-side cases live in run_tests.py (g)-(i). This
harness drives the real onionhost-update main() - loaded as a
module, with only its external commands staged (the fuzz_legs
pattern) - through the run where the package installs fine but
the importer exits non-zero WITHOUT recording the delivered
set, because its restart failed. Before the fix, that branch
logged "the importer refused or failed - the previous image
set still serves" and never health-checked: the claim was
false (the new set was already imported) and nothing recovered
the box. The fix judges the branch by the record plus health:

  (u1) importer failed, recorded set healthy: exit 4,
       status update-failed, and the log's claim is now one a
       health check actually confirmed; the tags and record
       still name the old set (importer contract).
  (u2) recorded set unhealthy, healthy after a stack restart:
       the updater restarts the recorded set and re-checks -
       exit 4, update-failed, previous set serving again.
  (u3) recorded set unhealthy even after the restart: the run
       fails closed - exit 5, fail-closed marker written,
       gateway stopped before the stack.
  (u4) importer exits non-zero but the record DID advance
       (killed on the way out after recording): the run is
       judged like a reported success - healthy means updated,
       the high-water mark moves, exit 0.

Run: python3 poc/images-delivery/updater_failure_tests.py [tree]
Exit status: number of failed assertions.
"""
import contextlib
import importlib.util
import io
import json
import os
import subprocess as real_subprocess
import sys
import tempfile
import types
from importlib.machinery import SourceFileLoader

HERE = os.path.dirname(os.path.abspath(__file__))
TREE = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else \
    os.path.abspath(os.path.join(HERE, "..", ".."))
BIN = os.path.join(TREE, "onionhost/rootfs-overlay/usr/local/bin")
IMPORTER = os.path.join(BIN, "onionhost-import-images")
sys.path.insert(0, HERE)
import run_tests as rt  # noqa: E402  (the poc World scaffolding)

FAILS = []
COUNT = {"n": 0}


def check(desc, cond):
    COUNT["n"] += 1
    print("%s %s" % ("PASS" if cond else "FAIL", desc))
    if not cond:
        FAILS.append(desc)


def load(name, path):
    spec = importlib.util.spec_from_loader(
        name, SourceFileLoader(name, path))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


OLD_PKG = "1.0.0+img.111111111111"
NEW_PKG = "1.0.0+img.222222222222"
PROBE = "/stub/onionhost-probe"
STACKCTL = "/stub/onionhost-stackctl"
FAKE_IMPORTER = "/stub/importer-recorded-then-failed"


class Case:
    """One staged world + one loaded updater module."""

    def __init__(self, name, health_mode):
        self.w = rt.World(name)
        self.v1 = self.w.make_images("v1")
        p = self.w.run()
        assert p.returncode == 0, "first import failed: %s" % p.stderr
        self.upd = tempfile.mkdtemp(prefix="upd-state-")
        self.calls = []          # every run() argv, in order
        self.probes = {"n": 0}
        self.health_mode = health_mode
        self.fake_installed = {"onionhost": "1.0.0",
                               "onionhost-images": OLD_PKG}
        self.repo = {"onionhost": "1.0.0",
                     "onionhost-images": NEW_PKG}
        self.delivered = {"version": None}
        env = {
            "ONIONHOST_UPDATE_STATE": self.upd,
            "ONIONHOST_IMAGES_CMD": IMPORTER,
            "ONIONHOST_IMAGES_MANIFEST": os.path.join(
                self.w.images, "IMAGES-VERSION"),
            "ONIONHOST_IMAGES_RECORD": os.path.join(
                self.w.state, "images-imported-version"),
            "ONIONHOST_HEALTH_CMD": PROBE,
            "ONIONHOST_STACKCTL": STACKCTL,
            "ONIONHOST_HEALTH_ATTEMPTS": "1",
            "ONIONHOST_HEALTH_RETRY_DELAY": "0",
            "ONIONHOST_HEALTH_SETTLE_MIN": "0",
            "ONIONHOST_HEALTH_SETTLE_MAX": "0",
            "ONIONHOST_RECIPE_STATE": os.path.join(self.upd, "recipes"),
            "ONIONHOST_RECIPE_PAYLOAD_ROOT": os.path.join(
                self.upd, "payload"),
            "ONIONHOST_REBOOT_REQUIRED": os.path.join(
                self.upd, "no-reboot-required"),
            "ONIONHOST_APT_ARCHIVES": os.path.join(self.upd, "archives"),
            "ONIONHOST_PROJECT_SOURCES": os.path.join(
                self.upd, "onionhost.sources"),
        }
        for d in ("recipes", "payload", "archives"):
            os.makedirs(os.path.join(self.upd, d), exist_ok=True)
        open(env["ONIONHOST_PROJECT_SOURCES"], "w").close()
        self._saved_env = dict(os.environ)
        os.environ.update(env)
        try:
            self.U = load("upd_%s" % name,
                          os.path.join(BIN, "onionhost-update"))
        finally:
            os.environ.clear()
            os.environ.update(self._saved_env)
        U = self.U
        U.RECIPE_PKGS = []
        U.ALL_KNOWN = ["onionhost", "onionhost-images"]
        U.disk_floor_for = lambda pkg: None
        U.run = self._run
        self.status_states = []
        real_write_status = U.write_status

        def recording_write_status(state, detail, packages):
            self.status_states.append(state)
            return real_write_status(state, detail, packages)
        U.write_status = recording_write_status
        U.subprocess = types.SimpleNamespace(
            run=self._sub_run, PIPE=real_subprocess.PIPE,
            DEVNULL=real_subprocess.DEVNULL,
            STDOUT=real_subprocess.STDOUT,
            TimeoutExpired=real_subprocess.TimeoutExpired)

    # -- the staged external world -------------------------------
    def _healthy(self):
        if self.health_mode == "healthy":
            return True
        if self.health_mode == "unhealthy":
            return False
        # recover_on_restart: only once the stack restart went by
        return any(c[0] == STACKCTL and c[1:] == ["restart"]
                   for c in self.calls)

    def _sub_run(self, argv, *a, **k):
        argv = list(argv)
        if argv[:2] == ["dpkg", "--compare-versions"]:
            return real_subprocess.run(argv, *a, **k)
        if argv[0] == "dpkg-query":
            v = self.fake_installed.get(argv[-1])
            return types.SimpleNamespace(
                returncode=0 if v else 1, stdout=v or "")
        if argv[0] == "apt-cache":  # madison
            v = self.repo.get(argv[-1])
            out = ""
            if v:
                out = "%s | %s | http://repo.invalid stable/main\n" \
                    % (argv[-1], v)
            return types.SimpleNamespace(returncode=0, stdout=out)
        if argv[0] == PROBE:
            self.probes["n"] += 1
            ok = self._healthy()
            return types.SimpleNamespace(
                returncode=0 if ok else 1,
                stdout="PROBE_OK stub 200\n" if ok else "")
        return types.SimpleNamespace(returncode=0, stdout="")

    def _run(self, cmd, timeout=1800):
        cmd = list(cmd)
        self.calls.append(cmd)
        if cmd[0] == IMPORTER:
            proc = real_subprocess.run(["sh", IMPORTER] + cmd[1:],
                                       env=self.w.env,
                                       capture_output=True, text=True)
            return proc.returncode
        if cmd[0] == FAKE_IMPORTER:
            # The exotic exit: the import completed and the
            # record was written, then the tool died on the way
            # out (non-zero with an advanced record).
            prev = self.w.record().get("version")
            delivered = None
            for line in open(os.path.join(self.w.images,
                                          "IMAGES-VERSION")):
                if line.startswith("version: "):
                    delivered = line.split(": ", 1)[1].strip()
            with open(os.path.join(self.w.state,
                                   "images-imported-version"),
                      "w") as f:
                f.write("version: %s\nprevious: %s\n"
                        % (delivered, prev))
            self.delivered["version"] = delivered
            return 1
        if cmd[:2] == ["apt-get", "install"] and \
                "onionhost-images" in cmd:
            # Installing the package lays the new tarballs +
            # manifest into the images dir.
            self.w.make_images("v2")
            self.fake_installed["onionhost-images"] = NEW_PKG
            return 0
        return 0

    # -- driving + reading ---------------------------------------
    def main(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = self.U.main()
        return rc, buf.getvalue()

    def status(self):
        path = os.path.join(self.upd, "status.json")
        if os.path.exists(path):
            return json.load(open(path))
        return {}

    def highwater(self):
        path = os.path.join(self.upd, "highwater.json")
        if os.path.exists(path):
            return json.load(open(path))
        return {}


def main():
    # (u1) importer restart failure; the recorded set is healthy
    c = Case("u1", "healthy")
    c.w.env["SYSTEMCTL_STUB_FAIL"] = "restart"
    rc, out = c.main()
    check("(u1) run exits 4 (update failed, rolled back state)",
          rc == 4)
    check("(u1) status is update-failed",
          c.status().get("state") == "update-failed")
    check("(u1) the health check was actually consulted",
          c.probes["n"] >= 1)
    check("(u1) the log claims only what health confirmed",
          "health check confirms the recorded image set" in out)
    check("(u1) the old unjudged wording is gone",
          "the importer refused or failed - the previous image "
          "set still serves" not in out)
    check("(u1) tags and record still name the old set",
          c.w.record().get("version") == c.v1
          and c.w.stored("localhost/onionhost-app:latest")
          == "imgid-onionhost-app.tar-v1")
    check("(u1) the rollback copy survived the run",
          c.w.stored("localhost/onionhost-app:rollback")
          == "imgid-onionhost-app.tar-v1")

    # (u2) recorded set down; a stack restart brings it back
    c = Case("u2", "recover_on_restart")
    c.w.env["SYSTEMCTL_STUB_FAIL"] = "restart"
    rc, out = c.main()
    check("(u2) run exits 4", rc == 4)
    check("(u2) the updater restarted the recorded set",
          any(call[0] == STACKCTL and call[1:] == ["restart"]
              for call in c.calls))
    check("(u2) status is update-failed (previous set serving)",
          c.status().get("state") == "update-failed")
    check("(u2) the log records the recovery",
          "serves again after a restart" in out)

    # (u3) recorded set cannot be made healthy: fail closed
    c = Case("u3", "unhealthy")
    c.w.env["SYSTEMCTL_STUB_FAIL"] = "restart"
    rc, out = c.main()
    check("(u3) run exits 5 (fail-closed)", rc == 5)
    check("(u3) status is fail-closed",
          c.status().get("state") == "fail-closed")
    check("(u3) the fail-closed marker was written",
          os.path.exists(os.path.join(c.upd, "fail-closed.marker")))
    ctl = [call[1] for call in c.calls
           if call[0] == STACKCTL and len(call) > 1]
    check("(u3) gateway stopped before the stack",
          "stop-gateway" in ctl and "stop" in ctl
          and ctl.index("stop-gateway") < ctl.index("stop"))

    # (u4) importer died after recording: judged as a success
    c = Case("u4", "healthy")
    c.U.IMAGES_CMD = FAKE_IMPORTER
    rc, out = c.main()
    check("(u4) run exits 0", rc == 0)
    check("(u4) the run wrote an 'updated' status on the way",
          "updated" in c.status_states)
    check("(u4) final status is the run's clean end-state",
          c.status().get("state") == "up-to-date")
    check("(u4) the high-water mark moved to the new package",
          c.highwater().get("onionhost-images") == NEW_PKG)
    check("(u4) the log judges it a healthy update",
          "updated to" in out and "healthy" in out)

    print("---")
    print("%d assertion(s) failed" % len(FAILS))
    return len(FAILS)


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Recreated runtime-gate simulation harness.

Covers every behaviour enumerated in ISO-BUILD-LOG's Review 2 proof
paragraph for the shipped gate+check (labelled OLD below) plus the
Review 3 Group E cases (labelled NEW: latch S8, absent-vs-error S9)
and the Review 4 task 13 case (labelled NEW: S14 latch ordering -
the stub systemctl kills the check on stop, simulating the
ExecStartPost self-stop; marker, latch and status must already
be written, and the stop must be `--no-block stop`).
Run: run_sim.py <repo-root> [old|new|all]
Exit status: number of failed assertions in the selected set.
"""
import json
import os
import shutil
import subprocess
import sys

REPO = os.path.abspath(sys.argv[1])
MODE = sys.argv[2] if len(sys.argv) > 2 else "all"
GATE = os.path.join(REPO, "onionhost/rootfs-overlay/usr/local/bin/onionhost-runtime-gate")
CHECK = os.path.join(REPO, "onionhost/rootfs-overlay/usr/local/bin/onionhost-runtime-gate-check")
BIN = "/tmp/rgate/bin"
BASE = "/tmp/rgate/work"

FAILS = []
COUNT = {"n": 0}


def check(desc, cond, group):
    if MODE != "all" and group != MODE:
        return
    COUNT["n"] += 1
    print("%s [%s] %s" % ("PASS" if cond else "FAIL", group, desc))
    if not cond:
        FAILS.append(desc)


class World:
    def __init__(self, name):
        self.dir = os.path.join(BASE, name)
        shutil.rmtree(self.dir, ignore_errors=True)
        self.stub = os.path.join(self.dir, "stub")
        self.state = os.path.join(self.dir, "state")
        os.makedirs(self.stub)
        os.makedirs(self.state)
        self.syslog = os.path.join(self.dir, "systemctl.log")
        self.loglog = os.path.join(self.dir, "logger.log")
        open(self.syslog, "w").close()
        open(self.loglog, "w").close()
        self.env = dict(os.environ)
        self.env.update({
            "PATH": BIN + ":/usr/bin:/bin",
            "PODMAN_STUB_DIR": self.stub,
            "SYSTEMCTL_LOG": self.syslog,
            "LOGGER_LOG": self.loglog,
            "ONIONHOST_PODMAN": os.path.join(BIN, "podman"),
            "ONIONHOST_RUNTIME_GATE": GATE,
            "ONIONHOST_RUNTIME_STATE": self.state,
            "ONIONHOST_SYSTEMCTL": os.path.join(BIN, "systemctl"),
        })

    def set(self, name, runtime):
        with open(os.path.join(self.stub, name + ".runtime"), "w") as f:
            f.write(runtime)

    def remove(self, name):
        p = os.path.join(self.stub, name + ".runtime")
        if os.path.exists(p):
            os.unlink(p)

    def flag(self, name):
        open(os.path.join(self.stub, name), "w").close()

    def unflag(self, name):
        p = os.path.join(self.stub, name)
        if os.path.exists(p):
            os.unlink(p)

    def gate(self):
        return subprocess.run([sys.executable, GATE], env=self.env,
                              capture_output=True, text=True)

    def gatecheck(self, *args):
        return subprocess.run(["bash", CHECK, *args], env=self.env,
                              capture_output=True, text=True)

    def stops(self):
        with open(self.syslog) as f:
            return [ln.strip() for ln in f if ln.strip()]

    def clear_stops(self):
        open(self.syslog, "w").close()

    def logger_lines(self):
        with open(self.loglog) as f:
            return f.read()

    def marker(self):
        p = os.path.join(self.state, "fail-closed.marker")
        return open(p).read() if os.path.exists(p) else None

    def status(self):
        p = os.path.join(self.state, "status.json")
        if not os.path.exists(p):
            return None
        try:
            return json.load(open(p))
        except ValueError:
            return "CORRUPT"

    def latch(self):
        p = os.path.join(self.state, "latched.json")
        return open(p).read() if os.path.exists(p) else None

    def snapshot(self):
        out = {}
        for fn in sorted(os.listdir(self.state)):
            with open(os.path.join(self.state, fn), "rb") as f:
                out[fn] = f.read()
        return out


WRAP = "runsc-wrap"

# ---- OLD 1: all present run runsc-wrap --------------------------------
w = World("s1")
for n in ("onionhost-a", "onionhost-b", "onionhost-u"):
    w.set(n, WRAP)  # app absent (condition-selected alternative)
r = w.gate()
check("all-wrapper: judge exit 0", r.returncode == 0, "old")
r = w.gatecheck()
check("all-wrapper: check exit 0", r.returncode == 0, "old")
check("all-wrapper: systemctl never called", w.stops() == [], "old")
check("all-wrapper: no marker", w.marker() is None, "old")
check("all-wrapper: status ok", (w.status() or {}).get("state") == "ok", "old")

# ---- OLD 2: absent B is not a violation -------------------------------
w = World("s2")
w.set("onionhost-a", WRAP)
w.set("onionhost-u", WRAP)
r = w.gate()
check("absent B(+app): judge exit 0", r.returncode == 0, "old")
r = w.gatecheck()
check("absent B(+app): check exit 0, no marker",
      r.returncode == 0 and w.marker() is None, "old")

# ---- OLD 3: app on crun ------------------------------------------------
w = World("s3")
w.set("onionhost-a", WRAP)
w.set("onionhost-u", WRAP)
w.set("onionhost-app", "crun")
r = w.gate()
check("crun app: judge exit 1", r.returncode == 1, "old")
check("crun app: judge prints BAD onionhost-app crun",
      "BAD onionhost-app crun" in r.stdout, "old")
w.set("onionhost-app", "crun")  # gate() did not stop it; restore for check
r = w.gatecheck()
check("crun app: check exit 1", r.returncode == 1, "old")
check("crun app: check stops ONLY onionhost-app",
      w.stops() == ["--no-block stop onionhost-app.service"], "old")
check("crun app: marker written", w.marker() is not None, "old")
check("crun app: marker names offender",
      "onionhost-app" in (w.marker() or ""), "old")
check("crun app: status runtime-violation",
      (w.status() or {}).get("state") == "runtime-violation", "old")
check("crun app: status names offender",
      "onionhost-app" in str((w.status() or {}).get("offenders", "")), "old")
# OLD 4: after fix (unit restarted under runsc-wrap) -> clean, cleared.
w.set("onionhost-app", WRAP)
r = w.gatecheck()
check("after fix: check exit 0", r.returncode == 0, "old")
check("after fix: marker cleared", w.marker() is None, "old")
check("after fix: status ok", (w.status() or {}).get("state") == "ok", "old")

# ---- OLD 5: A on plain runsc ------------------------------------------
w = World("s5")
w.set("onionhost-a", "runsc")
w.set("onionhost-b", WRAP)
w.set("onionhost-u", WRAP)
r = w.gate()
check("runsc A: judge exit 1", r.returncode == 1, "old")
r = w.gatecheck()
check("runsc A: check stops ONLY onionhost-a",
      w.stops() == ["--no-block stop onionhost-a.service"], "old")
check("runsc A: marker written naming A",
      w.marker() is not None and "onionhost-a" in w.marker(), "old")
# reset for later worlds is irrelevant (fresh world each case)

# ---- OLD 6: broken podman ----------------------------------------------
w = World("s6")
w.set("onionhost-a", WRAP)
w.flag("broken")
before = w.snapshot()
r = w.gate()
check("broken podman: judge exit 2", r.returncode == 2, "old")
r = w.gatecheck()
check("broken podman: check exit 2", r.returncode == 2, "old")
check("broken podman: nothing stopped", w.stops() == [], "old")
check("broken podman: no marker, state untouched",
      w.marker() is None and w.snapshot() == before, "old")

# ---- OLD 7: unparseable inspect output is an error ----------------------
w = World("s7")
w.set("onionhost-a", WRAP)
w.flag("garbage_onionhost-a")
r = w.gate()
check("garbage inspect output: judge exit 2", r.returncode == 2, "old")

# ======================================================================
# NEW cases (Review 3 Group E)
# ======================================================================
# ---- NEW 15a: latch holds across two further timer runs ----------------
w = World("n15")
w.set("onionhost-a", WRAP)
w.set("onionhost-u", WRAP)
w.set("onionhost-app", "crun")
r = w.gatecheck()
check("latch: initial violation stops app, marker+violation state",
      r.returncode == 1 and w.marker() is not None
      and (w.status() or {}).get("state") == "runtime-violation", "new")
# stub systemctl stop removed the app container: it is now absent.
for i in (1, 2):
    r = w.gatecheck()
    check("latch: timer run %d keeps marker" % i, w.marker() is not None, "new")
    check("latch: timer run %d keeps state runtime-violation" % i,
          (w.status() or {}).get("state") == "runtime-violation", "new")
    check("latch: timer run %d keeps status offenders naming app" % i,
          "onionhost-app" in str((w.status() or {}).get("offenders", "")), "new")
check("latch: latch file records stopped unit",
      w.latch() is not None and "onionhost-app" in w.latch(), "new")
check("latch: absent latched unit is not re-stopped",
      w.stops() == ["--no-block stop onionhost-app.service"], "new")
# fixing the cause and restarting the unit clears marker + latch
w.set("onionhost-app", WRAP)
r = w.gatecheck()
check("latch: fixed+restarted clears marker",
      r.returncode == 0 and w.marker() is None, "new")
check("latch: fixed+restarted clears latch file", w.latch() is None, "new")
check("latch: fixed+restarted status ok",
      (w.status() or {}).get("state") == "ok", "new")
# never-latched absent unit stays a non-violation after latch clears
r = w.gatecheck()
check("latch: post-clear absent B still not a violation",
      r.returncode == 0 and w.marker() is None, "new")

# ---- NEW 15b: explicit clear path ---------------------------------------
w = World("n15b")
w.set("onionhost-a", WRAP)
w.set("onionhost-app", "crun")
r = w.gatecheck()
assert w.marker() is not None
log_before = w.logger_lines()
r = w.gatecheck("clear")
check("clear: exit 0", r.returncode == 0, "new")
check("clear: marker removed", w.marker() is None, "new")
check("clear: latch removed", w.latch() is None, "new")
check("clear: status ok", (w.status() or {}).get("state") == "ok", "new")
check("clear: clear is logged",
      "CLEAR" in w.logger_lines()[len(log_before):], "new")
# after a manual clear, an absent (never re-violated) app is no violation
r = w.gatecheck()
check("clear: subsequent clean run stays clean",
      r.returncode == 0 and w.marker() is None, "new")

# ---- NEW 16: inspect error != absent ------------------------------------
w = World("n16")
w.set("onionhost-a", WRAP)
w.set("onionhost-b", WRAP)
w.flag("fail_inspect_onionhost-b")
r = w.gate()
check("inspect-error: judge exit 2 for present container",
      r.returncode == 2, "new")
before = w.snapshot()
r = w.gatecheck()
check("inspect-error: check exit 2", r.returncode == 2, "new")
check("inspect-error: enforcer changes no state",
      w.snapshot() == before, "new")
check("inspect-error: nothing stopped", w.stops() == [], "new")
# exists error also yields exit 2
w.unflag("fail_inspect_onionhost-b")
w.flag("fail_exists_onionhost-b")
r = w.gate()
check("exists-error: judge exit 2", r.returncode == 2, "new")
# absent container still judges absent (no violation) once errors clear
w.unflag("fail_exists_onionhost-b")
w.remove("onionhost-b")
r = w.gate()
check("absent after errors clear: judge exit 0", r.returncode == 0, "new")
# gate error while a latch stands leaves marker+latch+status untouched
w2 = World("n16b")
w2.set("onionhost-a", WRAP)
w2.set("onionhost-app", "crun")
w2.gatecheck()
assert w2.marker() is not None
before = w2.snapshot()
w2.set("onionhost-a", WRAP)
w2.flag("fail_inspect_onionhost-a")
r = w2.gatecheck()
check("inspect-error with latch: check exit 2, state untouched",
      r.returncode == 2 and w2.snapshot() == before, "new")
check("inspect-error with latch: marker+latch still stand",
      w2.marker() is not None and w2.latch() is not None, "new")

# ======================================================================
# Review 4 task 13 (finding S14): latch ordering / self-stop
# ======================================================================
# ---- S14: stub systemctl KILLS the check on stop -----------------------
# Simulates the case task 17's ExecStartPost= hook was added for:
# the offending unit is the very unit whose start job is running
# the check, so `systemctl stop` kills the check process itself.
# Pre-fix, the check stopped offenders BEFORE writing marker,
# latch or status, so the kill left no recorded state at all and
# the next timer run reported ok. Post-fix, state is written
# first and the stop is --no-block, so all three files must
# exist with the violation recorded even though the check was
# killed (returncode -9 = SIGKILL) before it could exit.
w = World("s14")
w.set("onionhost-a", WRAP)
w.set("onionhost-u", WRAP)
w.set("onionhost-app", "crun")
w.flag("kill_on_stop")
r = w.gatecheck()
check("S14 self-stop: check was killed by the stop (rc -9)",
      r.returncode == -9, "new")
check("S14 self-stop: stop was --no-block stop of ONLY the offender",
      w.stops() == ["--no-block stop onionhost-app.service"], "new")
check("S14 self-stop: marker exists after the kill",
      w.marker() is not None, "new")
check("S14 self-stop: marker names offender",
      "onionhost-app" in (w.marker() or ""), "new")
check("S14 self-stop: latched.json exists after the kill",
      w.latch() is not None, "new")
check("S14 self-stop: latched.json names offender",
      "onionhost-app" in (w.latch() or ""), "new")
check("S14 self-stop: status.json exists after the kill",
      w.status() is not None, "new")
check("S14 self-stop: status is runtime-violation",
      (w.status() or {}).get("state") == "runtime-violation", "new")
check("S14 self-stop: status names offender",
      "onionhost-app" in str((w.status() or {}).get("offenders", "")), "new")
# And the latch the killed check left behind still holds on the
# next (timer) run: the stopped unit is absent but latched, so
# the fail-closed state stands instead of reporting ok.
w.unflag("kill_on_stop")
r = w.gatecheck()
check("S14 self-stop: next timer run keeps the latch standing",
      r.returncode == 1 and w.marker() is not None
      and (w.status() or {}).get("state") == "runtime-violation", "new")

# ======================================================================
# Deanonymization audit R-10: the nft drift check stops U too
# ======================================================================
# onionhost-nft-gate-check is driven through its test seams with
# a stub gate whose exit code the case controls: on mismatch (1)
# BOTH tor containers must be stopped - before the fix only A
# was, leaving the clearnet-originating container running under
# a firewall the platform had judged wrong. On match (0) and on
# gate error (2) nothing is stopped (the error policy itself is
# unchanged; it is a reserved human-reviewer call).
NFTCHECK = os.path.join(
    REPO, "onionhost/rootfs-overlay/usr/local/bin/"
          "onionhost-nft-gate-check")


class NftWorld(World):
    def __init__(self, name):
        super().__init__(name)
        self.gate_stub = os.path.join(self.stub, "nft-gate-stub")
        with open(self.gate_stub, "w") as f:
            f.write("#!/bin/bash\nexit $(cat \"%s\")\n"
                    % os.path.join(self.stub, "nft-gate-rc"))
        os.chmod(self.gate_stub, 0o755)
        self.env["ONIONHOST_NFT_GATE"] = self.gate_stub

    def gate_rc(self, rc):
        with open(os.path.join(self.stub, "nft-gate-rc"), "w") as f:
            f.write(str(rc))

    def nftcheck(self):
        return subprocess.run(["bash", NFTCHECK], env=self.env,
                              capture_output=True, text=True)


w = NftWorld("r10a")
w.gate_rc(1)
r = w.nftcheck()
check("R-10 mismatch: check exits 1", r.returncode == 1, "new")
check("R-10 mismatch: A stopped",
      "stop onionhost-a.service" in w.stops(), "new")
check("R-10 mismatch: U stopped",
      "stop onionhost-u.service" in w.stops(), "new")
w = NftWorld("r10b")
w.gate_rc(0)
r = w.nftcheck()
check("R-10 match: exit 0, nothing stopped",
      r.returncode == 0 and w.stops() == [], "new")
w = NftWorld("r10c")
w.gate_rc(2)
r = w.nftcheck()
check("R-10 gate error: exit propagates, nothing stopped",
      r.returncode == 2 and w.stops() == [], "new")

print("---")
print("%d assertion(s), %d failed" % (COUNT["n"], len(FAILS)))
sys.exit(len(FAILS))

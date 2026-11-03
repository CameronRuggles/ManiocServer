#!/usr/bin/env python3
"""T1 follow-up harness (audit re-verification 2026-10-30,
T1-1 + T1-2).

T1-1: the untimed Debian install call can never do network
I/O - statically: it carries --no-download, and the source
skips the install (rc = the download's result) when the
timed download phase failed. (Running main() end-to-end
needs a staged apt/Tor venue that does not exist here;
these are call-shape facts, checked against the source
that will run.)

T1-2: _purge_superseded_kernels, unit-run with faked
subprocess boundaries: it purges every installed versioned
kernel except the running kernel's package and the newest
installed; it does nothing when only those two exist; a
listing failure or a purge failure is absorbed (log-only)
and never raises.
"""
import importlib.util
import os
import sys
import tempfile
import types
from importlib.machinery import SourceFileLoader

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
BIN = os.environ.get(
    "ONIONHOST_BIN_DIR",
    os.path.join(ROOT, "onionhost", "rootfs-overlay",
                 "usr", "local", "bin"))
TOOL = os.path.join(BIN, "onionhost-update")

failures = []


def check(name, cond):
    print("%s %s" % ("PASS" if cond else "FAIL", name))
    if not cond:
        failures.append(name)


src = open(TOOL).read()
check("install call carries --no-download",
      '"--no-download"' in src)
check("install is skipped when the download phase failed",
      "rc = dl" in src)
check("purge helper is defined", "_purge_superseded_kernels"
      in src)
check("purge runs only after a successful install phase",
      "if rc == 0:" in src
      and "_purge_superseded_kernels()" in src)

tmp = tempfile.mkdtemp(prefix="oh-t1f-")


def load(name, env):
    saved = dict(os.environ)
    os.environ.update(env)
    try:
        loader = SourceFileLoader(name, TOOL)
        spec = importlib.util.spec_from_loader(name, loader)
        mod = importlib.util.module_from_spec(spec)
        loader.exec_module(mod)
        return mod
    finally:
        os.environ.clear()
        os.environ.update(saved)


upd = load("oh_update_t1f", {"ONIONHOST_UPDATE_STATE": tmp})
upd.log = lambda *a: None


class _Uname:
    release = "6.1.0-21-amd64"


class _Proc:
    def __init__(self, stdout):
        self.stdout = stdout


def stage(installed, purge_rc=0, query_raises=False):
    calls = []

    import subprocess as _real_sp

    class _FakeSubprocess:
        PIPE = _real_sp.PIPE
        DEVNULL = _real_sp.DEVNULL

        @staticmethod
        def run(argv, **kw):
            if query_raises:
                raise RuntimeError("staged query failure")
            return _Proc("\n".join(installed) + "\n")

    def _fake_run(argv, timeout="UNSET"):
        calls.append((list(argv), timeout))
        return purge_rc

    upd.subprocess = _FakeSubprocess
    upd.run = _fake_run
    upd.os = types.SimpleNamespace(
        uname=lambda: _Uname(), environ=os.environ,
        path=os.path)
    return calls


K = "linux-image-"
# Running (21) is not the newest (23): keep both, purge 15.
calls = stage([K + "6.1.0-15-amd64", K + "6.1.0-21-amd64",
               K + "6.1.0-23-amd64"])
upd._purge_superseded_kernels()
purges = [c for c, _t in calls if c[:2] == ["apt-get", "purge"]]
check("purge called exactly once", len(purges) == 1)
check("purge takes only the superseded kernel",
      bool(purges)
      and purges[0][3:] == [K + "6.1.0-15-amd64"])
check("purge is untimed (a timed-out purge could wedge dpkg)",
      bool(calls)
      and all(t is None for _c, t in calls))

# Only the running kernel and the newest exist: no purge.
calls = stage([K + "6.1.0-21-amd64", K + "6.1.0-23-amd64"])
upd._purge_superseded_kernels()
check("nothing superseded: no purge call",
      not any(c[:2] == ["apt-get", "purge"] for c, _t in calls))

# Two older kernels behind the running one: both purged,
# newest==running kept.
calls = stage([K + "6.1.0-9-amd64", K + "6.1.0-15-amd64",
               K + "6.1.0-21-amd64"])
upd._purge_superseded_kernels()
purges = [c for c, _t in calls if c[:2] == ["apt-get", "purge"]]
check("two superseded kernels purged together",
      bool(purges) and purges[0][3:] == [K + "6.1.0-15-amd64",
                                         K + "6.1.0-9-amd64"])

# Failures are absorbed.
calls = stage([], query_raises=True)
try:
    upd._purge_superseded_kernels()
    absorbed_q = True
except Exception:  # noqa: BLE001 - the point of the check
    absorbed_q = False
check("listing failure is absorbed (log-only)", absorbed_q)
calls = stage([K + "6.1.0-15-amd64", K + "6.1.0-21-amd64",
               K + "6.1.0-23-amd64"], purge_rc=100)
try:
    upd._purge_superseded_kernels()
    absorbed_p = True
except Exception:  # noqa: BLE001
    absorbed_p = False
check("purge failure is absorbed (log-only)", absorbed_p)

print()
if failures:
    print("FAILURES: %d" % len(failures))
    for name in failures:
        print("  - " + name)
    sys.exit(1)
print("ALL T1 FOLLOW-UP CHECKS PASSED")

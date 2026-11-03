#!/usr/bin/env python3
"""T3 reboot-state detection tests (audit fix batch, task T3).

Exercises _reboot_state() from onionhost-update against staged
inputs. Hermetic: PATH is emptied so the needrestart source can
never fire, the flag-file path is an env override, and the
/lib/modules comparison runs against a staged directory via the
ONIONHOST_MODULES_DIR / ONIONHOST_RUNNING_RELEASE overrides.

Cases:
  1. no flag, only the running kernel installed  -> not required
  2. flag file naming a package                  -> required, named
  3. no flag, newer kernel installed, old running -> required (the
     rig case: Debian kernels write no flag file and the shipped
     image carries no needrestart)
  4. no flag, running is the newest of two        -> not required
  5. modules dir missing                          -> not required,
     no exception (best-effort record)
"""
import importlib.util
import os
import sys
import tempfile

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "..", "..")
UPDATER = os.path.join(
    ROOT, "onionhost", "rootfs-overlay", "usr", "local", "bin",
    "onionhost-update")

tmp = tempfile.mkdtemp(prefix="t3-reboot-")
flag = os.path.join(tmp, "reboot-required")
os.environ["ONIONHOST_REBOOT_REQUIRED"] = flag
os.environ["PATH"] = tmp  # hermetic: needrestart can never be found

spec = importlib.util.spec_from_loader("onionhost_update", loader=None)
mod = importlib.util.module_from_spec(spec)
with open(UPDATER) as f:
    code = compile(f.read(), UPDATER, "exec")
exec(code, mod.__dict__)

failures = []


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        failures.append(name)


def stage_modules(releases):
    mdir = os.path.join(tmp, "modules")
    os.makedirs(mdir, exist_ok=True)
    for d in os.listdir(mdir):
        os.rmdir(os.path.join(mdir, d))
    for rel in releases:
        os.makedirs(os.path.join(mdir, rel))
    return mdir


def run(modules_dir, running):
    if os.path.exists(flag):
        os.unlink(flag)
    if os.path.exists(flag + ".pkgs"):
        os.unlink(flag + ".pkgs")
    os.environ["ONIONHOST_MODULES_DIR"] = modules_dir
    os.environ["ONIONHOST_RUNNING_RELEASE"] = running
    return mod._reboot_state()


RUNNING = "6.12.107+deb13-amd64"
NEWER = "6.12.113+deb13-amd64"
OLDER = "6.12.90+deb13-amd64"

req, _ = run(stage_modules([RUNNING]), RUNNING)
check("only running kernel installed -> not required", req is False)

with open(flag, "w") as f:
    f.write("linux-image-6.12.113+deb13-amd64\n")
req, reason = mod._reboot_state()
check("flag file -> required", req is True)
check("flag file -> package named", "linux-image" in reason)
os.unlink(flag)

req, reason = run(stage_modules([RUNNING, NEWER]), RUNNING)
check("newer installed, old running -> required", req is True)
check("kernel reason given", "newer kernel" in reason)

req, _ = run(stage_modules([NEWER, OLDER]), NEWER)
check("running is newest of two -> not required", req is False)

req, _ = run(os.path.join(tmp, "does-not-exist"), RUNNING)
check("modules dir missing -> not required, no raise", req is False)

print("FAILURES: %d" % len(failures))
sys.exit(1 if failures else 0)

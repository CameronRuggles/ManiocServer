#!/usr/bin/env python3
"""T3-1 harness (audit re-verification 2026-10-30): the Debian
channel carries its own outcome in status.json, and the
Dashboard never renders "up to date" over a failed Debian
phase.

Write side (onionhost-update.write_status):
  - pre-T3-1 runs (Debian phase outcome unset) produce the
    pre-T3-1 record shape EXACTLY - no new keys - so the
    auditor-verified project-channel equivalence is kept;
  - a failed phase writes debian_ok=False and does NOT
    advance debian_last_successful_check;
  - a clean phase writes debian_ok=True and advances it;
  - a mid-run write (outcome unset) carries both forward.
Read side (wizard.update_status_text):
  - debian_ok False renders the "not completing" line, not
    the "up to date" line, with the last-completion age;
  - debian_ok True / absent renders exactly as before.

Venue discipline as in t3-reboot-state-test.py: both
modules are exec'd from the tree under test in a sandbox,
never from an installed copy; the updater's reboot probes
are pointed at staged paths.
"""
import importlib.util
import json
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
LIB = os.path.join(ROOT, "onionhost", "rootfs-overlay",
                   "usr", "lib", "onionhost")

tmp = tempfile.mkdtemp(prefix="oh-t3-1-")
failures = []


def check(name, cond):
    print("%s %s" % ("PASS" if cond else "FAIL", name))
    if not cond:
        failures.append(name)


def load(name, path, env):
    saved = dict(os.environ)
    os.environ.update(env)
    try:
        loader = SourceFileLoader(name, path)
        spec = importlib.util.spec_from_loader(name, loader)
        mod = importlib.util.module_from_spec(spec)
        loader.exec_module(mod)
        return mod
    finally:
        os.environ.clear()
        os.environ.update(saved)


upd = load("oh_update_t31", os.path.join(BIN,
                                         "onionhost-update"),
           {"ONIONHOST_UPDATE_STATE": tmp,
            "ONIONHOST_REBOOT_REQUIRED":
                os.path.join(tmp, "reboot-required"),
            "ONIONHOST_MODULES_DIR": os.path.join(tmp, "mods"),
            "PATH": "/nonexistent"})
STATUS = os.path.join(tmp, "status.json")


def record():
    with open(STATUS) as f:
        return json.load(f)


PRE_T31_KEYS = {"state", "detail", "checked_at", "packages",
                "owner_maintained", "reboot_required",
                "reboot_reason", "reboot_required_since",
                "last_successful_check"}

# 1. A run whose Debian outcome is unset writes the
#    pre-T3-1 shape exactly.
upd.CHECK_SUCCEEDED = True
upd.DEBIAN_PHASE_OK = None
if os.path.exists(STATUS):
    os.unlink(STATUS)
upd.write_status("up-to-date", "Everything is current.", [])
rec = record()
check("unset outcome: record keeps the pre-T3-1 key set",
      set(rec) == PRE_T31_KEYS)
check("unset outcome: project last_successful_check set",
      bool(rec["last_successful_check"]))

# 2. A failed Debian phase: debian_ok False, its success
#    time null (never completed).
upd.DEBIAN_PHASE_OK = False
upd.write_status("up-to-date", "x", [])
rec = record()
check("failed phase: debian_ok is False",
      rec.get("debian_ok") is False)
check("failed phase: debian success time still null",
      rec.get("debian_last_successful_check") is None)

# 3. A clean phase: debian_ok True, success time advances.
upd.DEBIAN_PHASE_OK = True
upd.write_status("up-to-date", "x", [])
rec = record()
check("clean phase: debian_ok is True",
      rec.get("debian_ok") is True)
check("clean phase: debian success time recorded",
      bool(rec.get("debian_last_successful_check")))
first_success = rec["debian_last_successful_check"]

# 4. A later failed phase: time does NOT advance.
upd.DEBIAN_PHASE_OK = False
upd.write_status("up-to-date", "x", [])
rec = record()
check("later failure: debian_ok False again",
      rec.get("debian_ok") is False)
check("later failure: debian success time unchanged",
      rec.get("debian_last_successful_check") == first_success)

# 5. A mid-run write (outcome unset) carries both forward.
upd.DEBIAN_PHASE_OK = None
upd.write_status("checking", "x", [])
rec = record()
check("mid-run write: debian_ok carried forward",
      rec.get("debian_ok") is False)
check("mid-run write: debian success time carried forward",
      rec.get("debian_last_successful_check") == first_success)

# ---- Dashboard rendering ----------------------------------
for name in ("tkinter", "tkinter.filedialog", "phrasegen",
             "sitegen"):
    sys.modules.setdefault(name, types.ModuleType(name))
sys.modules["tkinter"].filedialog = \
    sys.modules["tkinter.filedialog"]
spec = importlib.util.spec_from_loader(
    "wizard_t31", SourceFileLoader("wizard_t31",
                                   os.path.join(
                                       LIB, "wizard.py")))
wiz = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wiz)
wiz.UPDATE_STATUS_PATH = STATUS
wiz.UPDATE_MARKER_PATH = os.path.join(tmp, "no-marker")


def write_rec(obj):
    with open(STATUS, "w") as f:
        json.dump(obj, f)


today = record()["checked_at"]
write_rec({"state": "up-to-date", "debian_ok": False,
           "debian_last_successful_check": today,
           "last_successful_check": today,
           "checked_at": today})
text = wiz.update_status_text()
check("debian failed: dashboard does not say up to date",
      not text.startswith("Your software is up to date"))
check("debian failed: dashboard names the Debian channel",
      "Debian" in text and "not completing" in text)

write_rec({"state": "up-to-date", "debian_ok": False,
           "last_successful_check": today,
           "checked_at": today})
text = wiz.update_status_text()
check("debian never completed: dashboard says so plainly",
      "has not completed yet" in text)

write_rec({"state": "up-to-date", "debian_ok": True,
           "last_successful_check": today,
           "checked_at": today})
text = wiz.update_status_text()
check("debian ok: dashboard renders up to date as before",
      text.startswith("Your software is up to date"))

write_rec({"state": "up-to-date",
           "last_successful_check": today,
           "checked_at": today})
text = wiz.update_status_text()
check("pre-T3-1 record: dashboard renders as before",
      text.startswith("Your software is up to date"))

print()
if failures:
    print("FAILURES: %d" % len(failures))
    for name in failures:
        print("  - " + name)
    sys.exit(1)
print("ALL T3-1 CHECKS PASSED")

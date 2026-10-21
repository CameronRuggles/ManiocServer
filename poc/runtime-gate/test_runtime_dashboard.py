#!/usr/bin/env python3
"""Recreated runtime-card dashboard harness (wizard.runtime_status_text).

12 checks mirroring the Review 2 batch's dashboard harness: marker
beats status; violation renders; ok/missing/corrupt -> no card; plus
state files produced by the gate simulation render the card.
Usage: test_runtime_dashboard.py <wizard.py> [sim_state_dir ...]
"""
import importlib.util
import json
import os
import sys
import tempfile
import types

WIZARD = os.path.abspath(sys.argv[1])
CARD = ("Your site is off for safety. A part of it was not "
        "running inside its protective sandbox, so it was stopped.")

for name in ("tkinter", "tkinter.filedialog", "phrasegen", "sitegen"):
    sys.modules.setdefault(name, types.ModuleType(name))
sys.modules["tkinter"].filedialog = sys.modules["tkinter.filedialog"]

from importlib.machinery import SourceFileLoader
spec = importlib.util.spec_from_loader(
    "wizard_under_test", SourceFileLoader("wizard_under_test", WIZARD))
wiz = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wiz)

FAILS = []


def check(desc, cond):
    print("%s %s" % ("PASS" if cond else "FAIL", desc))
    if not cond:
        FAILS.append(desc)


check("build exposes RUNTIME_MARKER_PATH in runtime state dir",
      wiz.RUNTIME_MARKER_PATH.endswith("/runtime/fail-closed.marker"))
check("build exposes RUNTIME_STATUS_PATH in runtime state dir",
      wiz.RUNTIME_STATUS_PATH.endswith("/runtime/status.json"))

tmp = tempfile.mkdtemp(prefix="rgate-dash-")
status_path = os.path.join(tmp, "status.json")
marker_path = os.path.join(tmp, "fail-closed.marker")
wiz.RUNTIME_STATUS_PATH = status_path
wiz.RUNTIME_MARKER_PATH = marker_path


def set_status(obj, raw=None):
    if obj is None and raw is None:
        if os.path.exists(status_path):
            os.unlink(status_path)
        return
    with open(status_path, "w") as f:
        f.write(raw if raw is not None else json.dumps(obj))


def set_marker(present):
    if present:
        with open(marker_path, "w") as f:
            f.write("{}")
    elif os.path.exists(marker_path):
        os.unlink(marker_path)


set_marker(True)
set_status({"state": "runtime-violation"})
check("marker + violation status -> card", wiz.runtime_status_text() == CARD)
set_status({"state": "ok"})
check("marker + ok status -> card (marker wins)", wiz.runtime_status_text() == CARD)
set_status(None)
check("marker + missing status -> card", wiz.runtime_status_text() == CARD)
set_status(None, raw="{not json")
check("marker + corrupt status -> card", wiz.runtime_status_text() == CARD)
set_marker(False)
set_status({"state": "runtime-violation"})
check("no marker + violation status -> card", wiz.runtime_status_text() == CARD)
set_status({"state": "ok"})
check("no marker + ok status -> no card", wiz.runtime_status_text() == "")
set_status(None)
check("no marker + missing status -> no card", wiz.runtime_status_text() == "")
set_status(None, raw="{not json")
check("no marker + corrupt status -> no card", wiz.runtime_status_text() == "")
set_status({"state": "something-else"})
check("no marker + unrelated state -> no card", wiz.runtime_status_text() == "")

# State files from the gate simulation worlds, if provided, as
# <dir>=card (expect the card) or <dir>=nocard (expect no card).
for arg in sys.argv[2:]:
    d, _, expect = arg.rpartition("=")
    wiz.RUNTIME_STATUS_PATH = os.path.join(d, "status.json")
    wiz.RUNTIME_MARKER_PATH = os.path.join(d, "fail-closed.marker")
    lbl = os.path.basename(os.path.dirname(d.rstrip("/"))) or d
    want = CARD if expect == "card" else ""
    check("sim state %s -> %s" % (lbl, expect),
          wiz.runtime_status_text() == want)

print("---")
print("%d assertion(s) failed" % len(FAILS))
sys.exit(len(FAILS))

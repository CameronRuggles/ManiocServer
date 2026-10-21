#!/usr/bin/env python3
"""runsc-wrap classification / fail-closed harness (Repo Review 5 B-2).

Loads the REAL usr/local/bin/runsc-wrap as a module, points its
REAL_RUNSC at a recording stub and captures os.execv instead of
exec'ing, then drives bundle fixtures through main():

  W1  website bundle (nginx) WITH a stray netns entry -> entry
      stripped from config.json; argv = runsc --host-uds=create
      --network=none.
  W2  website bundle without netns -> config untouched; same argv.
  W3  app bundle (app-init) WITH netns -> website class: stripped,
      create + none.
  W4  tor bundle WITH netns -> spec byte-identical (bridge netns is
      runsc's to use as-is); argv = runsc --host-uds=all, and NO
      --network flag anywhere.
  W5  UNRECOGNISED bundle WITH a stray netns entry -> entry
      stripped (Review 5 B-2: the unrecognised branch passed
      --network=none but left the spec's netns in place); argv =
      create + none. FAILS against the pre-B-2 wrapper.
  W6  unrecognised bundle without netns -> config untouched;
      create + none.
  W7  create with NO bundle -> fail closed (SystemExit != 0),
      runsc never exec'd.
  W8  bundle with corrupt config.json + create -> fail closed,
      runsc never exec'd.
  W9  lifecycle verb (start) with no bundle -> pass-through exec
      with the legacy --host-uds=all shape.

Exit status: number of failed assertions (0 = all pass).
"""
import importlib.machinery
import importlib.util
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
WRAP = os.path.join(HERE, "..", "..", "onionhost", "rootfs-overlay",
                    "usr", "local", "bin", "runsc-wrap")

_loader = importlib.machinery.SourceFileLoader("runsc_wrap", WRAP)
_spec = importlib.util.spec_from_loader("runsc_wrap", _loader)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)
mod.REAL_RUNSC = "/stub/runsc"

FAILURES = []
EXECS = []


def check(sid, desc, cond):
    print("%s %s: %s" % ("PASS" if cond else "FAIL", sid, desc))
    if not cond:
        FAILURES.append("%s %s" % (sid, desc))


class _Exec(Exception):
    """Simulates a successful execv (which never returns)."""


def fake_execv(path, argv):
    EXECS.append((path, list(argv)))
    raise _Exec()


_real_execv = os.execv
os.execv = fake_execv


def make_bundle(args, with_netns):
    d = tempfile.mkdtemp(prefix="wrap-bundle-")
    ns = [{"type": "pid"}, {"type": "mount"}, {"type": "user"}]
    if with_netns:
        ns.append({"type": "network", "path": "/run/netns/stray"})
    cfg = {"ociVersion": "1.0.2",
           "process": {"args": args, "cwd": "/"},
           "root": {"path": "rootfs"},
           "linux": {"namespaces": ns}}
    with open(os.path.join(d, "config.json"), "w") as f:
        json.dump(cfg, f)
    return d


def read_cfg(d):
    with open(os.path.join(d, "config.json")) as f:
        return json.load(f)


def has_netns(d):
    return any(n.get("type") == "network"
               for n in read_cfg(d)["linux"]["namespaces"])


def run_wrap(argv):
    """Returns (exec_record_or_None, exit_code_or_None)."""
    EXECS.clear()
    sys.argv = ["runsc-wrap"] + argv
    code = None
    try:
        mod.main()
    except _Exec:
        pass
    except SystemExit as e:
        code = e.code
    return (EXECS[0] if EXECS else None), code


def bundle_argv(bundle, verb="create"):
    return ["--bundle", bundle, verb, "cid123"]


# --- W1: website + stray netns -------------------------------------
b = make_bundle(["nginx", "-g", "daemon off;"], with_netns=True)
before = open(os.path.join(b, "config.json")).read()
ex, code = run_wrap(bundle_argv(b))
check("W1", "website bundle exec'd runsc", ex is not None)
check("W1", "netns stripped from website bundle", not has_netns(b))
check("W1", "argv is create + network=none",
      ex and ex[1][1:3] == ["--host-uds=create", "--network=none"])
shutil.rmtree(b, ignore_errors=True)

# --- W2: website, no netns ------------------------------------------
b = make_bundle(["nginx"], with_netns=False)
before = open(os.path.join(b, "config.json")).read()
ex, code = run_wrap(bundle_argv(b))
check("W2", "website bundle exec'd", ex is not None)
check("W2", "config untouched when no netns",
      open(os.path.join(b, "config.json")).read() == before)
check("W2", "argv is create + network=none",
      ex and ex[1][1:3] == ["--host-uds=create", "--network=none"])
shutil.rmtree(b, ignore_errors=True)

# --- W3: app-init + stray netns --------------------------------------
b = make_bundle(["/usr/local/bin/app-init.sh"], with_netns=True)
ex, code = run_wrap(bundle_argv(b))
check("W3", "app bundle treated as website class (netns stripped)",
      not has_netns(b))
check("W3", "argv is create + network=none",
      ex and ex[1][1:3] == ["--host-uds=create", "--network=none"])
shutil.rmtree(b, ignore_errors=True)

# --- W4: tor + netns (bridge, by design) ------------------------------
b = make_bundle(["tor", "-f", "/etc/tor/torrc"], with_netns=True)
before = open(os.path.join(b, "config.json")).read()
ex, code = run_wrap(bundle_argv(b))
check("W4", "tor bundle exec'd", ex is not None)
check("W4", "tor spec byte-identical (bridge netns kept)",
      open(os.path.join(b, "config.json")).read() == before)
check("W4", "argv is --host-uds=all with no --network flag",
      ex and ex[1][1] == "--host-uds=all"
      and not any(a.startswith("--network") for a in ex[1]))
shutil.rmtree(b, ignore_errors=True)

# --- W5: unrecognised + stray netns (Review 5 B-2) --------------------
b = make_bundle(["/usr/bin/someapp", "--serve"], with_netns=True)
ex, code = run_wrap(bundle_argv(b))
check("W5", "unrecognised bundle exec'd", ex is not None)
check("W5", "netns stripped from UNRECOGNISED bundle", not has_netns(b))
check("W5", "argv is create + network=none",
      ex and ex[1][1:3] == ["--host-uds=create", "--network=none"])
shutil.rmtree(b, ignore_errors=True)

# --- W6: unrecognised, no netns ---------------------------------------
b = make_bundle(["/usr/bin/someapp"], with_netns=False)
before = open(os.path.join(b, "config.json")).read()
ex, code = run_wrap(bundle_argv(b))
check("W6", "unrecognised bundle exec'd", ex is not None)
check("W6", "config untouched when no netns",
      open(os.path.join(b, "config.json")).read() == before)
check("W6", "argv is create + network=none",
      ex and ex[1][1:3] == ["--host-uds=create", "--network=none"])
shutil.rmtree(b, ignore_errors=True)

# --- W7: create with no bundle -----------------------------------------
ex, code = run_wrap(["create", "cid123"])
check("W7", "create with no bundle fails closed (no exec)",
      ex is None and code not in (None, 0))

# --- W8: corrupt config.json --------------------------------------------
b = tempfile.mkdtemp(prefix="wrap-bundle-")
with open(os.path.join(b, "config.json"), "w") as f:
    f.write("{not json")
ex, code = run_wrap(bundle_argv(b))
check("W8", "corrupt bundle fails closed (no exec)",
      ex is None and code not in (None, 0))
shutil.rmtree(b, ignore_errors=True)

# --- W9: lifecycle verb, no bundle --------------------------------------
ex, code = run_wrap(["start", "cid123"])
check("W9", "lifecycle verb passes through with legacy UDS shape",
      ex is not None and ex[1][1] == "--host-uds=all")

os.execv = _real_execv
print("---")
print("%d assertion(s) failed" % len(FAILURES))
sys.exit(len(FAILURES))

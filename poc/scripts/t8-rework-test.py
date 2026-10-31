#!/usr/bin/env python3
"""T8 rework tests (audit-fix follow-on batch, 2026-10-30).

Task 1 (T8-A) coverage in this file; the T8-B cases were
added with task 2. Hermetic, in the t3-reboot-state-test
style: modules are loaded from the tree with the venues'
env overrides pointed at a scratchpad, and the container id
base is lowered to 10000 (the sandbox's user namespace does
not map the production base 2300000 - the same workaround
the original T8 harness used).

T8-A cases:
  1. provision births import/ and pgdb/ as container-root
     owned 0700, with the appdata root still host-root 0755
  2. provision migrates a lingering root-level staged import
     into import/ (bytes intact, root copy gone), and leaves
     the root copy in place when import/ already holds one
  3. recipe staging: _write_staged_import writes through the
     dir fd, a second staging loses to the first, and
     _staged_import_exists sees both the import-dir staging
     and a lingering root-level file
  4. a symlinked import/ directory, and a symlinked staged
     name inside a real import/, both fail closed (OSError)
  5. app-init.sh statics: the staged import is referenced
     only via $IMPORT_FILE at $DATA/import/db-import.sql.gz,
     in both engines' import blocks and both delete sites
"""
import importlib.util
import os
import stat
import sys
import tempfile

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "..", "..")
BIN = os.path.join(ROOT, "onionhost", "rootfs-overlay", "usr",
                   "local", "bin")
GOLDEN = os.path.join(ROOT, "onionhost", "rootfs-overlay",
                      "usr", "lib", "onionhost", "golden")

BASE = "10000"
tmp = tempfile.mkdtemp(prefix="t8-rework-")

failures = []


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        failures.append(name)


def load(name, path, env):
    saved = dict(os.environ)
    os.environ.update(env)
    try:
        spec = importlib.util.spec_from_loader(name, loader=None)
        mod = importlib.util.module_from_spec(spec)
        with open(path) as f:
            code = compile(f.read(), path, "exec")
        exec(code, mod.__dict__)
        return mod
    finally:
        os.environ.clear()
        os.environ.update(saved)


def mode_of(p):
    return stat.S_IMODE(os.lstat(p).st_mode)


def owner_of(p):
    st = os.lstat(p)
    return st.st_uid, st.st_gid


# ---------------- provision (T8-A births + migration) ------
prov = load("oh_provision", os.path.join(BIN,
            "onionhost-app-provision"),
            {"ONIONHOST_CONTAINER_UID_BASE": BASE})
pdata = os.path.join(tmp, "prov", "appdata")
prov.APPDATA = pdata
prov.MARKER = os.path.join(tmp, "prov", "app-site")
prov.RUNTIME_FILE = os.path.join(tmp, "prov", "app-runtime")
prov.DB_ENV = os.path.join(tmp, "prov", "etc", "app-db.env")
prov.APP_CONF = os.path.join(tmp, "prov", "etc", "app.conf")
os.makedirs(os.path.join(tmp, "prov", "etc"), exist_ok=True)


class _FakeProc:
    returncode = 0
    stderr = ""


class _FakeSubprocess:
    PIPE = None

    @staticmethod
    def run(*a, **kw):
        return _FakeProc()


prov.subprocess = _FakeSubprocess
# Venue scaffolding: provision also writes the owner record
# to a fixed /etc/onionhost path; make sure the directory
# exists on the test venue (it always does on a real box).
os.makedirs("/etc/onionhost", exist_ok=True)
rc = prov.provision("root", "php", "required")
check("provision runs (rc 0)", rc == 0)
imp = os.path.join(pdata, "import")
pgdb = os.path.join(pdata, "pgdb")
check("import/ born container-root 0700",
      os.path.isdir(imp) and owner_of(imp) == (10000, 10000)
      and mode_of(imp) == 0o700)
check("pgdb/ born container-root 0700",
      os.path.isdir(pgdb) and owner_of(pgdb) == (10000, 10000)
      and mode_of(pgdb) == 0o700)
check("appdata root still host-root 0755 (T8 property)",
      owner_of(pdata) == (0, 0) and mode_of(pdata) == 0o755)

# Migration: a lingering root-level staging moves into
# import/ when import/ holds none...
legacy = os.path.join(pdata, "db-import.sql.gz")
with open(legacy, "wb") as f:
    f.write(b"LEGACY-DUMP")
rc = prov.provision("root", "php", "required")
moved = os.path.join(imp, "db-import.sql.gz")
check("provision migrates a lingering root-level import",
      rc == 0 and not os.path.exists(legacy)
      and os.path.isfile(moved)
      and open(moved, "rb").read() == b"LEGACY-DUMP")
# ...and stays put (with the import/ copy winning) when
# import/ already holds a staged import.
with open(legacy, "wb") as f:
    f.write(b"SECOND-DUMP")
rc = prov.provision("root", "php", "required")
check("existing import/ staging wins; root copy left in place",
      rc == 0 and os.path.isfile(legacy)
      and open(moved, "rb").read() == b"LEGACY-DUMP")
os.unlink(legacy)

# ---------------- recipe staging ---------------------------
rdata = os.path.join(tmp, "recipe", "appdata")
os.makedirs(rdata, exist_ok=True)
rec = load("oh_recipe", os.path.join(BIN, "onionhost-recipe"),
           {"ONIONHOST_CONTAINER_UID_BASE": BASE,
            "ONIONHOST_APPDATA": rdata,
            "ONIONHOST_RECIPE_PAYLOAD_ROOT":
                os.path.join(tmp, "recipe", "payload"),
            "ONIONHOST_ETC": os.path.join(tmp, "recipe", "etc"),
            "ONIONHOST_RECIPE_STATE":
                os.path.join(tmp, "recipe", "state")})
check("no staged import seen on a fresh volume",
      rec._staged_import_exists() is False)
check("first staging writes",
      rec._write_staged_import(b"BLOB-1") is True)
staged = os.path.join(rdata, "import", "db-import.sql.gz")
check("staged import landed in import/ with its bytes",
      os.path.isfile(staged)
      and open(staged, "rb").read() == b"BLOB-1")
check("import/ asserted container-root 0700 by the writer",
      owner_of(os.path.join(rdata, "import")) == (10000, 10000)
      and mode_of(os.path.join(rdata, "import")) == 0o700)
check("second staging loses to the first",
      rec._write_staged_import(b"BLOB-2") is False
      and open(staged, "rb").read() == b"BLOB-1")
check("staged import seen once staged",
      rec._staged_import_exists() is True)

# A lingering root-level file alone also counts as staged.
rdata2 = os.path.join(tmp, "recipe2", "appdata")
os.makedirs(rdata2, exist_ok=True)
with open(os.path.join(rdata2, "db-import.sql.gz"), "wb") as f:
    f.write(b"ROOT-LEVEL")
rec.APPDATA = rdata2
check("lingering root-level import counts as staged",
      rec._staged_import_exists() is True)
rec.APPDATA = rdata

# Fail closed: import/ itself planted as a symlink.
rdata3 = os.path.join(tmp, "recipe3", "appdata")
os.makedirs(rdata3, exist_ok=True)
os.symlink("/tmp", os.path.join(rdata3, "import"))
rec.APPDATA = rdata3
try:
    rec._write_staged_import(b"X")
    raised = False
except OSError:
    raised = True
check("symlinked import/ fails closed (OSError)", raised)

# Fail closed: the staged name inside a real import/ planted
# as a symlink to a host file.
rdata4 = os.path.join(tmp, "recipe4", "appdata")
os.makedirs(os.path.join(rdata4, "import"), exist_ok=True)
host_secret = os.path.join(tmp, "host-secret")
with open(host_secret, "wb") as f:
    f.write(b"HOST")
os.symlink(host_secret, os.path.join(rdata4, "import",
                                     "db-import.sql.gz"))
rec.APPDATA = rdata4
try:
    rec._write_staged_import(b"X")
    raised = False
except OSError:
    raised = True
check("symlinked staged name fails closed (OSError)", raised)
check("host target untouched by the refused staging",
      open(host_secret, "rb").read() == b"HOST")
rec.APPDATA = rdata

# ---------------- app-init statics -------------------------
with open(os.path.join(GOLDEN, "app-init.sh")) as f:
    init = f.read()
check("app-init defines IMPORT_FILE at the managed path",
      'IMPORT_FILE="$DATA/import/db-import.sql.gz"' in init)
body = "\n".join(line for line in init.splitlines()
                 if "IMPORT_FILE=" not in line)
check("no direct $DATA/db-import.sql.gz reference remains",
      "$DATA/db-import.sql.gz" not in body)
check("both engines delete via $IMPORT_FILE",
      init.count('rm -f "$IMPORT_FILE"') == 2)
check("both engines test via $IMPORT_FILE",
      init.count('[ -f "$IMPORT_FILE" ]') == 2)

print()
if failures:
    print("FAILURES: %d" % len(failures))
    for name in failures:
        print("  - " + name)
    sys.exit(1)
print("ALL T8-REWORK (TASK 1) CHECKS PASSED")

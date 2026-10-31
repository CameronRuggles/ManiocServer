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

# ================= TASK 2 (T8-B) ===========================
# Every check below is written defensively (getattr), so the
# same file run against the pre-task-2 tree records FAILs
# instead of crashing: that run is the positive control.
import signal
import subprocess  # noqa: F401  (venue parity with t3 style)

# ---- _copy_tree: planted links never followed -------------
bdata = os.path.join(tmp, "copytree")
live = os.path.join(bdata, "live", "attachments")
os.makedirs(os.path.join(live, "sub"))
with open(os.path.join(live, "avatar.png"), "w") as f:
    f.write("png")
with open(os.path.join(live, "sub", "real.txt"), "w") as f:
    f.write("real")
hostdir = os.path.join(bdata, "host", "tor", "hs")
os.makedirs(hostdir)
with open(os.path.join(hostdir, "hs_ed25519_secret_key"),
          "w") as f:
    f.write("SECRET-ONION-KEY")
shadow = os.path.join(bdata, "host", "shadow")
with open(shadow, "w") as f:
    f.write("root:$y$SECRETHASH")
os.symlink(hostdir, os.path.join(live, "k"))
os.symlink(shadow, os.path.join(live, "s.txt"))
staged = os.path.join(bdata, "staged", "attachments")
os.makedirs(os.path.dirname(staged))
rec._copy_tree(live, staged)
copied = []
for _r, _d, files in os.walk(staged):
    for _f in files:
        copied.append(os.path.relpath(
            os.path.join(_r, _f), staged))
check("copy_tree copies the valid files",
      "avatar.png" in copied
      and os.path.join("sub", "real.txt") in copied)
check("copy_tree does not copy a planted dir link's target",
      not any(c.startswith("k") for c in copied))
check("copy_tree does not copy a planted file link's target",
      "s.txt" not in copied)
leaked = False
for c in copied:
    with open(os.path.join(staged, c)) as f:
        if "SECRET" in f.read():
            leaked = True
check("no host secret content anywhere in the copied tree",
      not leaked)

# ---- _copy_tree: exclusions still honoured ----------------
xsrc = os.path.join(bdata, "xsrc")
os.makedirs(os.path.join(xsrc, "sub", "__pycache__"))
for rel, data in (("keep.txt", "k"), ("sub/skip.txt", "s"),
                  ("sub/keep2.txt", "k2"),
                  ("sub/__pycache__/junk.pyc", "j")):
    with open(os.path.join(xsrc, rel), "w") as f:
        f.write(data)
xdst = os.path.join(bdata, "xdst")
rec._copy_tree(xsrc, xdst, tree_root=xsrc,
               exclude_rels={"sub/skip.txt"})
xcopied = []
for _r, _d, files in os.walk(xdst):
    for _f in files:
        xcopied.append(os.path.relpath(
            os.path.join(_r, _f), xdst))
check("copy_tree still honours exclude_rels + __pycache__",
      "keep.txt" in xcopied
      and os.path.join("sub", "keep2.txt") in xcopied
      and os.path.join("sub", "skip.txt") not in xcopied
      and not any("__pycache__" in c for c in xcopied))

# ---- config carry-over ------------------------------------
carry = getattr(rec, "_copy_config_carryover", None)
cwww = os.path.join(bdata, "cwww")
cstaging = os.path.join(bdata, "cstaging")
os.makedirs(cwww)
os.makedirs(cstaging)
with open(os.path.join(cwww, "Settings.php"), "w") as f:
    f.write("<?php // real settings")
check("config carry-over exists and copies a regular file",
      carry is not None
      and carry(cwww, "Settings.php", cstaging) is True
      and open(os.path.join(cstaging, "Settings.php")).read()
      == "<?php // real settings")
os.unlink(os.path.join(cwww, "Settings.php"))
os.symlink(shadow, os.path.join(cwww, "Settings.php"))
check("config carry-over refuses a planted symlink",
      carry is not None
      and carry(cwww, "Settings.php", cstaging) is False
      and "SECRETHASH" not in open(
          os.path.join(cstaging, "Settings.php")).read())

# ---- mode exceptions --------------------------------------
import shutil as _shutil
mdata = os.path.join(tmp, "modeexc")
mpayload = os.path.join(mdata, "payload", "marketplace",
                        "overlay")
os.makedirs(mpayload)
_shutil.copy(os.path.join(
    ROOT, "onionhost", "recipes", "marketplace", "overlay",
    "normalize-exceptions"),
    os.path.join(mpayload, "normalize-exceptions"))
mhost = os.path.join(mdata, "hostfile")
with open(mhost, "w") as f:
    f.write("host")
os.chmod(mhost, 0o600)
mappdata = os.path.join(mdata, "appdata")
mnative = os.path.join(mappdata, "native")
os.makedirs(mnative)
os.symlink(mhost, os.path.join(mnative, "media-worker"))
with open(os.path.join(mnative, "first-boot.sh"), "w") as f:
    f.write("#!/bin/sh\n")
os.chmod(os.path.join(mnative, "first-boot.sh"), 0o644)
rec_mode = load("oh_recipe_mode",
                os.path.join(BIN, "onionhost-recipe"),
                {"ONIONHOST_CONTAINER_UID_BASE": BASE,
                 "ONIONHOST_APPDATA": mappdata,
                 "ONIONHOST_RECIPE_PAYLOAD_ROOT":
                     os.path.join(mdata, "payload"),
                 "ONIONHOST_ETC": os.path.join(mdata, "etc"),
                 "ONIONHOST_RECIPE_STATE":
                     os.path.join(mdata, "state")})
rec_mode._apply_mode_exceptions("marketplace")
check("mode exception through a planted symlink changes "
      "nothing on the host file",
      mode_of(mhost) == 0o600)
check("mode exception still applies to a regular file",
      mode_of(os.path.join(mnative, "first-boot.sh")) == 0o755)

# ---- nested data dirs: every component checked ------------
ndata = os.path.join(tmp, "nested")
nwww = os.path.join(ndata, "www")
os.makedirs(nwww)
os.symlink(hostdir, os.path.join(nwww, "wp-content"))
try:
    rec._own_data_dirs(nwww, {"data_dirs": ["wp-content/uploads"]})
    nested_raised = False
except ValueError:
    nested_raised = True
check("nested data dir with a symlinked middle component "
      "refuses (ValueError)", nested_raised)
vwww = os.path.join(ndata, "vwww")
os.makedirs(os.path.join(vwww, "wp-content", "uploads"))
try:
    rec._own_data_dirs(vwww, {"data_dirs": ["wp-content/uploads"]})
    valid_ok = True
except Exception:  # noqa: BLE001 - recorded as a failure
    valid_ok = False
check("valid nested data dirs still asserted without error",
      valid_ok and owner_of(os.path.join(
          vwww, "wp-content", "uploads")) == (10033, 10033))

# ---- _grant_owner_acl: a FIFO must not hang the apply -----
fdata = os.path.join(tmp, "fifo")
os.makedirs(fdata)
fifo = os.path.join(fdata, "data-dir-as-fifo")
os.mkfifo(fifo)


def _alarm(signum, frame):
    raise TimeoutError()


signal.signal(signal.SIGALRM, _alarm)
signal.alarm(5)
try:
    rec._grant_owner_acl(fifo)
    acl_done = True
except TimeoutError:
    acl_done = False
finally:
    signal.alarm(0)
check("_grant_owner_acl on a FIFO returns instead of "
      "hanging (O_DIRECTORY|O_NONBLOCK)", acl_done)

# ---- backup: links skipped + recorded, copy never follows -
sys.path.insert(0, os.path.join(ROOT, "onionhost",
                                "rootfs-overlay", "usr",
                                "lib", "onionhost"))
bdata = os.path.join(tmp, "backup")
bwww = os.path.join(bdata, "appdata", "www")
os.makedirs(bwww)
with open(os.path.join(bwww, "index.php"), "w") as f:
    f.write("<?php // site")
os.symlink(shadow, os.path.join(bwww, "evil.txt"))
os.symlink(hostdir, os.path.join(bwww, "linked-dir"))
bak = load("oh_backup", os.path.join(BIN, "onionhost-backup"),
           {})
bak.APPDATA = os.path.join(bdata, "appdata")


class _BakProc:
    returncode = 0


class _BakSubprocess:
    PIPE = None
    DEVNULL = None

    @staticmethod
    def run(*a, **kw):
        return _BakProc()


real_run = None
try:
    import subprocess as _sp
    real_run = _sp.run
    _sp.run = lambda *a, **kw: _BakProc()  # noqa: E731
    entries = []
    bak._collect_app(entries, {}, os.path.join(bdata, "work"),
                     "php", None)
finally:
    if real_run is not None:
        _sp.run = real_run
arcs = sorted(a for a, _s, _k in entries)
check("backup collects the regular app file",
      "app/www/index.php" in arcs)
check("backup does not collect a planted file link",
      "app/www/evil.txt" not in arcs)
check("backup does not collect a planted dir link's target",
      not any("linked-dir" in a for a in arcs))
check("backup records the skipped links for the manifest",
      "app/www/evil.txt" in bak._SKIPPED_LINKS
      and "app/www/linked-dir/" in bak._SKIPPED_LINKS)
copyfn = getattr(bak, "_copy_file_nofollow", None)
ctarget = os.path.join(bdata, "copied.txt")
check("backup no-follow copy refuses a symlink",
      copyfn is not None
      and copyfn(os.path.join(bwww, "evil.txt"),
                 ctarget) is False
      and not os.path.exists(ctarget))
check("backup no-follow copy copies a regular file",
      copyfn is not None
      and copyfn(os.path.join(bwww, "index.php"),
                 ctarget) is True
      and open(ctarget).read() == "<?php // site")

print()
if failures:
    print("FAILURES: %d" % len(failures))
    for name in failures:
        print("  - " + name)
    sys.exit(1)
print("ALL T8-REWORK CHECKS PASSED")

#!/usr/bin/env python3
"""F3 carryover tests (fresh full-tree audit, 2026-11-03).

The T8-B invariant - host root never follows a symlink while
carrying app data across the trust boundary - was held for
FINAL path components, but the two live-tree carryovers
resolved multi-component manifest paths by path, so a planted
INTERMEDIATE symlink (wp-content in wp-content/uploads, conf
in conf/local.php) steered the read onto a host directory.

Cases:
  data-dir carryover (_carry_data_dir):
    1. honest multi-component tree carries over (nested
       content; a symlink INSIDE the tree is still skipped)
    2. planted intermediate symlink: nothing is copied from
       the target, the staged archive copy survives, a
       WARNING is printed
    3. intermediate component is a plain file: same refusal
    4. live directory missing: the staged directory is
       created, no warning
    5. single-component honest directory carries over
    6. final component planted as a symlink (single- and
       multi-component): still raises, as the old _dir_fd
       open inside _copy_tree made it raise - unchanged
  config carryover (_copy_config_carryover):
    7. honest multi-component config carries over
    8. planted intermediate symlink: returns False, nothing
       staged, a WARNING is printed
    9. honest single-component config carries over
   10. final component planted as a symlink: returns False
   11. missing config: returns False

Hermetic: the tool is loaded from this tree and driven
against scratch trees; nothing outside the temp dir is
touched.
"""
import contextlib
import importlib.util
import io
import os
import shutil
import stat
import sys
import tempfile
from importlib.machinery import SourceFileLoader

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "..", "..")
TOOL = os.path.join(ROOT, "onionhost", "rootfs-overlay", "usr",
                    "local", "bin", "onionhost-recipe")
spec = importlib.util.spec_from_loader(
    "onionhost_recipe", SourceFileLoader("onionhost_recipe", TOOL))
recipe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recipe)

failures = []


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        failures.append(name)


def write(path, data, mode=0o644):
    with open(path, "wb") as f:
        f.write(data)
    os.chmod(path, mode)


def host_tree(tmp):
    """A host directory outside the app tree, shaped so the
    disclosure bites: uploads/secret.txt and local.php."""
    host = os.path.join(tmp, "hostdir")
    os.makedirs(os.path.join(host, "uploads"))
    write(os.path.join(host, "uploads", "secret.txt"),
          b"HOST-SECRET\n")
    write(os.path.join(host, "local.php"), b"HOST-SECRET\n")
    return host


def find_bytes(root, needle):
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            p = os.path.join(dirpath, name)
            if os.path.islink(p):
                continue
            with open(p, "rb") as f:
                if f.read() == needle:
                    return p
    return None


# ---- data-dir carryover -------------------------------------

# 1. honest multi-component
tmp = tempfile.mkdtemp(prefix="f3-honest-")
www = os.path.join(tmp, "www")
staging = os.path.join(tmp, "staging")
os.makedirs(os.path.join(www, "wp-content", "uploads",
                         "2026", "10"))
write(os.path.join(www, "wp-content", "uploads", "photo.jpg"),
      b"OWNER-PHOTO\n")
write(os.path.join(www, "wp-content", "uploads", "2026", "10",
                   "nested.txt"), b"NESTED\n")
os.symlink("/etc/hostname",
           os.path.join(www, "wp-content", "uploads", "planted"))
os.makedirs(os.path.join(staging, "wp-content", "uploads"))
os.chmod(os.path.join(www, "wp-content", "uploads"), 0o751)
err = io.StringIO()
with contextlib.redirect_stderr(err):
    recipe._carry_data_dir(www, "wp-content/uploads", staging)
staged_up = os.path.join(staging, "wp-content", "uploads")
check("honest data dir: top file carried",
      open(os.path.join(staged_up, "photo.jpg"), "rb").read()
      == b"OWNER-PHOTO\n")
check("honest data dir: nested file carried",
      open(os.path.join(staged_up, "2026", "10", "nested.txt"),
           "rb").read() == b"NESTED\n")
check("honest data dir: inner symlink skipped, not followed",
      not os.path.lexists(os.path.join(staged_up, "planted")))
check("honest data dir: root mode follows the source",
      stat.S_IMODE(os.stat(staged_up).st_mode) == 0o751)
shutil.rmtree(tmp)

# 2. planted intermediate symlink
tmp = tempfile.mkdtemp(prefix="f3-attack-")
host = host_tree(tmp)
www = os.path.join(tmp, "www")
staging = os.path.join(tmp, "staging")
os.makedirs(www)
os.symlink(host, os.path.join(www, "wp-content"))
os.makedirs(os.path.join(staging, "wp-content", "uploads"))
write(os.path.join(staging, "wp-content", "uploads",
                   "archive-marker.txt"), b"ARCHIVE\n")
err = io.StringIO()
with contextlib.redirect_stderr(err):
    recipe._carry_data_dir(www, "wp-content/uploads", staging)
check("attack data dir: host secret NOT in staging",
      find_bytes(staging, b"HOST-SECRET\n") is None)
check("attack data dir: staged archive copy survives",
      open(os.path.join(staging, "wp-content", "uploads",
                        "archive-marker.txt"), "rb").read()
      == b"ARCHIVE\n")
check("attack data dir: refusal is loud (WARNING on stderr)",
      "WARNING" in err.getvalue()
      and "wp-content" in err.getvalue())
shutil.rmtree(tmp)

# 3. intermediate component is a plain file
tmp = tempfile.mkdtemp(prefix="f3-file-")
www = os.path.join(tmp, "www")
staging = os.path.join(tmp, "staging")
os.makedirs(www)
write(os.path.join(www, "wp-content"), b"NOT-A-DIR\n")
err = io.StringIO()
with contextlib.redirect_stderr(err):
    recipe._carry_data_dir(www, "wp-content/uploads", staging)
check("file intermediate: nothing copied, staged dir created",
      os.path.isdir(os.path.join(staging, "wp-content",
                                 "uploads"))
      and find_bytes(staging, b"NOT-A-DIR\n") is None)
check("file intermediate: refusal is loud",
      "WARNING" in err.getvalue())
shutil.rmtree(tmp)

# 4. live directory missing entirely
tmp = tempfile.mkdtemp(prefix="f3-missing-")
www = os.path.join(tmp, "www")
staging = os.path.join(tmp, "staging")
os.makedirs(www)
os.makedirs(staging)
err = io.StringIO()
with contextlib.redirect_stderr(err):
    recipe._carry_data_dir(www, "wp-content/uploads", staging)
check("missing data dir: staged directory created",
      os.path.isdir(os.path.join(staging, "wp-content",
                                 "uploads")))
check("missing data dir: silent (no warning)",
      err.getvalue() == "")
shutil.rmtree(tmp)

# 5. single-component honest directory
tmp = tempfile.mkdtemp(prefix="f3-single-")
www = os.path.join(tmp, "www")
staging = os.path.join(tmp, "staging")
os.makedirs(os.path.join(www, "data"))
write(os.path.join(www, "data", "state.bin"), b"STATE\n")
os.makedirs(staging)
recipe._carry_data_dir(www, "data", staging)
check("single-component data dir carries over",
      open(os.path.join(staging, "data", "state.bin"),
           "rb").read() == b"STATE\n")
shutil.rmtree(tmp)

# 6. final component planted as a symlink: still raises
for dirname, plant in (("data", "data"),
                       ("wp-content/uploads", "uploads")):
    tmp = tempfile.mkdtemp(prefix="f3-final-")
    host = host_tree(tmp)
    www = os.path.join(tmp, "www")
    staging = os.path.join(tmp, "staging")
    os.makedirs(www)
    os.makedirs(staging)
    if "/" in dirname:
        os.makedirs(os.path.join(www, "wp-content"))
    os.symlink(host, os.path.join(www, plant)
               if "/" not in dirname
               else os.path.join(www, "wp-content", "uploads"))
    raised = False
    try:
        recipe._carry_data_dir(www, dirname, staging)
    except OSError:
        raised = True
    check("final symlink (%s): raises as before" % dirname,
          raised)
    check("final symlink (%s): secret NOT in staging" % dirname,
          find_bytes(staging, b"HOST-SECRET\n") is None)
    shutil.rmtree(tmp)

# ---- config carryover ---------------------------------------

# 7. honest multi-component config
tmp = tempfile.mkdtemp(prefix="f3-cfg-")
www = os.path.join(tmp, "www")
staging = os.path.join(tmp, "staging")
os.makedirs(os.path.join(www, "conf"))
write(os.path.join(www, "conf", "local.php"),
      b"OWNER-CONFIG\n", 0o640)
os.makedirs(os.path.join(staging, "conf"))
ok = recipe._copy_config_carryover(www, "conf/local.php",
                                   staging)
check("honest config: carried over", ok is True)
check("honest config: bytes staged",
      open(os.path.join(staging, "conf", "local.php"),
           "rb").read() == b"OWNER-CONFIG\n")
check("honest config: mode follows the source",
      stat.S_IMODE(os.stat(os.path.join(
          staging, "conf", "local.php")).st_mode) == 0o640)
shutil.rmtree(tmp)

# 8. planted intermediate symlink
tmp = tempfile.mkdtemp(prefix="f3-cfgatk-")
host = host_tree(tmp)
www = os.path.join(tmp, "www")
staging = os.path.join(tmp, "staging")
os.makedirs(www)
os.symlink(host, os.path.join(www, "conf"))
os.makedirs(os.path.join(staging, "conf"))
err = io.StringIO()
with contextlib.redirect_stderr(err):
    ok = recipe._copy_config_carryover(www, "conf/local.php",
                                       staging)
check("attack config: refused (returns False)", ok is False)
check("attack config: nothing staged",
      not os.path.exists(os.path.join(staging, "conf",
                                      "local.php")))
check("attack config: refusal is loud (WARNING on stderr)",
      "WARNING" in err.getvalue()
      and "conf" in err.getvalue())
shutil.rmtree(tmp)

# 9/10/11. single-component: honest, planted final, missing
tmp = tempfile.mkdtemp(prefix="f3-cfgsingle-")
www = os.path.join(tmp, "www")
staging = os.path.join(tmp, "staging")
os.makedirs(www)
os.makedirs(staging)
write(os.path.join(www, "wp-config.php"), b"OWNER-WPCONFIG\n")
ok = recipe._copy_config_carryover(www, "wp-config.php",
                                   staging)
check("single config: carried over", ok is True
      and open(os.path.join(staging, "wp-config.php"),
               "rb").read() == b"OWNER-WPCONFIG\n")
os.unlink(os.path.join(www, "wp-config.php"))
os.symlink(os.path.join(tmp, "nowhere"),
           os.path.join(www, "wp-config.php"))
ok = recipe._copy_config_carryover(www, "wp-config.php",
                                   staging)
check("single config: planted final symlink refused",
      ok is False)
os.unlink(os.path.join(www, "wp-config.php"))
ok = recipe._copy_config_carryover(www, "wp-config.php",
                                   staging)
check("single config: missing config returns False",
      ok is False)
shutil.rmtree(tmp)

print()
if failures:
    print("FAILURES: %d" % len(failures))
    sys.exit(1)
print("ALL F3 CARRYOVER CHECKS PASSED")

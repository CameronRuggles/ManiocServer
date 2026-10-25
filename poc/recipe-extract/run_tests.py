#!/usr/bin/env python3
"""Regression tests for onionhost-recipe._extract_tree archive safety
(review 2026-10-25, finding F4).

Run: python3 poc/recipe-extract/run_tests.py
Exit status: number of failed assertions.

Cases:
  benign zip      - ordinary files extract and are readable
  traversal zip   - a member named ../../evil must be REFUSED
                    (before this fix it was silently sanitised into
                    the destination by zipfile; refusal is the
                    fail-closed behaviour the tar path already had)
  symlink zip     - a symlink member must be REFUSED (extracting it
                    as a regular file, zipfile's default, would
                    plant a file whose name later tooling could
                    mistake for the link; a live symlink would be
                    worse)
  traversal tar   - a tar member escaping the destination must be
                    REFUSED (filter="data" - pre-existing behaviour,
                    kept under test so it cannot regress silently)
Paths are derived from this file's location, never a hardcoded
home directory (review 2026-10-25, finding F7).
"""
import importlib.util
import io
import os
import sys
import tarfile
import tempfile
import zipfile
from importlib.machinery import SourceFileLoader

HERE = os.path.dirname(os.path.abspath(__file__))
TREE = os.path.abspath(os.path.join(HERE, "..", ".."))
TOOL = os.path.join(
    TREE, "onionhost/rootfs-overlay/usr/local/bin/onionhost-recipe")

spec = importlib.util.spec_from_loader(
    "onionhost_recipe", SourceFileLoader("onionhost_recipe", TOOL))
recipe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recipe)

FAILS = []


def check(desc, cond):
    print("%s %s" % ("PASS" if cond else "FAIL", desc))
    if not cond:
        FAILS.append(desc)


def make_zip(path, members):
    with zipfile.ZipFile(path, "w") as z:
        for name, data, link in members:
            if link:
                zi = zipfile.ZipInfo(name)
                zi.create_system = 3
                zi.external_attr = (0o120777 << 16)
                z.writestr(zi, data)
            else:
                z.writestr(name, data)


work = tempfile.mkdtemp(prefix="recipe-extract-test-")

# benign
zp = os.path.join(work, "ok.zip")
make_zip(zp, [("index.php", "<?php // ok", False),
              ("sub/page.txt", "hello", False)])
root, seed, settings = recipe._extract_tree(
    zp, os.path.join(work, "w-ok"), {})
check("benign zip extracts",
      os.path.isfile(os.path.join(work, "w-ok", "extract",
                                  "index.php")))

# traversal
zp = os.path.join(work, "evil.zip")
make_zip(zp, [("../../evil.txt", "x", False),
              ("index.php", "<?php", False)])
try:
    recipe._extract_tree(zp, os.path.join(work, "w-evil"), {})
    refused = False
except ValueError:
    refused = True
check("traversal zip refused with ValueError", refused)
check("traversal zip wrote nothing outside its workdir",
      not os.path.exists(os.path.join(work, "evil.txt")))

# symlink member
zp = os.path.join(work, "link.zip")
make_zip(zp, [("link-to-etc", "/etc", True),
              ("index.php", "<?php", False)])
try:
    recipe._extract_tree(zp, os.path.join(work, "w-link"), {})
    refused = False
except ValueError:
    refused = True
check("symlink zip member refused with ValueError", refused)

# tar traversal (pre-existing filter="data" behaviour)
tp = os.path.join(work, "evil.tar.gz")
with tarfile.open(tp, "w:gz") as t:
    data = b"x"
    ti = tarfile.TarInfo("../../evil-tar.txt")
    ti.size = len(data)
    t.addfile(ti, io.BytesIO(data))
try:
    recipe._extract_tree(tp, os.path.join(work, "w-tar"), {})
    refused = False
except Exception:
    refused = True
check("traversal tar refused", refused)

print("---")
print("%d assertion(s) failed" % len(FAILS))
sys.exit(len(FAILS))

#!/usr/bin/env python3
"""Version-ordering proof for the onionhost-images package
(full-tree audit 2026-11-03, Finding 1).

The updater judges the images package by dpkg ordering:
repo_best_version takes the dpkg-max the repository offers,
and the high-water mark refuses anything that compares lt
against it. The package version used to be VERSION+img.<hash>
- a content hash, which orders lexically, not by build order.
This harness builds two same-base image sets with the REAL
build script, choosing contents whose hashes are INVERTED
against build order (the newer set carries the lower hash -
the case that broke the channel), and drives the updater's
real selection/refusal functions with them:

  (v1) the versions carry the build counter in build order
       (epoch-scheme), with the content hash unchanged;
  (v2) repo_best_version selects the NEWER set, not the
       higher hash;
  (v3) the newer set is not refused under the older mark;
  (v4) the older set IS refused under the newer mark;
  (v5) transition: even the lowest counter version sorts
       above the worst pre-scheme mark (epoch beats hash);
  (v6) rebuilding identical content at the same counter
       reproduces the identical version.

Run against a pre-fix tree the same assertions fail - the
repository's best is the older set and the newer build
compares lt against its mark - which is the control.

Run: python3 poc/images-delivery/version_order_tests.py [tree]
Exit status: number of failed assertions.
"""
import hashlib
import importlib.util
import os
import subprocess
import sys
import tempfile
import types
from importlib.machinery import SourceFileLoader

HERE = os.path.dirname(os.path.abspath(__file__))
TREE = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else \
    os.path.abspath(os.path.join(HERE, "..", ".."))
BUILD = os.path.join(TREE, "build/build-onionhost-images-deb.sh")
UPDATER = os.path.join(
    TREE, "onionhost/rootfs-overlay/usr/local/bin/onionhost-update")
TARS = ["onionhost-tor.tar", "onionhost-web.tar", "onionhost-app.tar"]
BASE = "1.0.0"

FAILS = []


def check(desc, cond):
    print("%s %s" % ("PASS" if cond else "FAIL", desc))
    if not cond:
        FAILS.append(desc)


def combined_of(seed):
    lines = []
    for t in TARS:
        content = ("imgid-content-%s-%s\n" % (seed, t)).encode()
        lines.append("%s: %s\n" % (t, hashlib.sha256(content)
                                   .hexdigest()))
    return hashlib.sha256("".join(lines).encode()).hexdigest()


def dpkg_lt(a, b):
    return subprocess.run(
        ["dpkg", "--compare-versions", a, "lt", b]).returncode == 0


def build(seed, counter, work):
    imgdir = os.path.join(work, "imgs-%s" % seed)
    outdir = os.path.join(work, "out-%s-%s" % (seed, counter))
    os.makedirs(imgdir, exist_ok=True)
    os.makedirs(outdir, exist_ok=True)
    for t in TARS:
        with open(os.path.join(imgdir, t), "w") as f:
            f.write("imgid-content-%s-%s\n" % (seed, t))
    env = dict(os.environ)
    if counter is not None:
        env["IMAGES_BUILD_COUNTER"] = str(counter)
    proc = subprocess.run(["bash", BUILD, imgdir, BASE, outdir],
                          env=env, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError("build failed: %s" % proc.stderr)
    debs = [d for d in os.listdir(outdir) if d.endswith(".deb")]
    assert len(debs) == 1, debs
    return subprocess.run(
        ["dpkg-deb", "-f", os.path.join(outdir, debs[0]), "Version"],
        capture_output=True, text=True).stdout.strip()


def load_updater(versions):
    spec = importlib.util.spec_from_loader(
        "upd_v", SourceFileLoader("upd_v", UPDATER))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    real_run = subprocess.run

    def staged(argv, *a, **k):
        if argv[:2] == ["dpkg", "--compare-versions"]:
            return real_run(argv, *a, **k)
        if argv[0] == "apt-cache":
            out = "".join(
                "%s | %s | http://repo.invalid stable/main\n"
                % (argv[-1], v) for v in versions)
            return types.SimpleNamespace(returncode=0, stdout=out)
        return types.SimpleNamespace(returncode=1, stdout="")

    m.subprocess = types.SimpleNamespace(
        run=staged, PIPE=subprocess.PIPE, DEVNULL=subprocess.DEVNULL,
        STDOUT=subprocess.STDOUT,
        TimeoutExpired=subprocess.TimeoutExpired)
    return m


def main():
    work = tempfile.mkdtemp(prefix="version-order-")
    # Two sets whose HASH order inverts their BUILD order: the
    # older set must carry the higher hash, or the control case
    # below is not the defect's shape.
    old_combined = combined_of("oldset")
    new_seed = None
    for i in range(200):
        cand = combined_of("newset-%d" % i)
        if dpkg_lt("%s+img.%s" % (BASE, cand[:12]),
                   "%s+img.%s" % (BASE, old_combined[:12])):
            new_seed, new_combined = "newset-%d" % i, cand
            break
    assert new_seed is not None, "no inverted seed found"
    print("hash order inverted: newer %s < older %s (12-hex)"
          % (new_combined[:12], old_combined[:12]))

    v_old = build("oldset", 7, work)
    v_new = build(new_seed, 8, work)
    check("(v1) versions are epoch+counter in build order, "
          "hashes unchanged",
          v_old == "1:%s+img.7.%s" % (BASE, old_combined[:12])
          and v_new == "1:%s+img.8.%s" % (BASE, new_combined[:12]))

    U = load_updater([v_old, v_new])
    check("(v2) repo_best_version selects the newer set",
          U.repo_best_version("onionhost-images") == v_new)
    check("(v3) the newer set is not refused under the old mark",
          not U.dpkg_compare(v_new, "lt", v_old))
    check("(v4) the older set is refused under the new mark",
          U.dpkg_compare(v_old, "lt", v_new))

    v_first = build("oldset", 1, work)
    worst_old_mark = "%s+img.%s" % (BASE, "f" * 12)
    check("(v5) the first counter version beats the worst "
          "pre-scheme mark", U.dpkg_compare(v_first, "gt",
                                            worst_old_mark))
    check("(v6) same content + same counter reproduces the "
          "identical version", build("oldset", 7, work) == v_old)

    print("---")
    print("%d assertion(s) failed" % len(FAILS))
    return len(FAILS)


if __name__ == "__main__":
    sys.exit(main())

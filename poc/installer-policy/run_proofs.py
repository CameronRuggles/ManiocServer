#!/usr/bin/env python3
"""A26 proofs: recipes are installers, not update channels
(owner decision 2026-10-21).

End-to-end, with the REAL builder, the REAL applier and the
REAL generated postinst - the updater half of the policy (never
installs recipe packages, reports owner_maintained, floors
cannot fail-close) is proven in poc/gate4fix R1-R4; this venue
proves the tree-level half:

  A  install WordPress from the v1 recipe package (apply +
     install hook, so the install is COMPLETE), modify and add
     files the way an owner would, then configure the v2
     package over it (its real postinst, run against the real
     absolute paths in a mount namespace) -> the postinst
     reports the app already installed and the whole app tree
     plus the recipe state record stay BYTE-IDENTICAL.
  B  a FRESH venue (no state record) configuring the same v2
     package -> the postinst installs it, at the v2 payload
     version, v2 file content and all: fresh installs get the
     current recipe version.
  C1 a fresh venue whose payload declares a security floor
     ABOVE its own version -> the applier refuses the first
     install before placing anything (floors gate install
     time).
  C2 the completed venue A install re-applied with that same
     floor-raised payload -> the apply proceeds: a floor never
     judges an app that is already installed.

The v2 package is an honest repackage of the v1 recipe (the
builder's own machinery): same app, package version bumped,
one shipped file changed inside the archive, pin updated - the
shape of a recipe-only fix release, exactly what used to swap
an installed app's tree through the update channel.

Exit status: number of failed assertions (0 = all pass).
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
TREE = os.path.expanduser("~/workspace/onion-host-os")
TOOL = os.path.join(
    TREE, "onionhost/rootfs-overlay/usr/local/bin/onionhost-recipe")
BUILDER = os.path.join(TREE, "build/build-recipe-deb.sh")
SRC_RECIPE = os.path.join(TREE, "onionhost/recipes/wordpress")
WORK = os.path.join(HERE, "work")
ONION = "b" * 52 + "d.onion"
V1 = "7.1.3+oh.1"
V2 = "7.1.3+oh.2"
FLOOR_V3 = "99.0+oh.1"
MARKER = "A26-PROOF-MARKER packaged payload v2"
ADMIN_USER = "siteadmin"
ADMIN_PASS = "Proof-Admin-1"
SITE_TITLE = "Notes from the Proof Kitchen"

FAILURES = []


def check(name, cond):
    print("%s %s" % ("PASS" if cond else "FAIL", name))
    if not cond:
        FAILURES.append(name)


# ------------------------------------------------------------------
# Package building (the real builder, three honest packages)

def _rezip_with_marker(src_zip, dst_zip):
    """Copy the app archive, changing one shipped file's bytes
    (the readme gains a marker comment) - a payload difference
    a tree swap would have delivered."""
    zin = zipfile.ZipFile(src_zip)
    names = zin.namelist()
    target = next(n for n in names if n.endswith("/readme.html"))
    with zipfile.ZipFile(dst_zip, "w",
                         zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == target:
                data += ("\n<!-- %s -->\n" % MARKER).encode()
            zout.writestr(item, data)
    zin.close()
    return target


def build_packages():
    pkgs = os.path.join(WORK, "pkgs")
    shutil.rmtree(WORK, ignore_errors=True)
    os.makedirs(pkgs)
    built = {}
    for tag, version, floor, change in (
            ("v1", V1, None, False),
            ("v2", V2, None, True),
            ("v3", V2, FLOOR_V3, True)):
        rdir = os.path.join(WORK, "recipe-" + tag)
        shutil.copytree(SRC_RECIPE, rdir)
        if change:
            recipe = json.load(open(os.path.join(
                rdir, "recipe.json")))
            arc = os.path.join(rdir, "archive",
                               recipe["archive"]["file"])
            _rezip_with_marker(arc, arc + ".new")
            os.replace(arc + ".new", arc)
            with open(arc, "rb") as f:
                recipe["archive"]["sha256"] = hashlib.sha256(
                    f.read()).hexdigest()
            json.dump(recipe, open(os.path.join(
                rdir, "recipe.json"), "w"), indent=1)
        if floor:
            with open(os.path.join(rdir, "floor.txt"), "w") as f:
                f.write(floor + "\n")
        out = os.path.join(pkgs, tag)
        os.makedirs(out)
        r = subprocess.run([BUILDER, rdir, version, out],
                           capture_output=True, text=True)
        assert r.returncode == 0, r.stdout + r.stderr
        deb = os.path.join(
            out, "onionhost-recipe-wordpress_%s_all.deb" % version)
        assert os.path.isfile(deb), r.stdout
        ext = os.path.join(WORK, "extract-" + tag)
        subprocess.run(["dpkg-deb", "-x", deb, ext], check=True)
        ctl = os.path.join(WORK, "control-" + tag)
        subprocess.run(["dpkg-deb", "-e", deb, ctl], check=True)
        built[tag] = {
            "deb": deb, "extract": ext,
            "payload": os.path.join(
                ext, "usr/share/onionhost/recipes"),
            "postinst": os.path.join(ctl, "postinst"),
            "version": version}
    return built


# ------------------------------------------------------------------
# Venues (production-shaped: etc + varlib, env-override seams)

def make_venue(name):
    v = os.path.join(WORK, name)
    for d in ("etc", os.path.join("varlib", "appdata"),
              os.path.join("varlib", "recipes"),
              os.path.join("varlib", "tor", "hs")):
        os.makedirs(os.path.join(v, d))
    with open(os.path.join(v, "etc", "app-db.env"), "w") as f:
        f.write("DB_NAME=onionhost_app\nDB_USER=onionhost\n"
                "DB_PASSWORD=proof-only-password\n")
    with open(os.path.join(v, "etc", "recipe-selection"),
              "w") as f:
        f.write("wordpress\n")
    with open(os.path.join(v, "etc", "recipe-admin.env"),
              "w") as f:
        f.write("RECIPE_ID=wordpress\nRECIPE_ADMIN_USER=%s\n"
                "RECIPE_ADMIN_PASSWORD=%s\nRECIPE_SITE_TITLE=%s\n"
                % (ADMIN_USER, ADMIN_PASS, SITE_TITLE))
    with open(os.path.join(v, "varlib", "app-site"), "w") as f:
        f.write("{}\n")
    with open(os.path.join(v, "varlib", "tor", "hs",
                           "hostname"), "w") as f:
        f.write(ONION + "\n")
    return v


def tool_env(venue, payload_root):
    env = dict(os.environ)
    env.update({
        "ONIONHOST_RECIPE_PAYLOAD_ROOT": payload_root,
        "ONIONHOST_ETC": os.path.join(venue, "etc"),
        "ONIONHOST_APPDATA": os.path.join(venue, "varlib",
                                          "appdata"),
        "ONIONHOST_CONTAINER_UID_BASE": "0",
        "ONIONHOST_RECIPE_STATE": os.path.join(venue, "varlib",
                                               "recipes"),
        "ONIONHOST_HS_HOSTNAME": os.path.join(
            venue, "varlib", "tor", "hs", "hostname"),
        "ONIONHOST_EDGE_SOCK": os.path.join(venue, "edge.sock"),
    })
    return env


def run_tool(env, *args):
    return subprocess.run([sys.executable, TOOL] + list(args),
                          env=env, capture_output=True, text=True)


def www(venue, *parts):
    return os.path.join(venue, "varlib", "appdata", "www", *parts)


def state_of(venue):
    try:
        with open(os.path.join(venue, "varlib", "recipes",
                               "wordpress", "state.json")) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def snapshot(root):
    out = {}
    for dirpath, _dirs, files in os.walk(root):
        for name in files:
            p = os.path.join(dirpath, name)
            with open(p, "rb") as f:
                out[os.path.relpath(p, root)] = hashlib.sha256(
                    f.read()).hexdigest()
    return out


# ------------------------------------------------------------------
# The fake WordPress installer (the WP unit suite's pattern): the
# hook drives the app's own installer form over the edge socket.

FAKE_SERVER = r'''
import http.server
import json
import os
import socketserver
import sys
import urllib.parse

SOCK, UNIT = sys.argv[1], sys.argv[2]
FORM = ('<html><form id="setup" method="post" '
        'action="install.php?step=2">'
        '<input name="weblog_title"></form></html>')


class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _cap(self, form=None):
        with open(os.path.join(UNIT, "capture.jsonl"),
                  "a") as f:
            f.write(json.dumps({"method": self.command,
                                "path": self.path,
                                "form": form}) + "\n")

    def _send(self, body, code=200):
        b = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        self._cap()
        if self.path.startswith("/wp-admin/install.php"):
            return self._send(FORM)
        if self.path == "/":
            return self._send("<html><body>Hello world!"
                              "</body></html>")
        return self._send("<html>?</html>", 404)

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        form = dict(urllib.parse.parse_qsl(
            self.rfile.read(n).decode()))
        self._cap(form)
        return self._send(
            "<html><h1>Success!</h1><p>WordPress has been "
            "installed. Thank you, and enjoy!</p></html>")


class S(socketserver.ThreadingUnixStreamServer):
    daemon_threads = True


try:
    os.unlink(SOCK)
except FileNotFoundError:
    pass
S(SOCK, H).serve_forever()
'''


def complete_install(venue, env):
    """apply + install-hook against the fake installer: the
    install is COMPLETE (state seeded), as publish leaves it."""
    r = run_tool(env, "apply", "wordpress")
    assert r.returncode == 0, r.stdout + r.stderr
    server_py = os.path.join(venue, "fake_wp.py")
    with open(server_py, "w") as f:
        f.write(FAKE_SERVER)
    server = subprocess.Popen(
        [sys.executable, server_py,
         os.path.join(venue, "edge.sock"), venue],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(100):
            if os.path.exists(os.path.join(venue, "edge.sock")):
                break
            time.sleep(0.1)
        r = run_tool(env, "install-hook", "wordpress")
        assert r.returncode == 0 and "INSTALL_HOOK_OK" in \
            r.stdout, r.stdout + r.stderr
    finally:
        server.terminate()


# ------------------------------------------------------------------
# Postinst runs: the REAL generated maintainer script against
# the REAL absolute paths, in a private mount namespace.

_CREATED = []


def ensure_mountpoints():
    for d in ("/var/lib/onionhost", "/etc/onionhost",
              "/usr/share/onionhost",
              "/usr/share/onionhost/recipes"):
        if not os.path.isdir(d):
            os.makedirs(d)
            _CREATED.append(("dir", d))
    tool_link = "/usr/local/bin/onionhost-recipe"
    if not os.path.exists(tool_link):
        with open(tool_link, "w"):
            pass
        _CREATED.append(("file", tool_link))


def cleanup_mountpoints():
    for kind, path in reversed(_CREATED):
        try:
            if kind == "dir":
                os.rmdir(path)
            else:
                os.unlink(path)
        except OSError:
            pass


def run_postinst(venue, pkg):
    env = dict(os.environ)
    env["ONIONHOST_CONTAINER_UID_BASE"] = "0"
    script = " && ".join([
        "mount --bind %s /var/lib/onionhost"
        % os.path.join(venue, "varlib"),
        "mount --bind %s /etc/onionhost"
        % os.path.join(venue, "etc"),
        "mount --bind %s /usr/share/onionhost/recipes"
        % pkg["payload"],
        "mount --bind %s /usr/local/bin/onionhost-recipe" % TOOL,
        "sh %s configure" % pkg["postinst"]])
    # Mount namespace only (-m, not -rm): the runs are already
    # root, and a user namespace would refuse the applier's
    # chowns to the container uid mapping (EINVAL) - the venue
    # wants the real uid space with private mounts.
    return subprocess.run(["unshare", "-m", "bash", "-c", script],
                          env=env, capture_output=True, text=True)


def check_debver_cmp():
    """The applier's pure-Python Debian version comparison
    (it may not shell out to dpkg - minimal contexts have no
    dpkg binary) must agree with the real dpkg on the shapes
    that matter: the recipes' own versions, floors, tildes,
    epochs, revisions."""
    import importlib.machinery
    import importlib.util
    loader = importlib.machinery.SourceFileLoader("recipe_tool",
                                                  TOOL)
    spec = importlib.util.spec_from_loader("recipe_tool",
                                           loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    pairs = [("7.1.3+oh.1", "7.1.3+oh.1", 0),
             ("7.1.3+oh.1", "7.1.3+oh.2", -1),
             ("7.1.3+oh.2", "99.0+oh.1", -1),
             ("1.27.3+oh.1", "1.27.3+oh.10", -1),
             ("2026-07-14c+oh.1", "2026-07-14c+oh.1", 0),
             ("1.0~rc1", "1.0", -1),
             ("1:1.0", "2.0", 1),
             ("1.0-1", "1.0-2", -1),
             ("2.0.0", "10.0.0", -1)]
    for a, b, want in pairs:
        got = mod._debver_cmp(a, b)
        check("debver %s vs %s -> %d" % (a, b, want),
              (got > 0) - (got < 0) == want)


def main():
    check_debver_cmp()
    pkgs = build_packages()
    check("v1 and v2 payloads differ (the v2 archive changed)",
          snapshot(os.path.join(pkgs["v1"]["extract"], "usr"))
          != snapshot(os.path.join(pkgs["v2"]["extract"], "usr")))
    with open(os.path.join(pkgs["v2"]["payload"], "wordpress",
                           "manifest.json")) as f:
        check("v2 payload manifest carries the v2 version",
              json.load(f)["version"] == V2)
    ensure_mountpoints()
    try:
        # --- A: completed install + owner edits + v2 postinst --
        va = make_venue("venue-a")
        env_a = tool_env(va, pkgs["v1"]["payload"])
        complete_install(va, env_a)
        st = state_of(va)
        check("A: install completes at the v1 version",
              st.get("installed") and st.get("seeded")
              and st.get("version") == V1)
        r = run_tool(env_a, "is-installed", "wordpress")
        check("A: is-installed agrees (exit 0)", r.returncode == 0)

        # Owner modifications: edit a shipped file, add a
        # plugin, add an upload, tweak the config.
        with open(www(va, "index.php"), "a") as f:
            f.write("\n<?php // owner edit: landing tweak\n")
        os.makedirs(www(va, "wp-content", "plugins",
                        "owner-plugin"))
        with open(www(va, "wp-content", "plugins", "owner-plugin",
                      "owner-plugin.php"), "w") as f:
            f.write("<?php // the owner's own plugin\n")
        with open(www(va, "wp-content", "uploads",
                      "owner-note.txt"), "w") as f:
            f.write("owner upload\n")
        with open(www(va, "wp-config.php"), "a") as f:
            f.write("\n// owner-tweaked marker\n")
        before = snapshot(os.path.join(va, "varlib"))

        r = run_postinst(va, pkgs["v2"])
        check("A: v2 postinst exits 0 over an installed app",
              r.returncode == 0)
        check("A: v2 postinst reports the app already installed",
              "already installed" in r.stdout)
        check("A: app tree + recipe state byte-identical after "
              "the v2 package configure",
              snapshot(os.path.join(va, "varlib")) == before)
        with open(www(va, "readme.html"), "rb") as f:
            check("A: the v2 payload marker never reached the "
                  "installed tree", MARKER.encode() not in
                  f.read())

        # --- B: fresh venue + v2 postinst -> installs v2 -------
        vb = make_venue("venue-b")
        env_b = tool_env(vb, pkgs["v2"]["payload"])
        r = run_tool(env_b, "is-installed", "wordpress")
        check("B: is-installed says no (exit 1) before install",
              r.returncode == 1)
        r = run_postinst(vb, pkgs["v2"])
        check("B: v2 postinst exits 0 on a fresh venue",
              r.returncode == 0)
        check("B: the fresh postinst actually applied (no gate "
              "message)", "already installed" not in r.stdout)
        st = state_of(vb)
        check("B: fresh install lands at the v2 version",
              st.get("installed") and st.get("version") == V2)
        with open(www(vb, "readme.html"), "rb") as f:
            check("B: fresh install serves the v2 file content",
                  MARKER.encode() in f.read())

        # --- C1: floor above payload version, fresh -> refused -
        vc = make_venue("venue-c")
        env_c = tool_env(vc, pkgs["v3"]["payload"])
        r = run_tool(env_c, "apply", "wordpress")
        check("C1: below-floor first install is refused",
              r.returncode != 0
              and "security floor" in (r.stdout + r.stderr))
        check("C1: the refusal placed nothing (no www, no state)",
              not os.path.exists(www(vc))
              and not os.path.exists(os.path.join(
                  vc, "varlib", "recipes", "wordpress",
                  "state.json")))

        # --- C2: the same payload over a completed install -----
        env_a3 = tool_env(va, pkgs["v3"]["payload"])
        r = run_tool(env_a3, "apply", "wordpress")
        check("C2: a raised floor never judges an installed app "
              "(re-apply proceeds)", r.returncode == 0)
        check("C2: the installed app's state survives the "
              "floor-raised apply", state_of(va).get("seeded")
              and state_of(va).get("installed"))
    finally:
        cleanup_mountpoints()

    print("---")
    print("%d assertion(s) failed" % len(FAILURES))
    return len(FAILURES)


if __name__ == "__main__":
    sys.exit(main())

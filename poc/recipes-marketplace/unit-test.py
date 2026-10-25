#!/usr/bin/env python3
"""Host-side unit checks for the Marketplace recipe paths of
onionhost-recipe (A23 recipe 5): the native generalisations
this recipe exercises - a db.engine "postgres" manifest, the
native_serve TCP declaration, first-install-only app.env
rendering (the native_config seam carrying an environment
file, with NO credentials in it), the migrate/first-boot
file staging, the binary swap + rollback, and
await-first-boot. Run against the payloads extracted from
the real recipe .debs, with all product paths redirected
into a scratch tree via the tool's ONIONHOST_* environment
overrides (the earlier slices' pattern). Neither binary is
executed here - the sandbox does that; these checks pin the
applier's file-level contract, plus the D8 ownership
assertion on the native root."""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# Tree under test (review 2026-10-25, F7): derived from this file's
# location, so the harness tests the checkout that contains it -
# never a hardcoded home-directory path. MANIOC_TREE overrides.
TREE = os.environ.get(
    "MANIOC_TREE", os.path.abspath(os.path.join(HERE, "..", "..")))
TOOL = os.path.join(
    TREE, "onionhost/rootfs-overlay/usr/local/bin/onionhost-recipe")
UNIT = os.path.join(HERE, "unit")
ONION = "m" * 52 + "d.onion"
ADMIN_USER = "marketboss"
ADMIN_PASS = "Test-Admin-12-chars"
SITE_TITLE = "Teton Trading Post"

passed = []


def check(name, cond):
    assert cond, "FAIL: %s" % name
    passed.append(name)
    print("PASS", name)


def extract_deb(deb, root):
    shutil.rmtree(root, ignore_errors=True)
    os.makedirs(root)
    subprocess.run(["dpkg-deb", "-x", deb, root], check=True)
    return os.path.join(root, "usr/share/onionhost/recipes")


def fresh_env(payload_root, with_admin=True):
    for d in ("etc", "appdata", "state", "hs"):
        shutil.rmtree(os.path.join(UNIT, d), ignore_errors=True)
        os.makedirs(os.path.join(UNIT, d))
    with open(os.path.join(UNIT, "hs", "hostname"), "w") as f:
        f.write(ONION + "\n")
    env = dict(os.environ)
    env.update({
        "ONIONHOST_RECIPE_PAYLOAD_ROOT": payload_root,
        "ONIONHOST_ETC": os.path.join(UNIT, "etc"),
        "ONIONHOST_APPDATA": os.path.join(UNIT, "appdata"),
        "ONIONHOST_CONTAINER_UID_BASE": "0",
        "ONIONHOST_RECIPE_STATE": os.path.join(UNIT, "state"),
        "ONIONHOST_HS_HOSTNAME": os.path.join(UNIT, "hs",
                                              "hostname"),
        "ONIONHOST_EDGE_SOCK": os.path.join(UNIT, "edge.sock"),
    })
    if with_admin:
        stage_admin(env)
    return env


def stage_admin(env):
    with open(os.path.join(UNIT, "etc", "recipe-admin.env"),
              "w") as f:
        f.write("RECIPE_ID=marketplace\n"
                "RECIPE_ADMIN_USER=%s\n"
                "RECIPE_ADMIN_PASSWORD=%s\n"
                "RECIPE_SITE_TITLE=%s\n"
                % (ADMIN_USER, ADMIN_PASS, SITE_TITLE))


def run(env, *args):
    return subprocess.run([sys.executable, TOOL] + list(args),
                          env=env, capture_output=True, text=True)


def native(*parts):
    return os.path.join(UNIT, "appdata", "native", *parts)


def state():
    with open(os.path.join(UNIT, "state", "marketplace",
                           "state.json")) as f:
        return json.load(f)


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def mode(path):
    return os.stat(path).st_mode & 0o777


def main():
    os.makedirs(UNIT, exist_ok=True)
    payload1 = extract_deb(
        os.path.join(HERE, "pkgs",
                     "onionhost-recipe-marketplace_"
                     "0.1.0+oh.1_amd64.deb"),
        os.path.join(UNIT, "root-oh1"))
    payload2 = extract_deb(
        os.path.join(HERE, "pkgs",
                     "onionhost-recipe-marketplace_"
                     "0.1.0+oh.2_amd64.deb"),
        os.path.join(UNIT, "root-oh2"))

    # --- payload / manifest ------------------------------------
    with open(os.path.join(payload1, "marketplace",
                           "manifest.json")) as f:
        manifest = json.load(f)
    check("manifest: native, postgres db, tcp serve, first_boot",
          manifest["runtime"] == "native"
          and manifest["db"] == {"engine": "postgres",
                                 "required": True}
          and manifest["native_serve"] == {"port": 8080,
                                            "type": "tcp"}
          and manifest["first_boot"] is True
          and manifest["admin_password_min"] == 12)
    arc1 = os.path.join(payload1, "marketplace", "archive",
                        manifest["archive"]["file"])
    check("payload binary matches the manifest sha256",
          sha(arc1) == manifest["archive"]["sha256"])
    arc2 = os.path.join(payload2, "marketplace", "archive",
                        manifest["archive"]["file"])
    check("oh.2 payload binary differs (a real swap target)",
          sha(arc2) != sha(arc1))

    # --- first install demands the staged administrator --------
    env = fresh_env(payload1, with_admin=False)
    proc = run(env, "apply", "marketplace")
    check("apply without staged admin refused",
          proc.returncode != 0
          and "administrator details" in proc.stderr)
    check("nothing landed after the refusal",
          not os.path.exists(native("app"))
          and not os.path.exists(native("app.env")))

    # --- first apply --------------------------------------------
    stage_admin(env)
    proc = run(env, "apply", "marketplace")
    check("first apply ok",
          proc.returncode == 0
          and "RECIPE_APPLY_OK" in proc.stdout
          and "first_install=yes" in proc.stdout)
    check("binary at native/app, executable",
          os.path.isfile(native("app"))
          and mode(native("app")) == 0o755
          and sha(native("app")) == sha(arc1))
    env_text = open(native("app.env")).read()
    check("app.env rendered: wizard title is the SITE_NAME",
          ("SITE_NAME=%s" % SITE_TITLE) in env_text)
    check("app.env has no unsubstituted tokens",
          "__SITE_TITLE__" not in env_text
          and "__ONION__" not in env_text)
    check("app.env locks the stagenet demo shape",
          "DEPLOY_PROFILE=demo" in env_text
          and "INSTANCE_NETWORK=stagenet" in env_text
          and "BIND_ADDR=127.0.0.1:8080" in env_text)
    check("app.env carries NO database credentials",
          "DATABASE_URL=" not in env_text
          and "DB_PASSWORD=" not in env_text)
    check("media-worker staged beside the app, executable",
          os.path.isfile(native("media-worker"))
          and mode(native("media-worker")) == 0o755)
    migs = sorted(os.listdir(native("migrations")))
    check("all nine migrations staged",
          len(migs) == 9 and migs[0].startswith("0001")
          and migs[-1].startswith("0009"))
    check("migrate + first-boot steps placed, executable",
          mode(native("migrate.sh")) == 0o755
          and mode(native("first-boot.sh")) == 0o755)
    envcopy = native(".recipe-admin.env")
    check("admin env staged on the volume, 0400, values intact",
          os.path.isfile(envcopy) and mode(envcopy) == 0o400
          and ADMIN_PASS in open(envcopy).read())
    exc = open(os.path.join(UNIT, "etc",
                            "normalize-exceptions")).read()
    check("overlay written: key file pinned at 0600",
          "0600 native/marketplace.key" in exc
          and "0400 native/.recipe-admin.env" in exc)
    st = os.stat(native())
    check("D8: native root is www:www (base+33) at 02775",
          (st.st_uid, st.st_gid) == (33, 33)
          and (st.st_mode & 0o7777) == 0o2775)
    check("state: not seeded until first boot reports",
          state()["seeded"] is False)

    # --- update apply: env frozen, binary swapped --------------
    env_before = open(native("app.env"), "rb").read()
    with open(native(".first-boot-done"), "w") as f:
        f.write("done\n")
    os.unlink(native(".recipe-admin.env"))
    env = dict(env)
    env["ONIONHOST_RECIPE_PAYLOAD_ROOT"] = payload2
    proc = run(env, "apply", "marketplace")
    check("update apply ok, not a first install",
          proc.returncode == 0
          and "first_install=no" in proc.stdout)
    check("binary swapped to oh.2; oh.1 kept as .app-prev",
          sha(native("app")) == sha(arc2)
          and sha(native(".app-prev")) == sha(arc1))
    check("app.env untouched by the update (per-install state)",
          open(native("app.env"), "rb").read() == env_before)
    check("admin env NOT re-staged on update",
          not os.path.exists(native(".recipe-admin.env")))
    check("seeded survives the update apply",
          state()["seeded"] is True)

    # --- native rollback -----------------------------------------
    proc = run(env, "rollback", "marketplace")
    check("rollback swaps the binary back",
          proc.returncode == 0
          and "RECIPE_ROLLBACK_OK" in proc.stdout
          and sha(native("app")) == sha(arc1))
    check("broken binary kept aside as .app-broken",
          sha(native(".app-broken")) == sha(arc2))
    check("app.env still untouched after rollback",
          open(native("app.env"), "rb").read() == env_before)
    st = os.stat(native())
    check("D8: native root re-asserted at rollback",
          (st.st_uid, st.st_gid) == (33, 33)
          and (st.st_mode & 0o7777) == 0o2775)

    # --- await-first-boot ----------------------------------------
    env = fresh_env(payload1, with_admin=True)
    proc = run(env, "apply", "marketplace")
    assert proc.returncode == 0, proc.stderr
    env_fast = dict(env)
    env_fast["ONIONHOST_FIRST_BOOT_TIMEOUT"] = "2"
    proc = run(env_fast, "await-first-boot", "marketplace")
    check("await times out without the marker (publish fails)",
          proc.returncode != 0)
    check("host admin env survives a failed await (retryable)",
          os.path.isfile(os.path.join(UNIT, "etc",
                                      "recipe-admin.env")))
    with open(native(".first-boot-done"), "w") as f:
        f.write("done\n")
    proc = run(env, "await-first-boot", "marketplace")
    check("await succeeds once the marker exists",
          proc.returncode == 0
          and "FIRST_BOOT_OK" in proc.stdout)
    check("host admin env shredded after first boot",
          not os.path.exists(os.path.join(
              UNIT, "etc", "recipe-admin.env")))

    # --- oh.4: per-install provisioning + the real binary ----
    # The application at the pinned commit refuses to start
    # outside its Development profile when either per-install
    # file is absent (PCM audit fixes AL1 / HT F1): the key
    # file (KEY_FILE_PATH) and the HT id file (HT_ID_FILE_PATH).
    # The recipe now provisions both - slot 2 carries the oh.4
    # payload in current runs. A fresh install from it is
    # provisioned by the staged step itself, then the real
    # binary is started with the recipe's env shape.
    env = fresh_env(payload2, with_admin=True)
    proc = run(env, "apply", "marketplace")
    check("oh.4 fresh apply ok (first install)",
          proc.returncode == 0
          and "first_install=yes" in proc.stdout)
    check("provision-secrets staged beside migrate, executable",
          os.path.isfile(native("provision-secrets.sh"))
          and mode(native("provision-secrets.sh")) == 0o755)
    exc = open(os.path.join(UNIT, "etc",
                            "normalize-exceptions")).read()
    check("overlay pins the HT id file 0600, the step 0755",
          "0600 native/marketplace.htid" in exc
          and "0755 native/provision-secrets.sh" in exc)

    def recipe_env(**overrides):
        # The rendered app.env IS the recipe's env shape; its
        # data paths name the production volume root, so they
        # are re-pointed at this scratch volume. DATABASE_URL
        # (never in app.env) names a port nothing listens on:
        # a binary that clears its config checks must fail
        # THERE, at the database pool.
        e = {"PATH": "/usr/bin:/bin",
             "DATABASE_URL": "postgres://app:app@127.0.0.1:1/app"}
        for line in open(native("app.env")):
            line = line.strip()
            if not line or line.startswith("#") \
                    or "=" not in line:
                continue
            k, v = line.split("=", 1)
            e[k] = v
        for k in ("KEY_FILE_PATH", "HT_ID_FILE_PATH", "MEDIA_DIR",
                  "MEDIA_WORKER", "BLOB_DIR"):
            if k in e:
                e[k] = os.path.join(
                    UNIT, "appdata", "native",
                    os.path.basename(e[k]))
        e.update(overrides)
        return e

    def boot(e):
        return subprocess.run([native("app")], env=e,
                              capture_output=True, text=True,
                              timeout=60)

    penv = recipe_env()
    proc = subprocess.run(["sh", native("provision-secrets.sh")],
                          env=penv, capture_output=True, text=True)
    check("provisioning step runs clean on a fresh install",
          proc.returncode == 0)
    keyf, htidf = native("marketplace.key"), \
        native("marketplace.htid")
    ktxt = open(keyf).read() if os.path.isfile(keyf) else ""
    check("key file minted: exists, 0600, 64 lowercase hex",
          os.path.isfile(keyf) and mode(keyf) == 0o600
          and re.fullmatch(r"[0-9a-f]{64}", ktxt) is not None)
    itxt = open(htidf).read() if os.path.isfile(htidf) else ""
    check("HT id file minted: exists, 0600, mkt_ + 32 hex",
          os.path.isfile(htidf) and mode(htidf) == 0o600
          and re.fullmatch(r"mkt_[0-9a-f]{32}", itxt) is not None)

    KEY_SIG = "cannot load marketplace key file"
    HT_SIG = "cannot load HT marketplace id file"
    out = boot(recipe_env(KEY_FILE_PATH=native("no-such.key")))
    check("control: binary refuses when the key file is absent",
          out.returncode == 2 and KEY_SIG in out.stderr)
    out = boot(recipe_env(HT_ID_FILE_PATH=native("no-such.htid")))
    check("control: binary refuses when the HT id file is absent",
          out.returncode == 2 and HT_SIG in out.stderr)
    out = boot(recipe_env())
    combined = out.stderr + out.stdout
    check("binary passes both config checks, reaches the DB pool",
          out.returncode != 0
          and KEY_SIG not in combined and HT_SIG not in combined
          and "connect" in combined.lower())

    before = (open(keyf, "rb").read(), open(htidf, "rb").read())
    proc = subprocess.run(["sh", native("provision-secrets.sh")],
                          env=penv, capture_output=True, text=True)
    check("second provisioning pass: both files byte-identical",
          proc.returncode == 0
          and (open(keyf, "rb").read(),
               open(htidf, "rb").read()) == before)

    print("\nUNIT: %d checks passed" % len(passed))
    return 0


if __name__ == "__main__":
    sys.exit(main())

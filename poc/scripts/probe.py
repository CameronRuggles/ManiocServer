#!/usr/bin/env python3
"""OnionHost PoC probe for a RUNNING standalone-runsc web sandbox (B).

This is the tranche-2 miniature of DESIGN-v3 A8's fixed probe. It returns
exit codes only in normal operation (no stdout/stderr). Use --verbose only
for manual debugging; the Dashboard/production pattern consumes the code.

Exit codes:
   0  all checks pass
  10  sandbox state is not running / cannot be queried
  11  running process identity is not the expected nginx process
  12  in-sandbox inspection could not run
  13  live network interface set is not {lo}
  14  live route table is not empty
  15  unexpected live TCP/TCP6 socket entries inside B
  16  onion-service key material is visible inside B
  20  OCI root is not marked read-only
  21  OCI capabilities exceed the PoC allow-list
  22  OCI mount set / socket-volume mount differs from expectation
  30  expected host socket is absent or is not a socket
  31  expected host socket does not answer an HTTP request

The Podman production fields (podman inspect NetworkMode etc.) cannot be
used in this nested sandbox because tranche 1 proved podman->runsc is
setns-blocked here. This PoC therefore checks the equivalent live facts:
runsc state, the OCI spec actually used at launch, /proc/net/* inside the
running sandbox, key-path absence, and a real request through the host UDS.
"""

import argparse
import json
import os
import socket
import stat
import subprocess
import sys

RUNSC = "/usr/local/bin/runsc"
ALLOWED_CAPS = {"CAP_AUDIT_WRITE", "CAP_KILL", "CAP_NET_BIND_SERVICE"}
EXPECTED_MOUNT_DESTINATIONS = {"/proc", "/dev", "/sys", "/run/web", "/tmp"}


def fail(code, verbose, message):
    if verbose:
        print(f"probe: {code}: {message}", file=sys.stderr)
    raise SystemExit(code)


def run(argv, verbose=False):
    return subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          text=True, timeout=20)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="runsc root directory")
    ap.add_argument("--id", required=True, help="runsc container id")
    ap.add_argument("--bundle", required=True, help="bundle directory")
    ap.add_argument("--shared", required=True, help="host socket directory")
    ap.add_argument("--socket", required=True, help="socket filename in --shared")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()
    v = args.verbose

    # 10/11: live runtime identity.
    p = run([RUNSC, "--root", args.root, "state", args.id], v)
    if p.returncode != 0:
        fail(10, v, "runsc state failed")
    try:
        state = json.loads(p.stdout)
    except Exception:
        fail(10, v, "runsc state was not JSON")
    if state.get("status") != "running":
        fail(10, v, f"status={state.get('status')!r}")

    cfg_path = os.path.join(args.bundle, "config.json")
    try:
        with open(cfg_path) as f:
            cfg = json.load(f)
    except Exception:
        fail(22, v, "bundle config unreadable")
    argv = cfg.get("process", {}).get("args", [])
    if not argv or os.path.basename(argv[0]) != "nginx":
        fail(11, v, f"process args={argv!r}")

    # 20-22: launch-spec posture (the spec the running sandbox was made from).
    if cfg.get("root", {}).get("readonly") is not True:
        fail(20, v, "OCI root.readonly is not true")
    caps = cfg.get("process", {}).get("capabilities", {})
    for field in ("bounding", "effective", "inheritable", "permitted"):
        vals = set(caps.get(field, []))
        if not vals.issubset(ALLOWED_CAPS):
            fail(21, v, f"capability field {field}={sorted(vals)}")
    mounts = cfg.get("mounts", [])
    destinations = {m.get("destination") for m in mounts}
    if destinations != EXPECTED_MOUNT_DESTINATIONS:
        fail(22, v, f"mount destinations={sorted(destinations)}")
    web_mounts = [m for m in mounts if m.get("destination") == "/run/web"]
    if len(web_mounts) != 1 or web_mounts[0].get("source") != args.shared:
        fail(22, v, "socket volume mount differs")

    # 12-16: inspect the live sandbox, not just its template.
    inspection = r'''
echo '==DEV=='; cat /proc/net/dev
echo '==ROUTE=='; cat /proc/net/route
echo '==TCP=='; cat /proc/net/tcp
echo '==TCP6=='; cat /proc/net/tcp6 2>/dev/null || true
echo '==KEY=='; if [ -e /var/lib/tor/hs ]; then echo present; else echo absent; fi
echo '==ROOTWR=='; if [ -w /etc/nginx/poc.conf ]; then echo writable; else echo readonly; fi
'''
    p = run([RUNSC, "--root", args.root, "exec", args.id,
             "/bin/sh", "-c", inspection], v)
    if p.returncode != 0:
        fail(12, v, f"exec inspection rc={p.returncode} err={p.stderr.strip()}")
    sections = {}
    current = None
    for line in p.stdout.splitlines():
        if line.startswith("==") and line.endswith("=="):
            current = line.strip("=")
            sections[current] = []
        elif current is not None:
            sections[current].append(line)
    ifaces = set()
    for line in sections.get("DEV", []):
        if ":" in line:
            name = line.split(":", 1)[0].strip()
            if name and name not in ("Inter-|", "face"):
                ifaces.add(name)
    def body_count(name):
        lines = [l for l in sections.get(name, []) if l.strip()]
        return max(len(lines) - 1, 0)  # minus header line
    facts = {
        "IFACES": " ".join(sorted(ifaces)),
        "ROUTES": str(body_count("ROUTE")),
        "TCP": str(body_count("TCP")),
        "TCP6": str(body_count("TCP6")),
        "KEY": (sections.get("KEY", [""])[0].strip() if sections.get("KEY") else ""),
        "ROOTWR": (sections.get("ROOTWR", [""])[0].strip() if sections.get("ROOTWR") else ""),
    }
    if v:
        print(f"probe facts: {facts}", file=sys.stderr)
    if ifaces != {"lo"}:
        fail(13, v, f"IFACES={facts['IFACES']!r}")
    if facts["ROUTES"] != "0":
        fail(14, v, f"ROUTES={facts['ROUTES']!r}")
    if facts["TCP"] != "0" or facts["TCP6"] != "0":
        fail(15, v, f"TCP={facts['TCP']!r} TCP6={facts['TCP6']!r}")
    if facts["KEY"] != "absent":
        fail(16, v, f"KEY={facts['KEY']!r}")
    if facts["ROOTWR"] != "readonly":
        fail(20, v, f"ROOTWR={facts['ROOTWR']!r}")

    # 30-31: host-visible socket really answers.
    sock_path = os.path.join(args.shared, args.socket)
    try:
        st = os.stat(sock_path)
    except OSError:
        fail(30, v, "socket stat failed")
    if not stat.S_ISSOCK(st.st_mode):
        fail(30, v, "socket path is not a socket")
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect(sock_path)
        s.sendall(b"GET /version.txt HTTP/1.0\r\nHost: localhost\r\n\r\n")
        data = s.recv(4096)
        s.close()
    except Exception:
        fail(31, v, "socket HTTP request failed")
    if b" 200 " not in data.split(b"\r\n", 1)[0]:
        fail(31, v, f"unexpected HTTP status line: {data[:80]!r}")

    raise SystemExit(0)


if __name__ == "__main__":
    main()

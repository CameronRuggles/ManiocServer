#!/usr/bin/env python3
"""PoC-ONLY shim between podman and runsc for this sandbox.

The outer sandbox seccomp-blocks setns(2) entirely, so runsc cannot JOIN
any pre-existing network namespace podman references (it resolves one even
for a path-less spec entry, via its caller). This shim REMOVES the network
namespace entry from the bundle's config.json so the gVisor sandbox makes
its own netns, then selects networking explicitly per container command:
  nginx -> --network=none  (loopback-only inside gVisor: the design's B)
  tor   -> --network=host  (A needs real egress to reach the Tor network)
Also forces --ignore-cgroups (cgroup delegation is blocked here too).

TEST-HARNESS ADAPTATION TO A SANDBOXED VM ONLY — not part of the design.
On bare metal, stock podman + runsc needs none of this.
"""
import json, os, sys

REAL_RUNSC = "/usr/local/bin/runsc"

def main():
    args = sys.argv[1:]
    bundle = None
    for i, a in enumerate(args):
        if a == "--bundle" and i + 1 < len(args):
            bundle = args[i + 1]
    extra = ["--ignore-cgroups"]
    if bundle:
        cfg_path = os.path.join(bundle, "config.json")
        try:
            with open(cfg_path) as f:
                cfg = json.load(f)
            ns = cfg.get("linux", {}).get("namespaces", [])
            kept = [n for n in ns if n.get("type") != "network"]
            if len(kept) != len(ns):
                cfg["linux"]["namespaces"] = kept
                with open(cfg_path, "w") as f:
                    json.dump(cfg, f)
            cmd = cfg.get("process", {}).get("args", [])
            prog = os.path.basename(cmd[0]) if cmd else ""
            if prog == "nginx":
                extra += ["--network=none", "--host-uds=create"]
            elif prog == "tor":
                extra.append("--network=host")
        except Exception as e:
            print(f"runsc-shim: spec edit failed: {e}", file=sys.stderr)
    os.execv(REAL_RUNSC, [REAL_RUNSC] + extra + args)

if __name__ == "__main__":
    main()

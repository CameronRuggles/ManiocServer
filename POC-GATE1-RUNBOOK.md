# OnionHost PoC — Gate #1 Runbook

*Prepared 2026-10-10, from DESIGN-v2.md §4, §6 and Appendix B.
Status: preparation only. Nothing is built. The PoC itself still needs
Cameron's go, and the engine choice (below) is his call.
This is the "afternoon, stack only, no ISO" PoC v2 estimates — no
Calamares, no LUKS, no dashboard, no editor in this pass.*

## What Gate #1 actually tests

One question, from Appendix B item 1:

> Can nginx, running under gVisor (`runsc`), bind a unix socket on a
> shared volume so the Tor container can reach it — while the website
> container has **no network at all**?

Everything else in v2 (no-network B, hash-gated Tor start, one human
secret) rests on this working on the chosen engine/runtime versions.
If it fails, v2 already names the fallback — it is **not** a silent
weakening (see Fail branch).

## The one open decision — and why it does not block this runbook

- **Branch P (v2 default):** Podman rootless + Quadlet systemd units.
  Dockerfiles run unchanged; daemonless; systemd ordering makes the
  §6 firewall gate natural.
- **Branch D (documented fallback):** rootful Docker + `runsc`,
  no userns-remap.

Both branches run the *same* test with the *same* pass criteria.
Cameron only has to say "Podman" or "Docker" — the rest of this
runbook is identical either way.

## Stack under test (both branches)

- Host: a throwaway Debian 13 VM or spare box (NOT a production
  machine, no real site, no real onion key that matters).
- A — Tor gateway container, `runsc` mandatory:
  tor from the Tor Project signed repo, SocksPort OFF,
  `HiddenServicePort 80 → unix:/run/web/http.sock`.
- B — Website container, `runsc` mandatory, **no runc fallback**:
  nginx-unprivileged, `network: none`, read-only rootfs,
  cap_drop ALL, no-new-privileges, listening only on the unix
  socket in a socket-volume shared with A only.
- No database container. One static test page in B.

## Steps

1. Install engine (per branch) + `runsc`; register `runsc` as a
   runtime. Confirm a trivial container starts under `runsc` on
   this engine/version — if it cannot, stop: that is a Gate #1 fail
   for this branch, not a reason to fall back to runc for B.
2. Build A and B from plain Dockerfiles (Branch P: run via Quadlet
   units; Branch D: run via compose/systemd as in v1 practice).
3. Start B. Verify nginx has created/bound `/run/web/http.sock`
   in the shared socket-volume — this is the specific
   host-UDS-creation support Appendix B flags as unproven
   (the `--host-uds=create`-equivalent under gVisor).
4. Start A with the torrc above; wait for the v3 onion address to
   be published.
5. Run the pass/fail checks below. Record engine, Podman/Docker,
   runsc, tor and Debian versions alongside the result — the gate
   is version-specific.

## Pass criteria (all must hold)

- [ ] A page served from B is reachable through the onion address
      (Tor Browser or `torsocks curl` to the .onion).
- [ ] From inside B: no default route, no DNS resolution, no ARP
      neighbours, no host/bridge IP reachable. `network: none`
      is verified, not assumed.
- [ ] From inside B: the onion key volume and A's DataDirectory
      are not readable in B's mount view.
- [ ] Socket file permissions: only A and B can reach the socket;
      nothing else on the host can.
- [ ] No TCP port is listening on the host for the website
      (socket only — `ss -ltn` shows nothing new).
- [ ] Restarting B produces a working site again on the same
      socket path (no manual socket cleanup).
- [ ] Cheap add-on while tor is built (Appendix B item 3):
      record `tor --list-modules` output — PoW must be present
      before any UI copy ever claims it.

## Fail branch (decided in v2, not improvised)

If runsc cannot create/bind the host unix socket on the chosen
engine versions:

1. Try the other engine branch once (P → D or D → P) — the gate
   is per engine/version, and v2's fallback is an engine fallback
   first.
2. If both fail: adopt the review's M2 fallback — internal network
   + conntrack direction rules + static IPs between A and B —
   and record in DESIGN-v2 Appendix B that Gate #1 failed and
   which fallback was taken. B then *has* a network, tightly
   firewalled; the "no network at all" claim must be removed from
   the design and any copy wherever it appears. Never ship the
   claim on the fallback's evidence.
3. If `runsc` cannot start B at all on either branch: Go Live
   refuses (v2 §4, X3). There is no runc downgrade for B.

## Out of scope for this PoC

ISO/Calamares, LUKS phrase flow, the §6 hash-gated firewall unit
(Gate #1 first; the firewall gate is the natural next PoC step on
whichever engine passes), dashboard, editor/publisher, backups,
Private Files tier, update chain.

## Timebox

One afternoon, per v2 Appendix B item 5. If the afternoon ends
with "fails on both branches, versions recorded, M2 fallback
scoped," that is a successful PoC — it did its job before the
2–4-week home alpha was committed on an unproven socket trick.

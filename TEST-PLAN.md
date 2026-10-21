# OnionHost OS — Test Plan (agreed in principle, 2026-10-10)

## Stage 0 — Stack only (no ISO)
Run the Podman + Tor + website stack on Muse's machine. Cameron visits the
throwaway `.onion` in Tor Browser. Covers containers, socket handoff, leak
tests. Free, minutes per iteration.

## Stage 1 — Full OS in a browser (no USB)
Google Cloud Compute Engine VM with nested virtualisation enabled, region
us-west3 (Salt Lake City). QEMU/KVM inside it runs the ISO; noVNC gives
Cameron a password-gated, time-limited browser console to click through the
installer himself. Snapshot revert = a fresh blank machine in ~1 minute.
- Start the GCP account/free trial ($300 / 90 days) ONLY on PoC day — the
  clock starts at signup.
- Rig size: n2-standard-4 (~$0.19/hr, sessions only, stopped otherwise).
- Trial content is throwaway: fake site, fake keys. A cloud trial proves
  experience and mechanics, NOT the home-location secrecy story.

## Stage 2 — THE FINAL TEST: USB on a real spare computer (Cameron's)
The last gate before any release. Only real hardware can test: Secure Boot
on real firmware, the BIOS boot-menu key, Wi-Fi chipsets/firmware, real
graphics, argon2id unlock timing, gVisor on a real CPU, Tor over a real home
ISP connection (NAT/CGNAT, router untouched), and a real power cut.
Full lifecycle drill, in order, exactly as a stranger would do it:
1. Download the ISO, make the USB with Etcher (8 GB+ stick), boot it.
2. Full click-through install; hand-copy the generated disk phrase.
3. Reboot; type the phrase at the real prompt; complete the wizard; Go Live.
4. Visit the new `.onion` from a phone (Tor Browser).
5. Soak test: leave it running for days; confirm updates, self-checks,
   dashboard cards behave.
6. Yank the power cord. Machine must return locked; type the phrase; the
   site must come back.
7. Back up to a USB stick, wipe/reinstall, restore — the SAME `.onion`
   address must return.
8. Site OFF / "Shut down now" test.
The machine used WILL be erased — a spare, never a daily driver.

## Stage 3 — Novices, then the wild
Stage 2 repeated by 5+ real novices on their own spare hardware (incl. one
non-US keyboard, one Wi-Fi-only machine), plus external security review of
the built alpha, legal counsel, and reproducible-ISO + hardware-key signing
live. Only then: public release.

# Stage 2 — Real-hardware lifecycle drill (Cameron's runbook)

Goal: prove the whole product on a real spare computer, on a real home
network, with Cameron doing every user-facing step himself. Muse
observes/reports; Cameron's hands are the test.

## Kit
- Spare computer (will be **completely erased**). **UEFI boot is
  required** — the boot chain is UEFI-only by design; a legacy-BIOS
  install fails at the GRUB stub (confirmed in rebuild-2 testing).
  Wired Ethernet preferred; note if Wi-Fi-only (that's a data point,
  not a blocker).
- USB stick, 2 GB+ (will be erased). Balena Etcher or Rufus to write it.
- Paper + pen (the disk phrase and login words are hand-copied).
- Phone with Tor Browser (to visit the site as an outsider).
- The ISO: `onionhost-amd64.iso` (prod rebuild 2, the current public
  download at https://vespiary.org/onionhost/onionhost-amd64.iso —
  the Drive copy in OnionHost-Stage2 is the same file),
  1,146,880,000 bytes,
  sha256 `080e45ac048e9999d2de57f199d5411c53a442f4a7a7daaa49a92c0e4cb2b1c1`
  (verify the hash after download before writing the USB).
  NOTE: the older `onionhost-prod-amd64.iso` (1,139,898,368 bytes,
  sha256 35f3f34f…) is superseded — do not use it for this drill.

## The drill (TEST-PLAN Stage 2)
1. Write the ISO to USB; boot the spare machine from it.
2. Install: language/keyboard → network → claim page → erase disk.
   - Hand-copy the generated 7-word disk phrase. Verify words when asked.
     (There is no spare phrase — A25: the paper is the only key.)
3. Remove USB, reboot. Type the disk phrase **once**. Note: unlock
   seconds on this hardware; a typo should re-prompt, never a shell.
4. First boot wizard: copy + verify the generated 3-word login phrase;
   after the switch flips, log in with it; finish the wizard → Go Live.
   - Record the .onion address + scan the QR with the phone.
5. From the phone (Tor Browser, ideally on mobile data, not home Wi-Fi):
   the site loads.
6. Soak: leave it running. Check the Dashboard status card over the
   next days; note anything odd (noise, heat, restarts).
7. Yank the power cord mid-operation. Plug back in, unlock with the
   phrase: the site must return by itself.
8. Backup → wipe → reinstall from the same USB → restore: the **same**
   .onion address must come back.
9. End state: Dashboard → "Shut down now". Confirm it powers off fully.

## Tor republication timing (new — from the SMF slice, 2026-10-14)
Steps 3, 7 and 8 each restart the stack, and each restart is a free
measurement of the one number the SMF slice left open: how long Tor
takes to republish the site vs the health check's ~3–4 min envelope
(sandbox windows ran 2.5–4.5 min on degraded venue Tor; real hardware
is expected to be faster but is unmeasured). At each of those steps,
run the capture in `TOR-REPUBLISH-MEASUREMENT-2026-10-14.md` —
stopwatch from the moment you finish the disk phrase, phone on mobile
data, refresh every ~30 s, one log line per restart. No extra
restarts needed.

## Stage-2-only checks (from slice 3 findings)
- NTS time sync on real broadband (Netnod didn't answer through QEMU
  NAT; Cloudflare/PTB did). `timedatectl` / chrony tracking screenshot.
- Unlock timing on the real CPU (rig vCPU ≈ 12 s at iter-time 2000).
- Keyboard layout at the GRUB prompt (esp. if the machine's keyboard
  isn't plain US).
- Secure Boot on/off state of the machine + whether it just works.

## Record for every step
Screenshot or photo of the screen, wall-clock time, and anything that
made Cameron hesitate — hesitation points are usability bugs for the
Stage 3 novice sessions.

# OnionHost — Stage 3 tester session kit v1

Prepared 2026-10-13. Status: READY TO USE, not yet sent to anyone. Recruitment
starts only when Cameron green-lights the launch posts
(outreach/LAUNCH-POSTS-DRAFT-2026-10-12.md, factual pass done 2026-10-13).

## Why this exists

Stage 3 gate (DESIGN-v2 §9.1 / TEST-PLAN Stage 3): **at least five usability
sessions with real novices on their own spare hardware, including one non-US
keyboard layout and one Wi-Fi-only machine.** The session's product is not the
tester's success — it is their friction. Every hesitation, misread page, or
wrong turn is a bug report. Session zero already proved the value: Cameron,
on his phone, hitting the installer cold, caught the easily-missed encryption
checkbox that every scripted battery had sailed past.

## Who qualifies

- Non-technical is the point: "can follow a recipe" is the whole bar.
- Adults only (project positioning).
- Has a spare computer they can **completely erase** (never a daily driver),
  UEFI boot (the boot chain is UEFI-only by design), a 2 GB+ USB stick,
  paper + pen, and a phone with Tor Browser.
- Across the five sessions, deliberately include: one non-US keyboard, one
  Wi-Fi-only machine. Note Secure Boot on/off state per machine.

## Before the session (Muse/Cameron, ~10 min)

- [ ] Tester has the current ISO: prod rebuild 2,
      `onionhost-amd64.iso`, 1,146,880,000 bytes,
      sha256 `080e45ac048e9999d2de57f199d5411c53a442f4a7a7daaa49a92c0e4cb2b1c1`
      (same values as STAGE2-RUNBOOK.md — re-check there if a newer rebuild
      has shipped; do NOT hand out the superseded `onionhost-prod-amd64.iso`).
- [ ] Agree the observation channel: in person, or screen-share / phone-held
      remote view (the phone-driven remote session already proved workable).
- [ ] Consent, plainly: the tester is watched and notes are taken on where
      they get stuck; no telemetry, no recording of their site content, they
      can stop any time. Their machine WILL be erased — confirm twice.
- [ ] Send the tester instruction sheet below, verbatim. Nothing else.
      No hints in advance.

## Tester instruction sheet (send as-is)

> Thank you for testing. The job is simple to describe: install this from the
> USB stick onto your spare computer and get your website live, using only
> what's on the screens. There is no wrong way to do this — if you get stuck,
> that is exactly what we need to see, so please don't apologise for it.
>
> A few ground rules:
> - Say what you're thinking out loud as you go, especially when a screen
>   confuses you or you aren't sure what to do next.
> - I won't answer how-to questions during the session. If you're truly
>   blocked for more than a couple of minutes, say so and we'll note it —
>   that's a finding, not a failure.
> - You'll be asked to hand-copy a short phrase onto paper. Keep the paper;
>   you'll need it again.
> - When the site is live, open it on your phone's Tor Browser — ideally on
>   mobile data, not your home Wi-Fi.
> - Afterwards we'll pull the power cord out while it's running, plug it
>   back in, and see if it comes back on its own. That's planned, not an
>   accident.
> - The whole thing should take about an hour. Your computer will be
>   completely erased by the install.

## Observation checklist (observer fills in, one row per step)

Mirror of the STAGE2-RUNBOOK drill, watched rather than performed:

| # | Step | Watch for | Time | Hesitation / misread (verbatim if possible) |
|---|------|-----------|------|----------------------------------------------|
| 1 | Write ISO to USB; boot from it | Do they know how to pick the boot device? | | |
| 2 | Install: language/keyboard → network → claim page → erase disk | Keyboard layout correct at every prompt? Erase warning understood? | | |
| 3 | Hand-copy the generated 7-word disk phrase; verify when asked | Copy errors? Do they understand the paper IS the only key — no spare, no recovery if it is lost? | | |
| 4 | Remove USB, reboot, type disk phrase once | Unlock time on this hardware; typo → clean re-prompt? Forgotten USB left in? | | |
| 5 | First-boot wizard: copy + verify 3-word login phrase; finish → Go Live | Confusion between the two phrases (disk vs login)? | | |
| 6 | Record .onion address / scan QR; site loads on phone (Tor Browser, mobile data) | Do they find the address without help? | | |
| 7 | Power yank mid-operation; plug back in; unlock; site returns by itself | Surprise/distress at the step? Recovery understood? | | |
| 8 | Backup → wipe → reinstall from same USB → restore; SAME .onion returns | Can they find backup/restore unaided? Do they believe the same address came back? | | |
| 9 | Dashboard → "Shut down now"; machine powers off fully | Any doubt it is really off / really locked? | | |

Per-session header: date · tester (first name or alias) · machine
(make/rough age, wired or Wi-Fi-only, keyboard layout, Secure Boot state) ·
observer · session number (1–5+).

Also record: NTS/time-sync sanity if visible, fan noise/heat complaints,
and any moment the tester reached for a concept that isn't in the
four-concept budget (DESIGN-v3 A11 as amended by A25: disk phrase ·
generated login words · restart-needed card · Repair button) — a tester
inventing a fifth concept is a design signal, not a tester error.

## Scoring the session

- **Completed unaided** / **completed with N blocks** (a block = stuck >2 min
  or observer had to intervene) / **did not complete** (note the step).
- Count blocks per step across all sessions. **Triage rule: the same step
  blocking or confusing two or more testers is a page that gets redesigned,
  not a tester who gets blamed.** One-off fumbles are noted, not acted on.
- Gate is met at 5+ sessions with the keyboard and Wi-Fi-only cases covered,
  and every repeat-friction page either fixed or explicitly accepted by
  Cameron with the reason written here.

## After each session

- [ ] Thank-you note to the tester the same day (Cameron sends).
- [ ] Friction log merged into this kit's running table (step → count →
      disposition: fix / accepted / watch).
- [ ] Any defect that is a security or data-loss issue jumps the queue —
      it does not wait for the five-session tally.
- [ ] Note whether this tester would be a good "session two" candidate
      after fixes (re-test the redesigned pages on fresh eyes first;
      repeat testers only confirm a fix, they don't find new friction).

## Running friction log

| Step | Sessions hit | Disposition |
|------|--------------|-------------|
| (session zero, Cameron by phone) Installer encryption checkbox easily missed | 1 (pre-gate) | FIXED — encryption forced by the installer flow; watch step 2/3 above to confirm novices now sail through it |

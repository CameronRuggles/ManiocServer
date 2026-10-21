# Tor republication timing — real-hardware measurement protocol

Prepared 2026-10-14, for Cameron's Stage 2 run (see STAGE2-RUNBOOK.md).
This closes the one measurement the SMF recipe slice left open.

## Why this number matters

After **any** stack restart, the onion descriptor has to republish
before the site is reachable through Tor — and before the updater's
health check can pass. If republication takes longer than the health
check waits, a perfectly healthy update fails its check, rolls back,
and the machine fails closed (the designed safe direction, but a bad
user experience if it happens on healthy hardware).

What the sandbox showed (ISO-BUILD-LOG.md, SMF slice, 2026-10-13):

- The probe/health-check envelope is roughly **3–4 minutes**
  (one health check ran at ~3.7 min post-restart).
- Sandbox republication windows that passed took **~2.5–4.5 min** —
  i.e. right at the edge of the envelope.
- One loop recorded **21 failed probe attempts over ~16 min**, while a
  host-side Tor simultaneously sat at 45% bootstrap for 20+ min —
  the sandbox venue's Tor was degraded throughout, so these numbers
  say little about real hardware.
- Gate 4's identical health flow passed post-restart on its venue.

Expectation for real hardware is seconds-to-minutes, but that is
**expected, not measured**. Three restarts already in the Stage 2
drill are free measurement opportunities — this protocol just adds a
stopwatch and a log line to each.

## What to capture at each restart

Restarts already in the drill: **step 3** (first reboot + unlock),
**step 7** (power yank + unlock), **step 8** (restore reboot).
Do the same capture at all three; do not add extra restarts.

For each restart, record:

| Field | How |
|---|---|
| T0 | Wall-clock time you finish typing the disk phrase and press Enter. Start the phone stopwatch here. |
| Network | Phone on **mobile data** (not home Wi-Fi), per runbook step 5. Note if that wasn't possible. |
| First success | Stopwatch time when the site **first loads fully** in Tor Browser on the phone. Refresh every ~30 s; note the number of failed/timed-out attempts before the first success. |
| Dashboard | When the Dashboard status card first shows the site as up, if you happen to see it — note stopwatch time, or "not observed". |
| Conditions | Anything unusual: slow home network, Tor Browser needing a new circuit/identity to connect, machine busy (update running). |

One line per restart is enough, e.g.:

```
step 7 — T0 19:42, mobile data, first load 1:35 (2 failed refreshes), dashboard up ~1:10
```

## How the result will be read

- **First success consistently under ~2 min** → real-hardware
  republication sits comfortably inside the ~3–4 min health-check
  envelope; the sandbox margin problem is a venue artifact and the
  envelope can be called proven for the rig battery.
- **First success in the 2.5–4.5 min band** → margin is genuinely
  thin even on real hardware; the health-check envelope is the thing
  to revisit before promising updates to novice users.
- **Any restart over ~5 min, or wild variance between the three** →
  the number, the network conditions, and the attempt count are the
  evidence needed to decide whether it's Tor weather, the home
  network, or the stack's restart sequence.

No pass/fail for the drill itself rides on this — the site returning
at all is the Stage 2 criterion. This capture only decides whether
the updater's timing margin is proven or still open.

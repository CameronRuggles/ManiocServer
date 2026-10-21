# FIX BRIEF — Encryption must not depend on a stock checkbox
### OnionHost installer · raised by Cameron's first phone-driven install, 2026-10-12

## The defect (field report already logged in ISO-BUILD-LOG.md)

Cameron drove the slice-3 test ISO via noVNC on his phone — the first
non-automated human install. It failed loudly at `onionhostbootkey`:

> "Install passphrase not available in GlobalStorage (luksPassphrase)"

Root cause, established from the live session: `lsblk` on the target
showed vda2 as **plain ext4** — encryption was never enabled on the stock
Calamares Partitions page, so no LUKS volume existed and the passphrase
handoff never engaged. The fail-closed design worked (no unencrypted
system shipped), but the flow has a real UX defect: whether the entire
product promise engages depends on the user finding and ticking a stock
"Encrypt system" checkbox, on whatever screen size they have. Automated
installs never exposed this — the drivers ticked it explicitly.

**Requirement:** encryption is forced on by the flow itself, OR the
installer stops the user *at the Partitions page* with plain-language
recovery instructions — never ten minutes later at bootkey with a
technical error.

## What exists today (verified in the workspace tree, 2026-10-12)

- `build/build-iso.sh` writes `/etc/calamares/modules/partition.conf`
  explicitly (the heredoc near the sequence-wiring section). Current
  contents include `luksGeneration: luks2`, `defaultFileSystemType:
  "ext4"`, `allowManualPartitioning: true`, `userSwapChoices: [none]` —
  **nothing that defaults or forces the encrypt option on.**
- The phrase ViewStep (`calamares/plugin-src/onionhostphrase/`) already
  stores the generated phrase into GlobalStorage as `luksPassphrase`
  in the obscured form the partition chain expects — i.e. the phrase
  step runs *before* partition in the show sequence (build-iso.sh wires
  `onionhostphrase` + `onionhostspare` immediately after `keyboard`).
- `calamares/modules/onionhostbootkey/main.py` already contains the
  exact detection logic an early guard needs: `_luks_devices()` scans
  GlobalStorage `partitions` for entries whose `fsName` starts with
  `luks` or that carry a `luksMapperName`. Its failure is simply in the
  wrong phase — it runs in exec, after the disk is already written.

## Route A — force encryption on (preferred if the stock module allows)

Goal: on the erase-disk path, the "Encrypt system" option is on by
construction, not by user vigilance.

1. Check Calamares 3.3.14's partition module (the version this codebase
   already cites for the `obscure()` transform) for a supported way to
   default/pre-seed the ChoicePage encrypt checkbox — a `partition.conf`
   key, or the page honouring a pre-existing GlobalStorage
   `luksPassphrase` (which the phrase step already sets before the
   partition page is shown). **Do not assume a key exists; verify
   against the 3.3.14 source before writing config.**
2. If the stock page supports it: set it in the `partition.conf`
   heredoc in `build-iso.sh`, alongside `luksGeneration: luks2`.
3. If it does not: this becomes a small patch/wrap of the ChoicePage
   default in the build, or Route B becomes the shipping fix and
   Route A is recorded as upstream-blocked. Either outcome is
   acceptable — what is not acceptable is shipping neither.

## Route B — early guard right after Partitions (implementable today)

A show-phase step sequenced immediately after `partition` in
`settings.conf`, using the same sed-wiring pattern build-iso.sh
already uses for the phrase pages:

1. On entry (and on attempted advance), inspect GlobalStorage
   `partitions` with the same rule as bootkey's `_luks_devices()`:
   at least one partition with `fsName` starting `luks` or a
   `luksMapperName` present, AND a non-empty `luksPassphrase`.
2. If the check passes: advance silently, zero extra user friction.
3. If it fails: block advancing and show plain language, e.g. —
   *"Encryption isn't on yet, and this machine is never installed
   without it. Go back one page, tick **Encrypt system**, then come
   forward again. Your 7 words from the earlier page are still the
   ones that will lock this disk — you don't need new ones."*
   (Confirm that last sentence against actual phrase-step behaviour
   before shipping the copy — if re-entering the flow regenerates
   the phrase, the copy must say so.)
4. Manual partitioning (`allowManualPartitioning: true`) must pass
   the guard when the user hand-builds a LUKS layout, and must be
   stopped with the same message when they don't.

Route B alone satisfies the field report's minimum ("stops you at
that page with clear words"). Route A + B together are the target:
forced-on for the erase path, guard as the backstop for every path.

## Acceptance tests (all on the rig, throwaway disks)

1. **Cameron reproduction:** erase-disk, deliberately leave the
   checkbox unticked → install is stopped at the guard (Route B)
   or the checkbox is already on (Route A). The bootkey failure
   string must be unreachable via this path.
2. **Happy path:** erase-disk with encryption on → install completes,
   bootkey converts the slot, role map written (existing smoke
   battery stays green).
3. **Manual path:** manual partitioning with a hand-made LUKS
   partition → guard passes; without → guard stops with the same
   plain-language page.
4. **Regression:** the automated install drivers (which tick the
   checkbox by script) still complete unchanged.
5. **Small-screen check:** the guard page is readable and actionable
   at phone/noVNC size — that is the screen class that found this.

## Out of scope

- No change to the A19.1 slot layout, PBKDF2 conversion, or bootkey's
  fail-closed behaviour — bootkey failing loudly stays as the last
  line of defence; this fix moves the *first* line to the right page.
- Not a prod-ISO rebuild trigger by itself; fold into the wizard/
  polish tranche already named in the field report.

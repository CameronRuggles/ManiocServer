# OnionHost OS — Skeleton ISO Build Log (ISO-BUILD-PLAN steps 1–2)

## Index (added 2026-10-22)

Section line numbers are for this file as it now stands, index
included. Covers the log’s top-level (#) and second-level (##)
sections; third-level (###) subsections are not listed.

- L84 — OnionHost OS — Skeleton ISO Build Log (ISO-BUILD-PLAN steps 1–2)
- L86 — Standing conventions for this log (adopted 2026-10-20, Repo Review 4)
- L99 — Run date: 2026-10-11 · Host: Stage 1 rig (GCP onion-rig-1, nested KVM) · Working title paths only
- L100 — Scope of this tranche: pipeline + bootable/installable skeleton. No wizard logic beyond stubs (none needed yet).
- L104 — Final artifact
- L114 — Pipeline (as built)
- L117 — Test results (QEMU/KVM on the rig, OVMF Secure-Boot-capable firmware image, virtio disk 24 GiB)
- L131 — Failures hit and fixed (in order)
- L138 — Process/integrity notes
- L144 — Exact next blockers for step 3 (onionhost package)
- L152 — STEP 3, SLICE 1 (2026-10-12) — boot unblocked; onionhost package skeleton live end-to-end
- L166 — TASK 1 — Boot past GRUB: SOLVED via encrypted /boot + PBKDF2 phrase slot (A19.1)
- L279 — TASK 2 — Scaffolding strip: VERIFIED
- L334 — TASK 3 — onionhost package skeleton: RUNS END-TO-END
- L429 — Entropy-source gate (A19.1) — RECORDED, not implemented this slice
- L438 — Rig / process notes for this slice
- L461 — Blockers / next for the wizard tranche
- L483 — STEP 3, SLICE 2 — the wizard tranche (2026-10-12)
- L494 — Task 1 — GRUB passphrase retry loop: PASS
- L511 — Task 2 — Generated-phrase installer module: PASS
- L556 — Task 3 — Spare phrase step: PASS
- L569 — Task 4 — First-boot wizard S0->S1->S2: PASS
- L600 — Task 5 — onionhost-rekey: PASS
- L620 — Process notes / deviations
- L923 — FIELD REPORT — Cameron's phone-driven install, 2026-10-12
- L942 — STEP 3, SLICE 4 — content tiers (Simple Pages + Journal) (2026-10-12)
- L1153 — STEP 3, SLICE 5A — installer + editor fixes from Cameron's hands-on session (2026-10-12)
- L1349 — STEP 3, SLICE 5B — backup / restore (2026-10-12/13)
- L1499 — PROD REBUILD 2 + DOWNLOAD (2026-10-12)
- L1662 — STEP 3, SLICE 6B — DYNAMIC PLUMBING (implementation; rig battery deferred)
- L1862 — GATE 4 — UPDATE PIPELINE (implementation; rig/ISO battery deferred)
- L2102 — A23 RECIPE 1 — SMF (implementation; rig/ISO battery deferred)
- L2531 — GATE 4 FOLLOW-UP — fail-closed stickiness (2026-10-13)
- L2619 — A23 RECIPE 2 — WORDPRESS (implementation; rig/ISO battery deferred)
- L2899 — A23 RECIPES 3+4 — DOKUWIKI + GITEA (implementation; rig/ISO battery deferred)
- L3283 — RIG BATTERY — DYNAMIC TIER + RECIPES (2026-10-14)
- L3303 — Pre-battery integration work (workspace tree)
- L3323 — PART 1 — ISO REBUILD
- L3348 — PART 6 (pulled forward) — SMF OFFICIAL CHECKSUM ATTEMPT
- L3356 — PART 2 — INSTALL + FORUM (first attempt on build #2: DEFECT FOUND)
- L3412 — PART 6 — MUSL-STATIC RUST REFERENCE BUILD (checkbox)
- L3420 — PART 1 (continued) — BUILD #3 WITH THE MODE FIX
- L3451 — PART 2 — INSTALL + FORUM (build #3 ISO)
- L3756 — PRODUCT FIX SLICE — D1–D6 + ENVELOPE (2026-10-14)
- L3964 — RIG MINI RE-VERIFICATION + PUBLISH (2026-10-14)
- L3974 — PART 1 — ISO REBUILD: PASS
- L4163 — D7 FIX (2026-10-14)
- L4305 — RIG PART-3 RE-RUN + PUBLISH (2026-10-14)
- L4322 — PART A — ISO REBUILD WITH THE D7 FIX: PASS
- L4356 — Part B — fresh Gitea install, zero guest workarounds: FAIL (NEW DEFECT D8)
- L4405 — NEW DEFECT D8 (D7-residual) — native root unwritable through the production engine
- L4438 — Part C — WordPress: NOT ATTEMPTED
- L4443 — Part D — publish: WITHHELD
- L4451 — Part E — teardown + poweroff
- L4465 — D8 INVESTIGATION + FIX (2026-10-14)
- L4475 — The mechanism, as measured (supersedes the Part-3 attribution)
- L4542 — Truth table (venue; requester rows: root = container root)
- L4579 — The fix
- L4642 — Proofs (poc/d8-fix/proof/, phases run 2026-10-14)
- L4701 — Rig-deferred (NOT proven by this slice)
- L4730 — MARKETPLACE RECIPE — A23 RECIPE 5 (2026-10-17)
- L4743 — What the recipe needed that no earlier recipe did
- L4816 — Defects found (platform + recipe), all fixed in the tree
- L4865 — A defect in the marketplace itself (tree untouched; reported)
- L4884 — Proofs (sandbox venue; poc/recipes-marketplace/)
- L4966 — Rig-deferred (NOT proven by this slice)
- L4982 — PUBLIC REBRAND APPLIED — MANIOC SERVER / POLYCULTURE MARKETS (2026-10-17)
- L5057 — REPO REVIEW 2 FIX BATCH (2026-10-20)
- L5696 — REPO REVIEW 3 FIX BATCH (2026-10-20)
- L6072 — REPO REVIEW 4 FIX BATCH (2026-10-20)
- L6427 — SPARE FEATURE REMOVED — S13 CLOSED BY REMOVAL (2026-10-20)
- L6613 — REPO REVIEW 5 FIX BATCH (2026-10-20)
- L6801 — PUBLIC TREE CHANGE (2026-10-20) — GCP APPEAL DRAFT REMOVED
- L6815 — RECIPES ARE INSTALLERS — A26 (2026-10-21)
- L7011 — DEANON AUDIT FIX BATCH (2026-10-21)


## Standing conventions for this log (adopted 2026-10-20, Repo Review 4)
- **Write-time phrase rule:** this log never records a generated
  passphrase (disk, spare, or login) at write time. Where an
  install record must refer to one, a marker stands in its place.
  The ci-scan phrase rules (5-word runs, plus 3-word runs in
  secret context) are a backstop for entries predating this rule
  and for accidents — never the primary control.
- **Values rule:** findings, records and correspondence about
  this project report passphrases and addresses by class and
  location only; values are never quoted, in whole or in part.
- Redaction markers in older entries are repairs under the
  pre-rule regime and are kept visible as part of the record.

## Run date: 2026-10-11 · Host: Stage 1 rig (GCP onion-rig-1, nested KVM) · Working title paths only
## Scope of this tranche: pipeline + bootable/installable skeleton. No wizard logic beyond stubs (none needed yet).

---

## Final artifact
- **ISO**: `~/iso-build/onionhost-skeleton-amd64.iso` on the rig — **1,048,657,920 bytes (≈1001 MiB)**
- **SHA-256**: `28acd2cbf448c0b4cad4a75891cac8a77b09850042e766b72f5751a682a1cc6c`
- **Snapshot pin**: snapshot.debian.org **20251011T143150Z** (Debian 13.1, trixie, amd64, main)
- **SOURCE_DATE_EPOCH**: 1760193110 (== snapshot timestamp)
- **Kernel**: 6.12.43+deb13-amd64 · **Calamares**: 3.3.14-1 + calamares-settings-debian
- **Build wall-clock**: ~13 min for the first complete build; ~15 min for the final build (mmdebstrap ≈ 10 min, squashfs xz ≈ 3 min, mkrescue seconds). Several rebuilds were run during debugging (see incidents).
- **Build script (canonical copy)**: `build/build-iso.sh` in this repo; rig copy at `~/iso-build/build-iso.sh`; per-run pins in `~/iso-build/BUILD-INFO` (also baked into the image at `/etc/onionhost-build-info`).
- **Test driver**: `build/qemu-drive.py` (QEMU monitor + screendump→PNG), `build/guest-ssh.sh` (SSH into the guest via rig hostfwd :2222).

## Pipeline (as built)
mmdebstrap (root mode, `--variant=important`, `--skip=cleanup/apt`, snapshot mirror, `Check-Valid-Until false`) → chroot customisation (locales en-US; keyboard us+de switchable; pre-created live user; LightDM autologin; explicit Calamares `partition.conf`; `/etc/default/grub` synthesised; `update-initramfs`) → mksquashfs (xz) → `grub-mkrescue` hybrid ISO (BIOS isolinux + UEFI GRUB from the host's grub-mkrescue; ESP chain on installed systems is Debian's signed shim→grub). Rootfs contents: kernel, systemd, LightDM+XFCE, Calamares, cryptsetup(+initramfs), podman, tor (Debian's — **deviation**: plan says Tor Project repo pin; skeleton only), chrony, nftables, openssh-server + xdotool (rig test access).

## Test results (QEMU/KVM on the rig, OVMF Secure-Boot-capable firmware image, virtio disk 24 GiB)

### (a) ISO boots live — **PASS**
Boots from ISO under OVMF to the XFCE live desktop, autologin as the live user, Calamares starts. Evidence: `build/shots/04-live-desktop.png`, `build/shots/40-clean-desktop.png` (final ISO).

### (b) Calamares install into qcow2 — **PASS (clean run on final ISO)**
Guided flow driven by xdotool over guest SSH: Welcome → Location (America/New_York default) → Keyboard (en-US) → Partitions: **Erase disk + "Encrypt system" ticked**, passphrase entered twice → Users → Summary (**"Debian 23.71 GiB LUKS2"**, GPT, 300 MiB FAT32 ESP at /boot/efi, no swap) → Install. **All 40 jobs completed; session log ends "completion: succeeded", 0 ERRORs; Finish page "All done."** Evidence: `build/shots/45-clean-summary.png`, `build/shots/46-clean-result.png`, full session log `build/calamares-session-clean-install.log` (1083 lines).

### (c) Installed system reboots to a LUKS prompt — **PASS**
Reboot from the qcow2 (no ISO): OVMF loads the registered **Boot0007 "Debian"** entry (`\EFI\Debian\shimx64.efi`) and GRUB prompts: **"Enter passphrase for hd0,gpt2 (4f9115c2-b39b-4ec8-bd31-4fc8202b833d):"** — the new volume's LUKS UUID. Evidence: `build/shots/47-clean-luks-prompt.png`.

### Known limitation found by going one step further (NOT part of the (c) criterion)
Typing the (verified-correct) passphrase at the GRUB prompt yields **"error: Invalid passphrase"** and no `(crypto0)` device. Verified on the rig host via qemu-nbd + `cryptsetup open --test-passphrase`: **the passphrase is correct**; both LUKS keyslots use **PBKDF argon2id** (luksDump), and **Debian trixie's signed GRUB 2.12-9 cannot unlock argon2id**. Calamares' erase layout puts /boot inside the LUKS root, so boot depends on GRUB cryptodisk — a dead end with argon2id. Debian's d-i avoids this with a separate unencrypted /boot. **This is step-3 blocker #1** (fix candidates below).

## Failures hit and fixed (in order)
1. **mmdebstrap apt conflict** — `--variant=standard` pulls `systemd-timesyncd`, which conflicts with `chrony` over `time-daemon`. → `--variant=important`.
2. **Live user authentication totally broken** — live-config's built-in default password (legacy DES crypt of "live") is rejected by trixie's PAM/libxcrypt: greeter login AND console/graphical autologin all failed ("Authentication failure" on tty3). → **Pre-create the live user in the image** (live-config's user-setup explicitly skips existing users) with a modern hash (skeleton password: `onion`); autologin set in LightDM's main config + conf.d.
3. **No `partition.conf`** — calamares-settings-debian ships none; the module would have used compiled defaults. → Wrote an explicit one; **`luksGeneration: luks2`** verified in the install Summary.
4. **First install FAILED at job 30/40** — Debian's `calamares-bootloader-config` helper runs `apt-get install grub-efi` inside the target: **"Package 'grub-efi' has no installation candidate."** Root cause: mmdebstrap cleans `/var/lib/apt/lists`, so the target had no package candidates (installed packages still report "already newest" from dpkg status, masking it). Cascades: missing /etc/default/grub (grub-common's copy is ucf-generated and never materialises under mmdebstrap) → sed/update-grub errors. → Three build fixes: **ship `grub-efi` in the image**, **`--skip=cleanup/apt`** (keep lists), **synthesise `/etc/default/grub`** in customisation. The failed install was then also finished by hand (crypttab + KEYFILE_PATTERN + GRUB_ENABLE_CRYPTODISK + grub-install) purely as a salvage to probe the boot path — that salvage is what produced the first (c) evidence (`build/shots/34-luks-prompt.png`) and exposed the argon2id finding; the PASSes above are from the subsequent clean run.
5. **Guest-automation traps (rig-side, recorded for future tranches)** — QEMU screendump doesn't render the pointer (blind mouse calibration impossible → use guest-side xdotool); monitor `sendkey` typing is ~3 s/char (monitor recv timeouts) — fine for passphrases, painful for commands, so bake SSH access into test images instead; typing into a guest that is still at the GRUB menu corrupts the boot entry ('e' opens the editor) — always screenshot-verify the desktop before sending keys; live-config forces sshd `PasswordAuthentication no` (worked around with a baked pubkey + an `sshd_config.d` drop-in, which wins over the main file).

## Process/integrity notes
- Two build invocations briefly overlapped once (a stale detached build plus a relaunch); both wrote the same output paths. The final artifact pair (rootfs ↔ ISO) was verified mutually consistent by content checks (grub-efi present, authorized_keys present, lists present, ISO sha matches its .sha256) before the clean test run, which used that pair.
- No injected "operator/stop" instructions appeared in tool output during this tranche.
- BIOS/legacy boot path (isolinux in the hybrid ISO) was **not** tested — UEFI only, per plan order.
- The GCP rig VM was left RUNNING; the QEMU test VM is stopped.

## Exact next blockers for step 3 (onionhost package)
1. **Boot-past-GRUB (argon2id)** — choose and implement one: (i) separate unencrypted /boot partition via Calamares `partitionLayout` in partition.conf (d-i pattern; initramfs — which handles argon2id fine — then owns unlocking; GRUB needs no cryptodisk; the design's "console LUKS prompt" becomes the initramfs prompt), or (ii) a PBKDF2 boot keyslot for GRUB (KPMcore/cryptsetup options — not exposed by Calamares' partition.conf as far as this build shows; both slots came out argon2id). Option (i) is the known-good Debian pattern; needs a layout test + crypttab/keyfile re-verification. Until then, full-boot is blocked; installs and LUKS-prompt behaviour are proven.
2. **First-boot experience is stock Debian** — installed system has the live user's leftovers to strip (calamares `removeuser`/packages jobs in settings-debian handle the live user, but our pre-created-user trick + `/etc/lightdm` autologin drop-in + test sshd drop-in/authorized_keys are skeleton scaffolding that must NOT survive into the onionhost image; the S0 autologin state machine replaces them).
3. **Tor from Debian** (0.4.9.x) rather than the pinned Tor Project repo packages the plan specifies; pin when the onionhost package lands its golden torrc (PoC verified the same version feature set).
4. **onionhost package itself** — containers A/B/U Quadlet units with the wrapper-runtime + per-container runsc golden flags from the Stage 1 rig results (`--host-uds=create` for B, `--host-uds=all` + stripped netns for A), golden nft table + JSON-compare gate, generated-phrase Calamares module (replacing typed passphrases), dashboard stub. Gate R's `--disable-keyring` initramfs decision (A18) must be baked into the initramfs config at this step.

---

# STEP 3, SLICE 1 (2026-10-12) — boot unblocked; onionhost package skeleton live end-to-end

Scope: step-3 blocker #1 (GRUB/argon2id), scaffolding strip (Task 2),
onionhost package skeleton (Task 3). Method: iterated test-flavour
builds on the rig (`FLAVOUR=test OH_PROBE=1`, WORK `~/iso-build-test`,
builds 3–15), each followed by a full clean install (Calamares driven
over guest SSH via xdotool; installs #1–#8) and a scripted boot test
(`build/boottest3.py`: wrong phrase → GRUB rescue re-prompt → correct
phrase → greeter stability → login → in-guest verification capture).
A mid-slice design ruling (**A19.1**, superseding A19's dual-slot
idea) changed the target layout while the work was in flight; the
implementation follows A19.1, not the original brief's twin-slot
sketch.

## TASK 1 — Boot past GRUB: SOLVED via encrypted /boot + PBKDF2 phrase slot (A19.1)

**Chosen: brief option (a) as amended by A19.1 — /boot stays inside
the encrypted root; the user phrase slot uses PBKDF2 (GRUB 2.12 can
unlock it); a separate per-install random keyfile slot serves the
initramfs. The unencrypted-/boot fallback (b) was NOT needed.**

Final installed LUKS layout (verified by `cryptsetup luksDump` on the
installed disk after every install): slot for the **install phrase =
pbkdf2/sha256, 2,287,467–2,311,675 iterations** (target `--iter-time
2500`, calibrated by cryptsetup on the install host); slot for the
**random keyfile = argon2id** (KDF immaterial — 2048-byte CSPRNG
keyfile; GRUB never touches it). No argon2id phrase slot remains.
Note: current installs produce TWO slots; the A19.1 SPARE phrase slot
(PBKDF2) is enrolled by the future Maintenance/wizard flow — stock
Calamares has no spare-phrase UI. That is a wizard-tranche item, not
a slice-1 gap in the boot mechanism itself.

### GRUB unlock cost (the ~15 s budget)
- Calibration experiments (cloned volume, GRUB serial timing):
  host `--iter-time 2000` → 1,464,490 iters → **9.05 s** unlock;
  `--iter-time 6000` → 4,356,960 iters → **31.00 s**. GRUB's PBKDF2
  runs ≈4.5–5.2× slower than the host cryptsetup benchmark, roughly
  linear — so `--iter-time` (host-calibrated) is the right knob and
  the ratio is the transferable constant.
- Production target chosen: `--iter-time 2500`
  (`onionhostbootkey`, `ITER_TIME_MS`). Measured on installed systems
  (boot tests 2–8): phrase Enter → `Slot "2" opened` in **13.2–15.2 s**
  (13.22, 13.82, 14.02, 14.22, 14.62, 14.82, 15.22 across runs).
  **Flag:** this sits AT the ~15 s budget edge on the rig's virtual
  CPU; for slower home hardware, drop the target to 2000
  (~11–12 s expected) — revisit in the wizard tranche with real
  hardware timings.
- One phrase entry total: after GRUB unlocks, the initramfs opens
  the root **silently via the embedded keyfile** — no second prompt;
  system boots straight to the LightDM greeter (screenshot-verified;
  no autologin in the installed target).

### How the slot gets converted: `onionhostbootkey` jobmodule
Calamares/KPMcore always creates argon2id phrase slots, so a
Calamares Python jobmodule (`onionhost/calamares/modules/
onionhostbootkey/`, sequenced after `luksbootkeyfile`) converts in
the install transaction: add a PBKDF2 slot for the same phrase →
verify with `--test-passphrase --key-slot` → **kill the argon2id
phrase slot** → verify the final layout; any non-compliance **fails
the install loudly**. Three real bugs were found and fixed on the
way (each failure loud, none silent):

1. **Calamares GlobalStorage stores the passphrase OBSCURED.**
   `luksPassphrase` is `Calamares::String::obscure()`-transformed
   (chars > U+0021 map to U+1001F − codepoint; the transform is its
   own inverse; Calamares 3.3.14 `ChoicePage.cpp:698`,
   `src/libcalamares/utils/String.cpp:113-124`). Proven numerically
   in the module's (since removed) debug log: the stored value for
   the test phrase is 28 code points / 78 UTF-8 bytes, sha256 prefix
   `f2ad874f6d…` vs the plain phrase's `c4bbcb1fbe…`; the raw stored
   value opens NO slot. Fix: `_unobscure()` in the module.
   **Wizard-tranche consequence:** a generated-phrase module must
   insert the phrase into GlobalStorage **in obscured form** to match
   what downstream Calamares jobs expect.
2. **crypttab timing.** The module originally also relocated the
   keyfile into `/etc/cryptsetup-keys.d/`, but Calamares' `fstab`
   job rewrites crypttab AFTER `luksbootkeyfile`; the relocation
   moved into `onionhostcleanup` (runs after `fstab`, before
   `initramfscfg`).
3. **`cryptsetup luksKillSlot` needs `--key-file <phrase file>`**
   as remaining-key proof; `--batch-mode` alone fails
   non-interactively with "No key available with this passphrase."

### A19.1 keyfile hygiene + the embedding trap
- Keyfile lives at `/etc/cryptsetup-keys.d/root.key`, dir **0700**
  root:root, file **0400** root:root (2048 random bytes);
  `UMASK=0077` in initramfs.conf; resulting initrd is **0600**;
  crypttab references the exact file (`keyscript=/bin/cat` retained).
- **Trap:** Debian's `encrypt_hook` only embeds the hardcoded legacy
  path `/crypto_keyfile.bin`, and the cryptroot hook does NOT copy
  keyfiles for `keyscript=` entries — the A19.1 relocation silently
  broke embedding. Fix: overlay initramfs hook
  `etc/initramfs-tools/hooks/zz-onionhost-keyfile` copies the keyfile
  into the initramfs at the exact path.
- **A18 (`--disable-keyring`) mechanism:** Debian trixie's cryptroot
  has NO crypttab option or conf-hook for it (inspected
  `/usr/lib/cryptsetup/functions`). Implemented as overlay hook
  `etc/initramfs-tools/hooks/zz-onionhost-cryptsetup`, which replaces
  the cryptsetup binary *inside the initramfs only* with a wrapper
  injecting `--disable-keyring` on `open`/`luksOpen` (real binary
  kept as `cryptsetup.real`).
- **A18 VERIFIED from installed systems:** after login,
  `dmsetup table --showkeys` shows the raw 128-hex volume key (e.g.
  `433ed0e6…7293f`, `970eba41…83f4`, `f7644a3f…16b4` across
  installs), NOT a `:logon:` keyring reference — i.e. the
  initramfs-created mapping itself is in the keyring-disabled
  format Gate R required.
- **No keyfile in the ISO:** build-time assertion in `build-iso.sh`
  passes on every build ("A19.1 check OK: no keyfile in ISO
  rootfs"), and a `find` over the prod squashfs for `*.key` /
  `crypto_keyfile*` / `root.key` returns nothing.

### A19.1 installed-system checks (verified on fresh targets)
- **Swap: absent** — `partition.conf userSwapChoices: [none]`;
  fstab has ESP + LUKS root only.
- **kdump: absent** — kdump-tools is not in the image (disabled by
  absence; build log line records it per build).
- **/var/log sweep for the install phrase: clean** on the installed
  target; no Calamares.log is copied into the target.
- **PRODUCT FINDING — GRUB does not re-prompt.** A wrong phrase at
  GRUB 2.12 drops to the `grub>` rescue shell (no retry). Recovery
  path proven in every boot test: `cryptomount hd0,gpt2` →
  re-prompt → correct phrase → `normal` → boot continues. A typo
  would strand a non-technical user at a rescue prompt:
  **the wizard tranche MUST add a GRUB retry loop** (or equivalent
  recovery UX). Recorded as a blocker below.

## TASK 2 — Scaffolding strip: VERIFIED

Leak confirmed first on the skeleton's installed target (live `user`
uid 1000 + operator authorized_keys, `testuser`, LightDM autologin
drop-in active, sshd + test drop-in, xdotool). Fix = build-time
flavour separation (`FLAVOUR=prod` default; `FLAVOUR=test` carries
the live-session test access ONLY — sshd + xdotool + operator key +
known live password `onion`; **the prod live user gets a per-build
random password, never recorded**) + the `onionhostcleanup`
jobmodule. Verified on fresh installed targets (NBD, read-only):

- Users: root + the install-created user only; `/home` has no live
  `user`; autologin drop-in removed, autologin lines re-commented.
- openssh-server/xdotool **purged** (dpkg state `un`, no binaries);
  ssh.service masked; authorized_keys gone; `ss -ltn` on the running
  installed system shows **nothing listening**.
- sleep/suspend/hibernate/hybrid-sleep masked.
- `onionhostcleanup` also performs the keyfile relocation (above)
  and asserts the crypttab/keyfile end state.
- **Prod image audit** (squashfs of `onionhost-amd64.iso`, build
  prod-1, 1,335,011,328 bytes, 2026-10-12T04:56Z): no
  `/usr/sbin/sshd`, no xdotool binary, no `~/.ssh`, no sshd_config;
  live user shadow is a yescrypt hash of the per-build random
  password; root is locked (`*`); package-status hits for
  "openssh-server" are only other packages' Breaks/Suggests lines.
- **Prod live session works as designed:** boots to the live desktop;
  `sudo -n id` → `uid=0(root)` rc=0 (live-config grants the live
  user passwordless sudo at boot — that, not the random password, is
  the installer elevation path, via Debian's
  `calamares-install-debian` → `sudo calamares`); Calamares 3.3.14
  launches and renders (screenshot evidence).
- **Prod install attempt (keyboard-driven; see rig note below):**
  the install ran to the exec phase and the `onionhostbootkey`
  module **failed it loudly** — "Install passphrase not available in
  GlobalStorage (luksPassphrase); cannot convert the phrase slot" —
  because that drive could not tick the Encrypt checkbox, and an
  unencrypted install produces no `luksPassphrase`. This is the
  guard working as designed: **an unencrypted install is refused,
  not silently shipped.** The encrypted install path itself is
  flavour-independent (identical Calamares config + jobmodules in
  both ISOs) and was proven end-to-end on eight test-flavour
  installs. A fully-driven encrypted *prod* install remains
  unexercised for a rig reason only (below).
- Post-audit fix (in `build-iso.sh`, applies from the next build):
  the `onionhostprobe` diagnostics module's FILES shipped in prod
  (inert — not in the exec sequence unless `OH_PROBE=1`); the build
  now deletes it from prod rootfs outright. Defence in depth: a
  module that can write GlobalStorage contents has no business
  existing on the production image.
- Debug hygiene: the bootkey module's interim debug instrumentation
  (wrote phrase length + sha256 prefix to /tmp) has been **stripped
  from the shipped source**; the version in both ISOs' final builds
  is the clean one (and it is the clean one that produced the loud
  failure above).

## TASK 3 — onionhost package skeleton: RUNS END-TO-END

Shipped in the image (source of truth: `onionhost/rootfs-overlay/` +
`onionhost/calamares/`; canonical build `build/build-iso.sh`):
Quadlet units `onionhost-a/b/u.container` + `onionhost.network`
(rootful Podman, `PodmanArgs=--runtime=runsc-wrap`), `runsc-wrap`
wrapper runtime (per-container gVisor flags/host-UDS per A18),
golden templates (torrc with the PoC settings incl. PoW defenses —
`PoWQueueRate 250 / Burst 500` still UNCALIBRATED, an alpha item;
client-torrc; nginx.conf with Gate-H header hygiene), the
canonical-JSON nftables gate (`onionhost-nft-gate` +
`onionhost-nft-compare.py` + load service + 5-min timer; golden
table is still the PoC miniature, NOT the production policy),
`onionhost-generate-configs` (renders /etc/onionhost, owns state-dir
ownership + the `http.sock → b1.sock` symlink), `onionhost-probe`
(the A4 self-check: fetch own onion via U's SOCKS), tmpfiles.d
plumbing, sleep-target masks, image import service (tor/web rootfs
tars ≈381 MB / ≈375 MB, mmdebstrap `--variant=important` —
slimming is future work), runsc pinned release-20251006.0
(sha512-verified).

### Four runtime bugs found on the installed system, fixed, re-verified
1. **gVisor cannot use the host network from inside a user
   namespace.** A/U originally used `Network=host` (A18's recipe);
   runsc start failed: "cannot run with network enabled in root
   network namespace". Root cause: A18's egress proof predates
   `--userns=auto` on A, and podman 5 emits NO netns entry for
   host/none modes (podman 4.9 emitted the entry the recipe
   stripped). A kernel rule, not a bug: a child userns cannot join
   the init-userns-owned host netns. **Fix:** A/U moved to a
   dedicated podman bridge network (`onionhost.network`, subnet
   10.89.77.0/24) whose netns is owned by each container's userns;
   wrapper leaves tor bundles' spec netns untouched. Outbound-only
   is all an onion gateway/client needs. (Design note: this refines
   A18's mechanism, not its intent; the nft gate's production form
   must police the bridge path instead of host-netns egress.)
   Sub-bug: podman 5.2's Quadlet generator does NOT pull a
   referenced `.network` service in by itself ("network not found";
   generated service sat `inactive (dead)`). Fix: `[Install]
   WantedBy=multi-user.target` in the .network + explicit
   Wants/After in A/U.
2. **`UserNS=auto` makes volume ownership a lottery.** Tor refused
   its state dir ("Directory /var/lib/onionhost/tor/hs cannot be
   read: Permission denied") — host-root-owned 0700 dirs are
   "nobody" inside the userns, and auto allocation changes per
   recreate. **Fix:** fixed `UIDMap`/`GIDMap` per container
   (A=2100000, U=2200000, B=2300000, 65536 each — same private-
   userns mechanism as A5's auto, at fixed offsets), and
   `onionhost-generate-configs` chowns the state dirs to the
   container roots every boot.
3. **Tor's listener-directory strictness.** Tor refuses socket
   dirs not owned by its own user / accessible to others (control
   socket: "/run/onionhost/control is not owned by this user (root,
   0) but by nobody (65534)"). Fix: tmpfiles.d creates
   `/run/onionhost/control` (0700, 2100000) and
   `/run/onionhost/client/socks` (0700, 2200000); consumers reach
   the sockets as host root / via the privileged probe, per A4.
4. **B's socket bind.** nginx: `bind() to unix:/run/onionhost/web/
   b1.sock failed (13: Permission denied)` — the exchange dir must
   be 0777 (now also asserted in generate-configs, not just
   tmpfiles), and B runs with `UMask=0000` so `b1.sock` is created
   world-writable for A's tor (a different userns uid) to connect.
   The web socket is not a privilege boundary in this design (it
   serves the public site); the control socket is, and is locked.

Also fixed en route: rootful Podman 5 `UserNS=auto` needs a
`containers` pool user (system user + subuid/subgid
`containers:2000000:536870912` added); the host `tor` package's
`tor@default` (127.0.0.1:9050) is masked — first onionhost
containers are the only Tor on the box. Live-session caveat: in the
LIVE session the stack also starts and the image-import service
fails (podman overlay driver cannot run on live-boot's overlayfs);
suppressing the stack in live sessions is a wizard-tranche
refinement. Warning seen: "aardvark-dns binary not found, container
dns will not be enabled" — bridge containers currently get no DNS;
tor's operation does not depend on it (directory fetches are to IPs
via the consensus), recorded for the production-policy pass.

### End-to-end proof (test build 15, install #8, boot test #8 — all 2026-10-12)
- Install "completion: succeeded" (43 jobs); wrong phrase rejected
  at GRUB; rescue re-prompt; correct phrase → Slot 2 opened in
  **14.22 s**; greeter; login.
- In-guest verification: **all seven onionhost services `active`**;
  `podman ps`: **onionhost-a, onionhost-b, onionhost-u all Up**;
  A's tor and U's tor both log **"Bootstrapped 100% (done)"**;
  nginx 1.26.3 serving in B (no network) with `b1.sock` bound
  behind the host-owned `http.sock` symlink; **onion address
  minted**: `gjvb3q3nlaehon26avfam5vn2bcc4nlpg2vpzyboxmgmqhlhbwrq5vqd.onion`;
  **`onionhost-probe` fetched the placeholder page through the real
  onion path** (U's SOCKS → Tor → rendezvous → A → http.sock → B):
  **HTTP/1.1 200 OK**, `Server: nginx`, content-derived
  ETag/Last-Modified, **no Date header** (Gate H holds);
  `ss -ltn` empty (no host TCP listeners); dm table shows the raw
  volume key (A18 format).

## Entropy-source gate (A19.1) — RECORDED, not implemented this slice
Wizard-tranche release gate: the generated-phrase path must use
`getrandom()` blocking until the kernel CSPRNG is seeded, select
from the full ~7776-word list with bias-free rejection sampling
(no modulo reduction). Applies to the disk phrase, the login
phrase, and the per-install keyfile (keyfile currently: 2048 bytes
from the install environment's CSPRNG via cryptsetup — audit the
exact source when the wizard lands).

## Rig / process notes for this slice
- The QEMU monitor has **no working mouse** in this VM config
  (usb-tablet absolute events via `mouse_move` never move the
  guest pointer; `sendkey` works). Test-flavour driving therefore
  used guest SSH + xdotool; the prod live session (no SSH by design)
  was driven keyboard-only as far as Qt focus allowed — the
  Partitions page's Encrypt checkbox could not be ticked
  keyboard-only (focus not discernible; Alt+E is not its mnemonic),
  which is why the prod install attempt ran unencrypted into the
  bootkey guard. An in-guest /dev/input injector was prototyped
  too late to matter. On real hardware this is a non-issue (a
  person clicks); for future rig work, bake the injector into the
  test flavour.
- Calamares GUI pacing lesson (again): chained clicks race page
  transitions and the Users form comes up empty or with a mangled
  login (auto-suggestion appends). Drive pages in separate calls
  and screenshot-verify the form before Next.
- One service restart mid-slice briefly interrupted tooling; rig
  state was re-verified from on-disk logs before continuing (the
  build in flight was unaffected).
- The GCP rig VM is left **RUNNING** per this slice's instructions;
  QEMU guests are stopped.

## Blockers / next for the wizard tranche
1. **GRUB retry loop** (product finding above) — a typo currently
   strands the user at a `grub>` rescue shell.
2. **Generated-phrase Calamares module** — mint the 7-word disk
   phrase + 3-word login phrase; insert the disk phrase into
   GlobalStorage **in obscured form** (see Task 1 finding 1);
   entropy gate above applies.
3. **Spare-phrase enrolment** (A19.1 SPARE slot, PBKDF2) +
   Maintenance re-key flow with the real-GRUB-boot test A19.1
   requires.
4. **Live-session suppression** of the onionhost stack (don't run
   containers / image import in the installer session).
5. **Production nft policy** for the bridge topology + gate
   re-verification; PoW queue calibration (Gate 5 follow-up);
   container DNS decision (aardvark-dns).
6. GRUB `--iter-time` margin decision for slow home hardware
   (2500 vs 2000) with Stage-2 hardware timings.
7. Image slimming (two ≈380 MB container rootfs tars dominate the
   1.3 GB ISO) and BIOS/legacy boot testing (still untested).

---

# STEP 3, SLICE 2 — the wizard tranche (2026-10-12)

Built and tested on the Stage-1 rig (GCP onion-rig-1). All five tasks
PASS with real-install evidence. Test systems: install A (WITH spare,
build 6 ISO; wizard.py hot-patched on disk for the bug found during
its own test, then the fix rebuilt into build 7), install B (spare
skipped, build 7). Final ISOs: test build 7 = 1,346,957,312 bytes,
sha256 6dbc88be1c5d7a5f0529989755e682b29465a7d583eb31f81be12498933c1650;
prod build (same tree) = 1,341,134,848 bytes,
sha256 ba6baf294de46b2f8a16ff009782b4f10e00023eaaf36e8402efb2d91ae9f2bd.

## Task 1 — GRUB passphrase retry loop: PASS

- Calamares job `onionhostgrubstub` (after bootloader) rewrites the
  ESP stub (EFI/debian/grub.cfg): grub-install's own cryptomount line
  is wrapped in an INDEFINITE while loop with plain-language echoes
  ("This computer is locked with a passphrase." / "That passphrase
  was not accepted. Check that Caps Lock is off, then try again.").
  Recorded choice: indefinite loop - the ~12 s PBKDF2 cost per
  attempt is the rate limit; a cap could strand the owner.
- Same transform shipped for the running system
  (/usr/local/bin/onionhost-grub-stub + apt DPkg::Post-Invoke hook).
- Scripted boot on install A (boottest-slice2.py mode=loop): wrong
  phrase -> REPROMPT True, AT_RESCUE_SHELL False -> correct phrase
  boots. Serial + screenshot evidence (rig ~/slice2/boots/,
  shot-after-wrong.png): our messages + second "Enter passphrase"
  prompt visible, no grub> shell.

## Task 2 — Generated-phrase installer module: PASS

- Two framework findings that shaped this task:
  1. Pure-QML Calamares view modules DO NOT LOAD in Debian's
     Calamares 3.3.14 ("invalid interface qml"; pythonqt absent too).
     The phrase/spare pages are therefore C++ Widgets viewstep
     plugins (source: onionhost/calamares/plugin-src/, modelled on
     the shipped `license` module), compiled against the Calamares
     3.3.14 source headers + installed libs in a pinned-snapshot
     chroot on the rig. BUILD DEBT: plugin compilation is a manual
     rig step this slice; it must be automated into build-iso.sh
     before any release (A14 reproducibility).
  2. Calamares 3.3 executes job modules ONLY in the exec phase
     (ExecutionViewStep is the sole jobs() caller) - a show-phase
     generation job never runs. Generation therefore happens inside
     the phrase view step itself on first activation (getrandom(2)
     flags=0 = blocks until seeded; EFF large wordlist, 7776 unique
     entries, build-gated count+uniqueness; 13-bit rejection
     sampling, no modulo). The step inserts the phrase into
     GlobalStorage in Calamares' obscured form as luksPassphrase
     (+ integrity copy + spare candidate). The Python
     phrasegen.py (same algorithm) serves the wizard and rekey.
  3. Sampler verification: the exact randBelow() source was
     extracted and distribution-tested in the chroot (400k draws,
     all 7776 outcomes, min 25 / max 80, mean 51.4) after an
     off-by-one in the bit-length math (31-clz -> 32-clz) was
     caught pre-build; Python generator likewise tested locally.
- End-to-end: three real encrypted installs driven through the
  actual pages (screenshot-read phrases typed back at verification,
  3 randomised positions; Next stays disabled until all match).
  Displayed phrases opened their disks offline (cryptsetup open /
  --test-passphrase) and booted via GRUB (below).
- PBKDF2 target --iter-time 2000 (was 2500): GRUB unlock on the rig
  vCPU measured 12.22 s ENTER->opened for the main phrase (loop
  test), 27.43 s and 12.22 s on the two spare-phrase boots - treat
  per-attempt cost as ~12 s on this vCPU with real variance by
  slot position and load; slice 1's 2500 measured 13.2-15.2 s, so
  2000 is a modest real gain, still CPU-bound on home hardware.
- PHRASE-LOG GREP (required report): Calamares session log of
  install A (1,620 lines): ZERO occurrences of any main- or
  spare-phrase word. Full-filesystem grep of install A attempt 1:
  ZERO phrase hits ("paralyze" appears only in dictionaries and
  the wordlist itself). Install B /var/log grep: ZERO. The phrase
  is never logged.

## Task 3 — Spare phrase step: PASS

- Optional page after the main phrase page; nothing enrols unless
  the user creates AND verifies the spare (onionhostSpareAccepted=1
  in GS); bootkey then adds it as its own PBKDF2 slot (--iter-time
  2000, --test-passphrase verified in-transaction).
- Slot-role map written to /etc/onionhost/luks-roles.json (0644).
  Install A: SPARE=0, KEYFILE=1, MAIN=2 (luksDump: 2x PBKDF2 +
  keyfile argon2id). Both phrases boot (two scripted boots).
- Install B (spare skipped): luksDump shows EXACTLY two slots
  (1=keyfile argon2id, 2=phrase PBKDF2); role map SPARE: null;
  displayed phrase opens the volume.

## Task 4 — First-boot wizard S0->S1->S2: PASS

- firstrun job writes state=S0, the LightDM autologin drop-in
  (session onionhost-wizard), the helper sudoers rule, and
  faillock deny=5 / 900 s / 900 s with PAM wiring (verified in the
  installed files offline).
- Driven end-to-end on install A: S0 kiosk wizard (no desktop)
  -> 3-word login phrase generated, copied, verified (2 random
  positions) -> atomic commit via onionhost-wizard-helper
  (chpasswd -> fsync -> drop-in removed -> state=S1 -> LightDM
  restart) -> greeter login WITH the 3-word phrase -> wizard
  resumes (site-type stub) -> Go Live stub -> state=S2
  (verified: cat state = S2; podman ps shows A/B/U up).
- Power pulls (kill -9): at S0 -> reboot returns to the wizard
  welcome, state S0, no half-transition. At S1 -> reboot returns
  to the greeter (no autologin), phrase login works, wizard
  resumes at S1.
- Stack up with nobody logged in: on a spare-phrase boot where
  the wizard was never touched and no login happened, an
  EXTERNAL Tor client on the rig fetched the placeholder page
  from install A's onion address
  (7tuabtoxtctr73wo5d74hkgmyu6otbmsnk3jcdyevpwooc6xr23elaid.onion):
  "This OnionHost site is running." Probe on the completed
  system: PROBE_OK, HTTP 200, RC=0.
- REAL BUG FOUND + FIXED by this tranche's testing: the wizard
  regenerated the login phrase on EVERY phrase-page render, so
  "Show the words again" silently switched the words and
  verification against the first paper copy could never pass.
  Fixed (generate once per wizard session) and retested clean.
  (Calamares C++ pages already had generate-once semantics.)

## Task 5 — onionhost-rekey: PASS

- Root helper per A19.1: role map -> volume key from the running
  mapping (works because A18's --disable-keyring open keeps it
  recoverable) into /dev/shm 0700/0600 only -> new phrase ->
  luksAddKey PBKDF2 --iter-time 2000 -> --test-passphrase ->
  luksKillSlot old MAIN -> atomic role-map update ->
  update-initramfs. Maintenance boot entry (custom.cfg
  "OnionHost Maintenance", systemd.unit=onionhost-maintenance.target)
  generated by grubstub; rekey also runs from the desktop.
- Acceptance on install A (transcript captured): MAIN slot 2
  replaced by slot 3. Reboot battery: OLD phrase fails at GRUB
  with re-prompt (REPROMPT True, AT_RESCUE_SHELL False); NEW
  phrase boots ("Slot 3 opened"; ENTER->opened 25.83 s in that
  run - two PBKDF2 derivations, GRUB tries SPARE slot 0 before
  MAIN slot 3); SPARE phrase still boots
  (ENTER->opened 12.22 s, slot 0 tried first). Transcript
  contains no secrets (volume key never in argv/env/logs;
  phrase files shredded).

## Process notes / deviations

- Install A attempt 1 FAILED at onionhostgrubstub: the Maintenance
  entry extractor used a regex that cannot match Debian's
  menuentry line (options sit between the name and the brace).
  Replaced with a brace-counting scan; attempt 2 + install B
  complete all 45 jobs. The failure behaved as designed (loud,
  install aborted, nothing silently shipped).
- A 770-mode bug in overlay directories (rsync -a propagated 770
  onto /usr/share etc., breaking dbus/LightDM) was found and fixed;
  build-iso.sh now forces 755 on every overlay-touched directory.
- One build handoff report (build 1) carried numbers matching
  nothing on disk; on-disk logs govern (noted for the record).
- Rig/ops notes: QEMU monitor mouse_move needs 0-32767 absolute
  coordinates and the usb-tablet path never moved the guest X
  pointer in this setup - installer driving used guest xdotool,
  installed-system driving used PS/2 keyboard via the monitor
  (sendkey combos need dash syntax: ctrl-alt-t; a Tab after each
  wizard page transition is required before typing). Boottest
  guests sometimes ignore the monitor quit - kill by pidfile.
  Sandbox HOME flapped between /root and /home/hatch mid-session,
  breaking ~/.ssh resolution; absolute paths + an explicit
  UserKnownHostsFile fixed it (fresh pin; hostname verified
  onion-rig-1...onion-rig.internal on reconnect).
- GRUB's own "error: Invalid passphrase." lines still print above
  our friendly message at the boot prompt; cosmetic, parked.

=====================================================================
STEP 3, SLICE 3 — hardening: plugin-build automation, production nft
policy for the bridge topology, PoW calibration, ISO slimming, BIOS
boot test. (2026-10-12, rig onion-rig-1; test flavour throughout;
prod inherits at the next build. Evidence on the rig under
~/slice3/ and copied to slice3-evidence/ in this repo.)
=====================================================================

FINAL ARTIFACT (test): onionhost-test-amd64.iso
  1,145,683,968 bytes, sha256
  2751a067e92d2edafd79a7ed6e46ca01edc096c1b85d66a18ed7972e15fe8df5
  (three builds this slice: A = slimming only, B = + PoW template,
  C = + nft forward-chain fix. Install C ran build B, install D ran
  build C = the shipped artifact. The prod ISO was NOT rebuilt this
  slice.)

TASK 1 — Calamares plugin build automated: PASS.
- build-iso.sh gained a build_plugins() phase: an mmdebstrap chroot
  from the same pinned snapshot (cached at $WORK/calabuild) compiles
  onionhostphrase + onionhostspare against Calamares 3.3.14 headers.
  The orig tarball is fetched from the snapshot mirror and verified
  against the pinned sha256 fa158d679bb9384beaf4a2f821be6da63500b136
  31ad14acec9bb446565dad4a (from the signed .dsc). Compilation runs
  env -i with LC_ALL=C, TZ=UTC, SOURCE_DATE_EPOCH from the snapshot,
  and -ffile-prefix-map for both trees. Hashes are recorded in
  BUILD-INFO (plugin_phrase_sha256 / plugin_spare_sha256).
- Acceptance: the hand-built .so files were DELETED from both source
  trees, the script ran clean end-to-end, and the automated output
  is BYTE-IDENTICAL to slice 2's hand-built plugins (phrase
  f8d855778fed4caab3024339c5962ab6ef1bc05ae21d62e0d8e478e58688d52b,
  spare d891de38873338b4fe0d4f0e270535237b2f6f323682ccef5262bc70a49
  e72a4) — across two independent builds (manual rig step vs
  automated chroot). That is direct A14 reproducibility evidence.
- Install-side: on installs C and D the phrase page rendered,
  verification completed ("Your paper copy is correct."), the spare
  page skipped cleanly, and the installs finished ("All done.").

TASK 2 — Production nft policy for the bridge topology: PASS
(after one real bug was found by the acceptance battery and fixed;
see BRIDGE-NAME BUG below).
- The PoC miniature table is replaced by the production policy in
  golden/nft-golden.nft (table inet onionhost): input drop (lo +
  established + DHCP renewal only — nothing unsolicited, ever);
  output drop with egress by identity (DNS only for root/_apt/
  _chrony; TCP 80/443 only for root/_apt; NTP/NTS only for
  root/_chrony: UDP 123 + TCP 4460); forward drop with container
  egress = TCP from 10.89.77.0/24 to non-private destinations only
  (all container UDP dropped), established/related back.
- Two design-versus-reality corrections, both measured on the
  installed system and documented in the file header:
  (a) There is NO stub resolver: systemd-resolved is inactive and
      NetworkManager writes /etc/resolv.conf directly. DQ9's DNS
      enforcement is therefore the per-user port-53 output rules,
      not a resolver check.
  (b) A separate readiness bug: the 5-minute gate timer pointed at
      the boot gate service, which is oneshot + RemainAfterExit (so
      container A can BindsTo= it) — starting an already-active unit
      is a no-op, so the timer could NEVER re-check. Fixed by
      splitting: new onionhost-nft-gate-check.service + wrapper
      (onionhost-nft-gate-check) that re-runs the comparison; on
      MISMATCH it logs (daemon.err, tag onionhost-nft-gate-check)
      and stops onionhost-a — fail-closed per the design. The timer
      now targets the check service.
- Adjacent gap fixed while here: DQ10 mandates NTS but the stock
  image shipped plain pool NTP. Added etc/chrony/chrony.conf (stock
  file minus the plain pool, minus the DHCP sourcedir, cmdport 0)
  plus sources.d/onionhost-nts.sources (Cloudflare, Netnod,
  PTBTime, all "nts"). Verified in-guest on both installs: chronyc
  authdata shows Mode=NTS for all three; time.cloudflare.com was
  the selected sync source (^*), ptbtime1.ptb.de reachable; Netnod
  (sth1-ts.nts.netnod.se) did not answer from the QEMU NAT on
  either install — NTS itself is proven by the other two; worth a
  re-check on real hardware/ISP in Stage 2.
- Acceptance on installed test systems (install C with the live fix
  applied in-guest, then install D FRESH from the rebuilt ISO):
  (a) Clean boot: "onionhost-nft-gate: OK live table matches
      golden", gate rc=0, on both installs.
  (b) Drift: `nft add rule inet onionhost output accept`, then the
      check ran (timer fired on its own at +5 min AND was started
      manually): journal shows "onionhost-nft-gate-check: MISMATCH -
      stopping onionhost-a"; onionhost-a went inactive (systemd
      marks the check unit failed with status=1 — that IS the
      alert path). Repair (restart nft-load) -> gate OK again ->
      A restarted -> PROBE_OK.
  (c) Functional: onion reachable from an external rig-host Tor
      client (install C: HTTP 200, 2.9 s; install D: HTTP 200,
      7.3 s, placeholder page); U probe PROBE_OK (HTTP/1.1 200,
      Server: nginx, no Date header); desktop user's HTTPS fetch
      fails in name resolution and getent exits 2 (no egress);
      root's HTTPS fetch returns 200 (update path works); B
      NetworkMode=none and its netns contains only a down loopback,
      no routes (nsenter).
- BRIDGE-NAME BUG (the slice's most valuable catch): the Podman
  bridge INTERFACE is named "podman1" by podman — the NETWORK is
  named "onionhost", the interface is not. The policy's first cut
  matched iifname "onionhost" in the forward chain, which silently
  dropped ALL container egress: install C's A sat at "Bootstrapped
  5% (conn)" with connections timing out and the probe timed out,
  while every host-side check passed. Fix: the forward rule now
  matches the dedicated container SUBNET (the design's real
  invariant; host-local traffic never traverses forward). The
  file header records the trap. After the fix: A bootstraps 100%,
  probe OK, external fetch OK. Slice 1's "bridge network" wording
  in earlier logs refers to the network name — Stage 2 should not
  re-derive interface names from it.
- Rig procedure note: under the production table the test
  flavour's live-session sshd is unreachable by design (nothing
  inbound). Driving a live session now needs one console action
  first: `nft add rule inet onionhost input tcp dport 22 accept`
  typed via the monitor keyboard. Installed systems ship no sshd;
  this affects only rig automation.

TASK 3 — PoW calibration: PASS (bounded by the single-host ceiling,
stated plainly below).
- Rig: throwaway service on the rig host (shipped container tor
  0.4.8.16, product torrc settings, host networking — measuring
  tor's queue behaviour, not the firewall) + 12 parallel client tor
  processes, every fetch on a fresh isolated circuit.
- Sustained rate (60 s windows, fresh circuit per fetch):
    1 worker: 16/16 OK, 0.27/s, p50 2.90 s
    4 workers: 43/43 OK, 0.72/s, p50 3.27 s
    8 workers: 58/62 OK, 0.97/s, p50 3.25 s
    12 workers: 96/98 OK, 1.60/s, p50 3.93 s
  Throughput is bounded by public-Tor circuit latency, not the
  service: under a 48-worker flood the service CPU sat at ~2%.
- Floods (120 s windows, 4 legit + 44 flood workers):
    PoW ON 250/500: legit 63/63 OK p50 5.84 s; aggregate ~6.4/s
    PoW OFF:        legit 48/48 OK p50 7.87 s; aggregate ~6.0/s
    (identical within public-Tor noise — at ~6.4 attempts/s nothing
    needs defending yet, and 250 never engages: the maximum
    attempt rate this host can generate is ~2.5% of that rate.)
- Mechanism validation at the candidate calibrated rate (5/10):
    Moderate (90 s, 4+12): legit 66/66 OK p50 4.68 s; aggregate
      3.17/s stays under the rate — defense invisible, as designed.
    Saturating (120 s, 4+44): aggregate completions collapse
      6.4/s -> 0.45/s; flood completion 52%, legit 8/12 at p50
      9.21 s. The queue engages and converts the flood into
      client-side PoW cost. Caveat: legit and flood clients shared
      one host CPU here; real visitors solve on their own machines,
      so the legit figure overstates harm to distributed clients.
- GOLDEN VALUES (now in golden/torrc.tmpl, rendered on install D
  and verified): HiddenServicePoWDefensesEnabled 1,
  HiddenServicePoWQueueRate 5, HiddenServicePoWQueueBurst 10 —
  DQ3's rule (~2x the sustained rendezvous rate: Gate 5's rig
  baseline 2.23/s, corroborated by 1.6-6.4/s here). Unchanged from
  the template: IntroDoS 25/s burst 200, NumIntroductionPoints 3,
  MaxStreams 50 + CloseCircuit.
- Honest limits: a genuine introduction flood (hundreds/s, the
  regime the intro-DoS 25/s/point defense exists for) CANNOT be
  generated from one host with stock Tor clients — every attacker
  circuit costs full network latency (~6.4 attempts/s ceiling,
  measured). The intro-DoS settings are therefore carried from
  the design UNMEASURED; the PoW queue settings are measured.
  Attacker tooling that does not solve PoW was not built; the
  flood clients were stock tor and did solve when asked (that is
  what tor clients under a real flood would do too). Raw CSVs:
  rig ~/slice3/pow/results-*.csv (copied to slice3-evidence/).

TASK 4 — ISO slimming: PASS.
- Container rootfs builds (build_image_tar) moved from
  `important` to minbase, dropped --skip=cleanup/apt, and gained a
  strip hook (docs except copyright, man/info/lintian/i18n,
  zoneinfo, locale files, apt cache/lists removed).
    tor tar: 381,079,040 -> 87,549,440 bytes
    web tar: 375,365,120 -> 90,549,760 bytes
- xz test: podman import ACCEPTS .tar.xz (87.5 MB -> 23.1 MB) —
  verified by importing. Decision: ship plain tars anyway; they
  live inside the xz-compressed squashfs, so pre-compression buys
  ~nothing on the ISO (measured in the before/after below).
- ISO (test): 1,346,957,312 (slice 2) -> 1,145,683,968 bytes
  (-201,273,344, -14.9%). The tar-level saving (~578 MB) mostly
  evaporates in squashfs because the removed payload was highly
  compressible text/lists — recorded so nobody re-chases it.
- Hard floor re-proven: full install + wizard + stack up + probe
  passed on the slimmed ISO twice (installs C and D), and B's
  nginx from the minbase+strip web image served the placeholder
  through the real onion path.

TASK 5 — BIOS/legacy boot: PASS.
- The slice-2 ISO and then the FINAL slice-3 ISO were booted under
  pure SeaBIOS (q35, IDE CD-ROM, -boot order=d, no OVMF): both
  reached the XFCE live desktop ("OnionHost Live" session). The
  hybrid ISO's BIOS path (El Torito + i386-pc GRUB from
  grub-mkrescue) works; an early black frame at ~12 s is just
  SeaBIOS/GRUB text mode, the desktop follows by ~2 min.
  Screenshots: rig ~/slice3/bios-slice2iso/shot-final.png and
  ~/slice3/bios-slice3/shot-final.png.

INSTALL RECORDS (throwaway rig installs; disks on the rig):
- Install C (ISO build B): disk [phrase removed 2026-10-20 — Repo Review 3]; login [phrase removed 2026-10-20 — Repo Review 3];
  onion twxpozl3fcjgtsezn5buoywndzzaw6v6p4dvdbjxfxaz3eer6arhkuqd
  .onion; LUKS roles MAIN=2 (pbkdf2/sha256/2000 ms), KEYFILE=1,
  SPARE=null; keyfile /etc/cryptsetup-keys.d/root.key 0400 in a
  0700 dir; phrase grep over the TARGET's /var/log: zero hits (the
  only live-session journal occurrences were this session's own
  sudo command lines — test-driver artifact, live session only).
- Install D (ISO build C, the shipped artifact): disk [phrase removed 2026-10-20 — Repo Review 3]; login [phrase removed 2026-10-20 — Repo Review 3]; onion
  ypv547ps6eb2yy5iykwrm3qtcm4fwvs5wofsqyfu6cii3n4a7yhzsrad.onion;
  full smoke battery green (slice3-evidence/verify-smoke.txt).

CLEANUP / STATE LEFT: guests stopped; PoW clients + pow-svc
stopped and removed; the rig VM is left RUNNING per instructions.
The rig-host drill images localhost/test-tor:* / test-web:minbase
remain (harmless). Prod ISO rebuild (with the fixed nft policy and
calibrated torrc) is owed at the next prod build — nothing in this
slice touched prod.

=====================================================================
PROD REBUILD — slice-3 fixes land in the production ISO (2026-10-12)
=====================================================================

Full FLAVOUR=prod build with the current build-iso.sh (rig copy
~/slice3/build-iso.sh, sha256-identical to the workspace canonical
script). The rig's ~/onionhost-src was first verified byte-identical
to the workspace onionhost/ tree (rsync checksum dry-run: zero
diffs). Two stale items from the slice-2 prod build were cleared
first: the pre-slimming container tars in iso-build-prod/cache
(381,079,040 / 375,365,120 bytes) were deleted so the slimming
pipeline rebuilt them, and the slice-2 prod ISO was preserved as
onionhost-amd64-slice2.iso.bak (sha256 ba6baf29..., matches the
slice-2 record).

FINAL ARTIFACT (prod): onionhost-amd64.iso
  1,139,898,368 bytes, sha256
  35f3f34f3c64b6b45bbfdf8ef726cd72def8be42b8bdd582cd4d56fb91900a07
  (BUILD-INFO: flavour=prod, oh_probe=0, snapshot 20251011T143150Z;
  build log rig ~/prod-rebuild.log. Transferred to this workspace:
  releases/onionhost-prod-amd64.iso, sha256 re-verified after
  transfer — see below.)

VERIFICATIONS (against the built prod rootfs / rendered configs):
1. nft golden policy: PASS. The forward chain's only container
   egress rule is the subnet rule — `ip saddr 10.89.77.0/24
   ip daddr != @private_dst meta l4proto tcp accept` — and there
   are ZERO active (non-comment) rules matching iifname
   "onionhost" (the string survives only in the header comment
   documenting the slice-3 bridge-name trap).
2. Gate check: PASS. onionhost-nft-gate-check.service present
   (ExecStart=/usr/local/bin/onionhost-nft-gate-check, wrapper and
   gate scripts present + executable); onionhost-nft-gate.timer
   points Unit=onionhost-nft-gate-check.service and is enabled
   (timers.target.wants symlink present).
3. Chrony NTS: PASS. etc/chrony/sources.d/onionhost-nts.sources
   ships all three NTS sources (time.cloudflare.com, nts.netnod.se,
   ptbtime1.ptb.de, all `nts`).
4. torrc PoW: PASS. golden/torrc.tmpl in the rootfs carries
   HiddenServicePoWDefensesEnabled 1, HiddenServicePoWQueueRate 5,
   HiddenServicePoWQueueBurst 10; onionhost-generate-configs renders
   torrc by verbatim copy, and a simulated render (cp + chmod + mv,
   exactly as the script does) reproduces those values in the
   rendered torrc.
Build-side evidence also landed as designed: the automated plugin
phase compiled both Calamares plugins in the pinned chroot and
BUILD-INFO records plugin hashes byte-identical to the slice-2
hand-built / slice-3 automated values (phrase f8d85577..., spare
d891de38...), and the rebuilt container tars came out at the slim
slice-3 sizes (tor 87,549,440; web 90,549,760 bytes). A19.1 gates
in the build log: wordlist 7776 unique OK; no keyfile in ISO
rootfs OK.

LIVE-BOOT SMOKE (SeaBIOS, q35, IDE CD-ROM, no OVMF; screenshots in
build/shots/prod-smoke-*.png): the ISO booted to the "OnionHost
Live" XFCE desktop (autologin live user), Calamares launched from
the live session and walked Welcome -> Location -> Keyboard ->
Disk passphrase. The generated-phrase page RENDERS on the prod
ISO: 7 words displayed in order with the hand-copy instructions
and the "I have written them down" gate (throwaway smoke phrase,
rig VM only). First boot attempt had no disk attached and the
Welcome page correctly refused to proceed (no partitions / <15 GiB)
— re-run with a blank 24G virtio disk, Welcome clean, Next enabled.
A full unattended prod install remains blocked by the known QEMU
mouse limitation, as expected; the encrypted install flow is
flavour-independent and proven on test installs (slices 1-3).

STATE LEFT: smoke guest stopped; rig VM left RUNNING.

# FIELD REPORT — Cameron's phone-driven install, 2026-10-12
First non-automated human install (Cameron driving via noVNC on his
phone, slice-3 test ISO). The install FAILED LOUDLY at onionhostbootkey:
"Install passphrase not available in GlobalStorage (luksPassphrase)".
Root cause established from the live session: lsblk on the target shows
vda2 as PLAIN ext4 - encryption was never enabled on the stock
Partitions page, so no LUKS volume existed and the passphrase handoff
never engaged. The fail-closed design worked (no unencrypted system
shipped), but the flow has a real UX defect: whether the whole product
promise engages depends on the user finding and ticking a stock
Calamares "Encrypt system" checkbox, on whatever screen they have.
Automated installs never exposed this (drivers ticked it explicitly).
FIX REQUIRED (wizard/polish tranche): force encryption on in the
partition flow (pre-seed from the phrase step) AND/OR add an early
exec/show guard right after Partitions with plain-language recovery
instructions, instead of failing ten minutes later at bootkey.

---

## STEP 3, SLICE 4 — content tiers (Simple Pages + Journal) (2026-10-12)

Scope: replace the wizard's stub site pages with the real v1 tiers.
Publisher + content store, Simple Pages, Journal (+ Atom feed),
EXIF-scrubbing media ingest, wizard/Dashboard integration.
Evidence: `slice4-evidence/` (collect-*.txt from the two battery
installs, external fetches incl. headers, the crafted EXIF photo).
Test flavour throughout; prod inherits via the overlay.

### Task 1 — Publisher + content store: PASS (mechanism: SYMLINK SWAP, no B rotation)

New code: `usr/lib/onionhost/sitegen.py` (model, validation,
rendering, media scrub), templates in `usr/lib/onionhost/templates/`
(7 fixed templates, no JavaScript, everything escaped, no .onion
address anywhere in the output), `usr/local/bin/onionhost-publish`
(root CLI), wizard-helper gained `publish` + `probe-status`
subcommands (no new sudoers entries).

**Gate H correction (important):** the PoC finding "a running B
does not see host file edits until restarted" does NOT reproduce
on the shipped stack. On a copy of install D (podman 5 + runsc
release-20251006 + the production Quadlet mount) a scripted
experiment fetched only through the real probe path (U SOCKS →
Tor → A → http.sock → B): in-place edits of the served file
(EXP1), new files in the live tree (EXP5/EXP6), and a `current`
symlink swap under the RUNNING B (EXP2/EXP4) were ALL visible
immediately. The PoC invisibility was an artefact of the
standalone-OCI-bundle environment used in Stage 0. **Publish is
therefore: render a complete release tree → stamp → fsync →
rename to `releases/<seq>` → atomically swap the `current`
symlink (tmp link + os.replace + dir fsync) → prune to current +
previous.** B's nginx root is `/srv/site/current` (golden
template). No restart, no rotation, no half-written window: the
old release serves until the swap instant. Timings: a B restart
(the unneeded fallback) measured 0.8 s in EXP3; the publish
itself (render 6 files + re-scrub + stamp + swap) completes in
well under a second in-guest; an external fetch 31 s after the
Dashboard Publish press already served the new release (bound is
Tor latency, not the swap). `onionhost-generate-configs` also
repairs a missing `current` symlink at boot (points it at the
newest release).

Publisher defences: the user-space model/media store is treated
as untrusted — every rendered image is re-scrubbed (full PIL
re-encode) at publish time and the publish ABORTS if a re-encode
would change the format (polyglot/planted-file guard); any
failure leaves the previous release serving.

**403 incident + mode hardening (found by the battery):** the
first slice-4 build served 403 for the whole site — the overlay
shipped `site/releases/` and `releases/0/` as 0770 and the seed
page as 0640, and nginx's worker could not traverse/read them.
(The slice 1–3 placeholder sat directly in `site/`, which
generate-configs chowns; the new `releases/` layer was mine.)
Fixes, all shipped: overlay modes corrected (755/755/644); the
publisher now chmods every file 0644 and directory 0755
EXPLICITLY (the process umask is not a contract); and
generate-configs normalizes the whole site tree's modes at boot
as a safety net. Also recorded: `onionhost-probe` prints PROBE_OK
for ANY HTTP response through the path (a 403 read as "up") —
pre-existing slice-1 semantics; the new Dashboard status card
additionally requires a 200 status line before it says "Your
site is up and reachable."

### Task 2 — Simple Pages tier: PASS

Model: site title + up to 8 pages (heading + plain-text
paragraphs + optional photo). Fixed templates render an index +
one file per page + one shared stylesheet; no user HTML (all
output escaped); no JavaScript. Editor in the wizard (S1) and in
the Dashboard (S2, "Edit site"): big fields, Add page / Edit /
Delete, Choose photo (file picker), Save, Publish.

### Task 3 — Journal tier: PASS

Model: title + dated entries (YYYY-MM-DD + heading + text +
optional photo). Index is newest-first (date, then insertion
order); one page per entry; Atom feed whose per-entry
`<updated>` is the entry page's content-derived time and whose
ids are `urn:onionhost:entry:<id>` (no .onion, no wall clock).

### Task 4 — Media ingest scrub: PASS

Editor-path ingest copies the chosen photo into
`~/.config/onionhost/media/<sha256>.<ext>`, re-encoded via PIL:
EXIF orientation baked in BEFORE metadata drop, all metadata
stripped, max dimension 1600, JPEG q88 (PNG kept for PNG/alpha).
Bug found by local test before the battery: PIL's encoders write
`img.info` back out — a JPEG COM segment carrying the test
serial SURVIVED the first scrub implementation; fixed by
clearing `img.info` after transpose. Acceptance (through the
real editor UI): crafted 2400x1200 JPEG with GPS EXIF + unique
serial `SLICE4-SERIAL-7f3a9c51-UNIQUE` in ImageDescription AND a
COM segment → published → fetched over Tor from the rig host:
EXIF absent (PIL getexif() empty), serial absent (0 grep hits),
valid JPEG 1600x800, and the fetched bytes' sha256 EQUALS the
content-hash filename (dfbed1cef57e…) — byte-identical proof
the served file is the scrubbed encode. A PNG/tEXt case was
verified locally the same way.

### Task 5 — Wizard/Dashboard integration: PASS

The S1 site-type stub is now the real choice (Simple Pages /
Journal radio); choosing a tier seeds a starter site (one
"Welcome" page / one "First entry" dated today). Go Live
publishes the (edited) starter site and sets state S2 — a fresh
install serves real content, not the placeholder. Dashboard
(S2) shows site title + tier, the probe status card (now
200-checked), "Edit site" reopening the editor, Publish, and
"Check again". Vocabulary stayed inside the budget: Pages /
Journal / Edit / Publish; no new secrets or concepts.

### Acceptance battery — Install 1 (Simple Pages), ISO sha256 4945eba7…
Disk phrase [phrase removed 2026-10-20 — Repo Review 3]; login [phrase removed 2026-10-20 — Repo Review 3]; onion
bi27iei5cbpjhvtk2d4mgm2yl6u2x3qx74hnmmmbac34ove6zsfzgzyd.onion.
Wizard → Pages → title "Slice Four Test Site" → Welcome edited
(text + the EXIF photo through the picker) → second page added
→ Go Live. External fetches from the rig host over Tor:
BEFORE publish the placeholder served 200 (after the mode fix);
AFTER: / 200 (title present), page-p1 200 (edited text),
page-p2 200, media photo 200 + scrub evidence above, NO Date
header. Guest collect: state S2, current → releases/1, probe
PROBE_OK HTTP 200. Dashboard cycle: status card "Your site is
up and reachable." → Edit site → text appended → Publish
(editor: "Published. Your site shows the new version now.") →
external fetch shows the new text; current → releases/2, prune
kept 1+2. **Mtime rule verified numerically** (stat vs
1577836800 + sha256 mod 10^8) on index.html (1656407365),
page-p1.html, and the photo — all MATCH.

### Acceptance battery — Install 2 (Journal), ISO sha256 37213829b40e…
Disk phrase [phrase removed 2026-10-20 — Repo Review 3] (a repeated word — sampling is with
replacement, legitimate); login [phrase removed 2026-10-20 — Repo Review 3]; onion
xenjgzm7d5zkdo7ft7fcptuki7up4cndg5t6nwcs6b6gn2g2rufdhqid.onion.
Wizard → Journal → title "Slice Four Journal" → starter entry
(2026-10-12) + "Trip Notes" (2026-10-08) + "First Week"
(2026-10-01) → Go Live. External: index order First entry →
Trip Notes → First Week (newest-first ✓); feed.xml 200 with
all timestamps content-derived (e.g. e1 <updated>
2022-12-15T04:23:05Z == entry-e1.html's rule time; nothing
near the wall clock or the owner's timezone); mtime rule MATCH
on entry-e1/e2, feed.xml, index.html; probe PROBE_OK 200.

### Bugs found by driving the real UI (all fixed in the shipped tree)
1. **Editor layout overflow (Pages main page)** — stacked
   buttons pushed Publish/Continue off the 900x640 window.
   Fixed: one Save/Publish/Continue row, shorter list.
2. **Journal edit form overflow** — the extra Date row pushed
   "Save this"/"Cancel" off-screen in a normal window (mouse
   users could not save an entry at all). Fixed: text box
   height 8→5, format hint folded into the Date label, wizard
   + dashboard windows now size to min(760, screen-30). FIX
   VERIFIED by hot-copying the patched wizard.py into install
   2 and re-opening an entry: Save/Cancel visible.
3. **Title silently lost** — typing a site title then opening
   a page/entry editor (without pressing Save first) discarded
   the title when the frame rebuilt; the battery's exact
   sequence hits this. Fixed: the title is captured into the
   model on EVERY transition away from the editor's main page.
   Verified live on install 2 ("Slice Four Journal" survived
   Add entry with no Save).
4. **Release-tree modes → site-wide 403** — see Task 1.
Also cosmetic: stray Tab/space characters can land in entry
text from keyboard-driven editing (Tk Text widgets consume Tab
as input); HTML rendering collapses them; real mouse users are
unaffected.

### Process notes (rig driving, for the next slice)
- A failed install attempt (empty LUKS passphrase fields due to
  a click offset) was REFUSED loudly by onionhostbootkey
  ("Install passphrase not available in GlobalStorage") and
  aborted with 0 LUKS partitions — the slice-1 fail-closed
  design working as intended; no silent unencrypted install.
- xdotool `--window` coordinates are offset by the window frame
  (-5,-29): clicks computed from raw screenshot geometry land
  ~29px high. QEMU monitor synthetic mouse (usb-tablet) did not
  move the guest pointer; keyboard + per-step focus screenshots
  are the reliable path, and occasional sendkey drops mean
  focus must be VERIFIED, not counted.
- Build wart (pre-existing): test builds must use OH_PROBE=1 —
  a cached rootfs whose settings.conf references onionhostprobe
  breaks Calamares when a later build strips the module.
- Test ISOs are back to ~1.35 GB because iso-build-test reuses
  the pre-slimming cache; size is a prod-build property, not
  chased here.

### Remaining content-tier gaps
- Editor is keyboard-hostile in places (Tk Text traps Tab;
  Ctrl+Tab is the traversal key) — fine for the mouse-first
  novice target, but a11y polish is owed before Stage 3.
- Journal index order for SAME-date entries is insertion order
  reversed; no per-entry time exists by design (A17.1).
- No draft/unpublish state: Publish is all-or-nothing per site
  (by design for v1).
- The probe's any-response PROBE_OK semantics remain for other
  consumers; only the Dashboard card was hardened to need 200.
- The final tree carries the post-battery wizard fixes (form
  fit, title capture, date-label width) that postdate ISO
  37213829…; a final test build was made after the battery so
  the shipped artifact matches the tree: 1,349,410,816 bytes,
  sha256 cf1a9b09b0e41cf73f6a99b955a08cf63d6208bcb212f39ed
  28945b84b1af904 (rootfs inspected: patched wizard + 755/644
  release seed present). Not re-installed end-to-end — the fit
  fix itself was verified hot-loaded on install 2 as recorded
  above, and the battery ISOs differ from it only in those
  wizard/layout files.

Rig state at end of slice: GCP VM LEFT RUNNING per instructions.
Install 2 guest left running at S2 (Journal live); install 1
guest stopped, its qcow2 kept on the rig.

## STEP 3, SLICE 5A — installer + editor fixes from Cameron's hands-on session (2026-10-12)

Fixes for the five defects from Cameron's phone-driven install (see
the FIELD REPORT above) and the slice-4 gap list. Battery ISO:
1,349,492,736 bytes, sha256 4115cf90a4b7d8237c2075745ffc3addeae4
ce158aacf6425956e69743382b57, snapshot 20251011T143150Z,
FLAVOUR=test, OH_PROBE=1. Evidence: slice5a-evidence/ (138
screenshots). Two battery guests (Simple Pages, Journal) plus a
live-only guest for the guard branches. cameron-test and the
slice-4 install-2 demo guest were not touched.

### Task 1 — encryption is FORCED, not checkbox-dependent: PASS

Mechanism shipped (strongest of the brief's options): a pinned
source patch to the Calamares 3.3.14 partition viewmodule, plus
preCheckEncryption, plus a guard viewstep as backstop. Why config
alone cannot force it (from the pinned 3.3.14 source, Debian
ships it unpatched): ChoicePage::onLeave() ALWAYS overwrites
GlobalStorage luksPassphrase with the widget state (empty when
not Confirmed), clobbering any pre-seed; the automated layouts
take the passphrase only from the on-screen widget; and the only
supported config key, preCheckEncryption, pre-ticks a box whose
empty fields still block Next. So the patch (0001-onionhost-
force-encryption.patch, sha256 c6b211c2a66c808034b132d8b160776
b148d2649e9e8bddf37fa7e6baba523b7) makes the flow phrase-driven
whenever GlobalStorage carries the generated-phrase marker:
Erase/Replace layouts are queued with the generated phrase,
the ChoicePage widget's passphrase fields are suppressed, its
checkbox state can neither block Next nor clobber the stored
phrase, and onLeave preserves the generated value. The manual
partition dialogs keep their own unsuppressed widget. With the
marker absent the module behaves exactly like stock 3.3.14
(proven live, below). partition.conf gains preCheckEncryption:
true so the box truthfully shows ON. New viewstep
onionhostguard sits immediately after partition in the show
sequence: Pass page when the stored passphrase equals the
generated one, Block page with plain-language recovery when it
does not, a Manual page for manual partitioning (Next disabled
until the user acknowledges the layout must be LUKS with the
7 words), and a no-phrase page when the phrase step never ran.
onionhostbootkey is unchanged and remains the last line of
defence. The patched module is compiled in the pinned-snapshot
chroot alongside the plugins; its NEEDED soname set is
hard-checked identical to stock; rebuilds are byte-identical
(partition module sha256 57386f1ead82ff0db09ed1d21f6562
b86a3a3c697303c49cf02c0184f0ecf062 in BOTH the battery and
final builds). Guard decision logic unit-tested in the chroot:
12/12 cases.

Acceptance, in real installs:
- (i) Cameron's path (guest 1, never touched the checkbox):
  box ticked by config, NO passphrase fields anywhere, "After:"
  preview "Debian 23.71 GiB LUKS2", guard Pass page, install
  completed, vda2 crypto_LUKS during exec, and the installed
  system booted to the S0 wizard after typing the generated
  phrase [phrase removed 2026-10-20 — Repo Review 3] at the GRUB prompt. (Round 1 of this guest failed
  late at the users job — useradd 'user' already exists: the
  drivers had picked login "user", which the TEST flavour
  pre-creates. A test-harness artefact; prod targets carry no
  such account. Rerun with login "owner" was clean.)
- (ii)+(iii) Sabotage (guest 2): the pre-ticked "Encrypt
  system" box was deliberately UNTICKED. The preview stayed
  "LUKS2", no passphrase fields exist to type into, the guard
  passed, the install completed ("All done."), and the system
  boots with the generated phrase [phrase removed 2026-10-20 — Repo Review 3].
- (iii) from the other direction (guest 3, live, phrase steps
  removed from settings.conf): the module falls back to stock —
  fields reappear, preview is plain ext4, Next blocks on the
  empty fields; after typing a passphrase the guard shows its
  "Something went wrong" page with Next disabled: a typed
  passphrase cannot substitute for the generated one.
- Manual branch (guest 3, live): guard shows "Check your
  partitions", Next disabled until the "Yes - encrypted
  (LUKS), with the 7-word passphrase." acknowledgement is
  ticked (session log: choice "manual" decision 2).

### Task 2 — Dashboard status card re-probes after Edit/Publish: PASS

Root cause: Dashboard.build_main rebuilt the card at "Checking
your site..." but only __init__ and the Check-again button ever
called check_status(), so a return from the editor never started
a probe. Fix: build_main ends with check_status(); a probe
generation counter keeps a stale probe thread from overwriting
a newer result; 200-required semantics kept (PROBE_OK and
HTTP 200). Evidence (guest 1): three Edit -> Back cycles; the
card was caught mid-cycle on "Checking your site..." and
resolved unaided each time — cycles 1-2 to "Your site is up
and reachable." within seconds on a warm Tor path; cycle 3,
run during the Tor-weather window below, resolved on its own
to the failure text "Your site is not reachable yet..." (a real
negative result at that moment; no probe process remained).
Guest 2's Dashboard likewise resolved to "up and reachable"
and started a fresh cycle on Edit -> Back.

### Task 3 — Editor keyboard sanity: PASS

Ctrl+A/C/X/V now bound conventionally on the editor's Entry
fields, its Text box, and the wizard's verify entries (Tk's
emacs bindings previously hijacked Ctrl+A). Tab and Shift-Tab
move focus out of the multi-line Text box without inserting a
tab. Backstop: sitegen.sanitize_model() runs at the top of
save_model (tabs -> space, CR/LF normalised, other C0 controls
and DEL dropped). Driven in the real UI (guest 1): Ctrl+A
selected the title, typing replaced it, Ctrl+X emptied the
field, Ctrl+V restored "Slice Five Pages"; Tab in the page
text left exactly "Alpha line" with focus moved to the
"Choose photo..." button; saved model read "Alpha line beta",
tab-free. Backstop driven in guest 2: a tab injected into
site.json was gone from the parsed model after a Dashboard
editor Save ("Written first, dated in the middle.").

### Task 4 — Journal editor lists entries newest-first: PASS

SiteEditor now displays Journal entries sorted exactly as
sitegen renders them (date, then reverse insertion order);
the on-disk model keeps insertion order. Guest 2 added entries
dated 2026-10-08, then 2026-10-12, then 2026-10-01; the editor
listed 10-12 / 10-08 / 10-01 in both the wizard and the
Dashboard editor, and the externally fetched index page listed
them in the same order.

### Task 5 — Date field label: PASS (after an in-slice fix)

First battery build restructured the row to label "Date:" plus
the hint as its own element, but at the app's standard 900 px
window the hint still clipped ("year-month-day, li...") — the
shared field() helper's 44-character entry left too little row.
Fix: field() takes an entry width; the date entry is 14 chars.
Verified in guest 2's real UI with the patched wizard.py
hot-loaded (guest file sha256 matched the source tree,
3bcae641a4bf4c7afd20259f3f73ea439bba427c7da1eb3372d6faa39b
20770b): the row reads "Date: [2026-10-12] year-month-day,
like 2026-10-12", fully in-row. The fix is in the final ISO
(rootfs wizard.py sha256 identical).

### Battery network evidence

- Guest 1 (Simple Pages, "Slice Five Pages"):
  ry3i7envfpewfps4whscj4zkqhgcu7ze4evq5es6hjushu3ofrmri6ad
  .onion — guest helper probe-status: PROBE_OK, HTTP 200;
  external fetch from the rig: 200, correct title and edited
  page text, NO Date header, content-derived ETag /
  Last-Modified. Login phrase [phrase removed 2026-10-20 — Repo Review 3].
- Guest 2 (Journal, "Slice Five Journal"):
  hdzkdp37kuq32ecr3exejzj36hpinfu2a2xcs3htoeo4jfmj7clhoryd
  .onion — probe-status PROBE_OK, HTTP 200; external fetch
  200, index order Newest/Middle/Oldest, no Date header.
  Login phrase [phrase removed 2026-10-20 — Repo Review 3].
- Tor weather: from ~18:37 guest time the onion paths
  degraded hard (guest probes and parallel shell probes
  timing out at 120-200 s; rig-client fetches failing), then
  recovered later in the evening; the same binaries fetched
  cleanly before and after. In that window guest 2's gateway
  container, whose first bootstrap had run on a partial
  consensus, never published; one restart (the designed
  A-rebuild path) bootstrapped in 45 s and the service then
  fetched fine. Recorded as environment behaviour.
- Operator note: to get an SSH channel into the battery
  guests the live nft ruleset was flushed from a desktop
  terminal; on guest 1 the slice-3 gate caught the drift on
  its 5-minute cycle and stopped container A — the gate
  working as designed (A was restarted once the gate timer
  was stopped for the battery). Installed targets ship no
  sshd (and mask ssh.service) and no xdotool; both were
  apt-installed into the throwaway guests only.

### Stale copy found + final test ISO

The phrase plugin's verified page still told users to tick
"Encrypt system" and type the passphrase — now wrong. Fixed:
"Encryption is switched on for you automatically, using these
same 7 words - there is nothing to tick and no passphrase to
type." Final test ISO rebuilt after the battery with that fix
and the Task 5 fix: 1,349,451,776 bytes, sha256
38d042802075b1b128623a5dec9d8bc2bc8def00de40bbb2e3adf01a6
fd0f272, snapshot 20251011T143150Z. BUILD-INFO: plugin_phrase
55d211623a192fa2b1fcf6a318ff43d821584ad312e21be7ea3f456f
39994f35 (changed — the copy fix), plugin_spare d891de38...
(unchanged), plugin_guard d4fb8e3ff1b8c4f58246e6f8ed591e
400310518d6af09c28c7161c5bd8218c46, partition module
57386f1e... (byte-identical to the battery build). Rootfs
inspection: show sequence includes onionhostguard after
partition; preCheckEncryption present; wizard.py matches the
fixed tree file; the phrase plugin contains the new copy and
none of the old. Live-boot smoke of the final ISO: boots,
installer sequence shows "Encryption check", phrase page
renders. The battery ISO differs from the final ISO only in
wizard.py (date entry width) and the phrase plugin (page
copy) — both fixes verified in the real UI above — so the
final ISO was not re-installed end-to-end, the same standard
as slice 4's final build.

Rig state at end of slice: GCP VM LEFT RUNNING. Battery
guests stopped, their qcow2s deleted (rig disk pressure);
slice-4 install-2 demo guest untouched and still running.

## STEP 3, SLICE 5B — backup / restore (2026-10-12/13)

Implements the design contract (BACKUP-RESTORE-ACCEPTANCE-2026-10-12,
13 items): backups need NO phrase to create — an age X25519 identity
is derived at install from the disk phrase via argon2id (backupkeys
v1: canonicalize phrase, argon2id t=3 m=65536 KiB p=1, 32-byte seed =
X25519 scalar); only the public recipient(s) are stored
(/etc/onionhost/backup.json, written by Calamares jobmodule
onionhostbackupkeys after onionhostfirstrun, with an in-transaction
age smoke test). MAIN and SPARE phrases derive SEPARATE recipients;
every backup is encrypted to both. The private identity exists only
while the owner types the phrase at restore. Restore is
Maintenance-only; the new install's own login words stand (account
decision: restore returns content + onion identity only). A19/A19.1
forbidden set kept out: LUKS keyfile, initramfs, /etc/cryptsetup-
keys.d, /etc/shadow, Tor guard state, luks-roles.json.

Pieces: usr/lib/onionhost/backupkeys.py (self-test ALL PASS incl.
RFC 7748 + age interop both directions), onionhost-backup,
onionhost-restore, onionhost-maintenance (menu: 1 Restore ·
2 Rekey · 3 Restart), Dashboard "Back up" button via
onionhost-wizard-helper `backup DEST`, restore marker +
"Your website is back" S1 wizard page, rekey refreshes the MAIN
backup recipient after a MAIN rotation.

### Battery (a) — guest A: PASS

Fresh install (fixed-encryption ISO lineage), Journal site "Slice
Five B Journal", entry "First Entry From A" (body marker ALPHA-5B),
EXIF-bearing photo ingested + scrubbed (served bytes
dfbed1cef57e53c34a…), releases 1+2, state S2. Onion:
yzckmqndkl65psrsjt6bp5e742vo5ubxumwca3mebr6u57ctuuj2qcad.onion —
external Tor fetch 200 (title, entry body, photo sha256 identical),
probe PROBE_OK. Backup made via the real Dashboard "Back up"
button: my-website-backup.onionhost-backup, 10,240 bytes.
Offline analysis (slice5b-evidence/A-backup-analysis.txt): wrapper
= exactly meta.json + payload.age; BOTH recipients + BOTH salts in
meta; payload decrypts with MAIN identity AND with SPARE identity;
wrong phrase refused; forbidden-name sweep clean on wrapper AND
payload; all 18 manifest entries sha256/size verify; onion address
recomputes from the stored public key; secret key is the 96-byte
Tor format. A phrases — [phrase removed 2026-10-20 — Repo Review 2].
backup.json recipients re-derived independently from phrase+salt:
BOTH MATCH.

### DEFECT FOUND + FIXED — Maintenance boots self-terminated

First B install's Maintenance entry appeared to "reset the
machine": the journal (extracted offline) showed the maintenance
service starting, the menu logging "session opened", and a reboot
~2 s later on all five attempts. Cause:
onionhost-maintenance.service used ExecStartPost for the
"press Enter to restart" prompt. ExecStartPost is a post-START
hook — it runs CONCURRENTLY with ExecStart — so its `read` raced
the menu for tty1 and any buffered input/EOF fired
`systemctl reboot` seconds into the session. Pre-5B the same line
sat under the rekey program and the race simply never bit in the
small drill samples. Fix (structural, in-tree): ExecStartPost
removed; ExecStart is now one shell chain —
menu; printf prompt; read; exec systemctl reboot — so the prompt
can only appear after the menu exits. Verified: menu stable,
full restore driven through it (B′ and C below). NOTE: this bug
also means slice 2/3/5A maintenance boots were one stray Enter
away from the same failure; the fix ships in the slice-5B ISO.

Side incident: during diagnosis the rig root filesystem hit 100%
(slice 3/4/prod build trees); the wedged guest-B symptoms that
followed were host-ENOSPC artifacts, not product defects. Freed
~13 GB of regenerable build trees; rig hygiene noted below.

### Two restore defects found by the battery + fixed

1. Superfloppy sticks missed: the restore stick-scan globbed only
   partitions (/dev/sd*[0-9] …); a partitionless FAT stick (the
   battery's own usb.img) presents as /dev/sda and was never
   mounted — "No backup file was found" with the stick plugged
   in. Fix: whole-device candidates added (mount failures skip
   cleanly); root-disk exclusion unchanged.
2. Fresh-install restore crashed mid-install:
   _swap_dir assumed the target exists; on an install that has
   never booted its services there is no tor/hs dir yet
   (FileNotFoundError after content+releases had swapped).
   Fix: missing target = plain rename; stale staging dirs swept
   at install start (retry converges — B′'s retry completed);
   unexpected exceptions now exit 1 with plain copy +
   traceback in the maintenance log instead of a raw traceback.
3. (Same window) Restore created ~/.config root-owned on a
   never-logged-in install, breaking the owner's first XFCE
   session (xfconfd failsafe dialog). Fix: the restore chowns
   the ~/.config chain to the owner (uid/gid from getpwnam).

B′ was patched offline (nbd+cryptsetup on the rig) to the fixed
restore build between attempts; the final ISO below carries all
three fixes natively and guest C installed from it.

### Battery (b) — guest B′ restore: PASS

Fresh install from the maintenance-fixed ISO (different disk
phrase: [phrase removed 2026-10-20 — Repo Review 2]; no
spare; login: [phrase removed 2026-10-20 — Repo Review 2]), restored BEFORE first normal
boot (S0 branch): Maintenance → stick found → A's MAIN phrase →
"The backup opened and checks out: "Slice Five B Journal"
(yzckmqnd…qcad.onion)" → "Your website is restored." Restart →
S0 wizard → login phrase → "Your website is back" page → Finish
setup → S2, marker consumed. Verification: state S2; containers
active; in-guest probe PROBE_OK HTTP/1.1 200 OK on A's onion;
EXTERNAL Tor fetch from B′: / 200 "Slice Five B Journal" +
"First Entry From A", entry page 200 with ALPHA-5B body, photo
200 with sha256 dfbed1cef57e53c34a… — byte-identical to A's
served photo. Evidence: slice5b-evidence/B-{index,entry}.html,
B-photo.jpg, B2-maintenance-log.txt, B2-shots/.

### Battery (c) — guest C wrong phrase: PASS

Fresh install from the FINAL ISO (disk: [phrase removed 2026-10-20 — Repo Review 2]; login: [phrase removed 2026-10-20 — Repo Review 2]), own Journal "Guest C Own Journal" live at
xmppyvubfjgwi7gd7kdf2gcdjlmwp44mr3srd77ygrx4uki7xcwzh2id.onion
(external 200). Maintenance → restore A's backup with B′'s phrase
(a valid-but-wrong paper) → exact acceptance copy: "That
passphrase did not open this backup. Nothing was changed. Check
the words on the paper and try again." → back at the menu;
maintenance log records FAILED (3). Restart → C serves its OWN
site: external fetch 200, index sha256 identical before/after
(99ef8ea6bf667dee…), probe PROBE_OK 200 on C's onion.

### Final test ISO + acceptance mapping

Final test ISO (FLAVOUR=test, OH_PROBE=1): 1,353,908,224 bytes,
sha256 cf6a3b516aec5657ca21c8c1764e02fa5634e4b86136ce55f715c0c4825812ec,
snapshot 20251011T143150Z. Rootfs inspection: backupkeys.py,
onionhost-backup/-restore/-maintenance present + correct modes,
jobmodule sequenced after onionhostfirstrun, age + argon2_cffi in
rootfs, maintenance.service = fixed ExecStart chain (no
ExecStartPost directive), restore carries the superfloppy +
swap + config-chain fixes, no crypto keyfile in rootfs.
Intermediate builds: 2dac52f0… (feature-complete, pre-fix),
2f11a405… (maintenance fix), f3ffcb12… (+ scanner fix),
cf6a3b51… (final, + swap/config fixes; C installed from it;
B′ restored on 2f11a405 + offline-patched restore binary — the
same file bytes the final ISO ships).
Acceptance 13 items: 12 PASS, item 11 PARTIAL BY DESIGN —
restores ARE logged (/var/lib/onionhost/maintenance-log.txt +
journal, quoted above for all three guests) but no Dashboard log
UI exists yet. Open decision unchanged (Cameron's call):
backup-destination wizard step vs first-Dashboard prompt.
Rig state at end of slice: VM LEFT RUNNING; battery guests A/B/C
stopped and deleted (21 GB free after their removal); slice-4
install-2 demo guest still running, cameron-test untouched; the
mid-slice 100%-full episode says the build trees want watching
on the next slice.

## PROD REBUILD 2 + DOWNLOAD (2026-10-12)

Cameron's ruling (2026-10-12 18:32 MDT): when an ISO is ready for
testing, upload it to the project page (vespiary.org/onionhost/) for
download. Gates per PROD-DOWNLOAD-GATE-2026-10-12.md: slice 5B
passed; this ISO is a PROD flavour cut AFTER 5B from the current
tree; the published SHA-256 is computed from the final uploaded
file; the footer claim that there is "no public download yet" is
removed in the same edit; no reproducible / independently-verified
claim is made anywhere.

### The build

Full FLAVOUR=prod OH_PROBE=0 build on the rig via build/build-iso.sh
(canonical workspace script, sha256 cd7abcc3...; the rig's older
copies were stale). The rig's ~/onionhost-src was first verified
byte-identical to the workspace onionhost/ tree (rsync -rcn, zero
content diffs). Slice-3 prod ISO preserved on the rig as
iso-build-prod/onionhost-amd64-slice3.iso.bak.

**Prod ISO: 1,146,880,000 bytes,
sha256 080e45ac048e9999d2de57f199d5411c53a442f4a7a7daaa49a92c0e4cb2b1c1**,
snapshot 20251011T143150Z, SOURCE_DATE_EPOCH 1760193110.
BUILD-INFO: plugin_phrase 55d21162... (changed since slice 3 by
the 5A phrase-page copy fix), plugin_spare d891de38...,
plugin_guard d4fb8e3f..., partition_module 57386f1e... (== the 5A
patched module, == the cache build), container images unchanged
(tor de6e04e4..., web 10d8c72e... - content-addressed, expected).

### In-image verifications (prod rootfs on the rig, all PASS)

- nft golden policy: forward accept is the subnet rule
  (ip saddr 10.89.77.0/24 ip daddr != @private_dst); the only
  iifname "onionhost" occurrence is a comment recording the cut
  that was replaced; zero active name-based rules.
- onionhost-nft-gate service + gate-check service/timer present;
  gate.timer enabled (timers.target.wants).
- chrony NTS sources: time.cloudflare.com / nts.netnod.se /
  ptbtime1.ptb.de, all `nts`.
- torrc template: HiddenServicePoWDefensesEnabled 1, QueueRate 5,
  QueueBurst 10.
- Forced encryption: rootfs partition module sha256 == patched
  build (57386f1e...); partition.conf preCheckEncryption: true,
  luksGeneration luks2; settings.conf sequences onionhostguard
  after partition (show) and onionhostbackupkeys after
  onionhostfirstrun (exec).
- Backup/restore: onionhost-backup / -restore / -maintenance
  (0755), /usr/lib/onionhost/backupkeys.py, onionhostbackupkeys
  jobmodule; maintenance.service = fixed ExecStart chain, no
  ExecStartPost directive.
- A19.1 gates in the build log: wordlist 7776 unique words;
  no keyfile material in the ISO rootfs; kdump-tools absent.
- Scaffolding strip: no openssh-server, no xdotool (binaries and
  dpkg status both empty), no authorized_keys anywhere in the
  rootfs, no sshd_config.d drop-ins, onionhostprobe module absent
  and unsequenced (OH_PROBE=0), live account password is a
  per-build random value (crypt-verified: not "onion", not "live").

### Live-boot smoke (SeaBIOS)

Prod ISO under SeaBIOS (q35, IDE CD-ROM): live desktop ("OnionHost
Live") -> Calamares launched -> phrase page renders with a
generated 7-word phrase. PASS (evidence: prod-rebuild2-evidence/
shot-cala-phrase.png). Note: a full install under SeaBIOS/BIOS was
also attempted and fails at onionhostgrubstub ("No GRUB stub found
at /boot/efi/...") - the design's boot chain is UEFI-only (the
grubstub job rewrites the EFI stub); BIOS installs are out of
scope. The install proof below therefore uses the 5A/5B battery
vehicle (OVMF Secure Boot pflash), as every prior slice battery
did.

### Prod install proof (UEFI guest on the rig, prod-verify)

Full install driven from THIS prod ISO by QEMU-monitor keyboard
plus xdotool installed into the live session only (live-overlay
change; cannot enter the installed target, which unpacks the
squashfs - and the rootfs strip checks above stand):

- Phrase page -> verified (words 2/6/7) -> spare skipped via
  "No spare - continue" -> Partitions: "Erase disk" selected,
  "Encrypt system" ticked by default, NO passphrase fields,
  layout = EFI 300 MiB FAT32 + 23.71 GiB LUKS2
  (prod-rebuild2-evidence/shot-u-erase2.png).
- Encryption check guard page: Pass state ("Encryption is on").
- Users (owner / owner-standardpc) -> Install -> "All done."
  (all OnionHost jobs incl. bootkey, grubstub, firstrun,
  backupkeys ran; Calamares surfaces any job failure as an
  install failure, as the BIOS attempt proved).
- Disk phrase (throwaway, rig guest): [phrase removed 2026-10-20 — Repo Review 3]; login phrase [phrase removed 2026-10-20 — Repo Review 3].
- First boot from disk: GRUB stub shows the plain-language
  passphrase prompt; phrase opens hd0,gpt2; S0 wizard generates
  the login phrase -> commit -> LightDM greeter -> owner login
  with the phrase -> S1: Simple Pages, starter site edited and
  Published ("Published. Your site shows the new version now.")
  -> Go Live -> "You are live" (S2).
- Dashboard: "Your website / My Website / Simple Pages / Your
  site is up and reachable." (probe 200 verdict rendered in the
  UI) with the 5B "Back up" button present.
- In-guest probe via the app's own channel (sudo -n
  onionhost-wizard-helper probe-status):
  PROBE_ONION m26lxw5gi6yxaxfugjbae25kof2vhgeqjucj4dmil5xtr7ia5vrb63qd.onion
  PROBE_OK HTTP/1.1 200 OK, followed by the starter page HTML.
- EXTERNAL fetch, independent network (fresh tor client outside
  the rig): HTTP 200, 319 bytes, <title>My Website</title> - the
  published starter site over the public Tor network. PASS.
- Caveat: fetches attempted through the RIG HOST's own tor client
  failed throughout this session for ALL onions tried, including
  two checksum-valid controls (the slice-4 demo site and
  DuckDuckGo's public onion) - the host client bootstraps 100%
  but cannot complete rendezvous right now; an environment fault,
  not a property of this build or guest (5A logged the same class
  of mid-battery Tor degradation). Recorded honestly; the
  independent-network fetch above is the external proof.
- prod-verify guest LEFT RUNNING at S2 (site live at the address
  above); slice-4 install-2 demo guest and cameron-test
  untouched; rig VM left running.

### Download hosting

Headroom checked first (vespoeig host: volume 1.8T free, account
usage 2.4G, no quota visible) -> direct hosting chosen.
ISO at https://vespiary.org/onionhost/onionhost-amd64.iso
(rsync resumable upload, sandbox -> host), chmod 644.
Server-side sha256 of the uploaded file:
080e45ac048e9999d2de57f199d5411c53a442f4a7a7daaa49a92c0e4cb2b1c1
== build hash.
Outside verification: page HTTP 200 with the new Download section
and the full SHA-256; ISO URL HTTP 200, Content-Length exactly
1146880000, Accept-Ranges: bytes; Range request (bytes
1048576-2097151) HTTP 206 and the returned 1 MiB is byte-identical
to the local verified ISO (sha256 30e14955... both sides).
Local copy: ~/workspace/onion-host-os/releases/onionhost-amd64.iso
(hash-verified after transfer; the slice-3 file it replaced is
kept beside it as onionhost-prod-amd64.iso).

### Drive refresh

Same ISO staged to the thevespi host (hash-verified there),
rclone copy to gdrive:OnionHost-Stage2/onionhost-prod-amd64.iso,
replacing the slice-3 prod file. First rclone run stalled at 68%
(this host cuts long transfers); restarted with retries/timeouts,
completed. rclone check: 0 differences found, 1 matching file.

### Site changes (vespiary.org/onionhost/)

- New "Try the alpha test build" Download section: alpha framing
  ("expect rough edges; testers wanted"), filename, size
  (1,146,880,000 bytes), full SHA-256, one-line verify instruction
  (sha256sum / shasum -a 256), requirements (spare 64-bit PC that
  can be erased, UEFI firmware, 8 GB RAM - 4 GB works, wired
  ethernet recommended, USB stick 4 GB+).
- Status section: backup/restore recorded as built and tested;
  now states an alpha test build is available for testers below.
  The pre-release gate list (hardware, novice users, external
  review of the built system, reproducible releases) is unchanged
  - no reproducible/verified claim added.
- Footer: the false "no public download yet" text replaced with
  "This page offers an alpha test build for testers - it is not a
  finished public release."
- One-claim discipline kept; no WorldExpanders reference anywhere
  on the page (verified 0 matches); contact remains Twitter
  @CameronRuggles + the Vespiary forum.

## STEP 3, SLICE 6B — DYNAMIC PLUMBING (implementation; rig battery deferred)

Date: 2026-10-13. Scope: implement the Slice 6 gate round's
adopted shape into the product tree — ONE combined app container
(nginx + PHP-FPM or a native process + MariaDB in a single
gVisor sandbox; service sockets sandbox-internal; only the edge
socket shared with gateway A) — plus site-type plumbing, the
format-2 backup extension, and VM-LOCAL acceptance. The rig was
unreachable from the build sandbox all session (egress proxy
resetting SSH), so: NO ISO was built and NO rig battery ran.
Venue-dependent verdicts are deferred below, not faked.

### Product tree (onionhost/)

- New Quadlet unit `onionhost-app.container` (Network=none,
  ReadOnly, UIDMap 2300000 — the B slot's map, tmpfs /tmp + /run,
  MemoryMax=3G, app-data volume at /srv/appdata, rendered configs
  + credentials file mounted read-only, starts only when the
  app-site marker exists). `onionhost-b.container` starts only
  when the marker does NOT exist: the two shapes are exclusive,
  selected by site kind. `runsc-wrap` classifies app-init bundles
  as B-class (netns stripped, --network=none).
- Golden templates: `nginx-app-php.conf.tmpl` (fastcgi,
  REMOTE_ADDR fixed 127.0.0.1 per gate P3),
  `nginx-app-native.conf.tmpl` (proxy_pass to the app's unix
  socket), `php-fpm-app.conf.tmpl` (pool user www-data, socket
  in /run, mysqli/PDO default socket pinned),
  `my-app.cnf.tmpl` (datadir on the app-data volume, socket at
  the Debian default path, native AIO off per gate P1),
  `app-init.sh` (sandbox PID 1: MariaDB -> per-install DB/user
  provisioning from the credentials file -> staged dump import
  -> PHP-FPM or the native binary (as www-data, via setpriv) ->
  nginx in the foreground; app trees permission-normalised at
  every start so owner-dropped files are app-writable and
  app-created files stay owner-manageable).
- `onionhost-app-provision` (new): writes the site-kind marker +
  runtime, creates the app-data skeleton (www/native group-shared
  with the owner, setgid), generates per-install DB credentials
  into /etc/onionhost/app-db.env (mode 0400, owned by the
  container root uid; "root-only" = host root + app container
  root), renders configs. `onionhost-generate-configs` renders
  the app configs when the marker exists and folds the owner gid
  into the app container's environment.
- `onionhost-appdata-guard` + service/timer (new): measured
  quota enforcement (default 20 GiB in /etc/onionhost/app.conf);
  on breach it stops the app, sets a flag file, logs to the
  maintenance log. Hard filesystem quota stays a deferred
  decision (see below).
- Site model: third kind "app" (+ runtime php|native) in sitegen
  validation/starters; the static renderer refuses app models.
  `onionhost-publish` gains the app branch (provision -> start
  the app unit -> wait for the edge socket) and deselects the
  slot when a static kind is published (app data left intact).
  Wizard: third site-type choice + a plain-language app brief
  page with the runtime choice; Dashboard shows the app details
  (via `onionhost-wizard-helper app-info`, which reads the
  root-only credentials file on the GUI's behalf) instead of
  the static editor for app sites.
- Backup FORMAT 2: app sites add app/runtime.txt +
  app/db-credentials.env (app-config), the www/native trees
  (app-data; native runtime is stopped for a cold SQLite copy),
  and a live MariaDB dump (mariadb-dump --single-transaction
  through the socket; the raw datadir is NEVER copied). Static
  backups are byte-for-byte the v1 content. Restore accepts
  formats 1 AND 2; the four-way onion identity check is
  unchanged; an app restore stages the dump on the app-data
  volume for the init import and installs the backed-up
  credentials (0400, container uid).
- `onionhost/APP-SITES.md` (new): the owner-facing install
  contract — what the platform provides, the two runtime
  contracts (PHP: folder, database details and where they are
  shown, no outbound anything, no email, REMOTE_ADDR is a
  fiction, uploads count against the allowance; native: a file
  named `app`, the two environment variables, cwd = data dir),
  SMF 2.1.7 as the worked example (including the settings a
  sealed world needs: immediate registration, no mail features),
  and the switching-kinds semantics. README updated.
- Image pipeline: build-iso.sh builds the app image (nginx +
  headers-more, PHP-FPM + extensions, MariaDB server/client,
  sqlite3), imports it in onionhost-import-images, enables the
  guard timer. NOT yet built into an ISO (see deferred).

### Recipe-ready slot (A23)

The slot was designed recipe-ready, per Cameron's A23 direction
(packaged, checksum-pinned app recipes — SMF first — as a future
wizard convenience ON TOP of the open slot; A20 still governs:
recipes are never a gate). Seams in place, recipes NOT built:
- Recipe files land in www/ (or native/) exactly as an owner's
  copy would; the slot cannot tell the difference, by design.
- DB seeding rides the restore mechanism: a SQL file staged on
  the app-data volume is imported by the app init on next start.
- Config overlays have rendered include points: an nginx fragment
  and a PHP-FPM fragment (generate-configs creates them once,
  comment-only, and never overwrites them afterwards).
- The app site model tolerates extra keys, so a recipe id lands
  without a model version bump.
Flags for the future packager (also in APP-SITES.md): (1) the
init's permission normaliser forces uniform modes across the
app folder — a recipe file needing special permissions
(executable, read-only config) needs an exception list in the
normaliser; (2) PHP executes anywhere in www/ — a recipe should
use its overlay to switch execution off in its app's upload
directory; the platform does not yet do this for hand installs;
(3) recipe config overlays that embed the generated DB
credentials need a substitution step at provision time (the
credentials are per-install and exist before first boot, so
this is a small step, but it does not exist yet).

### Real defects found by the acceptance and fixed in the tree

1. MariaDB socket path: my-app.cnf originally put the socket at
   /run/mysqld.sock while every un-configured client (the init's
   own provisioning calls, PHP defaults) expects the Debian path
   /run/mysqld/mysqld.sock — provisioning SQL silently never
   reached the server and "ready" was echoed anyway. Fixed:
   socket at the distro default everywhere (server config, FPM
   php_admin_value, wizard helper, wizard text, docs), the init
   creates /run/mysqld, and the provisioning branch now checks
   the SQL result and logs ERROR loudly on failure.
2. runuser aborts outright under gVisor ("Critical error -
   immediate abort") when starting the native binary. The init
   now uses setpriv (pure syscalls, no PAM session machinery —
   the right tool in a sealed container regardless).
3. PHP-FPM include of the A23 seam file used a '#' comment;
   FPM's config parser rejects those in included files. The FPM
   placeholder now uses ';' (nginx keeps '#').

### VM-local acceptance (poc/slice6b/) — verdicts

Venue: product-shaped runsc bundles mirroring the Quadlets
(product configs rendered by the product tools; harness shims
for systemctl/podman; the sandbox's 64k uid map forces a
uid-translation shim for host-side tool runs and uid-0 service
users inside the rootfs — venue deltas, recorded in
poc/slice6b/PLAN.md; production values are untouched).
poc/dynamic's gate-round sandboxes were not disturbed.

- Phase D, static regression: PASS. Product publish of a Pages
  starter served by the product static config through the edge
  socket (200, "My Website", no Date header, content-derived
  Last-Modified).
- Phase A, SMF 2.1.7 as an owner install: PASS. Files dropped
  into the app folder per APP-SITES.md (GitHub release archive,
  same sha256 as gate P3; official-package checksum
  verification remains open), web installer driven over the edge
  socket with the platform-generated DB credentials; then, over
  the socket: admin login, topic created + listed + body
  visible, reply posted + visible, guest read, second member
  registered + logged in (registration CAPTCHA switched off as
  the forum admin — a settings row, recorded; scripted-client
  notes in the harness: two-request token discipline, 10-second
  anti-bot registration timer, auto-login after registration).
  The installer driver needed the same form-filling generality
  fixes any scripted client would (named submit button,
  draft-vs-post button, agreement submit name).
- Phase B, native runtime: PASS. The gate P4 Rust binary placed
  at native/app; product publish switched the slot; KV set/get
  roundtrip through nginx -> app socket; SQLite file created on
  the app-data volume.
- Phase C, backup -> wipe -> restore: PASS. Format-2 backup of
  the live forum (manifest inspected after decryption:
  siteKind=app, db-dump present, credentials as app-config,
  www+native trees as app-data, NO raw datadir, no LUKS/initramfs
  material). Machine wiped to a different phrase AND a different
  onion; wrong phrase refused cleanly changing nothing; restore
  with the old phrase returned the SAME .onion; after publish,
  the forum served its topic + reply to a guest (dump imported
  by the init on first boot; restored credentials work), and the
  restored native app served its restored SQLite value through
  the edge after a runtime switch.
- Phase E, v1 back-compat: PASS. A genuine format-1 backup made
  with the pristine slice-5B backup tool restored with the NEW
  restore (meta format 1 verified) and the static site served.
- Quota guard smoke test: PASS (over-quota appdata -> flag file,
  maintenance-log entry, stop issued).
- The combined product-shaped sandbox (app6b) is left RUNNING
  with the restored forum live on the edge socket for
  inspection, like the gate round.

### Explicitly DEFERRED (rig battery follow-up slice)

- ISO rebuild with the app image + the full rig battery:
  install -> app publish -> forum over real Tor; sibling
  containers (A/U) coexistence recheck with the combined shape;
  PHP-FPM under the systrap platform on the rig's kernel (this
  VM's nested sandbox already runs systrap, but the rig is the
  deciding venue); MariaDB behaviour on the rig's real SSD
  (incl. the P1 autocommit/insert-rate observations); the
  runsc-wrap app classification under real Podman/Quadlet.
- Official SMF package checksum verification at recipe time
  (A23 work; the official download host 403s this sandbox).
- A musl-static build of the native reference binary (the
  acceptance used the gate's glibc build; harmless in the full
  Debian app image, required only for minimal future images).
- Hard filesystem quota for the app-data volume (currently
  measured enforcement via the guard timer).
- PHP execution-off in app upload directories (platform-level;
  flagged under A23 above).

## GATE 4 — UPDATE PIPELINE (implementation; rig/ISO battery deferred)

Implemented in the product tree (DESIGN-v2 §7 + DESIGN-v3 A4/A6/A9,
as amended by what the proof itself found - see "proof-driven
changes"). Installed machines now update IN PLACE over Tor; the ISO
remains birth-only. All proof ran VM-local (Stage-0/slice-6B sandbox
pattern, gVisor systrap bundles on this VM); the rig was unreachable
(SSH reset by the egress proxy) for the whole gate.

### What shipped in the tree

- **Signed project repo**: reprepro-free pipeline -
  `build/build-onionhost-deb.sh` (payload = the rootfs-overlay
  etc/+usr/, var/ never packaged; per-release floor written into
  `usr/share/onionhost/floor.json`; `--sabotage`/`--extra-dir` are
  proof-only knobs) and `build/make-onionhost-repo.sh`
  (apt-ftparchive Packages/Release, Valid-Until = Release Date +
  45 days injected as a header-only edit BEFORE signing, InRelease
  clearsigned + Release.gpg detached; RELEASE_DATE env can pin the
  Release Date for reproducible builds / skewed test clocks).
- **Key management (as implemented)**: software signing key NOW -
  ed25519, fingerprint
  38AA06376F68206F072939DE82610F8D4BEF9565, uid "OnionHost Release
  Signing (software key - PRE-RELEASE)
  <release-signing@onionhost.invalid>", expires 2028-10-12 - held
  OUTSIDE the tree in `~/workspace/onionhost-maintainer/gnupg/`
  (0700) with a README recording the A14 RELEASE GATE: before any
  public ISO advertises updates, generate the hardware key,
  re-export the public keyring, re-sign the repo, destroy the
  software key. Private material was never in the tree or any
  package (verified: the .deb carries only
  `usr/share/keyrings/onionhost-archive-keyring.gpg`, 300 B public).
  Re-sign cadence: monthly against the 45-day Valid-Until (amber at
  expiry, "may be unmaintained" at +90d per DESIGN-v2 §7).
- **Repo as an onion service**: v3 onion
  tpt6oez5hqsmeifbd3ltjb7d4nnfys4dqyyu2mukh2v53eh5nd7fbfyd.onion
  (identity in the maintainer dir, served from this VM during the
  proof); the address is a public constant baked into the golden
  source template, like a mirror URL.
- **Tor-only fetch**: stock trixie apt CANNOT do SOCKS-over-unix
  (measured: apt-transport-tor 0.5 is symlinks onto the http method;
  apt 3.0.3's http method implements SOCKS5 for host:port proxies
  only and SILENTLY IGNORED a unix proxy, attempting a direct
  clearnet dial). The package therefore ships its own acquire
  method, `usr/lib/apt/methods/tor+http` (apt protocol: SOCKS5
  no-auth over U's unix socket, ATYP-domain connect, HTTP/1.1,
  hash verification of every Expected-* digest, Maximum-Size,
  partial-file + atomic rename; NO non-Tor code path), plus
  `etc/apt/apt.conf.d/52onionhost-tor-updates`:
  `Acquire::tor::Proxy "unix:///run/onionhost/client/socks/sock"`,
  `APT::Sandbox::User "root"` (U's socket dir is 0700 to U's uid by
  design - the same reason the Dashboard probe goes through the
  root helper), and the apt-transport-tor README hardening
  `Dir::Bin::Methods::http/https "false"` so a non-tor+ source
  fails closed instead of falling back to clearnet. Golden source
  templates (`usr/lib/onionhost/golden/apt-*.sources.tmpl`) are
  rendered by onionhost-generate-configs to
  /etc/apt/sources.list.d/{onionhost,debian}.sources: the project
  repo + Debian's official onion services (ftp + security,
  addresses from trixie's apt-transport-tor README); a legacy
  clearnet sources.list is retired exactly once to
  sources.list.onionhost.bak.
- **Updater**: `usr/local/bin/onionhost-update` +
  onionhost-update.service/.timer (OnCalendar 00:00 UTC,
  RandomizedDelaySec=24h, Persistent=true; service gated on
  ConditionPathExists=/run/onionhost/client/socks/sock;
  SuccessExitStatus 2 3 4, exit 5 stays a visible failure).
  Debian's apt-daily timers are masked in the overlay (symlinks to
  /dev/null) so nothing apt runs outside this tool - apt-daily-
  upgrade would otherwise install the managed package WITHOUT the
  floor/health orchestration. Flow: project-only apt update
  (Dir::Etc::sourceparts staging; channel independence - below) ->
  per package: repo-best vs high-water mark REFUSAL -> download-only
  -> floor read from INSIDE the signed .deb and persisted BEFORE
  install (Y8: the new floor judges the old version) -> install ->
  stack restart -> product probe health check (rc 0 AND " 200" in
  the PROBE_OK line) -> healthy: advance high-water, save the .deb
  as the rollback copy; unhealthy: roll back iff the saved copy is
  >= floor (re-check health), else FAIL CLOSED (gateway stopped
  first, then the stack; status fail-closed; exit 5). Debian base:
  full apt update + upgrade afterwards, best-effort, same Tor path.
  Status lands in /var/lib/onionhost/update/status.json
  (+ update.log, highwater.json, floors.json).
- **Dashboard**: one added status line under the existing site
  status (wizard.py `update_status_text()` + `update_label`):
  up-to-date/updated -> "Your software is up to date."; fail-closed
  -> "Your site is off for safety. Updates will install themselves
  when a fixed version is ready."; anything else/missing/corrupt ->
  "Updates will install themselves." Status text only - no button,
  no new concept (concept budget stays five).

### Proof (VM-local; machine bundle + repo service left running)

Machine: mmdebstrap trixie rootfs (snapshot 20251011T143150Z) in a
runsc bundle shaped like the product: tor-U (product client-torrc),
tor-A (product torrc/HS), nginx-B (product golden config), factory
v1.0.0 installed by dpkg at first boot (postinst rendered all
configs + apt sources and retired the clearnet list - verified).
Site onion (this proof instance):
s6vcuhqiundh5qkhbhozanavqkv7nb5zxksi2rcqrejqjsbzzjvsnsad.onion.
Sandbox substitutions, flagged: --network=host (setns blocked on
this VM; same substitution as Stage 0), a harness stackctl +
stack-launcher stand in for Podman/Quadlet process management,
single-root uid (generate-configs' container-uid chowns are undone
by the harness - in the product each daemon runs as its mapped
uid). Evidence: poc/gate4/ (logs/final-evidence.log, per-step
logs/, pkgs/, bundle-machine/, harness/).

Scenario results (updater log timestamps, UTC):
1. **Baseline** (repo = v1 only): status up-to-date; high-water
   1.0.0, floor 1.0 recorded. The same run's Debian pass fetched
   lists over Tor and **upgraded 27 real Debian packages in place**
   ("27 upgraded, 0 newly installed").
2. **Upgrade**: repo v1+v2 -> "onionhost: updated to 2.0.0 and
   healthy"; floor read from the signed v2 package; probe 200
   after restart; dpkg = 2.0.0; v2 .deb saved as rollback copy.
3. **Replay refusal**: repo rebuilt to v1-only (re-signed) ->
   "REFUSED onionhost: repository's best version 1.0.0 is below
   the high-water mark 2.0.0 - a replayed or rolled-back
   repository cannot downgrade this machine"; status
   refused-downgrade; dpkg stayed 2.0.0; site unaffected.
4. **Broken v3** (sabotaged launcher; floor 2.0 in its signed
   metadata): installed, health check FAILED (stack never came
   up), updater rolled back to the saved v2.0.0 (2.0.0 >= floor
   2.0 - legal). The rollback's confirming health check then
   timed out on sandbox Tor latency (see caveats) -> updater
   escalated to fail-closed rather than serve unverified.
5. **Below-floor trap + recovery**: repo v5 (good, floor 4.0):
   floor 4.0 learned BEFORE install; v5 installed; health check
   failed (gateway was down from step 4's fail-close; a sandbox
   uid artifact kept tor-A from restarting - harness-fixed);
   "**rollback target 2.0.0 is below the security floor 4.0 or
   unavailable - failing closed**". Next run exercised the new
   recovery branch: "recovering from fail-closed - restarting the
   stack on the installed 5.0.0 and re-checking health" -> first
   attempt stayed closed (gateway bootstrap slower than the probe
   envelope in this sandbox), second attempt: "**recovery healthy
   - site is back**", status up-to-date, installed 5.0.0, floor
   4.0; final probe PROBE_OK HTTP/1.1 200 OK.
   (The choreography's separate sabotaged-v4 step was overtaken by
   this sequence: the below-floor rule fired identically with
   v5's signed floor 4.0 against rollback target 2.0.0. The v4
   package remains in poc/gate4/pkgs/, unexercised.)
6. **Repo onion service**: InRelease fetched over the real Tor
   network from an independent client (HTTP 200, Valid-Until =
   +45d, Origin OnionHost); Release.gpg + InRelease signatures
   verified with gpgv against the shipped public keyring.
7. **Timer**: systemd-analyze accepts the units (only complaint:
   sysinit.target absent in the bare verify root); calendar
   expression normalizes and elapses daily 00:00 UTC; the 24h
   RandomizedDelaySec gives the designed per-machine uniform
   spread across the UTC day. Dashboard text function unit-tested
   against up-to-date/updated/fail-closed/other/missing/corrupt
   status files: all six outputs as specified.
8. **Debian leg caveat**: the security onion service answered
   throughout (lists + the 27-package upgrade prove the path).
   The main ftp onion persistently 404'd /debian/dists/trixie/
   metadata from every client tried during the proof window
   (directory listings show component dirs but no Release files -
   consistent with backends mid-sync for the 13.7 point release);
   the updater logged it and carried on (channel independence),
   retrying next run - the designed behaviour, but full
   main-archive fetch over Tor is NOT counted proven in this
   window and is on the rig list below.

### Proof-driven changes (found by the proof, fixed in the tree)

- Custom-method hash-key bug: apt sends Expected-MD5Sum; the
  method normalized to "MD5SUM" but indexed hashes by "MD5Sum" -
  every uncompressed index fetch died with KeyError 'MD5SUM'.
  Canonicalized; also methods now exit quietly on apt's SIGINT.
- Two-pass update: originally ANY source failure (incl. a Debian
  mirror outage) froze the signed project package. Now the project
  repo updates in its own restricted pass; Debian is a separate
  best-effort pass (upgrade still runs on partial lists).
- **Replay blindness**: apt's candidate can never be a downgrade,
  so candidate==installed masqueraded as "current" against a
  replayed repo. Decisions now use the repo's best offered version
  (`apt-cache madison`, dpkg-status pseudo-source excluded).
- **Fail-closed recovery hole**: after a post-install fail-close,
  later runs saw candidate==installed and never revived the stack
  - the site would have stayed off forever despite a good version
  being installed. Updater now carries a recovery duty: previous
  state fail-closed + installed >= floor -> restart stack +
  health-check on the "current" path; success advances the
  high-water mark to the verified version; failure re-closes.
  (The high-water advance was the last micro-fix; it landed after
  the proof machine's recovery run, whose on-disk highwater.json
  therefore still reads 2.0.0 - the tree's updater writes 5.0.0
  there. Noted rather than retro-edited.)
- Fail-closed now stops the stack as well as the gateway (the
  first implementation left B serving into a dead socket -
  unreachable, but "site off" should mean off).
- Standing note (pre-existing, found incidentally): the product
  probe reads a fixed 10-byte SOCKS reply; tor answers onion
  connects with a 22-byte ATYP-4 reply, so 12 NUL bytes prefix the
  status line in PROBE_OK output. Harmless for every consumer
  (the " 200" check is substring-based) - recorded, not changed.

### Sandbox caveats that bound the proof

- The guest clock in the gVisor sandbox lags the host ~20 min
  (systrap): apt rightly refused Release files dated in ITS
  future until proof repos were signed with RELEASE_DATE 40 min
  in the past. Production hosts run chrony NTS; the rig battery
  re-tests with true-time signing.
- Tor bootstrap/descriptor times in the nested sandbox are ~10x
  real-network (bootstrap stalls of 3-8 min observed); the
  probe's retry envelope (~10 attempts) twice expired against a
  cold gateway (step 4's rollback confirmation, step 5's first
  recovery attempt). On both occasions the updater chose the
  conservative branch (close / stay closed) - the failure mode is
  safe, but the envelope-vs-cold-start margin needs the rig's
  real timings before it can be called proven.

### DEFERRED (explicit)

- ISO rebuild carrying the new files + the full rig install
  battery (install -> update over Tor on the rig's real network,
  netns-level verification that no clearnet path exists - the
  config has no non-Tor route, but packet-level proof needs the
  rig's network namespaces).
- Network-namespace fidelity of the client sandbox (host-network
  substitution above) and runsc-wrap classification of the new
  units under real Podman/Quadlet; systrap behaviour of the
  updater's process tree on the rig kernel.
- Full Debian main-archive fetch over the ftp onion (external
  404 window during the proof; security onion proven instead).
- True-time repo signing end-to-end (sandbox clock lag forced
  past-dated proof repos).
- The hardware signing key itself (A14 release gate - software
  key until then, per the maintainer README) and the first
  monthly re-sign cycle.
- DESIGN-v2 §7's restart-honesty card ("Restart needed for a
  security fix"): outside this gate's Dashboard contract (status
  text only, no new concept) - remains unimplemented by design
  decision here, flagged for a later slice.
- App-recipe updates (A23) ride this pipeline but no recipe
  exists yet; recipe update/rollback is recipe-slice work.

## A23 RECIPE 1 — SMF (implementation; rig/ISO battery deferred)

The first project-packaged app on the slice 6B app slot, riding the
Gate 4 update pipeline: SMF 2.1.7 as a wizard site-type choice
("Forum"), installed, seeded and kept up to date by the platform —
packaging as a CONVENIENCE per A23, never a gate (the open slot is
unchanged). All three recipe flags left open by slice 6B are
resolved (below). VM-local acceptance in poc/recipes-smf/, shaped
like the Gate 4 proof machine (one runsc sandbox, real dpkg
database, product files, harness stack control); the rig is
unreachable from this venue, so the ISO build + rig battery are
DEFERRED (list at the end).

### Recipe format (in tree: onionhost/recipes/smf/)

A recipe is its OWN signed .deb, `onionhost-recipe-smf`, in the
same Gate 4 repo — NOT data inside the platform package: an SMF
security fix must not wait for a platform release, and the two
floors stay decoupled. Version scheme `2.1.7+oh.N` (dpkg ordering
does the rest). The recipe floor is a maintainer constant
(onionhost/recipes/smf/floor.txt, starting at 2.1.7+oh.1, so
rollback to oh.1 stays legal until deliberately raised), embedded
by the builder as usr/share/onionhost/recipes/smf/floor.json.

Payload under /usr/share/onionhost/recipes/smf/:

- manifest.json — id `smf`, app version 2.1.7, runtime=php, db
  required, table prefix `smf_`, archive file + sha256, data_dirs,
  and the wizard-facing one-liner: "Forum - discussion boards
  with member accounts (SMF), set up for you."
- archive/ — the pinned app archive; the applier verifies its
  sha256 against the manifest before extracting anything.
- overlay/nginx-app-extra.conf, overlay/php-fpm-app-extra.conf
  (comment-only for SMF — the seam stays uniform),
  overlay/normalize-exceptions.
- seed/tail.sql.tmpl — the sealed-world settings overrides,
  applied on top of SMF's own install SQL (below).

Archive provenance: the official download host
(download.simplemachines.org) still returns 403 from this venue,
so the vendored archive is the GitHub release archive of tag
v2.1.7, sha256
5efdadf64d91082f59176c983af26dc0e6e3dff50b5d0b1d2eeb60300b3d257d
(commit d49255b), the same archive the P3 gate and slice 6B used.
Second-source check: a fresh codeload download of the tag has
different zip bytes (GitHub zipballs are not byte-stable) but an
extracted tree content-identical to the vendored archive
(diff rc=0). Official-package checksum verification remains a
flagged open item.

### The three slice 6B flags, resolved

1. Normaliser exception list (platform change): the golden
   app-init.sh now applies /etc/onionhost/normalize-exceptions
   after its permission normalisation, in both the php and native
   branches — lines `MODE PATH`, PATH relative to the app-data
   root, octal modes validated, `..` and leading `/` rejected.
   SMF's list is exactly two entries: `0660 www/Settings.php` and
   `0660 www/Settings_bak.php` (they hold the DB password; SMF
   needed nothing else — it ran under the uniform modes in 6B).
   Supporting fix: onionhost-app.container now bind-mounts
   nginx-app-extra.conf, php-fpm-app-extra.conf AND
   normalize-exceptions (the unit never mounted the files its
   rendered configs include — a latent gap), and
   onionhost-generate-configs renders a comment-only
   normalize-exceptions placeholder exactly once, like the other
   seam files, so podman never creates a directory at the source.
2. PHP execution OFF in upload dirs (recipe nginx overlay,
   included inside the server block via the platform seam):
   `location ~* ^/(attachments|custom_avatar|cache|Packages)/
   .*\.(php[0-9]?|phtml)$ { deny all; }` — attachments is THE
   upload directory; Packages/cache files are include-only.
3. Provision-time credential substitution: the applier renders
   Settings.php from the payload template at apply time —
   $db_name/$db_user/$db_passwd from /etc/onionhost/app-db.env
   (per-install, generated at provision), $boardurl =
   http://<onion>, $webmaster_email = admin@<onion>,
   $image_proxy_enabled = false, a random $image_proxy_secret.
   Settings_bak.php is written identical, as SMF's installer
   does. Credentials are NEVER in the recipe package. On recipe
   updates the existing Settings.php/Settings_bak.php are carried
   over verbatim (SMF never rewrites them on upgrade; owner
   changes survive).

### Applier (new tool: usr/local/bin/onionhost-recipe)

`apply|rollback|status <id>`. Apply: verify archive sha256 →
extract → build the new www in staging on the app-data volume
(payload MINUS installer files — install.php, install_*.sql,
upgrade*.php|sql, update_*.php never land in the docroot; a
leftover installer redirects every page to itself and is an open
door) → copy the manifest's data_dirs (attachments/,
custom_avatar/, cache/) across from the live www → write the
overlays to /etc/onionhost → first install only: stage the seed
→ atomic swap (live www kept one generation as
appdata/.www-recipe-prev) → record
/var/lib/onionhost/recipes/<id>/state.json. A RECIPE-VERSION.txt
marker in www names id, package version and app version.
Documented semantic, same warning SMF itself gives: a recipe
update overwrites the app's core files; the preservation promise
is the database + data_dirs.

Seeding rides the established first-boot import: the applier
builds the seed from SMF's own install_2-1_mysql.sql, replicating
the installer's substitution table (single-pass strtr semantics;
db_prefix=smf_; boarddir=/srv/appdata/www; boardurl=http://
<onion>; attachdir as SMF's JSON map; InnoDB/utf8;
registration_method=0 immediate; a randomised sched_task_offset;
{$enableCompressedOutput}=1 and {$databaseSession_enable}=1 —
the installer form defaults, found by the unit checks; every
{$default_*} language value parsed from the payload's own
Install.english.php with SMF's db_escape semantics). The recipe's
seed tail then applies the sealed-world posture: avatar_download_
png=0 AND avatar_max_width/height_external=0 (the 65x65 defaults
make SMF fetch remote avatars server-side on profile save;
zeroing the limits removes that fetch path — external avatar
URLs degrade to plain hotlinks in visitors' own browsers);
gravatarEnabled=0; DELETE FROM smf_admin_info_files (the
version-check fetch list — the server-side update check and its
error-log noise are removed at the root, which is the
"suppressed where configurable" answer for SMF 2.1: there is no
config switch); mail_type stays 0 (PHP mail(); no MTA exists in
the image, so mail fails immediately and cleanly — that IS the
disabled posture; SMF 2.1 has no hard off switch); stats fixups
so the seeded admin is the forum's member #1. SMF's standard
welcome board/topic come from the substituted defaults — a
recipe forum starts as a completely ordinary SMF install.
Anti-reseed guard: seeding happens ONLY on first install, judged
by the absence of the live www/Settings.php, and a staged
db-import.sql.gz (e.g. a restore's) is never overwritten.

The .deb's postinst is the apply trigger: it runs
`onionhost-recipe apply <id>` only when /var/lib/onionhost/
app-site exists AND /etc/onionhost/recipe-selection names this
recipe; otherwise it exits 0 (ISO builds, unselected machines).
A failed apply fails the dpkg install, which the updater treats
as a failed update — health check, rollback and fail-closed
semantics apply unchanged. Rolling back the .deb re-runs the old
payload's postinst, which re-applies the previous payload.
onionhost-publish maintains /etc/onionhost/recipe-selection on
every app publish and runs apply BEFORE starting the container
on recipe publishes (an apply failure fails the publish before
anything starts).

### Admin creation — the flow chosen, and why

The owner sets the forum admin name + password AT THE MACHINE,
in the wizard: the app page gains a recipe choice (packaged
Forum (SMF) vs your-own-app) and admin fields. At Go Live the
wizard stages them through the new wizard-helper subcommand
`recipe-setup` (three lines on stdin — id, user, password — the
commit-login discipline: secrets never in argv or logs) into
/etc/onionhost/recipe-admin.env (0400, root). The applier
consumes it while building the seed and then SHREDS it
(overwrite + unlink). A first install with no staged admin env
is a hard apply error with nothing half-done: no silent
credential invention, ever. Alternatives rejected: SMF's own
web installer as first-run (it needs the DB credentials typed
into a web form and leaves install.php discipline to the owner —
the recipe exists precisely to remove that); inventing a
default admin (a known-credential backdoor by another name).

Password mechanics: the seed inserts the admin row (the
installer's exact column set, id_group=1) with SMF 2.1's legacy
hash sha1(lower(user) + password) — the host has no PHP and
trixie's python3.13 removed crypt, so bcrypt cannot be computed
at provision time with zero added dependencies, while hashlib
is stdlib. SMF's login path accepts the 40-char form and
upgrades it to bcrypt (password_hash, 60 chars, $2y$) at the
first successful login; the sha1 sits only inside the
LUKS-encrypted DB until then, and the staged seed file is
deleted by app-init right after import. Verified in acceptance:
admin passwd length 40 → 60 after the first login. The wizard
tells the owner to log in once after setup. The forum name is
left at SMF's default "My Community" (the owner renames it in
SMF admin — deliberately decoupled from the site title), and the
admin email is seeded as the placeholder admin@<onion>, to be
replaced in SMF admin.

### Updater changes (in tree)

- MANAGED is dynamic: ["onionhost"] plus every installed
  onionhost-recipe-* package discovered via dpkg-query (platform
  first; behaviour identical with no recipe installed).
- deb_floor() scans ALL tar members ending in /floor.json (a
  recipe package carries its own); the baseline disk-floor read
  generalises to the platform file, then a glob over
  /usr/share/onionhost/recipes/*/floor.json.
- NEW — factory-version rollback copy: at install time, if prev/
  holds no copy of the currently-installed version (the factory
  /ISO case — the updater only ever saved copies of versions IT
  installed healthily), the updater first fetches that version's
  .deb from the same signed repo and saves it as the rollback
  copy. Without this, the FIRST updater-driven update of any
  package could only fail closed on a health failure — a
  pre-existing Gate 4 gap its proof never exercised, found by
  this slice's scenario 2 and fixed before scenario 2b proved
  the clean path. Production repos must therefore keep the
  previous version's .deb published (the repo maker publishes
  exactly the directory it is given).
- build/make-onionhost-repo.sh also pools onionhost-recipe-*.deb
  under pool/main/o/<package-name>/. New builder
  build/build-recipe-deb.sh <recipe-dir> <version> <outdir>
  [--floor X] [--sabotage]; --sabotage is a PROOF-ONLY knob (it
  appends invalid PHP to index.php and re-seals the manifest
  hash, so the package is self-consistent and the app simply
  broken) — never ship a sabotage build outside a test repo.

Wizard/sitegen: starter_model(..., recipe=None) and validate_
model accept a sanity-checked recipe key (^[a-z0-9][a-z0-9-]*$);
the model tolerates the extra key with no version bump, so
backups and older models are untouched. APP-SITES.md's packaged-
recipes section now states the shipped SMF contract (admin
flow + first-login note, update behaviour + core-files warning,
the three flags as resolved). GUI code is pattern-faithful and
py_compile-checked only — the GUI battery is rig-deferred.

### Host-side unit checks (poc/recipes-smf/unit-test.py) — 32/32

The applier exercised against the real recipe .deb's payload
with env overrides: archive sha verification; first-apply tree
(no install.php / other/ / upgrade SQL in the docroot); Settings
rendering (credentials substituted, boardurl = the onion, image
proxy off, Settings_bak identical); admin env shredded after
apply; seed SQL (no leftover {$ placeholders, legacy sha1
present, registration_method 0, avatar/gravatar overrides,
admin_info_files DELETE, language defaults substituted, prefix
substituted); overlays written; state recorded; update apply
(owner's Settings tweak carried over, a data-dir file survived,
marker bumped, NO reseed, previous tree kept); sha-mismatch
refused with the site untouched; first install without a staged
admin refused with no docroot created. Re-run after the
scenario-4 fix below: still 32/32.

### Sandbox acceptance (poc/recipes-smf/) — verdicts

Machine bundle: mmdebstrap trixie rootfs (snapshot
20251011T143150Z, union package set incl. the app stack, real
dpkg db, 891 MB / 348 packages), booted once under runsc and
driven via runsc exec (rootfs writes are per-container in this
venue; cross-container state travels via the bind-mounted
"stick"). Test identities: admin forumadmin, member member2
(throwaway acceptance credentials, in the slice dir). Repo
service: the maintainer repo onion (tpt6oez5...onion) served
from a COPY of the maintainer hs dir; repos signed with the
pre-release software key, Release past-dated ~40 min (harmless:
in-machine clock == host clock in this venue).

Scenario 1 — fresh recipe forum, NO owner file-drop: PASS.
Platform 1.0.0 + recipe oh.1 dpkg-installed; the owner model
written through the product's own sitegen (recipe="smf"); admin
staged via recipe-setup (env 0400); publish printed
APP_PROVISION_OK db=created → RECIPE_APPLY_OK first_install=yes
seeded=yes → PUBLISH_OK, and the applier shredded the admin env.
Forum HTTP 200 on the edge socket ("General Discussion", "My
Community"); app-init imported the seed and consumed the import
file. DB verified: admin id_group=1; passwd 40 → 60 ($2y$) at
first login; registration_method=0, mail_type=0,
avatar_download_png=0, gravatarEnabled=0, totalMembers=1,
smf_admin_info_files count = 0. member2 registered (immediate)
and logged in; admin posted topic 2; a guest reads topic +
reply. PROBE_OK with HTTP 200 through the real Tor path (SMF
PHPSESSID headers, no Date header). One cold-bootstrap probe
attempt returned PROBE_TIMEOUT inside the probe's ~3-4 min
envelope — the venue Tor timing question below, not the app.
Updater baseline against repo v1 then passed rc=0 with BOTH
managed packages evaluated ("onionhost: 1.0.0 is current",
"onionhost-recipe-smf: 2.1.7+oh.1 is current", recipe floor and
high-water recorded separately), and 66 real Debian packages
downloaded and configured in place over Tor in the same run.

Scenario 2 — recipe update oh.1 → oh.2: DELIVERED, DATA
SURVIVED, health verdict failed on Tor timing → FAIL-CLOSED
(the designed safe direction). The updater installed oh.2
(postinst RECIPE_APPLY_OK first_install=no seeded=no) and
restarted the stack; the health check at ~3.7 min post-restart
got PROBE_FAIL (SOCKS rep=4) — descriptor republication in this
venue, while the forum was verifiably healthy at the edge the
whole time. Rollback was impossible for a reason that had
nothing to do with Tor: oh.1 had been installed BY HAND at
machine setup, so prev/ held no copy — the factory-version gap
described above. The updater failed closed (rc=5) and stopped
the gateway, exactly as designed when no legal rollback exists.
Two recovery runs followed: the first also timed out through
Tor (~348 s) and stayed fail-closed (correct); the second
(23:11→23:13 UTC) printed "recovery healthy - site is back" and
proceeded in the same run to scenario 2b. Data survival verified
at the edge after the whole episode: marker oh.2, guest reads
topic 2, member2 logs in.

Scenario 2b — recipe update oh.2 → oh.2.1: PASS END-TO-END,
the clean update proof. Log: "saved a rollback copy of the
installed 2.1.7+oh.2" (the new pre-install fetch) → install →
postinst apply oh.2.1 → restart → "updated to 2.1.7+oh.2.1 and
healthy"; prev/ then held oh.2.1 (the saved copy tracks the
last health-verified version); full run rc=0 including the
Debian tail; topic 2 still served afterwards — data survived a
second recipe update.

Scenario 4 — backup/restore of the recipe site (format 2):
PASS. Backup via the helper to the stick: BACKUP_OK, 3,072,000
bytes, manifest verified. Restore onto machine 2 (different
disk phrase, its own onion) with machine 1's phrase: rc=0, and
machine 2 came back at machine 1's onion (pxkvdkfl...onion —
the SAME onion returns, as in slice 5B) with the restored
credentials kept (APP_PROVISION_OK db=existing) and the staged
restore dump imported by app-init. Guest reads topic 2; BOTH
the admin and member2 logins work with the original credentials
(the bcrypt hash travelled in the dump). BUG FOUND + FIXED by
this scenario: the first publish on machine 2 REFUSED — the
applier judged first_install by its state record, which a
backup does not carry, and demanded staged admin details. Fix
(in tree): first_install is judged by the presence of the live
www/Settings.php — the app's own ground truth — not by state.
Re-publish then applied in sync mode (first_install=no
seeded=no) with the restore dump's sha256 verified untouched.

Scenario 3 — sabotage rollback: PASS (full arc, two attempts).
Attempt 1 (2026-10-13 23:16 UTC) was interrupted by the sandbox
VM being replaced mid-run: the sabotage was confirmed live at
the edge (marker oh.3, HTTP 500 from the PHP parse error) but
the updater's verdict was never collected and the sandbox's
ephemeral rootfs state died with the VM. The scenario was
therefore re-run end-to-end on a fresh machine (platform .deb
rebuilt from the current tree — content-equal to the original
pkgs .deb plus the two files pushed during attempt 1's session,
verified: the Settings.php first-install rule and the
factory-copy block are both in the rebuilt package; fresh
onion irnvsio5...onion; forum re-seeded with the same test
identities and topic 2; recipe oh.2.1 hand-installed, so prev/
started EMPTY and the factory-copy path was exercised again).
Re-run timeline (UTC): 23:39:41 "saved a rollback copy of the
installed 2.1.7+oh.2.1" → "installing onionhost-recipe-smf
2.1.7+oh.2.1 -> 2.1.7+oh.3" → 23:40:46 the health check got the
forum's real response headers through Tor but not a 200 (the
sabotage 500 — detected through the real probe path, not just
at the edge) → "update to 2.1.7+oh.3 FAILED its health check" →
"rolling back to 2.1.7+oh.2.1 (at/above floor 2.1.7+oh.1)" →
the prev .deb reinstalled, postinst RECIPE_APPLY_OK oh.2.1,
stack restarted 23:40:49. The rollback's own health check then
hit this venue's Tor republication window: PROBE_FAIL timed out
at 23:47:13 while the edge was verifiably serving 200 on oh.2.1
— so the run ended FAIL-CLOSED (rc=5) with dpkg, the www marker
and status.json all at oh.2.1 (installed = highwater = oh.2.1 ≥
floor oh.1; candidate oh.3): the designed safe end-state, one
step short of the clean rc=4. The maintainer remedy was then
exercised: oh.3 was pulled from the repo (repo re-published
without it) and a later updater run took the recovery branch —
after one fetch-failed retry (below) — "recovering from
fail-closed - restarting the stack on the installed 1.0.0" →
"recovery healthy - site is back" → "onionhost-recipe-smf:
2.1.7+oh.2.1 is current" → rc=0, status up-to-date. Final
verification: guest reads topic 2; member2 AND forumadmin log
in — every account and post created before the sabotage
survived the sabotage, the rollback, the fail-closed interval
and the recovery.

### Findings that outlive the slice

- Venue Tor timing vs the probe envelope (KNOWN, now measured
  three ways): after ANY stack restart, descriptor republication
  in this sandbox repeatedly exceeded the probe's envelope (one
  loop recorded 21 failed attempts over ~16 min; other windows
  passed at ~2.5-4.5 min; a host-side tor simultaneously sat at
  45% bootstrap for 20+ min — the venue's Tor was degraded
  throughout, as in slice 5A's battery). Gate 4's identical
  health flow passed post-restart on its venue. The rig battery
  must measure real republication latency on real hardware
  before the envelope margin can be called proven; until then
  fail-closed + the timer-driven recovery duty is the designed
  convergence, and it behaved as designed in every run here.
- NEW (update pipeline): a fetch-failed run OVERWRITES a
  fail-closed status.json. In the scenario-3 recovery sequence,
  an updater run whose repo fetch failed (the harness's stack
  stop had also stopped container U — a harness delta: in
  production U is a separate unit and the update timer is gated
  on its socket) wrote state "fetch-failed" ("Your site is
  unaffected") over the fail-closed record, which silently
  disarmed the next run's recovery duty — it read "all current"
  and never restarted the stack. In production the interleaving
  is unlikely (U down at run start is what the timer gate
  prevents), but the state machine is wrong regardless: a
  fetch-failed write must not clobber a fail-closed record, and
  the Dashboard must never say "unaffected" about a site that
  is deliberately off. Follow-up fix for the update pipeline:
  make fail-closed sticky across fetch-failed runs (skip the
  status write, or key recovery on a dedicated marker file).
  The recovery proof above was completed after restoring the
  sabotage run's exact status.json record (fixture repair,
  disclosed here) with U running and the gateway/app stopped —
  the production fail-closed posture.
- Venue bookkeeping: the sandbox VM replacement between
  attempts also wiped the host's tor binary; the re-run's repo
  service tor was the staged rootfs's own tor (0.4.8.16) run
  under its own dynamic loader. No product meaning.

### DEFERRED (explicit)

- ISO rebuild carrying the recipe + full rig battery: install
  → choose Forum in the wizard → forum over real Tor; the
  updater over the rig's real network incl. the packet-level
  no-clearnet proof; FPM/MariaDB behaviour on the rig; and the
  probe-envelope vs republication measurement on real hardware
  (the open production question above).
- Wizard GUI battery for the recipe pages (no GUI venue in this
  sandbox; the code is pattern-faithful + py_compile-checked).
- Official SMF package checksum verification (the official host
  403s this venue; the GitHub archive is content-verified
  against a second download — see provenance).
- Recipe DB migrations beyond patch-level file sync: SMF
  major-version upgrades need upgrade.php; the manifest has no
  migration hook yet. Recipe v1 covers patch-level updates
  (the oh.N cadence).
- Dashboard-side recipe staging for owners switching site kind
  AFTER setup (this slice wires the wizard first-run path; the
  publish path honours any staged admin env).
- The fetch-failed / fail-closed status fix (findings, above) —
  update-pipeline follow-up, not recipe work.
- Hard fs quota (the appdata guard stays measured, as in 6B);
  sibling-container re-test; the Gate 4 deferred list otherwise
  stands.
- Inherited by future recipes (WordPress, DokuWiki, Gitea):
  the recipe format above as-is — own signed .deb, manifest +
  pinned archive + overlays + seed, floors decoupled from the
  platform, postinst-apply gated on selection, seeding only on
  first install judged by the app's own ground-truth file, and
  the factory-copy updater behaviour that makes first updates
  safe.

## GATE 4 FOLLOW-UP — fail-closed stickiness (2026-10-13)

Fixes the update-pipeline finding recorded under "A23 RECIPE 1 —
SMF / Findings that outlive the slice": a fetch-failed updater
run overwrote a fail-closed status.json with state "fetch-failed"
("Your site is unaffected"), which silently disarmed the next
run's recovery duty (it keyed on the previous status) — a site
deliberately OFF for safety could be forgotten by the state
machine while the record claimed it was unaffected.

### Shape chosen: dedicated marker (option b) + guarded writes

- **`/var/lib/onionhost/update/fail-closed.marker`** is now the
  machine-state source of truth for the recovery duty, in the
  codebase's own grain: highwater.json and floors.json are
  already dedicated state files, while status.json is — by its
  own docstring — the Dashboard's record of the last run's
  outcome. Keying a safety duty on the presentation file was
  the root flaw. The marker carries `since` + per-package
  installed version and standing floor; it is written at all
  three fail-closed entries and cleared ONLY by a healthy
  outcome (successful update, healthy rollback, healthy
  recovery) — never by a run that merely failed to fetch.
- **Legacy adoption**: a machine closed by the pre-fix updater
  has the fail-closed status but no marker. The first fixed run
  arms recovery from either carrier and writes the marker from
  the legacy status, so already-closed machines self-heal their
  state on their next timer run.
- **Guarded writes (option a, belt-and-braces)**: BOTH
  fetch-failed writes (project-repo fetch, per-package
  download) now return exit 3 WITHOUT touching status.json
  while failed closed, so the record itself never claims
  "unaffected" about a closed machine.
- **Dashboard**: `update_status_text()` (wizard.py) gives the
  marker precedence over status content — marker present →
  the fail-closed string, whatever status.json says or whether
  it exists. The six Gate 4 cases and their exact strings are
  unchanged when no marker exists.

### Proof (VM-local state-machine tests; NO Tor re-run)

Per the fix's scope, reproduction and verification ran the
real `onionhost-update` code in subprocesses against PATH
stubs (repo unreachable = apt-get update/download failures;
offered/installed versions, health and stack control stubbed):
`poc/gate4fix/run_tests.py` (22 assertions, 5 interleavings)
and `poc/gate4fix/test_dashboard.py` (11 assertions) — originals
of both files preserved alongside as `.orig`.

- RED (original code): 7 updater failures — S1 fetch-failed
  run clobbered the fail-closed status and the next healthy
  run exited 0 WITHOUT taking the recovery branch or ever
  restarting the stack (the A23 finding, reproduced exactly);
  S2 recovery disarmed by a clobbered status; S4 the
  download-failure write clobbered identically. Dashboard
  original: the six Gate 4 cases pass; no marker support.
- GREEN (fixed code): 22/22 + 11/11. fail-closed →
  fetch-failed → normal run still recovers (stack restarted,
  status up-to-date, marker cleared); fail-closed → download-
  failed → state stands; healthy machine still records
  fetch-failed and grows no marker; below-floor recovery
  refusal still exits 5 without a stack restart; Dashboard
  returns the fail-closed string for marker + fetch-failed /
  missing / up-to-date status alike, and status rules again
  once the marker clears.
- A full sandbox Tor re-run is NOT required for this fix and
  was not performed: the change is confined to status/marker
  bookkeeping around unchanged fetch/install/health paths;
  it rides the next ISO + rig battery with the rest of the
  Gate 4 deferred list.

### Adjacent observations (reported, NOT fixed here)

- A recovering run that meets a replayed repo writes status
  "refused-downgrade" mid-run; the end-of-run branch restores
  the fail-closed status on the single-package path, but a
  later package's guarded download-failure return (exit 3, no
  status write by design) can leave status.json resting at
  "refused-downgrade" while closed. Presentation-only now —
  the Dashboard (marker precedence) and the recovery duty
  (marker-keyed) are both unaffected.
- The below-floor recovery refusal (exit 5) writes neither
  status nor marker: correct under the marker (it already
  stands), but status.json's `checked_at` goes stale for as
  long as a machine sits below floor. Cosmetic; same reason.

---

## A23 RECIPE 2 — WORDPRESS (implementation; rig/ISO battery deferred)

Second packaged recipe, on the format recipe 1 (SMF) proved,
in poc/recipes-wordpress/ (VM-local acceptance; the GCP rig is
still unreachable, so the ISO rebuild + rig battery for
everything since prod rebuild 2 remains owed, this slice
included). Recipe 2 also generalised the machinery in three
places future recipes inherit, and its acceptance found and
fixed three real defects — one of them in Gate 4's updater,
one in slice 5B's backup, and one in the recipe overlay seam
that recipe 1 shared.

### The recipe

`onionhost/recipes/wordpress/`, its own signed package
`onionhost-recipe-wordpress`, version scheme `<WP>+oh.N`,
floor `7.1.3+oh.1` in recipes/wordpress/floor.txt (floors stay
decoupled from the platform's, as with SMF). Manifest:
runtime php, db required, prefix `wp_`, data_dirs
[wp-content/uploads], config = wp-config.php rendered from the
archive's own wp-config-sample.php.

WordPress is 7.1.3 (the version wordpress.org's version-check
API named current). Archive provenance, verified two
independent ways — stronger than SMF's, because wordpress.org
publishes per-file checksums: (1) every file the official
checksum API (api.wordpress.org/core/checksums/1.0) covers —
3,782 of 3,782 — matches the API's published MD5; (2) a
second-source download of the GitHub mirror tag
(WordPress/WordPress) is byte-identical on all 3,735 files
the two sources share; the differences are packaging only
(the mirror carries legacy bundled themes the release zip no
longer ships and lacks Akismet's built assets). Zip sha256
eb58a90ed55147f90f7bd55d0d3334960a69b7e8a4cc142c8ddfea8965218227.

Sealed posture (rendered config + a must-use plugin the
recipe maintains, files/wp-content/mu-plugins/
onionhost-sealed.php): WP_HTTP_BLOCK_EXTERNAL=true with no
whitelist; AUTOMATIC_UPDATER_DISABLED + WP_AUTO_UPDATE_CORE
false; DISALLOW_FILE_EDIT=true; the update transients
answered "checked just now, nothing new" by filter (no dead
nags, and the version-check cron finds them fresh and skips
its phone-home); Gravatar off by filter (avatar_default =
blank, any gravatar.com avatar URL replaced with the local
blank.gif — Gravatar is a VISITOR-side fetch, the leak is the
URL in the page); core emoji scripts removed (they load from
s.w.org in visitors' browsers); XML-RPC denied at nginx;
self-registration seeded closed once via an ordinary option
(WordPress registration completes by emailed password-set
link, which can never arrive sealed; owner-overridable).

### Seeding decision — route (a): drive the real installer

WordPress has no static install SQL: its schema and default
options live in PHP (wp-admin/install.php, schema.php,
populate_options). Route (b) — replicating the installer's
database writes in SQL, SMF-style — would bake a brittle
per-version copy of that PHP behaviour into the recipe, and
its password would need a host-side hash WordPress accepts
(the host has no PHP). Route (a) drives WordPress's OWN
installer over the edge socket during publish. It is the
route this venue can prove (the slice-6 gate round drove
SMF's web installer the same way), it uses the application's
own schema/defaults code at every version, and as a bonus
the administrator password is hashed by WordPress itself —
the database shows `$wp$2y$12$...` (WP 7.x's prefixed
bcrypt) from birth. There is no legacy hash anywhere in
this recipe and no first-login upgrade to verify; the
brief's hash question is answered by making it moot.

Implementation, all general (nothing WordPress-specific in
the platform code beyond manifest data):

- The applier (`onionhost-recipe`) gained: manifest-driven
  config file/carryover/template names (SMF's Settings.php
  defaults preserved), a `wp-config` config renderer
  (per-install DB credentials from app-db.env, the manifest
  prefix, eight 64-char salts from the host CSPRNG — never
  in the package), optional seed SQL (hook recipes have
  none), `extra_files` payload placement (the mu-plugin),
  `exclude_paths`/`install_files` tree exclusions, data_dirs
  ensured to exist in staging (the WP zip ships no
  wp-content/uploads/ — found by the unit test), and the
  **install hook**: `onionhost-recipe install-hook <id>`,
  driven by a manifest `install` stanza (http-form type:
  probe path, form marker, installed marker, form path +
  field templates, success marker, advisory home marker).
  The hook probes until the installer answers usefully,
  recognises "already installed" (a retry, or a restored
  machine whose database came back with it) and finishes
  WITHOUT re-seeding, refuses to invent credentials when the
  staged admin env is missing, and on success removes the
  install_files from the served tree, marks the recipe
  seeded, and shreds the staged env. First-install judgement
  for hook recipes is the state record (the DB is the ground
  truth but is not host-readable); the restore case
  self-heals through the probe, proven in scenario 4.
- `onionhost-publish` runs the hook after the edge socket
  appears on recipe publishes; a hook failure fails the
  publish (the site is up but not "live" until installed),
  and retrying is safe because the hook is idempotent.
- Seeded-state preservation fix in the applier: an update
  apply previously rewrote state with seeded=False (the
  seed block only runs on first install); for hook recipes
  `seeded` is now carried from the state record. (SMF's
  behaviour is unchanged in effect; its 32 unit checks pass
  unchanged.)
- wizard-helper recipe-setup accepts an optional 4th stdin
  line (site title → RECIPE_SITE_TITLE) for installers that
  ask for one; the wizard's app page now enumerates
  /usr/share/onionhost/recipes/*/manifest.json instead of
  hard-coding SMF (labels and the administrator note come
  from the manifest; runtime forced from it too), and Go
  Live passes the model's title as the 4th line.
- build-recipe-deb.sh copies optional payload dirs
  (overlay/, seed/, files/) when present.

Plain permalinks only: the golden nginx app config answers
`location /` with try_files to files on disk, so WP pretty
permalinks cannot resolve; WordPress ships with plain
permalinks as its own default and the REST API answers in
its plain `?rest_route=` form (the form WP's own Link header
advertises). Recorded in APP-SITES.md; teaching the golden
template an index.php fallback for app sites is future
platform work, flagged not made. WP-Cron likewise cannot
fire sealed (its loopback spawn targets the site's own
onion URL, unreachable from inside the container): scheduled
posts sit past their time until published by hand; nothing
else depends on those runs here. Documented, not hacked.

### Findings (all fixed in this slice unless noted)

1. **The recipe nginx-overlay seam could not deny PHP.**
   nginx evaluates regex locations in file order, first
   match wins — and the golden config's `location ~ \.php$`
   precedes the recipe include, so a recipe's regex deny
   for upload directories is never reached. Proven both
   ways in the sandbox: with the first WP overlay draft
   (a regex deny copied from SMF's shape), a .php placed in
   wp-content/uploads/ EXECUTED (response body was the
   script's output). With a prefix location
   (`location ^~ /wp-content/uploads/ { try_files $uri =404; }`
   — prefix locations are selected before regexes), the
   same file is served as inert source text and everything
   else still works. **SMF's shipped overlay used the regex
   form and its acceptance never runtime-tested it**: the
   flaw was latent in recipe 1. Both overlays now use ^~
   prefix locations; the SMF tree fix awaits its next
   package build, and SMF runtime re-verification joins the
   deferred battery (the mechanism is proven against the
   identical golden template). A caution the log should
   keep: the first failing check greped the response for
   the script's marker string, which appears in the SOURCE
   too — execution vs source-serving is only distinguishable
   by reading the body, which is now the standing method.
2. **Gate 4's updater could undo its own rollback.** The
   managed phase rolled a sabotaged recipe back correctly —
   and the same run's Debian-base phase then ran an
   unqualified `apt-get upgrade` over all sources (project
   repo included) and re-installed the sabotage; the site
   was left serving HTTP 500 on the version that had just
   failed its health check. SMF's messier S3 arc masked this
   (it ended fail-closed with the gateway off). Fix in
   onionhost-update: the managed set is held
   (`apt-mark hold`) across the Debian phase and unheld
   after it, and the managed phase unholds defensively on
   entry so a leaked hold cannot wedge the next run. The
   gate4fix suites still pass (22/22 + dashboard set), and
   scenario 3 below was re-run end-to-end against the fix.
3. **Slice 5B's backup audit refused WordPress outright.**
   The forbidden-path check matched raw substrings, and WP
   core ships wp-includes/block-supports/shadow.php and an
   icon named shadow.svg — "shadow" is a marker (for
   /etc/shadow), so ANY WordPress backup failed on the
   spot. Fix in onionhost-backup: markers match whole path
   components, plus dotted prefixes for the versioned
   system shapes (initrd.img-*, crypto_keyfile.*); a
   14-case check of the rule passes, and the backup then
   completed. The audit still fails closed on the real
   shapes (a component exactly "shadow", "root.key",
   "luks-roles", "cryptsetup-keys", ...).
4. Minor: the oh.2 sandbox package's intended mu-plugin
   marker change missed (the target phrase spans a line
   break in the source), so oh.2's payload equals oh.1's and
   the update was version-only. The update mechanics under
   test do not depend on payload delta; recorded for
   accuracy.

### Acceptance (poc/recipes-wordpress/, Gate 4-shaped sandbox)

Unit checks: poc/recipes-wordpress/unit-test.py **39/39**
(renderer correctness incl. disjoint salt sets across
installs, carryover, exclusions, hook against a fake
installer incl. already-installed + rejection + no-admin
paths); SMF regression 32/32 on the generalised applier.

- **S1 fresh WordPress site, no owner file-drop: PASS.**
  Baseline dpkg (platform 1.0.0 + recipe oh.1) → sitegen
  model (recipe=wordpress) → recipe-setup (4 lines, env
  0400) → publish: APP_PROVISION_OK → RECIPE_APPLY_OK
  first_install=yes seeded=no → INSTALL_HOOK_OK
  via=installed → PUBLISH_OK, ~26 s. Verified: admin env
  shredded; install.php/upgrade.php absent from the served
  tree; wp-config.php 0660; wp_users hash `$wp$2y$12$`;
  blog_public=0; blogname = the staged title; siteurl =
  http://f27ttt5v3wyekchjp7sqhdm37yct5zm4zwsksl2ijwcu3rrr7qkcytqd.onion;
  admin login works; a post published via the REST API
  (rest_route form) and read by a guest; an image uploaded
  through the REST media endpoint landed in
  wp-content/uploads/2026/10/ and was fetched back
  byte-identical; a .php in uploads NOT executed (after
  finding 1's fix; image + front page still 200;
  /xmlrpc.php 403). External-HTTP block verified from
  inside the app: a temporary bootstrap page calling
  wp_remote_get on api.wordpress.org (https) and
  wordpress.org (http) got WP_Error
  `http_request_not_executed` in 0.00 s both times — the
  request dies in WP's HTTP layer before any socket
  exists; the same page showed avatar_default=blank, a
  local blank.gif avatar URL, users_can_register=0, and a
  neutral update_core transient (0 updates,
  version_checked=7.1.3). Page deleted afterwards.
- **S2 recipe update oh.1 → oh.2 via Gate 4: PASS, clean.**
  Baseline run first: both managed packages current,
  status up-to-date (and real Debian packages configured in
  place over Tor in the same run). After publishing repo
  v2: the updater fetched oh.2 over Tor, verified the floor
  from the signed package, saved a rollback copy of oh.1,
  installed (postinst RECIPE_APPLY_OK first_install=no
  seeded=yes), restarted, and its health check over the
  real Tor path returned the WordPress front page; run
  exit 0, high-water advanced to oh.2. Post + upload +
  front page verified after.
- **S3 sabotage rollback: PASS after finding 2's fix.**
  First run (pre-fix updater): oh.3 health check FAILED at
  ~90 s (empty body from the corrupted index.php),
  rollback to oh.2 applied and re-probed healthy — then
  the Debian phase re-upgraded to oh.3 and the site sat at
  500 (finding 2). With the fixed updater, the full arc
  re-ran: oh.3 installed, health FAILED, rollback to oh.2,
  and the Debian phase logged the managed set held +
  "kept back" + unheld; final state front=200 on oh.2, no
  holds left, run exit 4 (rolled back), post intact.
- **S4 backup/restore format 2: PASS.** Backup via
  onionhost-backup: BACKUP_OK, 35,543,040 bytes (after
  finding 3's fix; the first attempt was the refusal that
  exposed it). Machine 2 (second fixture instance, own
  disk phrase, own onion a4syvbku...) restored with
  machine 1's phrase: "The backup opened and checks out:
  'Notes from the Test Kitchen' (f27ttt5v...onion)", rc=0.
  After restart: site live at MACHINE 1's onion with the
  post, the upload (200), and the admin login all working;
  a fresh post published on machine 2 at the same onion.
  The recipe self-heal also proven there: machine 2 had no
  recipe state, so apply judged first_install=yes and the
  hook finished `via=already-installed` — no re-seed, no
  staged admin needed, installer file cleaned again,
  posts untouched.

### Deferred (explicit)

- ISO rebuild + rig battery for slices 6B, Gate 4, recipes
  1–2 (rig unreachable since 2026-10-13; includes real-Tor
  descriptor republication vs probe-envelope measurement —
  note S2's probe passed comfortably here while S3's
  health verdict took ~4 min to conclude, more data for
  that open question).
- SMF overlay ^~ fix: in the tree; runtime re-verification
  with its next package build / the rig battery.
- Wizard GUI battery for the generalised app page
  (enumerated recipes, per-recipe admin notes) — code
  reviewed + compiled, not yet driven on a desktop.
- WordPress version-bump recipes (DB upgrade path) and
  pretty permalinks (golden-template location / change):
  future platform/recipe work, as recorded above.
- WP-Cron firing sealed: a platform app-init cron hook is
  the honest shape if scheduled posts are ever promised;
  not built here.


## A23 RECIPES 3+4 — DOKUWIKI + GITEA (implementation; rig/ISO battery deferred)

Slice 3 of the A23 recipe programme: the last two first-wave
recipes, proving the two shapes recipes 1–2 did not — a
**flat-file PHP app with no database** (DokuWiki) and the
platform's **first native-binary recipe** (Gitea). Same
sandbox-harness pattern as slices 1–2 (records and evidence
under `poc/recipes-dokuwiki/`, `poc/recipes-gitea/`); both
recipes ride the Gate 4 channel as their own packages with
their own floors; all findings below are VM-local, the
rig/ISO battery remaining deferred as a whole. APP-SITES.md
gained both owner contracts plus a recipe-author appendix
documenting the manifest surface below.

### Platform generalisations (both recipes)

Written for the shapes, regression-proven against recipes
1–2 (SMF 32/32, WP 39/39, Gate-4-fix suites 0 failures, all
re-run at slice end-state):

1. **No-DB PHP + native DB modes.** `onionhost-app-provision
   --db {required,none}` (default: required for php, none for
   native); the app-site marker records `db=...`;
   `onionhost-publish` derives the mode from the recipe
   manifest (`db.required`, and non-php is always "none";
   an unreadable manifest fails safe to "required").
   `onionhost-generate-configs` appends `ONIONHOST_APP_DB`
   to `app-runtime.env`; the golden app-init starts MariaDB
   **only when a database is required** (log line "this
   site has no application database; MariaDB not started").
   A no-DB provision writes no `app-db.env` and demands
   none. Backup decides dump-vs-cold-copy from the recipe
   manifest; restore writes the marker's db line from what
   the backup actually carried.
2. **Cold copies widened.** Format-2 backup now takes the
   app tree COLD (container stopped) for native sites **or**
   PHP sites whose recipe declares no database — for a
   flat-file app the files are the database, so the
   native handling *was* the right handling; it is now keyed
   on "no external database" rather than "native".
3. **Config renderer `"none"`.** A recipe whose state lives
   entirely in `data_dirs` renders no config file and needs
   no db credentials; the applier's apply path treats
   renderer-none recipes as render-free (SMF/WP paths
   unchanged).
4. **Tar archives** (`archive.format: "tar"`, extracted with
   the `data` filter): DokuWiki's tarball carries unix
   permissions a zip would lose. Root-dir detection shared
   with the zip path.
5. **`extra_files` with `"after_data": true`**: payload
   files placed *after* the data_dirs carryover, so
   recipe-maintained files living *inside* a data dir are
   refreshed on every apply while owner files carry over
   (DokuWiki's protected configs). Placement, config render
   and overlay copy share helpers between apply/rollback.
6. **`install_files`**: manifest-named installer files may
   ride into staging on the FIRST install only (the http-form
   hook needs the real installer present); update applies
   keep excluding them via `exclude_paths`, and the hook's
   finish step removes them from the live tree.
7. **Native recipe support in `onionhost-recipe`**
   (`apply_native`): `archive.format: "file"` — one binary,
   sha-verified, staged as `.app.new` → fsync → chmod 0755
   → rename over `native/app`, old binary kept at
   `.app-prev`; rollback swaps back and keeps the broken
   one at `.app-broken` (the rollback subcommand gained a
   native branch). `native_files` staged with octal modes.
   `native_config {src,dst}` rendered FIRST install only —
   judged by the config file's own presence, like
   `config_file` — with `{onion}`, `{site_title}`,
   `{secret_key}`, `{internal_token}` substituted and any
   leftover token a hard error; written 0640.
8. **First-boot admin creation for native recipes**
   (generalises the install hook): manifest `first_boot:
   true`. First install copies the wizard-staged admin env
   into the volume as `native/.recipe-admin.env` (0400,
   treated as DATA, never executed). The golden app-init
   runs the recipe's `native/first-boot.sh` before starting
   the app whenever `.first-boot-done` is absent; the script
   creates the admin with the app's own CLI, shreds its env
   copy, writes `.first-boot-done`. `onionhost-publish`
   then runs `onionhost-recipe await-first-boot <id>`:
   polls for the marker (default 240 s), shreds the
   host-side staged env on success; on timeout the publish
   FAILS with the env still staged for retry — never
   half-consumed. A native apply refuses BEFORE changing
   anything when no admin is staged.
9. **Recipe-admin staging shared**: the wizard-helper
   `recipe-setup` env file is now also the native
   first-boot source; one `_staged_admin()` reader in the
   applier serves hook, seed and native paths. The
   manifest's `default_title` moved to manifest level for
   hook titles (SMF/WP manifests set it; behaviour
   unchanged).
10. **Sabotage builds generalised** in
    `build-recipe-deb.sh` by archive kind (native "file":
    the staged binary's first bytes XOR-scrambled;
    tar: a listed file corrupted inside a re-made tar; zip:
    the slice-2 path). The builder re-seals the manifest
    checksum from the STAGED archive, so sabotage packages
    stay self-consistent and fail only at health time, as
    designed.
11. **App image gains `git`** (`build-iso.sh` IMG_APP): a
    native app may hard-require a system tool the way
    Gitea hard-requires git (see below); inert sealed.
12. **Native apps get a home**: the golden app-init's
    native branch exports `HOME=$DATA/native/home` (on the
    volume, so it rides backups). The init's own HOME is
    root's, and a www-data app writing under $HOME died on
    it (Gitea's startup SSH-key sync, below). PHP branch
    unchanged.

Two in-slice pre-release rebuilds, recorded for honesty:
the sandbox platform `onionhost_1.0.0` package was rebuilt
once mid-slice after fix 12 (same version, corrected
payload; Gate-4-era slices did the same), and the Gitea
oh.1 below was rebuilt once after the first-boot migration
fix. Neither had shipped anywhere.

### Recipe 3 — DokuWiki 2026-07-14c (flat-file PHP)

`onionhost/recipes/dokuwiki/` — runtime php, db **none**,
`data_dirs [data, conf]`, config renderer "none",
`config_carryover` the four owner config files, install
hook http-form driving `install.php`.

- **Provenance (stronger than SMF's, equal to WP's)**:
  official tarball from download.dokuwiki.org,
  sha256 `7e9b4dcb…d183176`; the GitHub release asset for
  tag `release-2026-07-14c` is **byte-identical** (same
  sha256; extracted trees `diff -r` clean).
- **The admin-hash question, decided from the source**:
  DokuWiki's default passcrypt is bcrypt, but authplain's
  `checkPass` only *verifies* — there is NO
  rehash-on-login, so a host-seeded legacy hash would stay
  weak forever (SMF's upgrade-on-login rescue does not
  exist here). The recipe therefore **drives install.php**
  through the http-form hook: bcrypt from birth, verified
  live (`$2y$12$` in the seeded users file). No seed SQL
  at all (a `seed/README.txt` records why).
- **The registration posture is the installer's own**:
  the hook deliberately OMITS the allow-registration
  field, so the installer itself writes
  `disableactions = 'register'` into the owner's
  `local.php` — an ordinary owner-overridable option,
  exactly the WP posture, produced without recipe code.
  Policy fields chosen: ACL on, public-read (policy 1).
  The popularity field is never sent (no phone-home by
  construction).
- **Sealed pins** ride as protected configs placed
  after_data: `conf/local.protected.php` (updatecheck=0,
  fetchsize=0, remote=0) and `conf/plugins.protected.php`
  (extension manager and popularity plugin disabled).
  Nginx overlay denies `/data/`, `/conf/`, `/inc/`,
  `/bin/`, `/vendor/` via `^~` (media/pages are served by
  the app through its own scripts). Upload-dir PHP-off is
  structural here: uploaded media lives in `data/media`,
  inside the denied tree. Normalize-exceptions keep
  `users.auth.php` and `local.php` at 0660.
- **Unit checks 37/37** (`poc/recipes-dokuwiki/unit-test.py`):
  tar extraction, manifest markers cross-checked against
  the REAL installer + lang file, renderer-none apply with
  no app-db.env anywhere, first-install staging includes
  install.php while update excludes it, after_data refresh,
  carryover, checksum refusal, the hook against a fake
  installer (fields incl. NO allowreg; users file tightened
  to 0660 by the hook-finish mode pass), oh.1→oh.2 delta.
- **Sandbox acceptance PASS** (`poc/recipes-dokuwiki/`):
  fresh site via recipe, NO file drop: publish →
  `APP_PROVISION_OK runtime=php db=none` → hook
  `INSTALL_HOOK_OK via=installed` → PUBLISH_OK. Verified:
  bcrypt admin, installer's own register-off line,
  install.php removed, staged env shredded, protected
  configs live, **no MariaDB process anywhere on either
  machine**. Drive over the edge socket: front 200; 403
  on data/conf/inc paths; registration page shows the
  disabled posture; admin login; page created + guest-read
  with marker; media upload returns byte-identical through
  fetch.php; a .php "upload" refused by the app itself AND
  403 direct. **Probe over real Tor: PROBE_OK.**
- **Finding — the root-redirect shape**: at `/`, the golden
  template hands the app `id=/` and DokuWiki canonically
  302s to its start page — browsers fine, but the platform
  health contract (updater + Dashboard) requires 200 at
  the probe path, so every DokuWiki update would have
  misjudged a healthy site. The recipe's overlay rewrites
  exactly `/` to the start page (delivered as oh.2, a real
  functional delta). The general contract question is
  deferred (list below).
- **Update oh.1→oh.2** via the Gate 4 channel: "updated
  to 2026-07-14c+oh.2 and healthy", whole run exit 0
  including the Debian phase; content + admin intact.
- **Sabotage oh.3** (archive's index.php corrupted):
  health check failed, **rolled back to oh.2**, updater
  exit 4; dpkg + recipe version back on oh.2, page live.
- **Backup/restore format 2 PASS**: payload decrypted
  in-machine — www tree present, ZERO database artifacts
  (flat-file cold copy as designed); machine 2 restored
  with machine 1's phrase → **same onion**, marker
  `runtime=php db=none`, page + image + admin login all
  verified on the restore.

### Recipe 4 — Gitea 1.27.3 (native binary)

`onionhost/recipes/gitea/` — runtime native, db **none**
(SQLite is the app's own), `native_config` from
`seed/app.ini.tmpl`, `first_boot: true`, native package
architecture `amd64` (tree recipes stay `all`; the builder
now derives it).

- **Provenance (strongest of the four)**: binary sha256
  `4da93c2c…c12d971` agrees THREE ways — the publisher's
  .sha256 file, the dl.gitea.com binary, and the GitHub
  release asset — and the .sha256 file's **GPG signature
  verified good** (Teabot <teabot@gitea.io>, fingerprint
  CC64B1DB…329753F4B0). Raw binary 126,007,248 bytes; the
  recipe package compresses to ~38.2 MB.
- **app.ini from the source of truth** (the release's
  app.example.ini + the binary's own help): unix-socket
  serving is `[server] PROTOCOL = http+unix` +
  `HTTP_ADDR = /run/app.sock` (the design note's guessed
  http+path form is not the real config). ROOT_URL is the
  onion; DOMAIN the onion; SSH off (DISABLE_SSH + no
  SSH_DOMAIN/PORT advertised — SSH git is not offered in
  this design, APP-SITES.md says so); mailer disabled;
  `[mirror] ENABLED = false` (kills mirror creation
  outright); webhooks left configurable but documented
  undeliverable (no block-all value exists for
  ALLOWED_HOST_LIST; they fail sealed, as owners are
  told); registration DISABLE_REGISTRATION=true (verified
  live in the app's own words on the sign-up page);
  INSTALL_LOCK=true; secrets generated per install.
- **Gravatar, measured rather than assumed**: 1.27
  DEPRECATED `DISABLE_GRAVATAR` (moved to admin-panel
  config; the ini line is inert and logs a deprecation
  warning). Measured on the fresh install: avatars are
  fully local — identicon-style PNGs generated and served
  by Gitea itself, no gravatar.com reference in any page
  or response. The ini line stays (binds on versions that
  honour it); the posture rests on the measurement, and
  the admin panel is the owner's lever. Recorded in
  APP-SITES.md in measured terms.
- **The failure ladder** (each rung fixed at its own
  layer; the interesting ones are platform facts):
  1. `gitea admin user create` does NOT migrate the
     database — against a fresh file it fails "no such
     table: user". First-boot must run `gitea migrate`
     first (idempotent). Recipe fix; oh.1 rebuilt.
  2. Gitea REFUSES to run as root (deliberate upstream
     guard). The sandbox rootfs aliases www-data to uid 0
     (venue quirk); un-aliased there. Production unaffected
     (the app already runs as www-data).
  3. Gitea FATALs at startup without a **git binary** in
     PATH. Platform fix 11 above.
  4. Gitea FATALs writing `$HOME/.ssh` at startup with
     HOME=/root under a www-data process. Platform fix 12.
  First-boot then ran the whole chain clean — migrate →
  admin create → marker → env shredded on both sides.
- **Unit checks 27/27** (`poc/recipes-gitea/unit-test.py`):
  binary staging + `.app-prev` rotation, app.ini rendered
  ONCE (secrets differ across installs; second apply
  byte-identical), first-boot env staged first-install
  only, refusal without a staged admin changing nothing,
  `await-first-boot` success (marker → env shredded) and
  timeout (env preserved), native rollback.
- **Sandbox acceptance PASS** (`poc/recipes-gitea/`):
  publish → `APP_PROVISION_OK runtime=native db=none` →
  apply → **FIRST_BOOT_OK** → PUBLISH_OK. Drive over the
  edge socket: front 200; registration page states
  registration is disabled; admin login; repository
  created WITH server-side git (README listed); **git
  clone/commit/push over HTTP through the socket path**
  (a real push, `HEAD -> main`); public repo + pushed
  file readable anonymously; second admin-created user
  signs in. **Probe over real Tor: PROBE_OK, HTTP 200.**
- **Update oh.1→oh.2** (proof-bytes marker binary):
  fetched over the signed channel, floor verified,
  rollback copy saved, **"updated to 1.27.3+oh.2 and
  healthy"**; byte-level verified — live binary is the
  oh.2 build, `.app-prev` is the PRISTINE upstream sha;
  repo, pushed file and both logins intact. (Two earlier
  runs exited 3 "fetch failed" during a measured sick
  Tor window — the updater's designed pause; the site
  was untouched, as designed.)
- **Venue loss + rebuild**: a runtime event stopped the
  first acceptance machine mid-updater (its writable
  layer is per-container and was lost, as it also stopped
  the WordPress slice's machines — no data of theirs was
  touched by this slice). The machine was rebuilt from
  the staged rootfs; with all fixes baked into the
  packages it published cleanly first time
  (FIRST_BOOT_OK on the first gateway-up publish), the
  full drive re-passed, and the oh.2 update re-verified
  healthy with repos intact. Sabotage + backup/restore
  were then completed on the rebuilt machine (below).

- **Sabotage oh.3 → rollback → fail-closed → recovery**
  (the full Gate 4 arc, on the rebuilt machine): oh.3's
  scrambled-ELF binary failed its health check exactly as
  designed; the updater rolled back to oh.2 (dpkg and the
  live binary byte-identical to the oh.2 build, broken
  binary kept at `.app-broken`). The post-rollback probe
  then ALSO missed its envelope — descriptor republication
  in this venue window exceeded two consecutive loops —
  so the updater **failed closed**: marker written with
  installed oh.2 / floor oh.1, the designed Dashboard
  status text, stack stopped. Recorded plainly: the
  rollback mechanism passed; the second probe verdict is
  the standing venue-timing casualty (the rig battery's
  republication measurement exists precisely to size the
  production envelope). Recovery then exercised the
  designed branch end-to-end: with the repo returned to
  oh.2-as-best, a later updater run restarted the stack
  on the installed version, health-checked it —
  **"recovery healthy - site is back"** — and cleared
  the marker (final status "up-to-date"). Two operational
  notes: (a) the recovery fetch rides container U, which
  production's fail-closed deliberately does NOT stop (it
  stops the gateway and the app); the harness's single
  stackctl stops everything, so U was restarted by hand
  for the recovery runs — a harness infidelity, not a
  product gap; (b) three recovery attempts first exited 3
  "fetch failed while failed closed" during a measured
  Tor-weather window (repo-service guard reporting ~50%
  circuit timeouts) — the fail-closed state stood
  untouched through all of them, as designed, until the
  fourth attempt's window let it through.
- **Backup/restore format 2 PASS**: payload audit
  (decrypted in-machine with the product's own key
  derivation) — `app/native` tree incl. the binary,
  `data/gitea.db`, the rendered app.ini, the git
  repositories, and `.first-boot-done`; ZERO database-dump
  or credentials entries (native cold copy). Machine 2
  (baseline = platform + recipe oh.2) restored with
  machine 1's phrase, rc=0 → **same onion**, marker
  `runtime=native db=none`, zero MariaDB, repository +
  pushed file readable anonymously, **both** the admin
  and the second user signing in — and no admin staging
  needed on machine 2, because `.first-boot-done` rode
  the backup and the accounts live in the restored DB.
- **Size note for the ISO budget**: the Gitea recipe
  package is ~38.2 MB compressed (126 MB raw binary) —
  the largest recipe package so far (SMF/WP/DokuWiki are
  tree recipes of a few MB); four recipes together do not
  threaten the ISO budget, but a future recipe wave
  should keep counting.

### Deferred (cumulative — rig/ISO battery and follow-ups)

Everything from slices 6B, Gate 4, the stickiness fix and
recipes 1–2 remains deferred as recorded there; slice 3
adds or sharpens:

- **ISO rebuild + full rig battery** for 6B + Gate 4 +
  recipes 1–4 (real-Tor installs of all four recipes,
  main-archive-over-Tor fetch proof, true-time repo
  signing, **republication-vs-probe-envelope measurement**
  — now the single most-evidenced open risk: this slice
  alone hit the envelope three times), SMF official
  package checksum, wizard GUI battery for the
  manifest-enumerated app page.
- **SMF overlay ^~ runtime re-verification** (from slice
  2; still owed — WP, DokuWiki and Gitea overlays were
  runtime-proven here, SMF's was not re-run).
- **The health contract's probe path**: DokuWiki's root
  302 shape was fixed recipe-locally (exact-`/` rewrite);
  whether "200 at the site's root" is the right universal
  health contract — vs a per-recipe probe path in the
  manifest — deserves one platform look before more
  recipes land.
- **Recipe DB-migration story**: Gitea migrates its
  database at server start on version change; this recipe
  is patch-level only. A major-version recipe needs a
  designed migration step (backup-first, health-gated,
  rollback-on-failure across a migrated DB is NOT the
  current binary-swap semantics). Same question will meet
  SMF/WP major versions; answer it once, generally.
- **Gitea gravatar posture** rests on the measured 1.27
  local-avatar behaviour; re-measure on the next Gitea
  recipe bump (the ini switch is deprecated upstream).
- WP pretty permalinks + WP-Cron platform hook (from
  slice 2, unchanged).


# RIG BATTERY — DYNAMIC TIER + RECIPES (2026-10-14)

VERDICTS: Part 1 ISO rebuild PASS (build #3; builds #1/#2 failed —
see below). Part 2 install + forum FAIL as shipped (recipe seeding
defects D1–D3) / PASS after in-guest workarounds. Part 3 update
pipeline PASS (fail-closed machinery behaved exactly as designed
through two defect-driven rollbacks; run 3 clean; reboot proof
complete). Part 4 republication PARTIAL PASS (median 91 s, one
324 s outlier — envelope tail risk measured). Part 5 recipes:
Gitea FAIL as shipped (D4–D6) / PASS after workarounds incl.
git-over-Tor; WordPress PASS (D2 caveat); DokuWiki PASS (D1
caveat). Part 6 platform checks PASS. Part 7 teardown done.
Part 8 rig poweroff done (see the end of this section).
The battery ISO was NOT published anywhere.

Venue: GCP rig onion-rig-1 (n2-standard-4, us-west3-a), reinstated after
appeal 2026-10-14. Appeal commitment honoured throughout: ordinary CPU
load only — no load generation, no PoW calibration re-runs, no circuit
floods. All measurements below are functional, at product defaults.

## Pre-battery integration work (workspace tree)
- **Factory-package registration gap (found by pre-flight inspection,
  fixed before the build):** build-iso.sh never registered the platform
  or recipe packages in an installed system's dpkg database — Gate 4's
  proof had hand-installed factory v1.0.0 on its test box. Without it a
  real install has no updater factory version and the wizard (which
  offers exactly the recipes whose files are installed) shows no recipe
  choices. Fix: build-iso.sh now builds onionhost_1.0.0 + all four
  recipe debs into the image at /usr/lib/onionhost/factory-packages/
  (sha256s recorded in BUILD-INFO), and the onionhostfirstrun Calamares
  module dpkg-installs them into the target during install (fails the
  install loudly if it cannot — fail-closed style). build-onionhost-deb.sh
  gained an OH_OVERLAY override so it can run outside the workspace path.
- Rig disk hygiene before the builds: removed ~70G of regenerable older
  build trees (iso-build*, slice2/3/4, step3-test after preserving its
  OVMF_VARS.fd, prod-verify, prod-audit, calabuild, prod-smoke, the
  slice-3-era ISO, onionhost-src-new/tmp). Disk 87% used -> 15% used.
- Tree sync to the rig byte-verified with rsync -rc (zero content diffs
  both trees after fixing three skipped symlinks).

## PART 1 — ISO REBUILD
- Build #1 FAILED — genuine integration bug (see below), fixed.
- Build #2 PASS (but see the boot defect found in Part 2 — build #2's
  installs do not boot; the ISO was never published).
  ISO: 1,361,817,600 bytes, sha256
  0b4df12c3aa24a2cb31a6f225c08039b6ba8511716420e0555d597af096bd786.
- **Bug A (build-time, fixed):** Gate 4's shipped apt lockdown
  (Dir::Bin::Methods::http/https "false" in
  52onionhost-tor-updates) also disables apt inside the ISO build's own
  customize step, which installs from the https snapshot: 19x
  "The method 'https' is explicitly disabled". No ISO had been built
  since Gate 4 landed, so this was latent. Fix: the three build-time
  apt-get install lines in build-iso.sh pass
  -o Dir::Bin::Methods::http=http -o Dir::Bin::Methods::https=https;
  the shipped image's lockdown is untouched (verified in the rootfs).
- In-image verifications (build #2 rootfs, all PASS): all 5 factory debs
  planted with BUILD-INFO sha256s; image tars present (app 665,495,040 B
  incl. git; tor 87,549,440 B; web 90,549,760 B); onionhost-update,
  -probe, -recipe, usr/lib/apt/methods/tor+http present; lockdown config
  intact; golden torrc carries PoW defences (rate 5 / burst 10),
  MaxStreams 50 + close-circuit; partition module.so sha256 matches
  BUILD-INFO; firstrun contains the factory-install code; wordlist 7776
  lines; NO test scaffolding in the prod rootfs (no sshd, no xdotool,
  no authorized_keys); live user has a random per-build password.

## PART 6 (pulled forward) — SMF OFFICIAL CHECKSUM ATTEMPT
- From the rig, download.simplemachines.org returns HTTP 403 three ways
  (HEAD /, direct smf_2-1-7_install.zip GET, and with a Firefox UA) —
  Cloudflare bot-wall from the rig too. VERDICT: the official-package
  checksum remains unverifiable from every venue available to us; the
  Recipe 1 provenance (GitHub release archive + second-source tree
  comparison, contents identical) stands as the best available.

## PART 2 — INSTALL + FORUM (first attempt on build #2: DEFECT FOUND)
- Fresh UEFI install from build #2 ISO completed cleanly end-to-end
  (forced-encryption guard, generated phrase flow, factory debs
  installed by firstrun). Disk phrase flow, LUKS2 plan, GRUB phrase
  prompt all as designed.
- **DEFECT (release-blocking): the installed system DOES NOT BOOT.**
  GRUB accepts the phrase ("Slot 2 opened"), then the initramfs loops
  forever: `cat: /etc/cryptsetup-keys.d/root.key: No such file or
  directory` / `cryptsetup failed, bad password or options?` /
  "maximum number of tries exceeded", repeating. Root cause, fully
  traced (see below): the root keyfile is present in the installed
  rootfs (0400, relocated correctly by onionhostcleanup, crypttab
  correct) but ABSENT from the initramfs, because the initramfs hooks
  were overwritten at mode 0644 during the install and
  update-initramfs silently skips non-executable hooks.
- **Root cause — build-onionhost-deb.sh mode flattening:** the package
  builder staged the overlay, then ran
  `find $STAGE -type f -exec chmod 644 {} +` and restored 755 ONLY for
  usr/local/bin/* and usr/lib/apt/methods/*. The only other executables
  in the overlay are the two initramfs hooks
  (etc/initramfs-tools/hooks/zz-onionhost-cryptsetup — the A18
  --disable-keyring wrapper — and zz-onionhost-keyfile — the keyfile
  embedder). Both shipped at 644 in every platform .deb built since
  Gate 4. Two consequences:
  (a) THIS battery: firstrun's new factory dpkg -i wrote the 644 hooks
      over the image-planted 755 ones BEFORE Calamares' initramfs job
      built the image -> keyfile-less initramfs -> unbootable install.
  (b) LATENT, worse: on any machine that takes a platform update via
      the Gate 4 channel, the hooks on disk become 644. The running
      initramfs is unaffected, but the NEXT initramfs rebuild (e.g. a
      routine Debian kernel security update) silently produces an
      initramfs without the keyfile and without the A18 wrapper ->
      bricked box + silent loss of the A18 property. Gate 4's proof
      never rebuilt an initramfs after an update, so it passed.
  Blast radius audit: the two hooks are the ONLY executables outside
  the two restored dirs; recipe .debs flatten only their data payload
  (correct at 644; no executables shipped). No field machines have
  taken a platform update (the update repo has only ever served proof
  rigs), so no user machine is affected.
- **Fix (build-onionhost-deb.sh):** after the flatten, restore +x for
  every staged file whose source-overlay counterpart carries any
  execute bit (derived from the source tree, not a hardcoded list), and
  a build-time MODE GUARD that fails the build if any source-executable
  would ship non-executable. Verified in the sandbox: hooks now ship
  755 in the .deb; data files stay 644; binaries stay 755.
- Post-fix regression proof owed (added to Part 3): after a real
  v1->v2 update over Tor, run update-initramfs -u in the guest and
  verify the rebuilt initramfs still contains
  etc/cryptsetup-keys.d/root.key, then reboot and confirm the machine
  comes back with the phrase typed once.
- Side finding (rig tooling, not product): QEMU std-VGA + this kernel's
  fbcon renders as unreadable coloured static in screendump/VNC; the
  same guest under -vga virtio renders perfectly at every phase. The
  battery's guests were switched to virtio + VNC capture. Product
  installs on real hardware are unaffected (real GPUs/firmware).

## PART 6 — MUSL-STATIC RUST REFERENCE BUILD (checkbox)
- rustc 1.99.0 (rustup stable on the rig) + target
  x86_64-unknown-linux-musl + musl-gcc (bundled rusqlite C build):
  poc/dynamic/rust-app compiles clean in 1m43s (-j2). Result:
  3,983,248-byte ELF, "static-pie linked", ldd: "statically linked" —
  a zero-dependency binary for the native app slot, as A22 intends.
  PASS.

## PART 1 (continued) — BUILD #3 WITH THE MODE FIX
- build-onionhost-deb.sh fixed: after the 644 flatten, +x is restored
  for every staged file whose SOURCE-overlay counterpart carries any
  execute bit (derived from the tree, not a hardcoded list), plus a
  build guard that fails the build if any source-executable would ship
  non-executable. Sandbox-verified: both initramfs hooks ship
  -rwxr-xr-x in the .deb; data stays 644.
- Build #3 PASS (2026-10-14T17:18:12Z, BUILD_EXIT=0): ISO
  1,361,817,600 bytes, sha256
  7f9300e1c89b081591186401ec6d777380d5492b5ab0fbc1d4614e223e301860.
  In-image check: the planted factory platform .deb lists BOTH
  initramfs hooks as -rwxr-xr-x. Same size as build #2 (reproducible
  build; only the fixed .deb differs). NOT published.
- Update repo republished with fixed packages (platform 1.0.0 + 1.1.0,
  SMF oh.1 + oh.2), signed at true time: Release Date Wed, 14 Oct 2026
  17:01:16 UTC, Valid-Until Sat, 28 Nov 2026. Repo onion service live
  at tpt6oez5hqsmeifbd3ltjb7d4nnfys4dqyyu2mukh2v53eh5nd7fbfyd.onion.
- Reinstall from build #3 in progress (fresh disk, same test identity;
  new generated phrase recorded in the battery evidence). The boot
  test after this install is the gate for the fix: phrase typed once,
  initramfs must open root via the embedded keyfile with no error loop
  and no second prompt.
- Rig tooling note (battery infrastructure only): battery guests now
  launch with a virtio-serial command channel (host unix socket ->
  /dev/virtio-ports/onionhost.cmd) plus a tiny guest agent, giving the
  battery driver a reliable root shell in live/installer sessions
  where the prod flavour deliberately ships no sshd. QEMU monitor
  mouse and slirp guest->host connections proved unusable for this.

(remaining parts appended as they complete)

## PART 2 — INSTALL + FORUM (build #3 ISO)
- Fresh install from build #3 completed in Calamares with no error;
  firstrun's factory-package install ran (platform + all 4 recipe
  .debs). Pre-reboot inspection: initramfs hooks both 755,
  lsinitramfs lists etc/cryptsetup-keys.d/root.key, crypttab correct,
  dpkg shows onionhost 1.0.0.
- BOOT TEST PASSED (the .deb mode fix proven end-to-end): GRUB took
  the disk phrase once, Slot 2 opened, no /bin/cat keyfile loop, no
  second prompt; machine reached the first-boot wizard.
- Wizard completed: login phrase generated + verified, owner login,
  site-type -> own application -> ALL FOUR recipes offered (Wiki/
  DokuWiki, Git hosting/Gitea, Forum/SMF, Blog/WordPress) -> Forum
  chosen, recipe admin fields completed (forumadmin), Go Live ->
  "You are live". Forum onion:
  xrcdeleypilf4hf24y7qm66jlw3jn2furrh4tyvlaahgq2lyiovfwvyd.onion
- Stack on the installed system (also part 6 evidence): containers
  onionhost-a / onionhost-u / onionhost-app all Up under Quadlet,
  every one launched via /usr/local/bin/runsc-wrap (runsc-sandbox +
  runsc-gofer processes live); app container Network=none and its
  runsc sandbox runs --network=none; gateway reaches the app over
  /run/onionhost/web/b1.sock.

### FINDINGS — the recipe path is broken as shipped on a real install
  (three defects, all in the first-boot seeding path; each was
  worked around in-guest to continue the battery, workarounds NOT
  part of the product):
  D1. Seeded web tree ownership: the Go Live seed writes
      /var/lib/onionhost/appdata/www as host root; inside the
      container's userns it appears as nobody, and Settings.php is
      mode 0660 -> PHP-FPM (www-data) gets Permission denied and
      every page is HTTP 500. (In-container app-init normalize_tree
      does not repair the owner.) Workaround: chown -R the www tree
      to the container www-data mapping (host uid 2300033).
  D2. MariaDB provisioning fails under runsc: MariaDB root uses
      unix_socket auth; under gVisor the socket peer credentials
      are not accepted (ERROR 1698 for 'root'@'localhost'), so
      app-init's CREATE/ALTER USER never runs and SMF has no
      database user. Worse: app-init still runs its import branch
      when appdata/db-import.sql.gz exists - the import commands
      fail with the same 1698, the seed file is DELETED anyway and
      "database import done" is logged. The SMF schema + admin seed
      is silently lost on first boot. Workaround: skip-grant
      session in a throwaway container (same image, pinned uid/gid
      maps) to create the app user with the app-db.env password;
      seed SQL regenerated with the platform's own
      onionhost-recipe build_seed_sql (admin forumadmin) and
      imported as the app user (73 tables, admin row present).
  D3. The app image ships NO tzdata: /usr/share/zoneinfo is absent,
      so PHP's timezone database is empty (identifiers list = 0)
      and every SMF page dies with "Timezone database is corrupt"
      once the DB works. TZDIR is not honoured by this PHP build.
      Workaround: bind-mount the host /usr/share/zoneinfo into the
      app container via its Quadlet file (Volume= line) and
      recreate the container.
  After D1-D3 workarounds: forum serves HTTP 200 over REAL Tor
  from an independent client (rig host, its own tor SOCKS):
  "My Community - Index", General Discussion board present.
  Admin login over Tor: LOGIN_OK forumadmin (the seeded sha1 hash
  was accepted and upgraded by SMF per design).
  Verdict: part 2 FAIL as shipped (recipe first-boot seeding is
  broken three ways on a real install); PASS for install + boot +
  platform stack + Tor publication path. The three defects are
  exactly what this battery exists to catch; all are in the
  seeding/first-boot layer, none in the Tor/socket/gVisor wiring.
  External proofs over real Tor (rig host as independent client):
  - Admin topic posted: topic 2 "Battery welcome" on board 1
    (topic 1 is SMF's stock "Welcome to SMF!").
  - SMF OVERLAY RUNTIME RE-CHECK (deferred since recipe slice 2):
    a.php planted in the attachments dir was fetched over Tor and
    served as literal source text (HTTP 200, body = the raw
    <?php ... ?>), NOT executed - the recipe overlay's prefix
    locations keep PHP off in app-writable directories, as
    designed. PASS.
  - Member registration: works, but only through SMF's shipped
    anti-bot gates (registration CAPTCHA + a too-fast-submit
    check). The battery driver cannot pass a CAPTCHA, so the
    battery read the image itself (as a sighted user would) and
    completed registration: REGISTER 302, independent login check
    passed, member row in the database.
  - Member post over Tor: MEMBER_POST_OK; guest read of the
    admin's topic: GUEST_OK.
  Note (test-harness, not product): an earlier registration probe
  with swapped driver arguments printed a misleading OK from a
  login-side check; the database (single member row) is the
  ground truth used throughout.

PART 3 — UPDATE PIPELINE ON THE REAL NETWORK: PASS, with the
part-2 defects cascading through it exactly as designed-for.
  - Debian main archive over Tor: PROVEN (Gate 4's open item
    closed positively). A plain apt-get update + install in the
    guest fetched all three shipped sources via tor+http:
    Debian main trixie Packages [9,678 kB] from
    2s4yqjx5...onion, security [267 kB] from 5ajw6aqf...onion,
    trixie-updates; tcpdump 4.99.5 installed from them.
  - Run 1 (19:05:44Z): the updater fetched the project repo
    InRelease from the battery repo onion
    (tpt6oez5...onion, TRUE-TIME signed 2026-10-14 17:01 UTC),
    verified the floor (1.0) from the signed package, saved a
    rollback copy, downloaded onionhost 1.1.0 [132 kB] over Tor
    and installed it. The post-install health check FAILED:
    the response was an empty-body page from nginx - the
    forum was down because installing the platform package
    regenerated the shipped Quadlet file and /etc/onionhost
    configs, wiping the battery's part-2 workarounds, and the
    underlying tzdata defect (D3) broke SMF again. The updater
    rolled back to 1.0.0; the rollback was unhealthy for the
    same reason, so the machine FAILED CLOSED at 19:10:30Z
    (gateway stopped, site off, marker written) - the Y8
    behaviour working exactly as designed.
  - Packet capture of run 1 (guest enp0s3, 3,664 packets):
    egress only to Tor relays (ORPorts 9050/9001/9000/9993/
    443), NTS (192.71.80.206:4460), one NTP (123), and the
    slirp resolver (10.0.2.3:53). ZERO plaintext HTTP/DNS to
    public addresses. No-clearnet: PASS.
  - Durable repair for the re-run: tzdata baked into a derived
    app image on the guest (image import is one-shot/markered,
    so the tag survives package regeneration): PHP then lists
    419 timezones.
  - Run 2 (19:14Z): platform 1.1.0 installed and its health
    check PASSED (high-water recorded 1.1.0). The SMF recipe
    update to 2.1.7+oh.2 then FAILED its health check and
    rolled back - defect D1 again: the recipe applier's tree
    swap rewrites www as root, so the rollback tree was
    equally broken and the machine failed closed a second
    time (19:19:44Z).
  - Run 3 (19:26:54Z) with the applier given the ownership
    repair the product needs (test-machine patch only: chown
    the swapped www tree to the container's www-data mapping):
    "Updated to 2.1.7+oh.2" at 19:30:02Z, health check
    passed, fail-closed cleared automatically. Forum verified
    over Tor afterwards: HTTP 200, member content intact.
  - Post-update initramfs regression proof: after the
    updater-installed 1.1.0, both initramfs hooks on disk are
    mode 0755 (the .deb mode defect of build #2 would have
    re-broken them here). REBUILD + REBOOT PROOF (completed
    2026-10-14 ~21:20Z): update-initramfs -u rebuilt
    /boot/initrd.img-6.12.43+deb13-amd64 and lsinitramfs
    shows etc/cryptsetup-keys.d/root.key present; the
    machine was then rebooted and accepted the disk phrase
    typed ONCE (serial: Slot "2" opened), booted straight
    to the greeter on the rebuilt initramfs - no /bin/cat
    loop, no second prompt - and the forum answered HTTP
    200 over Tor. The updater path cannot brick the boot
    chain: PROVEN on real hardware.
  - The updater's Debian phase (apt-get upgrade riding the
    same run, ~158 packages over Tor) proceeded after the
    managed packages. Honest wrinkle: the phase was
    interrupted mid-configure by battery tooling (the guest
    agent's subprocess timeout killed the updater's process
    tree - a harness artifact, not product behaviour: a
    real owner's updater is not supervised by the battery
    agent). 77 packages were left unpacked-but-unconfigured;
    recovery was the standard dpkg --configure -a. (A
    manual interactive run of that command blocks on a
    libpam-systemd debconf question - "Override local
    changes to /etc/pam.d/common-*?" - whose safe answer is
    No/keep; under DEBIAN_FRONTEND=noninteractive the
    configure completed cleanly, 0 unconfigured.) The
    reboot proof above ran on the fully configured,
    upgraded system.

PART 6 — PLATFORM CHECKS: PASS.
  - Combined app container under real Podman/Quadlet +
    runsc-wrap: verified on the part-2 install (all three
    containers under runsc-wrap; app Network=none; nginx +
    PHP-FPM + MariaDB in the one container; forum works
    through the socket path).
  - MariaDB autocommit micro-measurement (in-container,
    InnoDB, flush_log_at_trx_commit=1, under runsc): 300
    single-row autocommit INSERTs in 778 ms = 2.59 ms/txn
    (~385 txn/s). Fsyc-bound as expected under gVisor; ample
    for a home-hosted forum. (Measured while the updater's
    Debian phase ran apt in the background - ordinary load.)
  - musl-static Rust checkbox: reference app rebuilt on the
    rig (rustc 1.99.0, musl target, static-pie ELF,
    3,983,248 bytes, ldd "statically linked");
    stage-rust.sh staging completed (rootfs = the binary
    alone + OCI bundle config); the bundle boots under the
    rig's runsc and the app reports LISTENING /run/sock/
    app.sock with its SQLite database open.
  - SMF official-package checksum: download.simplemachines
    .org returned HTTP 403 from the rig as well (three
    attempts incl. browser UA). The GitHub release archive +
    second-source tree comparison from the recipe-1 build
    stands as provenance; the official host will not serve
    either sandbox or rig.

PART 5 — SPOT RECIPES: Gitea FAIL as shipped / PASS after
in-guest workarounds (WordPress + DokuWiki: see below).
  - Gitea installed from the same prod ISO #3 onto a second
    fresh guest (ggitea; disk phrase + wizard flows all as
    designed; recipe picker offered all four recipes).
  - Go Live FAILED as shipped - three further defects, all in
    the recipe seeding/publish path (worked around in-guest
    only, NOT product fixes):
  - D4: the generated app-container config bind-mounts
    /etc/onionhost/app-db.env unconditionally, but the native
    (no-database) recipe path never creates that file -
    podman refuses to start the container
    ("statfs /etc/onionhost/app-db.env: no such file or
    directory"), so a native recipe can NEVER go live.
    Workaround: created the file empty (0600).
  - D5: the staged .recipe-admin.env is copied onto the app
    volume as host root:root 0400; inside the container's
    user namespace that owner is "nobody", so the first-boot
    script (container root) gets Permission denied and the
    administrator is never created. Workaround: chown to
    the container-root mapping (2300000), kept 0400.
  - D6: the seeded native config custom/conf/app.ini is
    likewise host-root 0660; the Gitea process (www-data)
    cannot read it - FATAL "permission denied" at startup.
    Workaround: chown the native tree to the container
    mappings + app.ini 0644 (the D1 mechanism, native side).
  - After the workarounds: first boot created 'giteaadmin',
    the staged admin env was shredded as designed, Gitea
    serves on its unix socket, wizard reported "You are
    live". Onion:
    7odq5wqv4r6p4qhnwphtaravfs3ooa6p6kffxdohwzch7xqihdtsmoyd.onion
  - End-to-end over REAL Tor from the rig host: GET / 200;
    admin login via API with the wizard-chosen credentials;
    repository created; **git push over HTTP through the
    socket path succeeded** ([new branch] main -> main);
    pushed README verified through the API.

PART 4 — REPUBLICATION MEASUREMENT: PARTIAL PASS (typical
margin comfortable; a real tail risk measured).
  - Method: 10x restarts of the gateway+app stack on the
    installed forum machine at ordinary load; seconds from
    restart to first HTTP 200 from an independent Tor client
    (rig host, its own Tor SOCKS), polled every 5 s.
  - Results (seconds): 93, 91, 86, 324, 98, 90, 95, 89,
    139, 90. Median 91 s; 8 of 10 within 86-98 s; one at
    139 s; one outlier at 324 s (5.4 min).
  - Verdict against the shipped probe/health-check envelope
    (~3-4 min): TYPICALLY comfortable - the median restart
    republishes with 2-4x headroom, nothing like the
    sandbox venue's uniformly degraded 2.5-4.5 min band.
    BUT 1 restart in 10 (324 s) would have EXCEEDED a
    4-minute envelope: a healthy update landing in that
    tail fails its health check, rolls back, and can fail
    closed. The envelope risk the sandbox raised is real
    but a TAIL phenomenon (~10%), not the norm. Recommend
    the envelope be revisited (health-check budget of
    ~6 min, or a retry before rollback is declared) -
    measured basis now exists.
  - WordPress (applied on gprod after part 4, switching the
    site from SMF): RECIPE_APPLY_OK 7.1.3+oh.1. The site
    served WordPress's own installer over Tor; the install
    completed through it ("Success!") and the blog answers
    HTTP 200 over Tor ("Battery Blog"). Publish-to-live +
    probe: PASS. Caveat: this machine's MariaDB already
    held the provisioned app user/database from part 2's
    workaround, so a FRESH WordPress-first install would
    still meet defect D2 - not re-tested here.
  - DokuWiki (applied next on the same machine):
    RECIPE_APPLY_OK 2026-07-14c+oh.1; the wiki serves over
    Tor (200 at doku.php?id=start); its own installer
    (install.php) completed and the administrator
    (dokuadmin) is present in users.auth.php with admin
    group. Publish-to-live + probe: PASS on this machine -
    noting gprod's recipe applier carries the battery's
    guest-only D1 ownership patch, so as-shipped DokuWiki
    first install inherits defect D1 like SMF did.
  - Part 5 verdict: Gitea FAIL as shipped (D4/D5/D6) /
    PASS after workarounds, full git-over-Tor proof;
    WordPress PASS (with the D2 caveat); DokuWiki PASS
    (with the D1 caveat). No recipe was cut.

PART 7 — TEARDOWN: DONE.
  - Removed the abandoned cameron-test guest (2.4G incl. its
    disk, websockify.log) and the cloudflared binary in the
    rig home; no cloudflared/websockify/noVNC processes were
    running. The abandoned battery cmdsrv on rig port 8899
    from an earlier session was killed.
  - Removed both guests this battery created (gprod, ggitea)
    after evidence capture: 172 + 63 screenshots, serial
    logs, the republication batch log and the build #3 log
    are in battery-rig-evidence/ in the workspace.
  - Removed rig-side battery staging artifacts (the Rust
    reference build tree and the stage-rust skeleton).
  - Pre-existing earlier-slice guests and trees (slice5a,
    slice5b, rig-poc, calasrc, step3-test) left untouched;
    disk after teardown: 66G free of 96G.

PART 8 — POWEROFF: the rig was powered off via SSH
(sudo poweroff) as the final rig action; the SSH session
dropped as expected.

PRODUCT FIXES OWED (from this battery's findings):
  - D1: recipe seeding + the applier's tree swap (install,
    update AND rollback paths) must chown the www tree to
    the container's www-data mapping.
  - D2: MariaDB provisioning must not rely on unix_socket
    peer credentials under runsc (ERROR 1698); the seed
    import branch must not delete an unapplied seed or log
    success on failure.
  - D3: the app image must ship tzdata.
  - D4: the generated app-container config must not
    bind-mount app-db.env for no-database (native) recipes.
  - D5/D6: files staged onto the app volume (admin env,
    native config) must be owned by the container-namespace
    mappings, not host root.
  - Part 4 follow-up: revisit the probe/health-check
    envelope (~6 min budget or a retry) against the
    measured 324 s republication tail.
## PRODUCT FIX SLICE — D1–D6 + ENVELOPE (2026-10-14)

Repairs, in the product tree, for the six recipe-layer defects
and the probe-envelope follow-up owed by the rig battery above.
All fixes are in the product tree (onionhost/ + build/); the
battery's guest-only workarounds were mechanism proofs and
were NOT copied. Proof is VM-local (the sandbox pattern of the
earlier slices): the recipe unit suites + gate4fix against the
fixed tree, then end-to-end sandbox scenarios for the paths
the battery broke. NO ISO was rebuilt or published; the rig
was not touched (still powered off) — the short rig
re-verification follows separately. Evidence files:
poc/fix-slice/*.out.

THE FIXES:

- D1 (www tree ownership; onionhost-recipe): the applier now
  chowns the staged www tree to the container's www-data
  mapping (host uid 2300033 = UIDMap base 2300000 + 33)
  BEFORE the swap, on the install AND update apply paths
  (single _apply path), and chowns the restored tree again
  on the rollback path (rollback_recipe), including the
  native rollback binary. New helpers _chown_tree /
  _makedirs_owned (lchown; links not followed). The uid base
  is env-overridable (ONIONHOST_CONTAINER_UID_BASE) for test
  venues whose kernel cannot chown to the production ids.
- D2 (MariaDB root auth + seed import; app-init.sh,
  onionhost-app-provision, onionhost-backup): provisioning
  now creates root with a per-install generated password
  (DB_ROOT_PASSWORD in app-db.env, token_hex(24)) instead of
  unix_socket auth: mariadb-install-db runs with
  --auth-root-authentication-method=normal, every root call
  goes through a db_root() helper using MYSQL_PWD (never
  argv), and a first-boot bridge adopts the generated
  password onto a fresh datadir (one passwordless login sets
  it; if that login fails it logs a loud ERROR). Existing
  installs without a root password gain one at the next
  publish's provision (atomic append; app credentials
  untouched; the wizard's app-info whitelist does NOT print
  it). Backup's ping/dump legs use the same password auth.
  The seed-import branch was rewritten: decompress to a temp
  file first, DROP/CREATE checked, import checked — on ANY
  failure it logs "app-init: ERROR ...", KEEPS
  db-import.sql.gz for retry at the next start, and never
  logs a false "database import done".
  Migration story: restore writes the backed-up app-db.env
  wholesale; a pre-fix backup's record gains a root password
  at the next publish; app-init's bridge adopts it. A
  datadir created pre-fix with socket-auth root cannot be
  bridged under gVisor (the passwordless login is what
  socket auth refuses) — it fails loud, documented here; no
  field machines exist, so no migration is owed in practice.
- D3 (tzdata; build/build-iso.sh): build_image_tar takes a
  keep-zoneinfo flag; the app image now includes the tzdata
  package AND keeps /usr/share/zoneinfo (the customize-hook
  strip is omitted for that image only; tor/web keep the
  strip, byte-identical hook otherwise). NOTE for the next
  build: the builder caches image tars — the cached app tar
  must be deleted for this to take effect (comment in the
  script says so).
- D4 (app-db.env bind source; onionhost-generate-configs):
  SHAPE NOTE — implemented as a guaranteed bind source, not
  a conditional mount. When dbmode=none and app-db.env is
  absent, generate-configs writes an empty comment-only
  placeholder (0400, container-root mapping 2300000) so the
  Quadlet unit's unconditional bind always has a real file.
  Reasoning: Quadlet units are consumed by the generator at
  boot/daemon-reload and publish does no daemon-reload, so a
  conditional mount cannot take effect at a site's first
  publish; the placeholder is the codebase's own idiom (the
  three recipe-seam files are guaranteed the same way).
  Nothing reads the placeholder (init skips MariaDB for
  db=none; the native runtime never looks), it carries no
  credentials, and provisioning's atomic write replaces it
  if the site ever gains a database.
- D5/D6 (staged-file ownership; onionhost-recipe native
  path): the first-boot admin env is staged with the
  container-ROOT mapping (2300000, mode 0400 — readable by
  the in-container root that consumes it, "nobody" no
  longer); native_files (first-boot.sh, custom/ tree) with
  the container-root mapping; the seeded native config
  (custom/conf/app.ini) and the app binary with the
  www-data mapping (2300033). app.ini's mode is 0660 after
  apply — the applier writes 0640, then the recipe's own
  normalize-exceptions pin it to 0660 (its secret keys;
  group = www-data's group). Directories the applier
  creates on the volume are created already-owned
  (_makedirs_owned), so no host-root dir can strand a tree.
- Envelope (onionhost-update): health_ok() is now a
  two-level check — the unchanged probe run (HEALTH_TIMEOUT
  600 s cap; Dashboard/probe behaviour untouched) retried
  up to HEALTH_ATTEMPTS=2 runs with HEALTH_RETRY_DELAY=45 s
  between them (both env-tunable), and only a budget-
  exhausted failure engages rollback/fail-closed, exactly as
  before. Nominal budget ~6–9 min against the battery's
  measured 324 s republication tail (median 91 s). Header
  docstring records the measurements.

REGRESSION RUNS (fixed tree, this slice):
- Recipe unit suites: SMF 32/32, WordPress 39/39,
  DokuWiki 37/37, Gitea 27/27 — ALL PASS. (The four unit
  harnesses set ONIONHOST_CONTAINER_UID_BASE=0: this
  sandbox's own userns map cannot chown to the production
  ids from the host side — EINVAL measured; in-sandbox the
  full id space works, see scenario proofs.)
- gate4fix: run_tests.py 35/35 PASS, test_dashboard.py
  11/11 PASS. New scenarios S6 (health succeeds only on the
  2nd probe run → update judged healthy, NO rollback,
  exactly 2 probe calls), S7 (health never succeeds →
  exactly HEALTH_ATTEMPTS runs, then fail-closed exit 5 +
  marker + status), S8 (shipped defaults: attempts=2,
  delay ≥30 s, per-run cap ≥380 s). Scenario (d) is thereby
  proven at the state-machine level.
- Initramfs-hook mode guard (battery fix) NOT regressed:
  the platform .deb built from the fixed tree ships both
  hooks -rwxr-xr-x (zz-onionhost-cryptsetup,
  zz-onionhost-keyfile), data files 644. A negative guard
  test is not constructible without editing the builder
  (the guard derives expectations from the source tree);
  recorded as such.

SCENARIO PROOFS (sandbox machines, fixed-tree .debs):
- (a) SMF fresh install, NO guest workarounds: publish
  clean (APP_PROVISION_OK db=created, RECIPE_APPLY_OK
  first_install=yes seeded=yes, PUBLISH_OK). D2: the app
  log shows the root-password bridge, "application
  database 'onionhost_app' ready", "database import done",
  no ERROR lines; the seed file was consumed; 73 SMF
  tables; the seeded admin row present. D1: a bare applier
  run leaves Settings.php at 2300033:2300033 mode 660 with
  ZERO files in www not owned by 2300033 (the post-start
  tree reads as the venue's www-data alias because app-
  init's normalise pass — by design — re-chowns to
  www-data:owner-group at every start; the battery's D1
  failure mode, unmapped "nobody" owners, cannot occur).
  Flows in-machine over the edge socket: admin login,
  admin topic posted, member registered (via SMF's admin
  registration — the public form is CAPTCHA-gated by SMF's
  stock seed, reg_verification=1, unchanged by this slice;
  the battery proved the human CAPTCHA path on the rig),
  member login, guest reads the topic. Probe over real
  Tor: PROBE_OK HTTP/1.1 200. D2 negative: a garbage
  (non-gzip) staged import produced the loud ERROR naming
  the file, the file was KEPT, and all 73 tables survived;
  after cleanup the forum serves again. The SQL-failure
  import branch shares the same keep-and-log structure and
  was not separately exercised live — stated plainly.
- (b) Gitea fresh native install: run on the recipes-gitea
  machine2 rootfs (real www-data uid 33; machine1's rootfs
  aliases www-data to uid 0, under which Gitea's own
  root-refusal makes a functional native run impossible —
  a PHP-venue delta, not a product property). Two explicit
  venue translations, neither touching a product or staged
  file: ownership asserted immediately after the applier
  (before the normalise pass), and the app-data parent made
  traverse-only (0711) to emulate the production volume
  mount boundary the sandbox's symlink exposes. The
  sandbox rootfs also lacked git (the product app image
  ships it — D3 tar closure); git 2.47.3 + its missing
  library deps were transplanted from the fixed tree's own
  app-image tar. Results: applier-only stats — app.ini
  2300033:2300033 0660 (D6), .recipe-admin.env
  2300000:2300000 0400 (D5), first-boot.sh 2300000:2300000
  0755 (D5), app binary 2300033:2300033; app-db.env
  placeholder present with zero credential lines (D4).
  Functional: FIRST_BOOT_OK, done marker present, volume
  AND host admin envs shredded; admin login OK; repo
  created (API-visible); git push over HTTP through the
  socket path OK; anonymous browse of the pushed file OK;
  probe over real Tor PROBE_OK 200. NOT proven in this
  venue: Podman's own acceptance of the D4 bind (the
  sandbox has no Podman/Quadlet — the harness runs the app
  stack as processes); that is rig re-verification work.
- (c) Recipe update + sabotage rollback (SMF machine):
  updater over the signed repo (Tor) took SMF oh.1 → oh.2:
  exit 0, "updated to 2.1.7+oh.2 and healthy", live tree
  oh.2, seeded topic + both members intact afterwards.
  Sabotaged oh.3 (recipe.json removed): health check failed
  (both envelope attempts), updater exit 4, "rolling back
  to 2.1.7+oh.2", dpkg back at oh.2, live tree restored,
  forum serves (guest read OK). A second sabotage run with
  the app initially down repeated the rollback cleanly
  (exit 4). D1 on the swap/rollback paths: the updater's
  applies go through the same _apply proven in (a); after
  each updater restart the tree reads as the venue's
  www-data identity (normalise), with no unmapped owners.
- D3 image proof: the builder's own build_image_tar,
  extracted verbatim, built the fixed app image from the
  pinned snapshot: tar 673,943,040 B, sha256
  fc3145d679c90dc438fe165a6a7500d088071459b80e6bfee8a624e2e6098634;
  510 zoneinfo entries incl. UTC, America/New_York,
  Europe/London; dpkg status shows tzdata 2025b-4+deb13u1
  "install ok installed". (Transport in this venue used
  the snapshot over the sandbox proxy after two CONNECT
  flakes; the package list and hook were the builder's
  own.) In-machine, the SMF stack's PHP reports 419
  timezone identifiers.

VERDICTS: D1 PASS, D2 PASS, D3 PASS, D4 PASS (shape note
above; Podman acceptance rig-deferred), D5 PASS, D6 PASS,
envelope PASS. Not provable in the sandbox and deferred to
the rig re-verification: real Podman/Quadlet start with the
D4 placeholder; the production uid view end-to-end (the
sandbox aliases runtime uids; ownership was proven in the
container-visible view inside the machines); a pre-fix
socket-auth datadir's loud failure (documented, no field
machines). No ISO built or published; rig untouched.

# RIG MINI RE-VERIFICATION + PUBLISH (2026-10-14)

Re-verification of the PRODUCT FIX SLICE (D1–D6 + envelope)
on the real rig, zero-workaround rule: any step needing a
guest-side workaround of the kind the battery used is a FAIL
for that part and stops the publish. Appeal commitment
honoured: ordinary CPU load only throughout. Rig:
onion-rig-1 (n2-standard-4, us-west3-a), 66G free at start.
(Parts appended as they complete.)

## PART 1 — ISO REBUILD: PASS
- Tree sync: workspace onionhost/ -> rig ~/onionhost-src and
  build/*.sh -> rig ~/oh-build + ~/, rsync -rc; verify dry-run
  shows zero content diffs (the three known symlinks — the two
  apt-daily timer masks and site/current — present with
  identical targets on both sides).
- Cached app image tar DELETED before the build (fix-slice
  D3 note); the build regenerated it with tzdata in the
  package list.
- FLAVOUR=prod OH_PROBE=0 build, WORK=~/battery/iso-prod,
  finished 2026-10-15T01:35:24Z. ISO: 1,362,046,976 bytes,
  sha256 bfdcb136e26020b35698cbff9570836fed40203f8cb2e8eba5d24071dcb5c174.
- D3 verified in the built image: cache/onionhost-app.tar
  regenerated (666,519,040 B), 510 /usr/share/zoneinfo
  entries incl. UTC, America/New_York, Europe/London; the
  rootfs copy is byte-identical (img_app_sha256
  6981747b58a190c46244eda693cf70be1cdfa65c3509f5d7458397e2497c0d48
  in BUILD-INFO matches both).
- In-image verifications (Prod Rebuild 2 set, all PASS):
  all 5 factory debs planted at
  /usr/lib/onionhost/factory-packages with sha256s matching
  BUILD-INFO; the planted platform deb ships both initramfs
  hooks -rwxr-xr-x (mode guard holds); EFF wordlist 7776
  lines; NO sshd, NO xdotool, NO authorized_keys in the
  rootfs; golden torrc carries PoW defences (rate 5 /
  burst 10), MaxStreams 50 + close-circuit; the Gate 4 apt
  lockdown (52onionhost-tor-updates: tor+http only, plain
  http/https methods "false") intact.

PART 2 — SMF FRESH INSTALL (guest gsmf, UEFI, fresh 24G disk): the
full product flow driven through the real UI (Calamares by keyboard,
wizard by Tk send), no guest-side changes of any kind.
- Install: generated disk phrase page, spare skipped, Partitions
  "Erase disk" with "Encrypt system" pre-ticked and NO passphrase
  fields (forced-encryption patch working as designed), guard page,
  clean install, "All done."
- Encrypted reboot: disk phrase typed ONCE at the GRUB stub prompt;
  booted to the S0 wizard (keyfile initramfs path intact).
- Wizard: login phrase generated + verified -> S1 (atomic commit;
  greeter login with the phrase works). Site type "Your own
  application" -> Forum (SMF) with admin name/password staged in the
  wizard -> Go Live -> S2, "You are live".
- Onion: mmg5cwg2mu2irdzqwlnupauzdh4gykyv2nuxwbhtpebomg6ab5tkokad.onion

POST-GO-LIVE PROOFS (all over real Tor from the rig, ZERO guest
workarounds):
- podman ps: onionhost-u Up, onionhost-a Up, onionhost-app Up (B
  retired as designed at Go Live).
- /etc/onionhost/recipe-admin.env ABSENT (shredded after consumption).
- App container log: MariaDB 11.8.3 ready; "app-init: MariaDB root
  password set from the provisioning record" (the D2 bridge);
  "app-init: application database 'onionhost_app' ready";
  "app-init: importing staged database import" -> "app-init:
  database import done". No ERROR lines. (One pre-bridge "Access
  denied for user 'root'@'localhost'" warning is the bridge's
  expected first probe.)
- onionhost-recipe status smf: 2.1.7+oh.1, seeded: true,
  first_install.
- DB: 73 tables in onionhost_app; admin row forumadmin present
  (seeded passwd LENGTH 40 = legacy sha1, as designed).
- **D1 PRODUCTION UID CHECK PASS**: the www tree (appdata volume)
  holds 666 files, ZERO not owned by host uid 2300033;
  Settings.php = 2300033:2301004 mode 660 — the check deferred from
  the sandbox, now proven in the production uid view.
- **D3 IN-CONTAINER PASS**: PHP in the running app container reports
  419 DateTimeZone identifiers.
- Probe: PROBE_OK, HTTP 200. External fetch from the rig via Tor:
  HTTP 200, NO Date header, SMF index renders ("My Community").
- **Admin web login over Tor: OK.** At first login SMF upgraded the
  seeded hash 40 -> 60 chars (bcrypt), as designed. Admin posted
  topic 2 "Mini verification topic".
- **Member registration via the human CAPTCHA path: OK.** The
  operator read the visual-verification image fetched through Tor;
  the first read was wrong (stock SMF rejected it), the second was
  accepted; memberone (id 2) is activated. Member logged in and
  replied in the admin's topic.
- **Guest (logged-out) read over Tor: OK** — topic + member reply
  visible.
- **Gateway restart republication**: `systemctl restart
  onionhost-a.service`; first external HTTP 200 at <= 20 s after
  restart (Tor state preserved on the host volume; typical-case
  confirmation, comfortably inside the widened envelope).

HARNESS NOTE (not a product defect; no guest state was changed):
SMF's own DB session handler (Sources/Session.php write()) skips
persisting a session when the creating request carries no cookie
("Don't bother writing the session if cookies are disabled"). A
curl flow that starts from an empty cookie jar therefore can never
log in: the login page's session is never stored, and the POST
validates against an empty session ("Session verification
failed"). A real browser always sends the cookie back after the
first response, so real users are unaffected. The test driver was
fixed client-side (warm-up fetch before the login page, follow
redirects). The battery's earlier successful login flow had this
property incidentally.

**PART 2 VERDICT: PASS** — fresh SMF install on the rebuilt ISO,
production uid view, no workarounds of any kind.

PART 3 — GITEA FRESH INSTALL (guest ggitea, UEFI, fresh 24G disk):
full product flow through the real UI, no guest-side changes.
Install clean ("All done."); encrypted reboot with the disk phrase
typed ONCE; S0 wizard -> login phrase [phrase removed 2026-10-20 — Repo Review 4]
-> S1; greeter login; wizard -> Your own application -> Git hosting
(Gitea) with admin staged (gitadmin) -> recipe applied
(onionhost-recipe status gitea: 1.27.3+oh.1, installed: true,
applied 2026-10-15T03:16:35Z) -> app container started by the
product at 03:16 UTC. Onion:
hp43ukk4uve6f5mtqitkajvczrfm6frqj4xf2ili4gaxlgrq7rtzruid.onion

**D4 SUB-PROOF: PASS.** generate-configs wrote the placeholder
/etc/onionhost/app-db.env for the no-DB native recipe (host
2300000:2300000, mode 0400, 218 bytes, comment-only), and the real
Podman/Quadlet stack STARTED onionhost-app with the unconditional
bind in place — the sandbox's open question is answered: Podman
accepts the D4 placeholder exactly as designed. Staged-file
ownership also correct (app.ini 2300033 mode 0660, app binary
2300033, first-boot.sh and custom/ 2300033).

**NEW DEFECT D7 — fresh Gitea installs cannot start (FAIL).**
The app container's init ran the recipe's first-boot step at
03:16:37 UTC and it failed:
  gitea first-boot: Command error: unable to initialize the
  database ... failed to create directories: mkdir
  /srv/appdata/native/data: permission denied
  app-init: ERROR: first-boot step failed; the app may have no
  administrator yet
Gitea web then died at startup on the same mkdir
(routers/init.go mustInit: [F] git.InitFull failed: unable to
prepare git home directory /srv/appdata/native/data/home ...
permission denied). Only nginx runs in the container; there is
no Gitea process. No .first-boot-done marker; the in-volume
.recipe-admin.env was never consumed; no admin exists.
ROOT CAUSE: /var/lib/onionhost/appdata/native (the native app
root) is owned by the container-ROOT mapping (host uid 2300000,
host gid 1004, mode 2775) — the Gitea process runs as the app
user (container uid 33 = host 2300033), which is neither the
owner nor in that group, so it cannot create its data/
directory inside its own app root. PHP recipes are unaffected
(Part 2): their writable directories are created by the applier
inside the www tree; Gitea is the first app that must create a
new top-level directory in its app root at runtime. The fix
slice's sandbox Gitea scenario passed because its venue uid
mapping made the applier-created directories effectively
app-user-owned (assertions were taken pre-normalise with the
app-data parent emulated) — the production uid view is exactly
what this re-verification existed to test, and it caught this.
PLATFORM BEHAVIOUR ON FAILURE: CORRECT. Go Live's publish ran
the await-first-boot wait, then failed closed: the wizard's Go
Live page shows "Publishing failed: onionhost-recipe: first-boot
step for recipe gitea did not report done; ... publish: recipe
gitea first-boot", state stayed S1, nothing was published.
(No operator workaround was attempted, per the zero-workaround
rule.)

**PART 3 VERDICT: FAIL** — D7 blocks fresh Gitea installs on the
rebuilt ISO. (D4 placeholder acceptance itself: PASS.)

PART 4 — WORDPRESS FRESH INSTALL: NOT ATTEMPTED. Its brief
precondition was Parts 2+3 fully clean; Part 3 failed.

PART 5 — PUBLISH: NOT DONE. The task's rule: publish only if
Parts 2 and 3 PASS (and 4 if attempted). Part 3 failed, so the
rebuilt ISO (sha256 bfdcb136e26020b35698cbff9570836fed40203f8
cb2e8eba5d24071dcb5c174, 1,362,046,976 bytes) is NOT published;
vespiary.org and Drive still carry Prod Rebuild 2 (080e45ac...).

SESSION OUTCOME: Part 1 PASS, Part 2 PASS, Part 3 FAIL (new
defect D7). The D1–D6 fixes are proven on real hardware; the
Gitea native-runtime data-directory ownership needs one more
fix (own the native app root — or pre-create its data_dirs —
to the app-user mapping, 2300033) and a fresh re-verification
of Part 3 before any publish.

PART 6 — TEARDOWN + POWEROFF: DONE. Session guests gsmf and
ggitea stopped and their rig-side guest directories removed
after evidence capture (mini-evidence/gsmf-shots/,
mini-evidence/ggitea-shots/, gsmf Tor artifacts). Rig powered
off via SSH `sudo poweroff`: a probe 12 s later still answered
(shutdown in progress); all probes from ~1 min on fail at SSH
key exchange — the endpoint no longer completes a handshake,
confirming the VM is down. No load generation of any kind was
run at any point in this session (appeal commitment honoured).

NEXT (for the fix round): D7 — the native app root (and any
runtime-created top-level app directories) must be owned by —
or pre-created for — the app-user mapping (host 2300033), the
same treatment D1 gave the www tree; then re-run Part 3 only.

## D7 FIX (2026-10-14)

Defect (from the mini re-verification, Part 3): on a fresh
Gitea install the native app root
/var/lib/onionhost/appdata/native was owned by the
container-ROOT mapping (host 2300000:1004, mode 2775). The
app runs as www-data (container 33 = host 2300033) - neither
owner nor group member - so its first mkdir (native/data)
was refused; first-boot failed, Gitea died at startup, and
publish failed closed (platform behaved correctly). PHP
recipes were unaffected: nothing creates a top-level entry
in the www root at runtime.

ROOT CAUSE, pinned to the mechanism: the native root is the
native app's WORKING DIRECTORY ($ONIONHOST_APP_DATA); the
app creates data/, its database and files directly in it.
Three product paths could birth or restore that root in the
broken state, and the container init could not repair any
of them - its normalise pass runs inside the app container's
user namespace, where chown of a directory whose current
group (the owner's host gid) is outside the container's gid
map is refused. (The www root carries the identical state
harmlessly: the normalise pass re-owns its CONTENTS, whose
groups are mapped, and no runtime actor creates top-level
entries in it.) The fix therefore belongs on the host side,
at every path that creates or restores the root - the
shared mechanism, not the Gitea recipe:

1. onionhost-app-provision (the shared mechanism; runs at
   every publish for every app site, recipes and
   owner-installed apps alike): the owner-managed-dirs loop
   now chowns native to the www-data mapping
   (CONTAINER_WWW_UID = 2300033) instead of the
   container-root mapping. Group (owner's) and mode (02775,
   setgid + ACL attempts) unchanged, so the owner's desktop
   access is exactly as before. The chown is unconditional:
   re-provision at any later publish also heals a root an
   older build created.
2. onionhost-generate-configs: the app-data skeleton's
   fresh-create branch no longer births native with the
   container-root mapping; a fresh native dir is created
   2300033:2300033 0755 (provision re-owns it to the
   group-shared steady state at publish). www/db unchanged.
3. onionhost-recipe: new _own_native_root() asserts the
   root's end state (www-data uid, owner's gid from
   /etc/onionhost/app-owner.env with a www-mapping fallback,
   mode 02775) and is called on every native apply
   (apply_native, right after the root is ensured) and on
   the native rollback branch after the binary swap - the
   same "assert on the way back" treatment D1 gave the
   restored www tree and binary. Nothing else in the
   applier changed; the D5/D6 staged-file discipline is
   untouched.
4. onionhost-restore (_install_app): the flatten-and-chown
   walk now parameterises the owner per subtree - the
   native tree (root, directories, files) comes back owned
   by the www-data mapping (2300033) instead of APP_UID;
   the www tree keeps the container-root mapping it has
   always had (its contents are re-owned downstream by the
   applier and the normalise pass). Restoring a native
   backup previously recreated the D7 state verbatim.

The owner-installed native app (APP-SITES.md contract, no
recipe involved) uses the same provision skeleton and the
same app-init native branch, so fix 1 carries it - proven
as phase P5 below.

PROOF (VM-local; harness in poc/d7-fix/, outputs in
poc/d7-fix/*.out). Venue honesty, stated plainly: this
sandbox cannot carry the production uid space on its real
filesystem (chown to an id outside the sandbox's own map is
refused, mount/setns/setresuid to those ids are blocked),
so the phases ran inside a runsc bundle machine on the
gitea slice's staged product rootfs (poc/recipes-gitea/
rootfs-machine2: real www-data 33, owner ohowner
1000:1000), driven by runsc exec - the Gate 4 / recipe
slices' established machine pattern. Inside that machine,
stat presents the production host-side ids the product
tools chown to, and the app-user write simulation runs as
the numeric host identity 2300033 (setpriv, clear-groups)
- the identity whose mkdir the rig refused. One venue
translation, not a product property: the staged rootfs
carries /var/lib/onionhost as 0770, so the phases make it
traverse-only (0711) to keep every write test measuring
the native root alone (in production the app reaches the
volume via its bind mount, never the host parent; the fix
slice used the same translation). A smoke test isolated
the arithmetic first: as 2300033, mkdir in a
2300000:1000/2775 dir = DENIED, in a 2300033:1000/2775 dir
= OK, owner-as-group-member = OK - the rig's outcomes.

Controls (pre-fix scripts, poc/d7-fix/originals) - D7
reproduced on every path before any fix was trusted:
- P0 provision + applier: native root 2300000:1000 2775
  after provision AND after a gitea oh.1 apply; app write
  test DENIED. PASS 6/6.
- P3a generate-configs fresh-create: native born
  2300000:2300000 755. PASS 1/1.
- P4a restore: native tree restored 2300000:1000; app
  write into the restored data/ DENIED. PASS 3/3.

Fixed tree:
- P1 provision: native root 2300033:1000 2775; www root,
  db dir, appdata root byte-identical to pre-fix; app
  identity creates data/, data/home and a file in the
  root (the created dir is 2300033:<owner gid> - the
  root's setgid bit passes the owner's group down, the
  designed sharing); owner still manages the root via the
  group. PASS 8/8.
- P2 applier cycle on P1's machine, no re-provision:
  apply oh.1 -> apply oh.2 -> rollback -> apply oh.2, the
  root asserted 2300033:1000 at every step; binary shas
  track the cycle (oh.1 upstream sha256 4da93c2c..c12d971
  restored exactly by rollback); staged admin env still
  2300000:2300000 0400 (D5), app.ini still 2300033 (D6);
  app write test green after first apply and after the
  full cycle. PASS 17/17.
- P3b generate-configs: fresh native 2300033:2300033 755;
  www/db fresh state unchanged. PASS 3/3.
- P4b restore: restored native root 2300033:1000 2775,
  data dir and binary 2300033:1000; www root unchanged
  (2300000:1000); app identity writes into the restored
  data/. PASS 6/6.
- P5 owner-installed native slot (no recipe): owner drops
  a program into the native folder from the desktop side;
  the app identity creates its data in $ONIONHOST_APP_DATA.
  PASS 3/3.

Regression (fixed tree, unmodified suites): gitea unit
27/27, SMF 32/32, WordPress 39/39, DokuWiki 37/37,
gate4fix run_tests.py 0 failures, test_dashboard.py 0
failures. The PHP paths were not disturbed: every PHP-side
ownership assertion in P1/P3b/P4b is the pre-fix value.

RIG-DEFERRED (by design; the Part 3 rig re-run is the
final proof): a fresh Gitea install on the rebuilt ISO
under the real Podman/Quadlet stack - the app container's
start against the re-owned volume, first-boot completion
in the production uid view, and publication, with zero
guest workarounds. Nothing in this slice rebuilds or
publishes an ISO, and the rig was not touched.

# RIG PART-3 RE-RUN + PUBLISH (2026-10-14)

Re-run of the mini re-verification's Part 3 (fresh Gitea)
after the D7 fix, with publish on a clean pass. Scope note:
the D7 fix touches only native-slot paths (app-provision's
native chown, generate-configs' skeleton native branch, the
recipe applier's native assert, restore's native subtree);
the www/db branches are byte-unchanged, and the mini
session's Part 1 (rebuild) and Part 2 (SMF fresh install,
zero workarounds, production uid view) verdicts therefore
stand for the platform and PHP paths — this session
re-proves the native/Gitea path end-to-end on the rebuilt
ISO. Appeal commitment honoured: ordinary CPU load only.
Rig: onion-rig-1 (n2-standard-4, us-west3-a), external IP
<rig-external-ip> this start, 66G free at start. (Parts appended
as they complete.)

## PART A — ISO REBUILD WITH THE D7 FIX: PASS
- Tree sync: workspace onionhost/ -> rig ~/onionhost-src and
  build/*.sh -> rig ~/oh-build + ~/, rsync -rc. The content
  diff was exactly the four D7 files (onionhost-app-provision,
  onionhost-generate-configs, onionhost-recipe,
  onionhost-restore) plus their __pycache__ companions;
  post-sync dry-runs show zero diffs, and the three known
  symlinks (two apt-daily timer masks, site/current) are
  present on the rig with identical targets.
- Cached app image tar DELETED before the build (fix-slice
  D3 note); the build regenerated it.
- FLAVOUR=prod OH_PROBE=0 build, WORK=~/battery/iso-prod,
  finished 2026-10-15T04:25:03Z. ISO: 1,362,051,072 bytes,
  sha256 1013659210095a8befa467ef55659ce34e9609570e64896e53fe612a5b816ed2.
- D7 FIX VERIFIED IN THE BUILT IMAGE: the planted platform
  deb (onionhost_1.0.0_all.deb) contains the provision
  script's native branch chowning to CONTAINER_WWW_UID
  (line 131, "... CONTAINER_WWW_UID if name == \"native\"")
  and onionhost-recipe carries _own_native_root (definition
  + apply/rollback call sites).
- In-image verifications (the mini session's Part 1 set, all
  PASS): all 5 factory debs planted at
  /usr/lib/onionhost/factory-packages with sha256s matching
  BUILD-INFO; both initramfs hooks in the planted platform
  deb ship -rwxr-xr-x (mode guard holds); A19.1 wordlist
  gate OK in the build log (7776 unique words); golden torrc
  carries PoW defences (HiddenServicePoWQueueRate 5 /
  Burst 10), MaxStreams 50 + close-circuit; the Gate 4 apt
  lockdown (52onionhost-tor-updates: tor+http) intact; NO
  sshd, NO xdotool, NO authorized_keys in the rootfs;
  regenerated app image tar carries tzdata (510
  /usr/share/zoneinfo entries incl. UTC, America/New_York) —
  img_app_sha256 ed1ef284a0c86540cf733afc70e9946719ebad59e0e828a4681fa408d82ba362.

## Part B — fresh Gitea install, zero guest workarounds: FAIL (NEW DEFECT D8)

The install half of the flow was clean end-to-end. Fresh
guest ggitea (24G disk, UEFI) installed from the Part A
ISO: disk-phrase page generated [phrase removed 2026-10-20 — Repo Review 3] (paper-check words 3/6/7
passed); the spare page was skipped (a spare was generated
by a keyboard-focus slip mid-drive, verified, then removed
with the page's own "Remove this spare" control — final
install state has no spare, matching the mini session);
Partitions "Erase disk" with "Encrypt system" ticked by
the forced-encryption patch (300 MiB FAT32 EFI + 23.71 GiB
LUKS2); guard page "Encryption is on"; Users Owner/owner/
onionhost-gitea; install "All done." First disk boot:
phrase typed ONCE at the GRUB stub, LUKS opened. Wizard
S0 -> login phrase [phrase removed 2026-10-20 — Repo Review 3] generated,
paper-checked, committed (state file S1) -> greeter login
with the phrase succeeded through PAM -> site type "Your
own application" -> recipe "Git hosting (Gitea)", admin
gitadmin staged in the wizard -> Go Live page. Guest onion
(never live): kfgajiettvtmqovvifxitirervs2wowggfl3ot7vcfwurppq5waivhqd.onion.

Sub-proofs that PASS:
- D4 placeholder under real Podman/Quadlet: generate-
  configs wrote /etc/onionhost/app-db.env (2300000:2300000
  0400, 218 bytes, dbmode=none) and onionhost-app.service
  went active against it — the app container started.
- D7 fix present in the running system: the native app
  root in the production uid view is 2300033:1004 mode
  2775, and every recipe-staged file inside it (Gitea
  binary, custom/, first-boot.sh, .recipe-admin.env 0400)
  carries the app-user mapping 2300033. The fix's
  host-side end state is exactly as designed.
- Platform fail-closed behaviour, again: state stayed S1,
  publish refused with a plain-language wizard message,
  staged admin env never consumed, no administrator
  created, no .first-boot-done marker.

Sub-proof that FAILS (the publish itself): first-boot did
not report done, on the first Go Live (2026-10-15T05:02Z)
AND on the wizard's own suggested retry (05:11:50Z) —
identical, deterministic. Gitea's migrate (run by
first-boot.sh via setpriv as www-data) dies with
"mkdir /srv/appdata/native/data: permission denied"; the
web start dies the same way in git.InitFull; the app init's
own root mkdir of native/home is also denied; only nginx
runs. No data/ tree exists. Evidence bundle:
part3-evidence/ (32 guest screenshots + part-b-failure-
evidence.txt with the full logs and stats).

## NEW DEFECT D8 (D7-residual) — native root unwritable through the production engine

D7's diagnosis stopped one layer too shallow. The host
stat is now correct, but under rootful Podman + runsc the
container's file operations on the bind-mounted appdata
are performed by the runsc gofer under the container-root
host identity (uid 2300000). That identity has no write
on a 2300033-owned 02775 directory: write is owner-only,
the directory's group is the owner's host gid 1004 —
outside the container gid map (it appears as 65534 inside,
so the app user's group class never applies either) — and
other is r-x. The sandbox D7 proof could not see this:
its venue could not carry the production uid space on a
real filesystem (disclosed in that slice), so the gofer
identity question never arose. Net user-visible effect is
identical to D7: a native recipe cannot create its data
tree and first-boot cannot complete; PHP/www recipes are
unaffected (their tree is container-root-owned, which the
gofer CAN write — consistent with the mini session's SMF
PASS and this session's clean www-side state). The fix
direction (product decision, not attempted here): give
the gofer's identity write on the native root — e.g.
group ownership by the container-root mapping with group
write + setgid, an ACL for the container-root uid, or
pre-creation of the app's top-level data directories by
the host-side applier with app-user ownership (files
created inside an existing app-owned data/ by the app
user still pass through the gofer, so this alone is not
sufficient for files the app creates later in existing
app-owned subdirs — the gofer write path itself needs
the access). Any fix must be re-proven on the rig under
the real engine, not only in a sandbox venue.

## Part C — WordPress: NOT ATTEMPTED
Per the session brief, Part C was conditional on a clean
Part B pass. (The mini session's WordPress spot-check PASS
stands, with its recorded caveat.)

## Part D — publish: WITHHELD
Part B failed, so per Cameron's standing rule the new ISO
is NOT published. vespiary.org and Drive still carry Prod
Rebuild 2 (sha256 080e45ac048e9999d2de57f199d5411c53a442f4a7a7daaa49a92c0e4cb2b1c1).
The Part A ISO (sha256 1013659210095a8befa467ef55659ce34e9609570e64896e53fe612a5b816ed2)
exists only on the rig build tree. No publish steps were
started.

## Part E — teardown + poweroff
Guest ggitea removed after evidence capture into
~/workspace/onion-host-os/part3-evidence/ (screenshots
01-32 + part-b-failure-evidence.txt). Earlier guests and
trees untouched. Rig powered off via SSH at the end of
the session; endpoint confirmed dead. No CPU-saturating
work was run at any point (appeal commitment honoured).

Session verdict: Part A PASS, Part B FAIL on NEW DEFECT
D8, Part C not attempted, publish withheld. The Gitea
recipe remains unshippable on the native slot until D8
is fixed and re-proven on the rig.


# D8 INVESTIGATION + FIX (2026-10-14)

Investigation venue and full outputs: poc/d8-fix/
(README-venue.md carries the id model; matrix outputs in
n1.out, n6-n3.out, n2-n4-n5-n7.out, n8-n10-db1.out,
w1-w3.out, probe.out). Product proofs: poc/d8-fix/proof/
(README-proof.md carries the harness notes; phases p0-p6).
No ISO was rebuilt or published in this slice; the rig was
not touched.

## The mechanism, as measured (supersedes the Part-3 attribution)

The Part-3 record attributed D8 to the runsc gofer
performing volume operations under the container-root host
identity (2300000). The model venue built for this slice
refutes that as the operative mechanism and replaces it:

RULE (L1, venue-proven): through the gVisor stack, a
create (mkdir / file create) inside a directory whose
GROUP ID IS NOT MAPPED in the container's user namespace
is refused — for every requester, including container
root (capabilities do not override), at any mode
(including 0777 world-write), with or without setgid, and
POSIX ACLs do not rescue it. The check keys on the
directory's own gid mapped-ness, not on the requester's
credentials: in the venue the same root requester creates
freely in mapped-gid directories and is refused in
unmapped-gid ones, everything else equal.

This one rule explains D7 (native root 2300000:1004 —
gid unmapped), D8 (2300033:1004 — same unmapped gid; the
D7 fix repaired the uid only), and why the battery's
Gitea worked: the battery-era workaround ran the
recipe layer's tree chown over the native tree, which
owns files to the www-data uid AND gid — the native root
became 2300033:2300033 (gid mapped), the venue's config
N3, the one pre-fix shape in the matrix whose performer
rows pass. It also falsifies two of the fix directions
sketched in the Part-3 record: an ACL for the performer
identity does NOT rescue an unmapped-gid directory
(matrix N5/N8, all creates still refused), and the
www tree was never "unaffected" by design — it was
unaffected by luck: the applier's tree chown happens to
give www directories a mapped gid, but any www data
directory created by the owner through the desktop or
returned by an older restore carries the owner's group
and breaks identically (matrix W3). Application file
creation in www data directories (SMF attachments,
WordPress uploads) had never been exercised in
production; it is the same bug class, and this slice
treats it as such.

Second layer (L2, from the rig evidence; the venue
cannot carry it — see the divergence note): with all ids
mapped, production performs non-root volume operations
with ordinary requester (in-container Unix) semantics.
Evidence: the mini session's SMF read its own
2300033:2300033 0660 Settings.php through the engine;
the battery's DokuWiki installer created files in its
www data dirs; the battery's Gitea ran a full workload
(git push over HTTP) in its 2300033:2300033 tree; MariaDB
initialises its datadir. A performer-identity-only model
cannot explain any of those.

VENUE DIVERGENCE (disclosed, load-bearing): this VM is
itself user-namespace'd, so the venue's runsc is detected
rootless and its gofer runs with reduced capabilities;
consequently ALL non-root volume operations are refused
in-venue regardless of configuration (even the app user
creating in a container-root-owned 0777 directory). The
venue is authoritative for L1 (the container-root rows
of the truth table) and for created-file ownership
(container-root creates land uid = container-root
mapping, gid = setgid-inherited from the directory). The
app rows rest on the rig evidence above. THE RIG RE-RUN
REMAINS THE FINAL PROOF for every app-row claim.

## Truth table (venue; requester rows: root = container root)

Config (target dir uid:gid mode)        root create   app create
N1 current product  WWW:OGID 2775      DENIED        DENIED
N2 pre-D7           ROOT:OGID 2775     DENIED        DENIED
N3 battery shape    WWW:WWW 2775       OK            venue-artifact*
N4                  WWW:ROOTGID 2775   OK            venue-artifact*
N5 = N1 + performer ACL (+default)     DENIED        DENIED
N6 = N1 without setgid, 0775           DENIED        DENIED
N7                  ROOT:OGID 2777     DENIED        DENIED
N8 = N1 + performer ACL (no default)   DENIED        DENIED
N9 = N4 + owner ACL                    OK            venue-artifact*
N10 ROOT:ROOTGID + WWW ACL             OK            venue-artifact*
DB1 db shape        ROOT:ROOT 0750     OK (999 req.)  venue-artifact*
W1 www data dir WWW:WWW under OGID
   parent                              OK            venue-artifact*
W3 www data dir WWW:OGID + ACL         DENIED        DENIED

* "venue-artifact": refused in-venue solely by the
divergence above; production behaviour for these rows is
the L2 evidence. Denied rows marked DENIED for the app
are denied on L1 grounds (the gid rule refuses before
requester semantics are reached) — those refusals are
configuration-caused, not venue-caused. Root-created
files land uid = container-root mapping with the
directory's setgid gid; a restart re-run reproduced the
run-1 rows exactly (ownership is stable across restarts,
so the fixed end state persists).

Corollaries proven in probe.out: chown/chmod of a volume
directory whose group is unmapped is also refused from
inside the container for non-owners (the D7 root cause:
the container init's normalise pass cannot repair such a
directory — it must be born right, host-side); and
container root CAN chown volume files across mapped ids
(MariaDB's first-start datadir chown is consistent).

## The fix

Invariant: every directory on an app create path carries
uid AND gid inside the container's id map; the app user
owns its writable trees (2300033:2300033, mode 02775
setgid); the desktop owner's access rides a named-user
POSIX ACL (rwx, access + default) written directly as
xattrs by the tools (deterministic, no setfacl
dependency). Least privilege: no world-write anywhere;
the container-root identity gains nothing it did not
have (it could already create in mapped-gid trees); the
owner's ACL is scoped to the tree roots, with the
default ACL propagating it to new subdirectories;
read-only trees (appdata root, db dir, site, tor) are
untouched.

Changed files (product tree, rootfs-overlay/usr/local/bin):

- onionhost-app-provision: the www and native roots are
  now owned (www-data uid, www-data gid) at 02775 (www
  was container-root:owner-gid; native was
  www-data:owner-gid); the shell-out setfacl attempt is
  replaced by _grant_owner_acl (direct xattr, access +
  default; a stderr WARNING if the filesystem refuses);
  a healer walk re-owns any directory under www/native
  whose uid OR gid is outside the container map to
  (www-data, www-data) — this repairs owner-dropped
  directories and trees left by older builds at every
  provision; app-owner.env now records ONIONHOST_OWNER_UID
  as well as the gid; the container id base is
  env-overridable (ONIONHOST_CONTAINER_UID_BASE) for test
  venues, mirroring onionhost-recipe (production never
  sets it).
- onionhost-generate-configs: a fresh www root is born
  in the same end state (was container-root 0755); the
  native root is born 02775 (was 0755). Appdata root and
  db unchanged.
- onionhost-recipe: _own_native_root now asserts the
  www-data GROUP (was the owner's gid — the D8 state,
  re-asserted on every apply and rollback!) plus the
  owner ACL; new _own_data_dirs asserts every directory
  under each manifest-declared data dir (SMF
  attachments/custom_avatar/cache, WordPress
  wp-content/uploads, DokuWiki data+conf) to
  (www-data, www-data, 02775) with the owner ACL on the
  data-dir roots, at apply (on the staging tree, before
  the swap) and at rollback; new _own_www_root asserts
  the www root itself the same way (an apply swap
  otherwise demotes it to the archive's 0755 — found by
  proof phase p4, fixed in this slice).
- onionhost-restore: _install_app now returns BOTH app
  trees at (www-data uid, www-data gid) with directory
  mode 02775 (www was container-root:owner-gid 0755,
  native www-data:owner-gid) plus the owner ACL on both
  roots; id base env-overridable as in the recipe tool.

Not changed: app-init.sh's normalise pass (its target
group — the owner's gid NUMBER — is a mapped id inside
the container, so it is L1-safe; its known partial
effectiveness pre-dates D8); backup (tarfile preserves
numeric ids; restore re-asserts the end state); the
recipe payloads and manifests.

## Proofs (poc/d8-fix/proof/, phases run 2026-10-14)

Controls (originals = the four tools with the fix's
semantic hunks reverted, generated by make-originals.py):
- p0: pre-D8 provision reproduces the D8 precondition
  exactly (www 32768:1000, native 32801:1000, the gid
  outside the venue map) — PASS 3/3.
- p5-control: pre-D8 restore returns www under the
  container-root mapping and both trees under the
  owner's group (dirs 0755) — PASS 4/4.

Fixed tree (venue id analog: base 32768, www 32801,
owner ohowner 1000):
- p1 provision: roots (32801:32801 2775); the healer
  re-owns planted unmapped-gid dirs; app-owner.env
  carries uid+gid; the app-identity write simulation
  (setpriv to 32801, plain-Unix on the real fs) creates
  in the native root — PASS 7/7.
- p2 generate-configs alone on a fresh tree: skeleton
  births www+native at (32801:32801 2775); appdata/db
  and the D4 placeholder unchanged — PASS 5/5.
- p3 Gitea cycle (apply oh.1 → oh.2 → rollback →
  oh.2) with real payloads: native root asserted at
  every step; binary restored to the oh.1 sha after
  rollback; D5 (staged admin env 0400 container-root)
  and D6 (app.ini 0660 www) intact; write simulation
  passes after the cycle — PASS 12/12.
- p4 SMF cycle: declared data dirs asserted
  (32801:32801 2775) after apply oh.1, apply oh.2 and
  rollback; Settings.php 0660; write simulations pass
  in attachments and cache — PASS 16/16.
- p5 restore: both trees return (32801:32801), dirs
  02775, files 0644; write simulation passes in the
  restored native root — PASS 6/6.
- p6 (host-side, because the venue gofer refuses
  xattrs outright — EOPNOTSUPP, measured): all three
  tools' ACL helpers land byte-correct named-user rwx
  entries in BOTH the access and default ACLs, and a
  full provision run on the host leaves www+native at
  (www:www 2775) WITH the owner ACLs attached —
  PASS 13/13.

Regression suites, unmodified, against the fixed tree:
SMF 32/32, WordPress 39/39, DokuWiki 37/37, Gitea
27/27, gate4fix run_tests 0 failures, test_dashboard
0 failures.

Venue limitations encountered and handled (details in
proof/README-proof.md): runsc's default rootfs overlay
swallows xattrs and hides writes (machine runs with
--overlay2=none on a real rootfs); the gofer caches file
content (variant switches restart the machine and print
in-machine tool sizes); runsc exec drops sandbox stderr
when redirected straight to a file (capture goes through
tee); generate-configs' literal other-container ids are
translated by a PATH chown shim confined to those trees;
payloads and recipe state live on the workspace disk
(/tmp's 512 MB tmpfs cannot hold them).

## Rig-deferred (NOT proven by this slice)

1. Every app-row (non-root requester) behaviour through
   the production engine: the app user's creates, reads
   and rewrites in the fixed trees under rootful
   Podman/Quadlet + runsc-wrap — including Gitea's
   first-boot mkdir of native/data (the D8 symptom) and
   its later rewrites of files the platform staged.
2. PHP application runtime writes in data directories
   (SMF attachment upload, WordPress media upload,
   DokuWiki page save) — never yet exercised in
   production; the fix covers their directories, the
   rig must exercise the writes.
3. Restart persistence of the fixed end state under
   the real engine (venue restart rows passed for the
   root requester; the container-restart path is the
   rig's).
4. The owner ACL's desktop-side effect on the real
   guest (owner opening the app folder in the file
   manager) — helpers proven on the host here; the
   guest's desktop is the rig's.

Disposition: fix is in the product tree and
sandbox-proven as above. Next step is a Part-3-only rig
re-run (fresh Gitea on a rebuilt ISO, zero workarounds)
and, on a clean pass, publish per Cameron's standing
rule. The Gitea recipe remains unshippable until that
re-run passes.

# MARKETPLACE RECIPE — A23 RECIPE 5 (2026-10-17)

Fifth packaged app, and the first that is neither PHP nor
unix-socket native: Cameron's Monero marketplace (frozen
Stage 10 tree, spec v2 MVP) packaged as the signed recipe
`onionhost-recipe-marketplace`. Owner's framing: wanted NOW,
while the marketplace is still changing, to surface
integration problems early and improve the OS demo; later
marketplace changes ship through the Gate 4 update path.
Venue: the per-slice gVisor sandbox family (a new machine,
mkt-machine, cloned from the Gitea slice's), no rig, nothing
published. The marketplace source tree was NOT modified.

## What the recipe needed that no earlier recipe did

- **PostgreSQL in the app slot** (first): the manifest gains
  `db: {required: true, engine: "postgres"}`. Provision
  `--db postgres` writes the shared per-install credentials
  record; the golden app-init grows `start_pg`: PostgreSQL
  runs inside the app sandbox as a process beside nginx and
  the app (initdb on first boot with the credentials
  record's root password as superuser password — password,
  never peer auth, per the D2 rule; datadir `appdata/pgdb`
  beside the trees, never inside one; the app role/database
  re-asserted idempotently at every start; DATABASE_URL
  assembled and exported by app-init only, so credentials
  exist in exactly one place at runtime and never in the
  package). IMG_APP gains postgresql, curl, libnettle8t64,
  libhogweed6t64 (the binary's linked libraries).
- **TCP serving**: the marketplace binds TCP loopback only
  and has no unix-socket support. The manifest gains
  `native_serve: {type: "tcp", port: 8080}`; generate-configs
  reads selection + manifest at render time (single source
  of truth) and renders a new golden template
  `nginx-app-native-tcp.conf.tmpl` — the native variant with
  the upstream swapped for 127.0.0.1:<port>. The app
  container still has no network; the edge wiring is
  unchanged.
- **Migrations as a recipe step**: the app never migrates
  itself (its deploy tooling applies 0001-0009 externally,
  in glob order, against a marker ledger). The recipe ships
  the nine migrations as native_files plus `files/migrate.sh`;
  the platform learns the general step: after DB start and
  before first-boot/app start, app-init runs
  `native/migrate.sh` at EVERY start; a migrate failure
  means the app is NOT started (nginx still serves, so the
  update health check sees the failure and rolls back).
- **A first ADMIN from the wizard**: the bare marketplace
  has no admin bootstrap (registering creates a buyer; the
  GCP demo needed a manual DB UPDATE). The recipe closes
  the gap: the wizard stages the owner's chosen admin
  (recipe-setup; host env 0400), first-boot starts the app
  briefly as www-data on loopback, registers the admin
  through the real /register form, promotes it with one SQL
  UPDATE, PROVES it by logging in and reading /moderation,
  then shreds the volume copy and writes .first-boot-done.
  Publish's await-first-boot completes the path and shreds
  the host copy.
- **Per-install app.env**: `native_config` renders
  `seed/app.env.tmpl` on first install only — SITE_NAME
  from the wizard's title, DEPLOY_PROFILE=demo and
  INSTANCE_NETWORK=stagenet locked (the recipe does not
  bypass the marketplace's own production-profile
  acceptance sentence; mainnet stays the owner's separate
  launch decision), BIND_ADDR=127.0.0.1:8080, key/media/
  blob paths on the native volume, the PAYMENTS_* and
  retention knobs at the owner-accepted pre-mainnet
  defaults. NO credentials and no DATABASE_URL in it.
  app-init parses it as DATA (literal KEY=value, never
  evaluated; platform-managed names cannot be set from it).
- **Backup/restore learn the engine**: a native+postgres
  backup takes a live pg_dump first, then the cold file
  copy; the dump rides the tarball as the app section's
  db-import.sql.gz and the app container's init imports it
  into a fresh database on next start; restore marks the
  site db=postgres from credentials+dump presence.

Binaries (host cargo release, nettle shims per AGENTS.md):
marketplace-app 12,149,440 B sha256 f56191a0…b0f25 (oh.1);
media-worker 1,269,560 B sha256 90d33c51…b75f8, staged as a
native_file — the second-binary shape is new to the
catalog. oh.2's app binary is the same source rebuilt with
stripped symbols (8,651,464 B, sha256 f4d62246…f3ee) as the
byte-different update target. Recipe versions 0.1.0+oh.1 /
+oh.2 (+oh.3 sabotage), floor 0.1.0+oh.1.

## Defects found (platform + recipe), all fixed in the tree

1. **start_pg superuser pwfile ownership**: initdb runs as
   postgres; the 0600 pwfile was root-owned → "could not
   open file /run/.pg-superuser.pw: Permission denied".
   Venue-independent (production identical). Fix: chown the
   pwfile to postgres before initdb. Companion: the server
   log file is postgres-owned from the start (pg_ctl appends
   as postgres).
2. **start_pg postmaster restart race** (the costly one):
   on a stack restart, the previous postmaster may still be
   shutting down (smart shutdown waits for the app's pooled
   connections) or, in venues without sandbox teardown,
   still running; pg_ctl start refuses on its lock file and
   the database was judged dead. Measured consequence: the
   first oh.2 update rolled back AND failed closed on this
   (both attempts hit the same live postmaster). Fix:
   start_pg now waits (bounded 30 s) for a live postmaster
   to exit, adopts one that is still running after the wait
   (it IS this datadir's server), and removes a stale lock
   left by a dead/zombie pid.
3. **Publish wrote the recipe selection too late**, and
   **restore never wrote it at all**: generate-configs
   renders the TCP/nginx variant from the selection, but
   publish wrote the selection AFTER provisioning (whose
   final step renders) and backups never captured the
   selection for restore to reinstate. Both invisible for
   the four unix-serve recipes; the first TCP-serve recipe
   exposes them: a restored marketplace (and a first
   publish, once its database worked) answered 502 behind a
   healthy application. Fix: publish writes/clears the
   selection BEFORE provisioning; restore reinstates it from
   the restored site model (and clears it on deselect)
   before its render. APP-SITES.md records the rule.
4. **TCP nginx template** (recipe-slice authoring error):
   the first cut was written as a fragment (no load_module,
   no http block) and nginx refused it. Rewritten as a
   faithful variant of the native template, differing only
   in the upstream.
5. **Recipe helper executables vs the normaliser**: the
   uniform pass flattens tree files to 0664 at every start;
   the golden init re-chmods only native/app. The
   media-worker's manifest 0755 was honoured at apply and
   lost at first start — image uploads failed with "Media
   worker error". Fix is the recipe's own seam: oh.2 pins
   0755 for media-worker, first-boot.sh and migrate.sh in
   overlay/normalize-exceptions. APP-SITES.md records the
   rule for future recipes.

## A defect in the marketplace itself (tree untouched; reported)

`crates/app/src/web.rs`, media_serve (line ~1282): the ref
validation requires EVERY character of the ref — extension
included — to be a hex digit or a dot:
`ref.chars().all(|c| c.is_ascii_hexdigit() || c == '.')`.
The letters of ".png"/".jpg" are not hex digits, so the
check can never pass and GET /media/<ref> returns 404 for
every legitimately stored image, on any platform. Proven
with a diagnostic build (a scratch COPY of the tree with the
swallowed branch instrumented; the frozen tree itself was
never modified): the handler extracts the correct ref and
computes ok=false. Upload/sanitize/store work; only
serving is dead. No test in the tree requests /media/... —
this is the recipe work's first full-stack exercise of the
route. The one-line fix belongs to the marketplace's own
gate process; the sibling check at messages.rs:184 is
correct (extensionless refs).

## Proofs (sandbox venue; poc/recipes-marketplace/)

- Unit (host, the recipes' standing harness): **31/31** —
  refusal without a staged admin, app.env rendering (title
  in, tokens out, no credential lines, stagenet lock),
  staged modes incl. media-worker executable, D8 native
  root at apply AND rollback, update swap with app.env
  frozen, rollback keeps the broken binary aside,
  await-first-boot timeout/success/shred.
- Clean provision from the .deb, one publish, final form:
  APP_PROVISION_OK db=created → RECIPE_APPLY_OK
  first_install=yes → FIRST_BOOT_OK → PUBLISH_OK, rc=0.
  All 9 migrations in the ledger; admin row present with
  role=admin; host staged env shredded.
- Acceptance drive over the edge socket: front page shows
  the wizard's title ("Teton Trading Post"); /limitations
  shows stagenet + demo; wizard admin logs in (303) and
  /moderation answers 200; buyer+seller registered; seller
  application approved by the admin at /moderation/sellers;
  payment identity + pool batch (4 fixture subaddresses)
  accepted; PGP key registered; listing created, published,
  visible in the catalogue; buyer order created with a pool
  subaddress assigned on the order/pay pages; seller
  accept → mark-paid (SellerAttestation) → fulfil → buyer
  complete; the order page reads Completed. Media upload
  through the media-worker: sanitize + store + DB row +
  listing-page link all proven (serving: the app defect
  above).
- Restart persistence: stack restart re-runs migrate
  (ledger current, nothing re-applied), first-boot
  correctly skipped, site answers.
- Update v1→v2 through the Gate 4 path: signed repo on a
  venue onion service, fetched over Tor by the updater;
  oh.2 applied (first_install=no), app.env and data
  untouched; verdict "updated to 0.1.0+oh.2 and healthy";
  high-water advanced. The same run first recovered the
  machine from the fail-closed state defect 2 had caused
  ("recovery healthy - site is back").
- Sabotage: oh.3 (ELF header scrambled, hash re-sealed)
  fetched, installed, applied; "FAILED its health check";
  automatic rollback to oh.2; site healthy; the Completed
  order intact.
- Backup/restore: backup of the live site (8,601,600 B,
  age-encrypted, live pg_dump + cold copy) → wipe →
  restore (phrase-derived decrypt, manifest verified,
  onion + title check out) → boot imports the dump
  ("database import done"), migrations current → front
  200, Completed order present, admin login + /moderation
  200 on the restored instance. This is the pass that
  exposed defect 3; re-run after the fix, the restore also
  reinstated the selection and rendered the TCP variant.
- D8: in-machine sweeps after apply, after update, and
  after rollback show the native root and its create-path
  dirs (native, native/media, native/migrations) at
  mapped-uid:owner-gid 02775 setgid; media-worker 0755 via
  the exceptions pin. The venue's gofer has no POSIX ACL
  xattrs, so the named-user ACL leg is asserted by the
  unit harness (base=0), as in the D8 slice.
- Regression: SMF unit 32/32 and Gitea unit 27/27 against
  the current tree (the shared recipe machinery's other
  consumers), all touched tools pass py_compile / sh -n /
  bash -n.

Venue notes (not product behaviour): the staged rootfs
carries /var/lib/onionhost at 0770 — in production the app
stack never traverses it (the volume is bind-mounted at
/srv/appdata), but the venue's shared filesystem makes
PostgreSQL (the first slot service running as a genuinely
unprivileged user; earlier daemons alias uid 0 here) the
first to be refused; prep-rootfs.sh chmods it 0755 and
records why. The venue's runsc rootfs is an overlay: files
created host-side after boot surface unreliably — venue
tools are delivered as fresh filenames or via /stick. The
venue PID 1 does not reap children (zombie pids can make
the harness's pid-file unit checks lie; the same
zombie-blindness briefly stranded one publish). Two early
publishes' captured outputs were garbled in delivery; every
verdict above was re-established from files and database
state, not from those captures. The repo onion for the
venue: vfhnfsce…vkid.onion; the site onion:
puxkshjm…xd3qd.onion.

## Rig-deferred (NOT proven by this slice)

Same posture as the earlier recipe slices: production-
engine app-row behaviour (PostgreSQL + marketplace as the
app user under rootful Podman/Quadlet + runsc-wrap),
restart persistence under the real engine, the owner
ACL's desktop effect, and a Part-3-style rig re-run.
Publish remains withheld pending the outstanding
regression checklist; the rig was not used.

Disposition: recipe + platform generalisations are in the
tree and sandbox-proven as above. Report:
RECIPE-MARKETPLACE-REPORT.md. The marketplace media-serve
defect is reported there for the marketplace's own gate
process; the marketplace tree is untouched.

## PUBLIC REBRAND APPLIED — MANIOC SERVER / POLYCULTURE MARKETS (2026-10-17)

Names decided by Cameron 2026-10-17 (see
NAMING-DECISION-SHEET-2026-10-16.md, DECIDED section;
classification in REBRAND-SCOPE-2026-10-17.md). This entry
records the bucket (a) PUBLIC BRAND surfaces changed in
the tree. Nothing was published: the live page at
vespiary.org/onionhost/ is untouched, no ISO was built,
and the next ISO publish still waits on the outstanding
rig regression checklist. Report:
REBRAND-APPLY-OS-REPORT.md.

Public surfaces changed:

- site/index.html: <title> and <h1> now "Manioc Server";
  the false "working title" footer disclaimer replaced
  with a developed-under-the-working-title line; the
  download link, link text and sha256sum instructions
  now name maniocserver-amd64.iso, matching the build
  output below. (The live page still serves the current
  prod-rebuild-2 ISO under its old name until a new ISO
  publishes and the page is uploaded — a separate step.)
- build/build-iso.sh: ISO output filename is now
  maniocserver-amd64.iso (prod) /
  maniocserver-<flavour>-amd64.iso; ISO volume label
  ONIONHOST_LIVE -> MANIOC_LIVE. Existing artefacts in
  releases/ keep their names (records of what shipped).
- wizard.py owner-facing strings: window titles
  ("Manioc Server Setup", "Manioc Server"), the welcome
  heading "Welcome to your Manioc Server", and body copy
  at the BYOC, recipe-pick, go-live and app-info pages.
- Desktop entries (autostart pair): Name= and Comment=
  now Manioc Server / Manioc Server Setup. Filenames and
  Exec= paths unchanged.
- Default placeholder site page (site/releases/0):
  <title> and heading now Manioc Server.
- Marketplace recipe display names in this tree:
  recipes/marketplace/recipe.json app name and catalogue
  name are now "Polyculture Markets" /
  "Marketplace (Polyculture Markets)"; APP-SITES.md's
  marketplace section heading and lead follow.
- Calamares view steps (phrase/spare/guard): NO CHANGE —
  verified by grep, their user-visible strings carry no
  product name at all (passphrase/encryption copy only);
  the only "OnionHost" occurrences in plugin-src are
  class/factory names, include lines, log prefixes and
  header comments (bucket b).

Deliberately UNCHANGED (bucket b, update contract):
the platform package name `onionhost` and all
`onionhost-recipe-*` package names; every /etc/onionhost,
/usr/lib/onionhost and /var/lib/onionhost path; systemd
and Quadlet unit names; ONIONHOST_* environment
variables; Calamares module names and C++ class/factory
names; plumbing filenames (tmpfiles, initramfs hooks,
apt config, .desktop filenames); the wizard's backup
file format extension .onionhost-backup and its dialog
label; marketplace_id `vespiary-market` (marketplace
tree, untouched by this pass).

Verification: bash -n on build-iso.sh, py_compile on
wizard.py, recipe.json parses; the marketplace recipe
unit harness (poc/recipes-marketplace/unit-test.py)
passes 31/31 against the platform tooling. Known
owner-visible leftovers the inventory did not classify
(GRUB boot menu entries and the live user's GECOS name
in build-iso.sh, the xsessions session-entry Name=) are
listed in REBRAND-APPLY-OS-REPORT.md for a follow-up
call; they were left untouched in this pass.

Addendum (2026-10-17, main session): the three owner-visible leftovers flagged by the rebrand pass were folded in — GRUB menu entries now "Manioc Server (live) - Install" / "Manioc Server (live, verbose)" (build-iso.sh:515,519), the live user's GECOS display name is "Manioc Live" (build-iso.sh:378), and the kiosk xsessions entry shows Name= "Manioc Server Setup". DesktopNames=OnionHost in that file was deliberately KEPT (it is a desktop-environment identifier token, not a display string). bash -n clean.


---

## REPO REVIEW 2 FIX BATCH (2026-10-20)

Scope: the 23-task fix brief in "Manioc Server — Public Repo
Review 2" (static review of the pre-rewrite initial commit + the
polyculture-markets companion HEAD), executed against the
working tree. NO git operations of any kind were performed
(no commit, no push, no history operation): every change below
is a working-tree edit, to be folded into the owner's chosen
history treatment afterwards. The maintainer tree
(onionhost-maintainer/) was not touched; the only fact taken
from it is the PUBLIC archive signing-key fingerprint printed
in its README, used as task 4's pinned constant.

Owner decisions taken during the batch (Cameron, 2026-10-20,
"do whatever you think is best and is most standard practice";
decided by Muse under that delegation):
  (1) History: REWRITE the initial commit with the redactions
      and force-push (repo verified first: 1 commit, 0 forks,
      0 stars/watchers — a clean window). Executed AFTER this
      batch, outside it.
  (2) Runtime gate: FAIL CLOSED. Implemented so in task 20.
  (3) Marketplace recipe: ship only once rebuildable from a
      pinned public commit. Provenance + AGPL pointer recorded
      now (task 12); the media-worker binary stays in place,
      posture unchanged, until the rebuild path exists.
  (4) Reproducibility: the live account's password is a LOCKED
      constant (task 8 extension below), not per-build random.
  (5) Build record: the full build log stays public WITH the
      targeted redactions (task 23); the unredacted raw record
      stays local.

### Group A — publishable tree (tasks 1–2)

Task 1 (.gitignore, P5): DONE. The .gitignore header is the
original prepared-for-publication header (.gitignore:1-6:
source, build scripts, docs and reports in; bulk binaries,
extracted trees, evidence captures and release images out) —
it was NOT rewritten in this batch. `*.gpg` was NOT narrowed:
the tree keeps the broad `*.gpg` at .gitignore:37, with the
two keyring negations at .gitignore:38-39
(!onionhost/rootfs-overlay/usr/share/keyrings/ and
!onionhost/rootfs-overlay/usr/share/keyrings/*.gpg)
re-including the public keyring. (Corrected 2026-10-20 under
Repo Review 3, finding P12.) Verified: git check-ignore + git status —
the archive keyring is now committable (untracked, not
ignored), seed *.gpg stays ignored, hs_ed25519_secret_key
under a recipe archive is ignored, a staged .deb and a stray
.onion key under recipes are ignored, module *.so ignored,
the tor+http method still tracked. The review's prediction
that users:users:1000 is what git sees here is borne out.
Task 2 (CI scan): DONE. build/ci-scan.sh (new, executable,
POSIX sh + embedded python3 — same lib/apt/methods/tor+http
idiom) scans the committable set (git ls-files -co
--exclude-standard), fails on private-key headers (PEM /
OpenSSH magic / the Tor secret-key file header), non-allowlisted global
IPv4, non-allowlisted /home/<user>/ literals, and ELF binaries
outside archive/ dirs. Plant harness: clean tree PASS (268
files); planted PEM FAILS naming file:line; planted Tor
header FAILS; planted public IPv4 FAILS; planted /home
literal FAILS; planted ELF in files/ FAILS while the same
bytes under archive/ PASS. .github/workflows/ci-scan.yml
(new) runs it on push + pull_request. REFINEMENT of the
review's S-plan, recorded: ipaddress counts some multicast /
reserved addresses as global (e.g. 233.252.233.233); the scan
ignores multicast/reserved/unspecified findings — the
nftables bogon set is data, not a leak — while the planted
GLOBAL address still fails. The allowlist was pruned at batch
end (coordinator): every pair naming a rig address or a gssh
/home path was removed once task 23's redactions landed, so
those literals now appear NOWHERE in the committable set,
this script included; the one surviving IP pair is the public
Netnod NTS address (192.71.80.206) in this log's packet-
capture record — public infrastructure.

### Group B — build inputs (tasks 3–8)

Task 3 (fetch step, B1): DONE. build/fetch-recipe-archives.sh
(new, executable): for each recipe — a present archive whose
sha256 equals the recipe.json pin is OK; a present archive
that does NOT match is a hard FAIL and is left untouched (a
corrupted cache is a tamper signal, never quietly re-fetched
over — the closing check's exact semantics); an absent archive
is downloaded from archive.url (new recipe.json field, task
11) and placed ONLY if its sha256 equals the pin; a recipe
with a source_build object (marketplace) is verify-only and
otherwise fails with build instructions. build-iso.sh calls
it in the factory-packages phase before the recipe loop,
FATAL on failure. Checks: real tree 5/5 OK rc 0; cold tree
(archives removed in a scratch copy) — dokuwiki / gitea /
wordpress fetched and pin-verified, marketplace REFUSED with
build instructions, SMF REFUSED (see task 11 limitation),
rc 1; corrupted-cache tree — FAIL with the mismatch message,
no download attempted, rc 1.
Task 4 (keyring gate, B3): DONE. build-iso.sh, near the top:
ARCHIVE_KEY_FPR constant (the public fingerprint from the
maintainer README) + PGP keyring existence check +
`gpg --show-keys --with-colons` fingerprint comparison, with
plain-language FATALs telling the builder exactly how to
export the PUBLIC key. All three branches proven standalone:
real keyring PASS; keyring moved away → fatal; throwaway key
with a different fingerprint → fatal mismatch.
Task 5 (runsc pin, B4): DONE. RUNSC_SHA512_PIN beside
RUNSC_URL (build-iso.sh); the digest of the local binary is
compared against the pin on BOTH the cached and the download
paths; mismatch exits with a message naming both digests.
Pin provenance: runsc release-20251006 downloaded from
storage.googleapis.com in the sandbox and verified against
the publisher's own .sha512 companion file (sha512sum -c OK)
before being pinned.
Task 6 (repo-relative build, B7): DONE. build-iso.sh: OH_SRC
may still override, but SRC now defaults to the checkout's own
onionhost/ tree; ALL build writes (compiled Calamares plugins,
BUILD-INFO) go to $WORK; the three plugins are installed into
the rootfs FROM $WORK. grep confirms no writes into $SRC
remain (remaining mentions are reads). The full-build "git
status stays clean" proof rides the next rig build (below).
Task 7 (.internal / resolv.conf, B8 part): DONE. The chroot
customise's last resolver step deletes /etc/resolv.conf; a
post-customise gate fails the build if a resolv.conf (file or
symlink) exists in the rootfs or any ".internal" string
appears under $ROOTFS/etc (offenders listed). Standalone gate
tests: clean rootfs OK; planted resolv.conf FATAL; planted
.internal in another /etc file FATAL naming the file;
symlink resolv.conf FATAL.
Task 8 (BUILD-INFO reproducibility, B8 part): DONE, with the
owner-question-4 extension. build-iso.sh writes
$WORK/BUILD-INFO.image = the full BUILD-INFO minus the
builder_host= and build_started_utc= lines; both in-image
copies (rootfs /tmp/BUILD-INFO, ISO-tree BUILD-INFO) use the
filtered file; the full record stays in $WORK only. Filter
proof: two generations byte-identical, forbidden keys absent.
Extension (decision 4 above): the prod live account no longer
gets a per-build random password — customise asserts the
LOCKED constant (usermod -p '!') and pins the shadow
password-change day to SOURCE_DATE_EPOCH, so the whole shadow
entry is a build constant. Functional proof on a scratch user:
`user:!:20372:0:99999:7:::` (passwd -S reports L, day =
SOURCE_DATE_EPOCH/86400), byte-identical across runs. The
rig build must still prove autologin works with the locked
account (below).


### Group C — recipe builder (tasks 9–10)

Task 9 (pin check + sabotage honesty, B2): DONE.
build-recipe-deb.sh verifies, before packaging: the staged
archive's sha256 equals the recipe.json pin (a missing
archive now points at fetch-recipe-archives.sh), and every
native_files entry carries a recipe.json sha256 that the file
matches (a missing field refuses the build). manifest.json
carries the PIN; a --sabotage build re-seals self-consistently
ONLY after corrupting the payload, and a non-sabotage
staged/pin mismatch aborts as a build bug instead of sealing.
Checks on scratch recipe copies: clean gitea build "pin
check OK: archive + 1 native file(s) verified", manifest
equals the pin; one-byte archive change → build REFUSED
naming both hashes; --sabotage wordpress build succeeds and
the .deb's manifest archive hash equals its (corrupted)
payload's hash and differs from the pin (self-consistent, per
the reviewer's own demanded end state).
Task 10 (native_files hashes at build time): DONE in the same
check (recipe.json fields are task 12's; verification is
shared with task 14's apply-time check).

### Group D — recipe records (tasks 11–12)

Task 11 (provenance URLs, B5/B6): DONE. archive.url added to
all five recipe.json files (SMF GitHub tag archive; wordpress
downloads.wordpress.org release zip; dokuwiki
download.dokuwiki.org tgz; gitea dl.gitea.com binary; the
marketplace repository URL). Fresh-download evidence from this
sandbox: wordpress, dokuwiki and gitea downloads reproduce
their pins EXACTLY. SMF KNOWN LIMITATION, recorded in the
recipe as archive.refetch_note: upstream publishes no release
asset for v2.1.7 (the GitHub release carries zero uploaded
assets), the only canonical download is GitHub's
auto-generated tag archive whose zip bytes are not stable
across generations (fresh fetch sha256 differs from the pin;
extracted contents verified byte-identical to the vendored
archive with diff -r), and download.simplemachines.org
returned HTTP 403 from every venue tried (sandbox and rig,
browser UA or not). The fetch step therefore refuses an SMF
re-download rather than accept an unpinned archive; a future
SMF version whose upstream ships a checksummed asset lifts
the limitation — the note says exactly that.
Task 12 (marketplace provenance, P4/B5): DONE (the
posture-independent half; shipping posture is decision 3).
recipe.json gained: native_files sha256 for all 13 entries;
archive.url = the companion repository; a source_build object
(repo, frozen commit, toolchain from rust-toolchain.toml,
build command `cargo build --release --locked -p app
-p media-worker`, outputs mapping incl. media-worker at
files/media-worker, and the AGPL corresponding-source
pointer). Frozen commit determination (evidence, not a
guess): the companion repo's commit
22a1eb587c4c587365b0816cb8a1db4e21b1e55f ("spec v2 MVP
(stages 0-10) + Direct Payments v1 + 2026-10-17 fix batch",
2026-10-18) is the companion's initial public commit; at that
commit its migration set is exactly 0001–0009 and all nine
byte-match this recipe's shipped copies (sha256 per file),
i.e. it records the tree this recipe was built from on
2026-10-17. The migration skew the review flagged (0010–0013
exist at companion HEAD) is therefore a later divergence, not
recipe staleness at build time; RECIPE-MARKETPLACE-REPORT.md
records the same conclusion in the tree's own words. The two
binaries are NOT byte-reproducible (Rust release builds),
stated in the recipe's commit_note; neither binary was
removed or re-shipped. One coordination note: the batch's own
pin machinery caught a same-batch edit — task 18's change to
files/first-boot.sh invalidated the pin written hours earlier;
the pin was recomputed from the shipped file (task 10/14
verification is what surfaced it).

### Groups E–H — secret and recipe-file handling (tasks 13–19)

All DONE (worker report; sandbox state-machine proofs).
Task 13 (_atomic_write): the temp file is unlinked if stale,
created O_EXCL BORN at its final mode, fchmod-pinned before
any bytes land; racing-placeholder and direct probes pass.
Task 14 (apply-time native verification): _verify_native_files
in onionhost-recipe runs before any placement; tampered file
→ refusal BEFORE placement (state assert shows zero native/
files), missing manifest pin → refusal (an old-format payload
is rejected, not applied on trust), unmodified payload
applies. Task 15 (interrupted-swap healing): _restore_missing_www
restores a missing www from .www-recipe-prev; it is called
at ONE point — in apply_recipe for non-native recipes,
before archive verification (publish reaches recipe sites
only through apply, so the publish path is covered).
Rollback was deliberately NOT given the call: it already
self-recovers from a missing www, and the helper there
would have broken its broken-tree handling. Crash state
heals before the new payload is verified (even a then-
refused payload leaves the restored tree serving); a normal
two-tree state is untouched. Task 16 (shred warning): _shred_file logs a
WARNING (stderr + journal) naming path and error when the
overwrite/unlink fails; the no-admin-refusal path stays clean.
Task 17 (wizard-helper): the platform env file is born 0400
(O_EXCL create at 0400 + fchmod before write; no transient
wider file — hostile-temp and pre-created-file probes pass);
the legacy chmod-then-write remains for genuinely external
targets. Task 18 (marketplace first-boot.sh): the admin
password now reaches curl on STDIN — both the register and
login calls use --data-urlencode "password@-" fed by a
printf pipeline (the brief's own suggested form), so the
password never appears in argv and no temp file exists to
shred; static proof (no "password=$" form remains; the
variable appears only in env parsing, the emptiness check,
and the two stdin pipelines) plus a local curl round-trip
delivering a hostile password byte-exact. Task 19 (backup):
.recipe-admin.env joins onionhost-backup's FORBIDDEN_MARKERS
and a FORBIDDEN_SUFFIXES rule refuses any ".tmp" path
component; a plant in the appdata tree is refused by name
with no backup written, the known false-positive guards
(shadow.php / index.php) stay admitted, and a clean fixture
still produces a backup. STRONGER than the brief's "omits or refuses": refusal
matches the tool's existing per-file forbidden semantics, and
an omission would have hidden exactly the signal the owner
needs. D8 invariant confirmed intact by the worker: D8's
end-state assertions (native root at the www-data mapping,
02775 setgid, owner ACL) re-checked against the changed code
paths in-venue.


### Groups I–J — gVisor enforcement (tasks 20–21)

(Coordinator's note, 2026-10-20: this section was rewritten
after the workers' full reports landed, to describe the
implementations as shipped and verified in the tree; an
earlier draft of this section described a different design
sketch and has been replaced in full.)

Task 20 (engine default + runtime gate, S1): DONE in tree;
on-box confirmation RIG-DEFERRED (list below). containers.conf:
runsc-wrap is now the engine DEFAULT and the ONLY registered
runtime — plain crun and plain runsc are deliberately NOT
registered, so a Quadlet unit that loses its
PodmanArgs=--runtime=runsc-wrap line still lands in the
wrapper (the units keep the explicit line as the visible
first layer). The gate mirrors the nft gate's judge /
enforcer / timer structure:
- onionhost-runtime-gate (judge only; exit 0 = every present
  container runs runsc-wrap, 1 = mismatch, 2 = gate could not
  run — unparseable inspect output is an error, never a
  silent pass, and the podman binary is probed first) reads
  OCIRuntime via podman inspect for onionhost-{a,b,u,app}; an
  absent container is not a violation (B and app are
  condition-selected alternatives).
- onionhost-runtime-gate-check (enforcer): on mismatch it
  logs loudly, stops ONLY the offending unit(s), and writes
  /var/lib/onionhost/runtime/status.json + a
  fail-closed.marker; on a clean check it clears both.
- onionhost-runtime-gate-check.service + .timer
  (OnBootSec=2min, OnUnitActiveSec=5min). Deliberate
  difference from the nft gate: NO boot precondition wiring —
  the gate is a POSTcondition (it inspects running
  containers), so nothing BindsTo= it; the timer covers the
  post-boot run. Fail-closed per owner decision 2.
- Dashboard: wizard.py gains RUNTIME_STATUS_PATH /
  RUNTIME_MARKER_PATH / runtime_status_text() (marker-first,
  the Gate 4 status pattern) and a dedicated runtime_label
  card in the main window — "Your site is off for safety. A
  part of it was not running inside its protective sandbox,
  so it was stopped." — refreshed in check_status alongside
  the update label; empty when OK.
- Build wiring: build-iso.sh's chmod-0755 list and
  systemctl-enable list gained the gate scripts and the
  timer (without which the gate would ship disabled).
Proof (sandbox, labelled simulation — no podman exists in
this venue): the shipped gate + check run unmodified against
PATH stubs fed fabricated inspect output, 21/21 PASS (crun
app container -> judge 1, check stops ONLY onionhost-app,
marker + status written with the offender named; after fix
-> clean, marker cleared; all-wrapper -> systemctl never
called; absent B not a violation; A on plain runsc -> A
stopped; broken podman -> exit 2, nothing stopped, no
marker). Dashboard card harness 12/12 PASS (marker beats
status; violation renders; ok/missing/corrupt -> no card;
the simulation's own state files render the card), and
poc/gate4fix test_dashboard.py passes 11/11 against the
modified wizard.
Task 21 (runsc-wrap fail-closed, S2/S3): DONE in tree. The
wrapper now fails closed on the create path: any invocation
naming a bundle (--bundle, either form) whose config.json
is missing / unreadable / corrupt — or whose netns-strip
write-back fails — exits non-zero WITHOUT exec'ing runsc,
as does a create/run with no bundle at all; the pre-review
catch-all that exec'd with only --host-uds=all is gone. One
deliberate boundary: post-create lifecycle verbs
(start/state/kill/delete) and --version probes legitimately
carry NO bundle and pass through with the pre-review flag
shape — containment is fixed at create time, and failing
closed there would break every stop/state call. Per class:
website + unrecognised bundles get --host-uds=create +
--network=none (netns entry stripped if one ever appears);
tor class keeps --host-uds=all and its spec untouched with
NO --network flag (A/U ride the dedicated bridge netns
podman creates; the pre-bridge --network=host fallback for
a tor bundle with no netns entry is REMOVED — host
networking is never a safe fallback). Proof (harness with
REAL_RUNSC repointed at a recording stub; shipped wrapper
otherwise byte-identical, 36/36 PASS): missing/corrupt
bundle cases exit non-zero with runsc provably never
exec'd; website/app argv carries create + none, no all, no
host; tor argv carries all, zero --network flags, bundle
byte-identical; the real poc bundle configs classify
correctly; flag shapes also validated against the real
runsc binary (all parse, rc=0). D8 / PROBE_OK preservation
is by construction: the probe path is visitor -> A (tor,
all — connects) -> website/app (create b1.sock — create
suffices, the exact shape poc/scripts/runsc-shim.py proved
for nginx); app-internal sockets never cross the host-UDS
boundary; D8's mapped-uid/gid create-path directories are
untouched. On-box PROBE_OK through the real onion path is
rig-deferred (this sandbox cannot run the poc bundles: no
podman, and its seccomp blocks the needed setns).

### Group K — tor+http (task 22)

DONE. The method now refuses, BEFORE opening any connection,
a non-unix PROXY setting: in socks_connect
(onionhost/rootfs-overlay/usr/lib/apt/methods/tor+http:79-88)
a proxy parsed as TCP is refused with a "proxy-refused"
FetchError, so no socket is created for it. The method does
NOT refuse request URIs that are not unix:// — it fetches
ordinary http URIs through the unix-socket SOCKS proxy, and
refusing them would block every update; the original wording
of this entry, which described a refusal of non-unix request
URIs and a harness exercising URI refusals, did not describe
the shipped code and is struck. One implementation detail,
recorded for accuracy: the refusal is the default, with a
developer-only override (the environment variable
ONIONHOST_TORHTTP_ALLOW_TCP_PROXY=1) inside the method for
testing — verified at batch end that NOTHING in the shipped
tree (units, apt config, scripts, docs) sets that variable,
so the delivered posture is refusal. (Corrected 2026-10-20
under Repo Review 3, finding P12.)

### Group L — documents (task 23)

DONE. Targeted redactions ONLY (this log's own batch entry is
this section; the redactions preceded it):
- STAGE1-RIG-SETUP.md: the rig external IP, SSH user + sudo
  posture, and the ssh_config Host block replaced with
  placeholders naming the operator's private runbook as the
  record's home; the Tailscale clause now plainly says a
  Tailscale-found internal address is not a rig address.
- THIS LOG: the rig external IP at the Part-3 build line
  replaced with <rig-external-ip>; the test-install disk and
  spare/login phrases at the three cited blocks (the
  phrases section, the fresh-install line, and the slice-6
  restore line) replaced with "[phrase removed 2026-10-20 —
  Repo Review 2]" markers. Nothing else in the log was
  edited by this task (verified by diff: 5 insertions,
  9 deletions, all mandated).
- The phrase-page screenshot build/shots/prod-smoke-phrase-page.png
  is DELETED (its build/shots siblings remain).
- build/gssh2.sh, gssh5b.sh, guest-ssh.sh now read the rig
  host from $RIG_HOST (refusing clearly when unset); all path
  literals are gone (the build/ directory keeps exactly two
  path literals tree-wide after the batch: a deliberately
  fictional public example, and one stale comment flagged
  below).
- EXPLAINER.md: the P6 sentence rewritten to describe the
  shipped mechanisms — the probe fetches the front page
  through Container U and reports a status only; the runtime
  gate checks each container's OCI runtime, is sandbox-proven
  with rig confirmation pending, and does not by itself prove
  network/mount properties.
- LEGAL-INTAKE-DRAFTS-v2-2026-10-17.md: "operates nothing"
  corrected (the maintainer DOES operate the Tor onion
  service that serves the update repository — stated
  plainly, with the fleet's Tor-only apt path described);
  reproducible-builds wording corrected to engineered-for,
  not yet proven (independent second build has not run);
  download location updated to the project's own site with
  the alpha ISO's current address recorded as its redirect
  target; the trademark item now discloses, as a fact for
  counsel, that the old name persists in package metadata
  and internal identifiers. The standing "re-verify the
  SFLC/EFF addresses before use" warning is preserved;
  nothing was sent anywhere.
- LICENSING.md (new): the licence map at the repository root
  (88 lines) — project licence (Apache-2.0) as the default;
  a GPL-3.0-or-later section listing the Calamares plugin
  sources, the Calamares job modules, the Calamares patch,
  and the other files carrying that SPDX header; the EFF
  large wordlist CC BY 3.0 US attribution; the WordPress
  mu-plugin's GPL-2.0-or-later; and the marketplace
  media-worker's AGPL-3.0-only, whose source LICENSING.md
  presents directly as the companion repository
  (LICENSING.md:81-88), with the exact provenance deferred
  to the recipe. There is NO recipe table, NO firmware
  section, NO vendored spake2 (ISC) entry and NO LGPL-2.1
  module in LICENSING.md — or anywhere in the tree. The
  WordPress mu-plugin now carries an explicit licence header
  (GPL-2.0-or-later, upstream-matching). P8's "suspected
  GPL-3.0 Calamares plugin" was VERIFIED, not assumed: the
  headers say GPL-3.0-or-later — recorded from the files.
  (Corrected 2026-10-20 under Repo Review 3, finding P12:
  the original version of this bullet described a recipe
  table, a firmware section, a vendored spake2 entry and an
  LGPL-2.1 module that do not exist, and described the
  marketplace source pointer as marked NOT a public
  corresponding-source pointer, which LICENSING.md does
  not say.) Two
  record-keeping caveats from the worker: P8 was INCOMPLETE
  (GPL-3.0-or-later headers also sit on five more Calamares
  modules, on phrasegen.py / sitegen.py / backupkeys.py /
  wizard.py, and on eight onionhost-* tools — LICENSING.md
  lists all of them, an SPDX grep being the evidence); and
  the EFF wordlist attribution rests on the review plus
  corroborating third-party sources — the vendored file
  carries no licence header, and EFF's own terms page was
  not fetched in this batch.
Closing check: git grep over tracked files for the rig-IP
families and the internal range returns nothing (rc 1); the
coordinator additionally grepped the full committable set
(tracked + this batch's new files): nothing.


### Regression (all product-tree changes in, before this entry)

- poc/recipes-smf unit suite: 32/32 passed.
- poc/recipes-wordpress unit suite: 39/39 passed.
- poc/recipes-dokuwiki unit suite: 37/37 passed.
- poc/recipes-gitea unit suite: 27/27 passed (see below).
- poc/gate4fix run_tests: 0 assertion failures.
- poc/gate4fix test_dashboard: 0 assertion failures.
- Bonus: poc/recipes-marketplace unit suite: 31/31 passed
  (see below); poc/d8-fix p3 adversarial cycle 12/12 against
  the new wizard + wrapper (task 21 proofs).

Fixture regeneration (poc artifacts only, git-ignored; no
test file was modified anywhere in this batch): tasks 10/14's
strict native_files verification correctly refuses the poc
fixture .debs built by the OLD re-sealing builder (their
manifests carry no native pins — exactly the unverifiable
shape the batch ends). The gitea (oh.1/oh.2/oh.3) and
marketplace (oh.1/oh.2) fixture packages were therefore
REGENERATED the way the new regime requires: each variant
kept its exact payload bytes (the variant binaries and
scripts extracted from the old fixtures — gitea oh.2 is the
genuine binary plus four trailing bytes, oh.3 an in-place
byte variant, as before), carried in a recipe directory whose
recipe.json pins THOSE bytes (the maintainer pin-bump a real
new release would get), and built with the NEW pin-checking
builder. The suites then passed against current-format
payloads with their test files byte-identical.

### What the review got wrong, or imprecise (re-examined)

- STRUCK: an earlier version of this list claimed P1 cited
  this log ":4747 rig-internal 10.x". Review 2 contains no
  ":4747" citation; its P1 log citation is
  ISO-BUILD-LOG.md:4235 (a second external IP). (Corrected
  2026-10-20 under Repo Review 3, finding P12.)
- STRUCK AND REVERSED: an earlier version of this list
  claimed P1's STAGE1-RIG-SETUP.md ":81-82" citation was
  really ":82 and :14" territory. That correction was itself
  wrong: at the pre-rewrite commit, STAGE1-RIG-SETUP.md:81
  holds the rig's external and internal IPs and :82 the SSH
  line, exactly as Review 2 cited. Review 2 was right.
  (Corrected 2026-10-20 under Repo Review 3, finding P12.)
- STRUCK: an earlier version of this list attributed the
  phrase "if SRC pointed elsewhere" to B7. Review 2 contains
  no such phrase; B7 concerns the runsc download resting on
  one server and says nothing about SRC (the source-path
  default is discussed in B4). (Corrected 2026-10-20 under
  Repo Review 3, finding P12.)
- S2's --network=host fail-open branch is UNREACHABLE under
  the shipped unit set (website-class units always pass
  --network=none; the branch's precondition never arises).
  Task 21 removed it anyway.
- STRUCK: an earlier version of this list attributed to P2
  a claim that "the log teaches the full phrase format", in
  the words "seven words from the EFF large list, typed at
  boot". Review 2 contains no such claim or wording; its P2
  evidence is the phrase blocks themselves and the screenshot
  phrase. (Corrected 2026-10-20 under Repo Review 3, finding
  P12.)
- P8 listed the Calamares plugins' GPL-3.0 as "suspected" —
  verified true in the headers. The mu-plugin's licence is
  now declared, closing that item by declaration. (An
  earlier version of this bullet added that a tx module is
  LGPL-2.1-or-later; no file in the tree carries an LGPL
  header, and that addition is struck. Corrected 2026-10-20
  under Repo Review 3, finding P12.)
- CORRECTED: an earlier version of this list described a B2
  "end-state demand" that the manifest must equal the staged
  archive's hash even when they disagree. Review 2 made no
  such demand: its B2 finding was that pins were never
  checked at build time, and its task 9 asked for the
  archive's sha256 to be compared with the recipe.json pin,
  exiting non-zero on mismatch, with re-sealing only under
  --sabotage. The builder as fixed does exactly that: the
  manifest carries the PIN; only a --sabotage build re-seals,
  and only after corrupting the payload — a non-sabotage
  disagreement aborts the build. (Corrected 2026-10-20 under
  Repo Review 3, finding P12.)

### Observed, deliberately NOT fixed in this batch

- An early draft of this entry recorded a supposed
  pre-existing NameError defect in onionhost-backup's except
  clauses. Struck as WRONG on direct verification
  (coordinator, 2026-10-20): the file's except clauses use
  plain OSError / ValueError builtins and `os` is imported —
  no such defect exists. The item rested on garbled preview
  material, not on the code.
- build/tmp/gssh.sh (gitignored scratch, NOT tracked and
  never committed) still carries a rig-IP jump-host pattern.
  Outside task 23's tracked-file scope; recorded so the
  follow-up tidy knows it exists on this disk only.
- The Group L sweep reported a stale /home path comment at
  build/fetch-recipe-archives.sh:12. Re-verified at batch end
  (coordinator): that file contains NO /home literal anywhere
  (full-file grep) — the report is not borne out, and there is
  nothing to tidy. The /home literals that do remain under
  build/ are in the *.py guest test drivers (the ci-scan's
  allowlisted testuser / rig cases) and the deliberate
  no-space placeholder example in STAGE1-RIG-SETUP.md's
  passphrase line.

### RIG-DEFERRED (owed to the next rig session)

1. Task 20's closing check as written in the brief, on a
   test box: delete the PodmanArgs=--runtime line from the
   app unit -> the site stays down with the runtime card
   visible (the containers.conf default + gate half); restore
   it -> the site returns. (The sandbox simulation proves the
   gate half; the engine-default half needs real podman.)
2. Image import with runsc-wrap as engine default
   (`podman import` / load of the image tars) — the brief's
   named open question for the default change.
3. Task 21 on-box: static + app sites return PROBE_OK
   through the real onion path with the rewritten wrapper
   (the sandbox proves argv/bundle behaviour only — it
   cannot run the poc bundles).
4. Backup's `podman exec` path sanity under the new engine
   default (expected unaffected — exec rides the existing
   container's runtime — listed for completeness).
5. Task 8: a PROD-flavour boot proving LightDM autologin
   works with the LOCKED live account (the batch's proof
   covers the shadow constant only).
6. Task 6: a full build-iso.sh run from the checkout proving
   `git status` stays clean through the whole build.
7. Task 20's oom= question remains open from BEFORE this
   batch (needs a rootful-capable venue; unchanged).
8. The publish-gate re-run this batch was sequenced ahead of:
   fresh Gitea install with zero workarounds on the D8-fixed
   tree, runtime writes (SMF attachment upload, WordPress
   media upload, DokuWiki page save), then publish.
9. (Added 2026-10-20, Repo Review 3 task 18 / S10): record
   the runtimes section of `podman info` and attempt
   `podman run --runtime=crun <test image>` (and
   `--runtime=runsc` for completeness); correct the comments
   at onionhost/rootfs-overlay/etc/containers/
   containers.conf:7-15 and
   onionhost/rootfs-overlay/usr/local/bin/runsc-wrap:5-8 to
   match what is observed — whether crun/runsc remain
   resolvable by name despite not being registered in the
   shipped containers.conf.
10. (Added 2026-10-20, Repo Review 3 task 17 / S11,
    functional): on a test box, force one container unit
    onto another runtime (e.g. set onionhost-app's
    PodmanArgs= to --runtime=crun), start the unit, and
    confirm from the journal that
    onionhost-runtime-gate-check's ExecStartPost= stops the
    unit within seconds of start (unit down, Dashboard
    runtime card visible), not at the timer's next run (up
    to 5 minutes); also confirm a healthy unit's start is
    not marked failed/restarted when the check finds a
    violation in a different unit (the '-' prefix
    behaviour), and that systemctl stop issued from a unit's
    own ExecStartPost= does not deadlock that unit's start.
11. (Added 2026-10-20, Repo Review 3 task 17 / S11, window
    measurement): measure the start-up window directly —
    timestamp container start vs gate stop for a unit forced
    onto another runtime, once with the ExecStartPost= line
    wired (expected: seconds) and once with it removed
    (expected: up to OnBootSec=2min at boot /
    OnUnitActiveSec=5min steady state) — and record both
    numbers.

### OWNER-DECISION remainders

- History treatment: DECIDED (rewrite + force-push) — the
  git operation itself happens after this batch, by the main
  session; this batch performed none.
- Marketplace shipping posture: decision 3 stands (ship only
  once rebuildable from the pinned public commit); the
  binary + record stay as they are until then. The migration
  settlement against the frozen commit is part of that work,
  not this batch's.
- (No dashboard-wording remainder: task 20's card shipped as
  a dedicated runtime label via the Gate 4 status pattern,
  as the Groups I–J section records.)

## REPO REVIEW 3 FIX BATCH (2026-10-20)

Scope: the 20-task fix brief in "Manioc Server — Public Repo
Review 3" (static review of the rewritten public commit that
the Repo Review 2 batch produced), executed against the
working tree. NO git operations and NO GitHub contact of any
kind were performed in this batch: every change is a
working-tree edit, to be folded into a second rewritten root
commit afterwards. Task 1's GitHub Support purge request
exists only as a DRAFT (workspace/onionhost-review3-pack/
github-purge-request-draft.md, outside the tree); filing it
is the owner's step, sequenced after the second rewrite.
Owner decisions 1–5 from the Review 2 batch stand; task 10
below is the enforcement mechanism for decision 3.

Process note, recorded plainly: the first Group B worker
reported completion with detailed check claims, but the
coordinator's tree verification found ZERO of its edits
present (git status clean; every cited line unchanged). The
worker was shut down, the group re-dispatched with a
diff-evidence requirement, and every verdict below rests on
the second run's evidence plus coordinator re-verification
against the tree (diff stat, greps, and a full regression
run by the coordinator, totals at the end).

### Group A — GitHub and the build record (tasks 1–4)

Task 1 (purge request): DRAFTED, not filed (see above). The
draft names the repo, both superseded-or-current commits,
both data classes (infrastructure addresses + SSH posture;
test-install passphrases — classes only, no values), and
both remedy asks (cached-view removal + unreachable-object
purge), and notes 0 forks / never announced.
Task 2 (full SHA out of the tree): DONE. Both occurrences
in REPO-REVIEW-PACK-for-claude-2026-10-20.md replaced with a
withheld-SHA placeholder; the Review 2 batch header's short
form (was :4973) reworded to "the pre-rewrite initial
commit". No full-length occurrence of the old commit's
identifier remains in tracked files (coordinator check:
git grep for the full SHA returns nothing; the short form
survives only inside this record's own descriptions of that
check, and in the about-to-be-replaced commit's message).
The identifier survives in full in the purge draft (outside
the tree) and maintainer records. The CURRENT commit's
message still names it in
short form — a commit message is not a tracked file; the
second rewrite's message is where that is settled.
Task 3 (P10 phrase redactions): DONE. All six Review 3
citations verified as genuine Diceware sets before
redaction. A class sweep (the task-7 detector's algorithm
plus a manual pass for standalone 3-word logins) found and
redacted FIVE further sets Review 3 had not cited: install
C and install D disk+login phrases, two Slice Five guest
login phrases, and the Gitea install login belonging to the
cited disk-phrase record. 16 markers "[phrase removed
2026-10-20 — Repo Review 3]" in total. Final sweep: zero
un-redacted phrase sets; the detector's remaining hits in
the log are ordinary prose (adjudicated under task 7).
(Corrected 2026-10-20 under Repo Review 4, finding P10:
that sweep's floor was the 5-word detector. One 3-word
LOGIN phrase set remained — the Part 3 Gitea fresh-install
record — invisible to a 5-word rule by construction. It is
redacted in the Review 4 fix batch, which also adds a
3-word secret-context scanner rule as backstop and records
the final class sweep there. Under the write-time phrase
rule adopted 2026-10-20 (see Standing conventions at the
head of this log), no generated phrase is recorded in this
log at all from that date; redaction markers remain only as
repairs to entries predating the rule.)
Task 4 (P12 record corrections): DONE. Eight visible
"(Corrected 2026-10-20 under Repo Review 3, finding P12.)"
notes mark the corrected passages: (a) the .gitignore entry
now describes the tree (broad *.gpg kept, header original);
(b) the tor+http entry now says non-unix PROXY refusal
(tor+http:79-88), not URI refusal; (c)+(d) the LICENSING.md
descriptions now match the 88-line file (no recipe table,
firmware section, spake2 or LGPL text exists anywhere in
the tree) and its companion-repo source pointer;
(e) the "what the review got wrong" subsection was
re-checked bullet by bullet against Review 2's text: the
":4747" bullet, the P1 line-number bullet (reversed —
Review 2's :81 citation was correct), a B7 phrase bullet
and a P2 "full phrase format" bullet were STRUCK as
attributing text Review 2 does not contain; the P8 bullet's
LGPL addition was struck (no LGPL header in the tree); the
B2 bullet was corrected to Review 2's actual task-9 demand;
the S2 bullet stands (it attributes no text). CORRECTED-
RECORD NOTE: task 4's statements describe the tree AS
SHIPPED at the Review 2 commit, per the brief — later tasks
in THIS batch changed some of the same ground again
(.gitignore negation narrowed by task 8, LICENSING.md
identifiers by task 20), so the corrected record and the
post-batch tree differ there by design, not by error.

### Group B — ci-scan, workflow, .gitignore (tasks 5–9)

Task 5 (P11 keys): DONE. The header pattern now matches
`PRIVATE KEY( BLOCK)?-----` (armoured PGP included), and a
new rule requires every *.gpg in the committable set to
list public-only under `gpg --show-keys --with-colons`
(no sec/ssb records). Plant proofs: armoured PGP private
key FAILS; binary secret-key export FAILS (sec record);
the real keyring (pub/fpr/uid only) passes.
Task 6 (P11 IP rule): DONE. A following "/" counts as CIDR
only when followed by a 1–2 digit prefix AND the address
is not preceded by "://". Plants (a well-known public DNS
address, written without its digits here so the record
itself stays scan-clean): the URL form and the bare
address-with-path form FAIL; `224.0.0.0/4` and the same
address with a /32 prefix pass; the tree's nft-golden
CIDRs still pass.
Task 7 (phrase detector): DONE, landed FIRST in its group
as briefed. New ci-scan rule: a run of >= 5 consecutive
EFF-wordlist words within a line pair is a finding
(wordlist resolved relative to the scanned tree; absent
list = rule no-ops), allowlistable only as exact
(file, run) pairs via PHRASE_ALLOW. Plant proofs: each of
the six P10 sets FAILS pre-redaction; the same text with
the task-3 marker substituted PASSES. ADJUDICATION
(coordinator): the detector's full first run on the real
tree produced 62 findings = 53 unique (file, run) pairs,
every one read in context: ordinary prose, source-code
identifier chains (wizard.py's HTML attribute words are
EFF words), Qt C++ tokens, one JPEG-library string inside
the media-worker binary. None is a generated passphrase.
All 53 pairs are allowlisted in PHRASE_ALLOW with an
adjudication comment; a real phrase set anywhere else, or
any new run in those files, still trips. Final tree scan
result is in the regression totals below.
Task 8 (.gitignore): DONE. The keyring negation is narrowed
to the single file
onionhost/rootfs-overlay/usr/share/keyrings/onionhost-archive-keyring.gpg,
and id_rsa / id_ecdsa / id_ed25519 (private halves only)
are ignored. git check-ignore proofs: a planted
keyrings/other.gpg IS ignored; id_ed25519 IS ignored;
the archive keyring is NOT ignored; .pub files unaffected.
Task 9 (workflow pin): DONE. ci-scan.yml now uses
actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683
# v4.2.2 (40-hex; SHA verified against two independent
public sources by the coordinator before dispatch).

### Group C — build-iso.sh + ship list (tasks 10–12)

Task 10 (B9, decision 3 enforcement): DONE. New tracked
ship list onionhost/recipes/SHIPPING (smf, wordpress,
dokuwiki, gitea; header comment records that the
marketplace is excluded until decision 3 is met). Both
the fetch step and the package loop in build-iso.sh — and
fetch-recipe-archives.sh standalone — resolve the SAME
selection: default = SHIPPING exactly; a different
selection via OH_RECIPES is a FATAL error unless
OH_NONRELEASE_BUILD=1 is also set, in which case both
scripts print a prominent NON-RELEASE banner and
build-iso.sh stamps release_status/recipes_source/
recipes_selected into BUILD-INFO. Ids are validated
(existing recipe.json, no duplicates). A release build is
structurally incapable of including the marketplace
recipe. Checks: factory packages for the default
selection built and listed — exactly the four SHIPPING
recipes, no onionhost-recipe-marketplace; cold-clone
simulation (archive dirs emptied): non-release override
(wordpress+dokuwiki+gitea) downloaded + pin-verified and
exited 0 past the fetch step, marketplace never attempted;
release fetch in the cold copy exited 1 AT SMF (downloaded
zip regenerated by GitHub, hash mismatch vs pin — the
accepted B6 limitation; the downloaded hash matched the
recipe refetch_note's recorded value byte-for-byte);
OH_RECIPES without the flag = FATAL from both scripts
before any work.
Task 11 (B10 keyring gate): DONE. The gate now requires
exactly one fpr record, no sec/ssb records, and fpr ==
the pinned fingerprint. Proven with a harness running the
verbatim shipped gate code: real keyring PASS; second
public key appended FATAL; secret material FATAL;
secret-only keyring (pin matched) FATAL; public-only
control PASS.
Task 12 (B12): DONE. build-iso.sh's stale header (Stage 1
rig / ~/onionhost-src claims) corrected. New top-level
README.md: entry point, host prerequisites, network
endpoints, the keyring + expected fingerprint, the ship
list + override. Mechanical check: all 17 environment
variables the build reads appear in the README.

### Group D — fetch + recipe builder (tasks 13–14)

Task 13 (B11 field parsing): DONE. The whitespace-split
read is gone: recipe fields are emitted one per line by
a Python emitter (a blank line stands for an empty field)
and missing fields fail BY NAME. (The brief's literal tab-separated read is
not implementable in bash — tab is IFS whitespace and
consecutive tabs collapse, the same shift bug; the
brief's Python alternative was used, reason in a code
comment.) Checks: empty archive.url -> "recipe.json names
no archive.url"; empty archive.file named likewise; the
real recipes parse and verify as before.
Task 14 (B11 archive copy): DONE. build-recipe-deb.sh
copies only archive/<archive.file> into the package.
Check: a stray file planted in a scratch recipe's
archive/ does not appear in `dpkg-deb -c` output; the
pinned archive does. ADJACENT FIX (pre-existing, found by
this group's testing, not a Review 3 item): the fetch
script never checked the exit status of the final
`install` placing a verified download (no set -e); when a
test /tmp filled mid-run it printed OK over a partial
copy. A one-line fail-closed guard now makes an install
failure a FAIL for that recipe; re-verified (real-tree
fetch exit 0/all OK; a partial file is refused as a
cached-pin mismatch on re-run).

### Group E — runtime gate (tasks 15–18)

HARNESS NOTE: Review 2's 21/21 gate simulation and 12/12
dashboard harnesses were never persisted to the tree (they
existed only as log claims). This group recreated both in
/tmp from the Review 2 proof paragraph's enumerated
behaviours; the coordinator has PERSISTED them into the
tree at poc/runtime-gate/ (run_sim.py,
test_runtime_dashboard.py, bin/ stubs) so the next review
can re-run them; the same persistence was done for the
Group F harness at poc/backup-proof/, and .gitignore
gained the matching poc/* exceptions for both dirs so
they are committable, not just present. Counts below are the recreated harness's
(53 assertions: 26 pre-existing behaviours + 27 new);
baseline against the pre-fix scripts reproduced S8/S9
exactly (14 of the 27 new cases failed).
Task 15 (S8 latch): DONE. onionhost-runtime-gate-check
now keeps a latch (latched.json beside status.json and
fail-closed.marker in /var/lib/onionhost/runtime/): a
violation records the union of stopped units; later runs
keep the marker and `state: runtime-violation` while any
latched unit is absent or not judged runsc-wrap; marker +
latch clear only when every latched unit is running under
runsc-wrap again, or via the explicit manual path
`onionhost-runtime-gate-check clear` (removes marker +
latch, writes status ok, logs a "CLEAR: explicit manual
clear by operator" line; unknown arguments exit 2). The
latch seeds from the marker's offenders too, so a standing
pre-fix violation stays latched after upgrade. status.json
/ marker shapes are unchanged; wizard.py untouched.
Checks: full simulation 53/53 (forced violation -> two
further timer runs leave marker + card state intact;
fix + restart clears; multi-offender partial fix does NOT
clear; manual clear works and is logged); runtime
dashboard harness 15/15; poc/gate4fix test_dashboard
11/11.
Task 16 (S9 absent vs error): DONE. The judge separates
absence (`podman container exists`: 0 present, 1 absent)
from failure (anything else, or an inspect failure for a
present container, -> judge exit 2); on exit 2 the
enforcer changes NO state (marker, latch, status
byte-identical). Checks (in the 53/53): stubbed inspect
failure for a running container -> exit 2, no state
change, nothing stopped; exists exiting 125 -> exit 2;
error during a standing latch -> state untouched.
ADJACENT DEFECT found and fixed in this group (not a
Review 3 item): the pre-fix enforcer wrote marker/status
JSON with a literal newline inside the offenders string
when two or more units offended — invalid JSON
(json.load fails). Impact was low (wizard.py keys on
marker existence first and tolerates corrupt status);
the rewrite space-normalises the list and all three
state files now parse for the multi-offender case.
Task 17 (S11 window): DONE in tree; on-box proof is
rig-deferred item 10 (+ measurement item 11). All four
container units gained `ExecStartPost=-/usr/local/bin/
onionhost-runtime-gate-check` in [Service], with a
comment: the leading "-" is deliberate — a violation in
another unit, or a gate error, must not mark the starting
unit failed and trigger Restart=on-failure; enforcement
is the check's own stop + latch. The four overlay
.container files were confirmed the shipped source of
truth (generate-configs emits no container units).
Task 18 (S10): RECORD-ONLY, as briefed — no code or
comment changes. Items 9–11 were appended to the
RIG-DEFERRED list in the Review 2 batch section above.

### Group F — onionhost-backup (task 19)

Task 19 (S12): DONE. The blanket FORBIDDEN_SUFFIXES
(".tmp") refusal is gone. Named platform secret files
(.recipe-admin.env, recipe-admin.env.tmp — exact
basenames) still refuse the backup, now with a
plain-language actionable message (names the file and
its path, says a setup/first-boot step did not finish,
tells the owner to finish the setup or remove the file
if abandoned; no "internal error" wording). Any other
*.tmp under appdata/ is SKIPPED — excluded from the
archive, recorded in the manifest's "skipped" list, and
printed as BACKUP_SKIPPED lines in the completion report
the owner sees. A *.tmp outside the appdata trees keeps
the pre-S12 refusal (deliberate scope: the brief's skip
rule covers appdata). All other forbidden-marker
behaviour unchanged. Proof harness (poc/recipes-* fixture
style) 20/20: planted x.tmp -> backup succeeds, omitted
from archive, named in report + manifest; planted
.recipe-admin.env -> plain refusal, NO backup written;
recipe-admin.env.tmp likewise; clean fixture +
shadow.php/index.php guards unchanged. The harness is
persisted at poc/backup-proof/proof.py (coordinator);
NOTE: it redirects the product's path constants into its
fixture tree but the product's staging mkdtemp is a
hard-coded literal (onionhost-backup:522-523,
dir="/var/lib/onionhost"), so the harness needs that
directory to exist on the host — on a real box it always
does; in this sandbox it was created for the run.

### Group G — recipe records + LICENSING.md (task 20)

Task 20 (P13): DONE. The companion's licence text was
verified at the frozen commit in the local companion
checkout (monero-marketplace-v2; git show of
marketplace/crates/app/Cargo.toml:5,
marketplace/crates/media-worker/Cargo.toml:5,
marketplace/deny.toml:8): all three state
AGPL-3.0-or-later — Review 3's claim is correct in full.
recipe.json's app.license and source_build.source_license
and LICENSING.md's two mentions now read
AGPL-3.0-or-later (grep: no AGPL-3.0-only remains);
app.source no longer cites a local workspace path (it
names the public companion repository + the pinned commit
in source_build); no local path remains in recipe.json.
LICENSING.md's EFF entry no longer asserts CC BY 3.0 US:
it cites EFF's copyright policy page as the source (the
page was fetched in this batch: it names CC BY 4.0 for
site content while the badge links 3.0 US — the record
cites the page rather than asserting a version for the
wordlist). Marketplace poc suite re-run: 31/31; no
fixture regeneration (metadata-only edits).

### Regression (coordinator-run, final tree)

- poc/recipes-smf unit suite: 32/32 passed.
- poc/recipes-wordpress unit suite: 39/39 passed.
- poc/recipes-dokuwiki unit suite: 37/37 passed.
- poc/recipes-gitea unit suite: 27/27 passed.
- poc/recipes-marketplace unit suite: 31/31 passed.
- poc/gate4fix run_tests: 0 assertion failures.
- poc/gate4fix test_dashboard: 0 assertion failures.
- poc/runtime-gate simulation (persisted this batch):
  53 assertions, 0 failed; runtime dashboard harness:
  0 failed.
- poc/backup-proof: ALL 20 CHECKS PASS.
- poc/d8-fix p3 adversarial cycle: 12 PASS lines, PHASE
  RESULT: PASS (proof machine re-staged from the current
  tree).
- build/ci-scan.sh on the final tree: PASS (278 files) —
  the P11 widened guards, the task-7 phrase rule with its
  53 adjudicated allowlist pairs, and the public-only
  *.gpg rule all green; the six P10 sets and the five
  additional sets from task 3 are gone. (This batch entry
  itself initially tripped the scan twice — two literal
  plant addresses quoted in the Group B section and one
  accidental wordlist run in the Group D section — and
  was reworded; the PASS above is the scan over the tree
  including this entry.)
- Spot checks: full-SHA grep clean; 16 Repo Review 3
  redaction markers; 8 P12 correction notes; SHIPPING =
  smf/wordpress/dokuwiki/gitea; ExecStartPost present in
  all four container units.

### Observed, deliberately NOT fixed in this batch

- Task 1 is a draft by design. Publication closure for
  P9 is owner-sequenced: second history rewrite (after
  this batch), then the support request covering both
  superseded commits.
- The current commit's message names the pre-rewrite
  commit in short form (task 2 note above) — settled by
  the second rewrite's message, not by a tree edit.
- S10 stays suspected (rig item 9). The "only registered
  runtime" comments in containers.conf and runsc-wrap are
  unchanged until the rig observation lands, per task 18.
- onionhost-backup's staging mkdtemp hard-codes
  /var/lib/onionhost (correct on a real box); only the
  proof harness's portability is affected (see Group F).

## REPO REVIEW 4 FIX BATCH (2026-10-20)

Scope: the fix brief in "Manioc Server — Fourth Review"
(static review of the public commit c85318a), tasks 1, 2
(record half), 4, 5, 6, 7, 8, 9, 10, 11, 13, 14, 15, plus
the record corrections under P14 and the copy fixes under
P16. Working-tree edits ONLY: no git operations, no GitHub
contact. Two brief items are NOT in this batch: task 3 (the
purge filing) is the owner's step, sequenced after the
next rewrite; task 12 (spare revocation, finding S13) is
EXCLUDED — an owner decision is pending, so this batch
neither implements revocation nor rewords the spare
promise anywhere (installer copy and EXPLAINER stand as
they were).

Owner decisions recorded for this batch (taken by the
owner's delegation, 2026-10-20):
  (1) Purge timing: file ONCE, after the next rewrite
      carries task 1's redaction. The purge request is
      DRAFTED, not filed (see task 2).
  (2) Write-time phrase rule ADOPTED as project
      convention: this log never records a generated
      phrase at all (see Standing conventions at the head
      of this log); the scanner rules are the backstop.
  (3) Keyring gate (task 8): count pub records and
      compare the fpr that follows the pub. A primary key
      with a signing subkey — the planned hardware-key
      shape — is the expected release shape and passes.
  (4) Launch copy (task 15): EXPLAINER's limited wording
      governs; launch material aligns to it, never the
      reverse.
This entry honours the values rule throughout: no phrase
or address value is quoted, in whole or in part.

### Group A — build log and history (tasks 1–2)

Task 1 (P10 remainder): DONE. The one 3-word LOGIN phrase
set the Fourth Review cited — the Part 3 Gitea
fresh-install record — is redacted with the dated marker
("[phrase removed 2026-10-20 — Repo Review 4]"). The
Review 3 batch entry's sweep claim is corrected in place
with a dated note: that sweep's floor was the 5-word rule
and the set was invisible to it by construction. Final
class sweep for this batch (task 4's 3-word rule plus the
5-word rule over the whole tree): the cited set was the
ONLY un-redacted phrase set found; after this redaction
the sweep finds zero. (Review 4 counted 21 redaction
markers in this log before this batch; this batch adds
one.)
Task 2 (P14, record half): DONE. The record states, here
and in the Review 3 entry, that the GitHub Support purge
request is a DRAFT that has NOT been filed; filing is the
owner's step after the next rewrite (decision 1 above).
The c85318a commit message's "is being pursued" wording
is NOT repeated as a claim anywhere in this record. FLAG
FOR THE NEXT REWRITE: its commit message must be written
to match — drafted, filing follows the rewrite — per
decision 1.

### Group B — ci-scan and .gitignore (tasks 4–7)

Task 4 (3-word phrase rule, P15): DONE. ci-scan gains a
3-word rule scoped to secret context: a run of three
consecutive EFF-wordlist words counts only when it
immediately follows a trigger word (login, spare, disk,
phrase), or when it is the entire word content of a short
quoted or bracketed segment. Same exact-pair allowlist as
the 5-word rule. First full run: 30 pairs, each read in
context — short prose and code fragments, a place name,
test labels, this log's own markers and correction prose —
all benign, all allowlisted as exact pairs with dated
comments. The one real hit was NOT allowlisted; it is
task 1's redaction. Check: a planted line in the trigger
form FAILS naming file and line; a plant in bare quoted
form FAILS; plants removed, the tree passes.
Task 5 (age identities + key-packet check, P15): DONE.
The key-pattern set gains the AGE-SECRET-KEY-1 prefix
followed by a long contiguous bech32 run (the rule fires
at 44+ characters; a complete identity carries more, and
the in-tree regression vector in backupkeys.py is split
across adjacent literals so it never reaches the
threshold — verified, no false positive). The public-only
GPG check now also runs on any committable file whose
first byte is an OpenPGP secret-key packet header (tag 5,
old- or new-format), not only on names ending .gpg; if
gpg lists no secret record for such a file, the header
alone is a finding. Check: a planted age identity FAILS;
a binary secret-key export renamed to a .pgp name FAILS;
a public export under a .pgp name passes; the real
keyring passes.
Task 6 (silent no-ops, P15): DONE, in the stronger form.
A missing or empty wordlist records a finding before
scanning; gpg absent from PATH records a finding; a gpg
error on a candidate file records a finding. The scan no
longer prints a bare PASS when one of its rules cannot
run. Check: run with gpg off PATH — FAIL with the refusal
line, no PASS; wordlist removed — FAIL likewise; normal
run — PASS.
Task 7 (.gitignore, P15): DONE. Added: *.agekey,
age-identity*, *.pgp, *.kbx,
application_default_credentials.json, *-credentials.json,
and the screenshot convention /shots-*/ plus
build/shots-*/ (new sibling folders only; the tracked
build/shots/ set is untouched). Check: git check-ignore
reports each of ten planted names as ignored, and the
tracked shots still list as tracked.

### Group C — build-iso.sh and README (tasks 8–10)

Task 8 (keyring gate counting, B13): DONE. The gate now
requires exactly one pub record, compares the pin
against the fpr record immediately following that pub,
and still fails on any sec/ssb record. README's keyring
section rewritten to describe exactly this, noting that a
signing subkey adds fpr records and passes. Check (gate
code extracted verbatim into a scratch harness): the
real tracked keyring passes; a throwaway key WITH a
signing subkey (record shape pub/fpr/uid/sub/fpr — the
case the old count rejected) passes with its primary
fingerprint as the harness pin; two primary keys in one
file fail; secret key material fails.
Task 9 (non-release naming, B15): DONE. A naming block
threads the existing release status: a non-release build
writes maniocserver-nonrelease-amd64.iso (flavour named
for non-prod) with volume label MANIOC_NONRELEASE; a
release build keeps its historical name and MANIOC_LIVE
exactly. README's "incapable" wording softened to
"cannot include it without a change to SHIPPING", and
the matching script comment likewise. Check: a full ISO
build is not possible in this venue; the naming block was
extracted verbatim and run across the four combinations
(release/non-release × prod/test) — file name and volume
label differ in every non-release case and are unchanged
in both release cases.
Task 10 (fork guide, B14): DONE. README gains "Forks and
rebuilders: using your own signing key", naming the four
coupled places by path — the keyring file, the pinned
fingerprint constant in build/build-iso.sh, the repo
onion address in the apt sources template (under
onionhost/rootfs-overlay/usr/lib/onionhost/golden/), and
KEYID in build/make-onionhost-repo.sh — with key
generation and PUBLIC-half export commands run in a
maintainer keyring outside the checkout, and an explicit
warning never to export secret material into the tree.
Check: the section names all four by path (verified by
grepping the section).

### Group D — recipe path validation (task 11, B16)

Task 11: DONE, in all three consumers. A recipe-supplied
value (archive.file, native_files src or dst) that is
absolute or carries a ".." path component is rejected,
naming the value and the recipe, before any write: in
build/fetch-recipe-archives.sh (before the target path is
formed), in build/build-recipe-deb.sh (a path-check block
before the staging dir is created — earlier than the
cited copy line, so the pin check's joins are covered
too), and in onionhost-recipe at manifest load (a single
validation call every command path goes through).
Component-wise comparison, so names merely containing
the two dots as a substring are unaffected. Check:
scratch recipes with a parent-traversal archive name, an
escaping native dst, and an absolute native src all fail
in each applicable consumer with nothing written outside
the scratch tree; unmodified real recipes (dokuwiki,
gitea, marketplace manifest loads; dokuwiki and
marketplace package builds) pass with no false positive.

### Group F — runtime gate latch ordering (task 13, S14)

Task 13: DONE. In onionhost-runtime-gate-check's
mismatch branch the order is now: write the marker, the
latch and the status FIRST, then stop offenders with
systemctl --no-block stop. The review's description of
the shipped order matched the code exactly. Untouched,
by design: the judge, the exit-2 path (an inspect error
still changes no state), the timer-path latch semantics,
and the manual clear subcommand. Check (harness case,
persisted in poc/runtime-gate/): the stub systemctl now
supports a kill-on-stop flag simulating the ExecStartPost
self-stop — it kills the check process mid-run — and the
new case asserts the check died (signal exit), the stop
issued was the no-block form against only the offender,
and marker, latch and status all stand afterwards with
the violation recorded; a following timer run keeps the
latch standing. Full suite: 63 assertions, 0 failed (53
prior, all still passing, + 10 new). A pre-fix
reconstruction run against the same harness fails 12
assertions including every new state assertion — the
case catches the defect it was written for. The dashboard
harness renders the fail-closed card from the killed
check's state (12/12).

### Group G — spare page and public copy (tasks 14–15)

Task 14 (spare page Next gating, S15): DONE in the
brief's preferred shape. The spare viewstep's
isNextEnabled() is now stage-dependent, mirroring the
phrase step's stage rule and the guard step's constructor
and state handling (siblings cited in the code comments):
Next is enabled only on Done, Skipped and Error. Show
and Verify gained an explicit "Discard this spare"
button recording the accepted flag as 0 and landing on
the Skipped page, whose text now states plainly that no
spare was made and a copied paper will not open the
computer. The enrolment job reads that same flag, so a
discarded or unverified spare is never enrolled. One
deliberate superset, recorded: the Choose stage is gated
too — the choice itself (create, or the page's own skip
button) must be explicit rather than drifted past;
reverting that one case is a one-line change. Check: no
Calamares compiler exists in this venue, so the closing
evidence is the traced stage × action table (every gated
stage has an in-page forward path and an explicit
discard path; no stage traps the owner), the sibling
pattern citations, balanced braces/parens in the edited
source, and the plugin build script's source list
unchanged (no new files). Rig-deferred: the on-install
exercise joins the rig list (item 12 below).
Task 15 (launch copy, P16): DONE. The launch draft's
flat claim is replaced with EXPLAINER's limits in the
post's own voice: the guarantee covers the network
address only, holds while the sandbox wiring does, and
carries the timing/uptime caveat. The site index page's
status line now describes what ships — static tiers plus
the four SHIPPING recipes and owner-installed software —
instead of dynamic software as future work; the
marketplace is not claimed (it is not on the ship list).
Check: greps confirm no unconditional leak claim remains
in the draft and the index page no longer calls dynamic
software future-only. Per decision 4, EXPLAINER itself
was not edited.

### Coordinator verification (this batch)

Every worker report was re-checked against the tree
(each arrived with its full diff; the diffs were read,
not summarised). Regression, run by the coordinator on
the final tree:
- poc/recipes-smf unit suite: 32/32 passed.
- poc/recipes-wordpress unit suite: 39/39 passed.
- poc/recipes-dokuwiki unit suite: 37/37 passed.
- poc/recipes-gitea unit suite: 27/27 passed.
- poc/recipes-marketplace unit suite: 31/31 passed.
- poc/gate4fix run_tests: 0 assertion failures.
- poc/gate4fix test_dashboard: 0 assertion failures.
- poc/runtime-gate suite: 63 assertions, 0 failed.
- poc/backup-proof: ALL 20 CHECKS PASS (venue note: the
  harness needs /var/lib/onionhost to exist and its PATH
  shims staged under /tmp; both were staged for the run,
  as in the Review 3 batch — the product behaviour on a
  real box is unaffected).
- poc/d8-fix p3 cycle, proof machine re-staged from the
  current tree: 12/12 PASS lines, PHASE RESULT: PASS.
- ci-scan: the tracked tree is clean. The in-repo run
  reports exactly two findings, both rig-user home-path
  literals inside the UNTRACKED audit pack file that was
  present before this batch (see Observed, below); the
  scan over the tracked file set alone passes, and the
  new rules add zero findings on tracked files.

### RIG-DEFERRED (additions from this batch)

12. Spare page gating (Review 4 task 14): on a fresh
    install, confirm Next is disabled on the spare
    page's Choose/Show/Verify stages, that verify and
    discard both land correctly, and that a discarded
    spare leaves no spare slot (the accepted flag 0 at
    the enrolment job).
(Items 1–11 stand as recorded in the Review 2 and
Review 3 batch entries; item 10's forced-runtime case is
also where task 13's on-box half closes.)

### Observed, deliberately NOT fixed in this batch

- The untracked audit pack file at the tree root
  (AUDIT-PACK-genespark-2026-10-20.md) contains two
  rig-user home-path literals and trips the in-repo scan.
  It predates this batch, is not tracked, and is the
  owner's briefing material — left untouched. It must
  NOT be folded into the next rewrite by a blanket
  stage-everything step; staging for the rewrite is a
  deliberate file list, as in the previous rewrites.
- The scanner excludes itself from its own text rules
  only when run inside its own tree (the CI and pre-push
  posture, which is how it ships). A walk-mode scan
  rooted at a foreign copy flags two adjacencies inside
  the scanner's own allowlist text. Observed during
  coordinator verification; the shipped posture is
  unaffected; recorded for the next scanner pass.
- Task 14's Choose-stage gating is a deliberate superset
  of the brief (recorded under task 14); one-line
  revert if the owner prefers the brief's literal scope.
- Spare revocation (S13, task 12) remains open by owner
  decision pending — see the scope note at the head of
  this entry. Nothing in this batch changes that state.

### Addendum (2026-10-20): S13 decided — promise withdrawn

Owner decision (2026-10-20): WITHDRAW the spare-revocation
promise until revocation exists (the withdraw branch of
Review 4 task 12; the implement branch was not taken). No
revocation code was written and spare enrolment behaviour
is untouched. Changes, all copy/status only:

- Installer spare page (OnionHostSpareViewStep.cpp, Choose
  stage): the "can be revoked later from the Maintenance
  menu" line is replaced — a spare cannot be taken back
  yet, its paper keeps working while it exists, and today
  the only way to end one is to erase the computer and
  reinstall. (Verified against the shipped Maintenance
  menu: restore / new disk passphrase / restart — no
  re-encryption action exists on the box today either, so
  the replacement names reinstall, the one ending that
  actually exists.)
- EXPLAINER.md (disk/phrases section): the "can be revoked
  from the dashboard" sentence is replaced to the same
  effect — no way to remove a spare yet, choose the person
  carefully, a spare opens the disk and can decrypt
  backups, erase-and-reinstall is today's only ending, a
  remove-spare action is designed but not built. The
  copied-image caveat is preserved verbatim in substance:
  an image copied while the spare was valid still opens
  with it, and full re-encryption remains the complete
  cure for that.
- DESIGN-v3-amendments.md (A3): design text unchanged; a
  dated "Implementation status" bullet now records
  revocation as DESIGNED, NOT YET IMPLEMENTED, the promise
  withdrawn from owner-facing copy the same day, and
  implementation still planned against that spec.
- WALKTHROUGH-SPEC-v1.md (C4): same treatment — a dated
  status note under the Spare key bullet; the design and
  its honesty requirements stand.
- BACKUP-RESTORE-ACCEPTANCE-2026-10-12.md item 12: a
  dated status note marks it not yet testable and states
  the interim rule (no owner-facing copy may promise or
  imply revocation at all); the item takes effect when
  revocation is built.
- Swept and deliberately left: BOOT-ACCEPTANCE-TESTS-
  slice1.md already frames spare boot/revoke tests as
  explicitly deferred/not built; BOOT-CHAIN-REVIEW-2 and
  TIMING-REVIEW-RESPONSE are dated review records whose
  "revoke" mentions concern re-key failure modes and onion
  keys, not the product promise; OWNER-GUIDE, site/,
  outreach/, the wizard and the Maintenance menu contain
  no revocation claim.

S13 status after this addendum: the false promise is
CLOSED by withdrawal. Revocation itself — killing the
spare's LUKS slot and removing its backup recipient, per
DESIGN-v3 A3 — is carried as an open, designed-not-built
product gap, planned but unscheduled. When it is built,
the honest copy (A3 revocation honesty, acceptance item
12) is restored with it and proven on the rig.

## SPARE FEATURE REMOVED — S13 CLOSED BY REMOVAL (2026-10-20)

Owner decision, same evening, superseding the addendum
above: REMOVE the spare-passphrase feature entirely. One
single disk phrase; if it is lost, everything is over. The
withdraw edits made earlier in the day (installer + EXPLAINER
copy) are reconciled into this removal — nothing of them
survives as spare copy, because there is no spare. Design
record: amendment A25 in DESIGN-v3-amendments.md, which
supersedes A3's spare provisions, A19.1's three-slot layout
and A11's five-concept budget (now FOUR concepts: disk
phrase, login words, restart card, Repair button). No
revocation code was needed and none was written; spare
enrolment behaviour was not adjusted but deleted. Working-
tree edits only, as with the batches.

Per-site evidence (every site swept, changed or
deliberately left):

INSTALLER
- onionhostphrase viewstep (OnionHostPhraseViewStep.cpp):
  the second generatePhrase call is gone; the
  onionhostSpareCandidate / onionhostSpareAccepted
  GlobalStorage inserts are gone; the debug line records
  the single phrase. The Show page's loss sentence now
  states the whole stake at the moment of creation: the
  paper is the only key, there is no spare and no other
  way in, and losing it loses the computer, the website
  and even the backups. The .h header comment no longer
  mentions a spare candidate. The Done page never named
  a next-step spare and is unchanged.
- The spare viewstep module is DELETED outright (not
  merely unregistered): plugin-src/onionhostspare/
  (.cpp + .h), calamares/modules/onionhostspare/
  module.desc, and rootfs-overlay/etc/calamares/modules/
  onionhostspare.conf. The build wiring proved simple
  enough that excision is clean: build-plugins.sh no
  longer builds it; build-iso.sh drops it from both
  plugin loops, from the BUILD-INFO hash lines
  (plugin_spare_sha256 is gone), and from the
  settings.conf show-sequence insertion (phrase page
  only after keyboard now). What remains in the tree:
  nothing of the module. LICENSING.md drops its two
  file lines; ci-scan.sh drops its one allowlist pair
  for the deleted file.

BOOT-KEY JOB (onionhostbootkey/main.py)
- The spare enrolment block is deleted: no second
  luksAddKey, no spare temp file (the shredded-secret
  list is back to phrase + phrase-new). The conversion
  still ends, as before, at exactly one PBKDF2 phrase
  slot — now the only phrase slot by construction.
- _write_role_map writes slots {MAIN, KEYFILE} only;
  the KEYFILE determination no longer subtracts a
  spare. The docstring's layout sentence and job list
  are updated (job 4 is now the role map).

BACKUP KEYS (onionhostbackupkeys/main.py)
- No spare salt, no spare derivation, no spare smoke
  test. backup.json is written as
  {"version": 1, "main": {salt, recipient}} — the main
  recipient only. The docstring's schema shows the same.

RUNTIME TOOLS
- onionhost-backup: recipients/salts are read from the
  "main" entry only; the backup metadata's salts map
  carries "main" only. (Encryption itself is unchanged:
  age to the listed recipients — now always exactly one.)
- onionhost-restore: the decrypt path derives identities
  from the main salt only. A pre-removal dual-recipient
  backup still opens with its MAIN phrase, so the
  removal orphans no backup; a spare phrase, where one
  was ever written down, simply opens nothing anymore.
- onionhost-rekey: the status line no longer prints a
  SPARE slot; the backup-recipient refresh comment now
  says the main entry is the only entry. Rekey reads
  slots.MAIN / slots.KEYFILE only, as before.

COPY (one secret, stated plainly; no spare offered,
mentioned as available, or promised anywhere)
- EXPLAINER.md: the model line is four ideas (spare
  dropped); the spare bullet is deleted outright; the
  "One paper secret" bullet now closes with the only-
  key statement — no spare, no second copy, no back
  door; a sealed machine whose paper is lost is gone
  for good, backups included. The running-machine
  "Lost the paper?" bullet (A18) is untouched and does
  not contradict it.
- WALKTHROUGH-SPEC-v1.md: concept line is FOUR (A11 as
  amended by A25); C3's backup text drops the spare-
  recipient parenthetical; C4's Spare key bullet is
  replaced by a REMOVED (A25) note; section 6 item 1
  (the spare-placement conflict) is marked superseded/
  moot; the Sources list is adjusted to match.
- site/index.html: "Four things to learn, total" (the
  optional spare is out of the list).
- outreach/TESTER-SESSION-KIT-v1.md: session row 3 now
  asks whether the tester understands the paper is the
  ONLY key; the budget paragraph is the four-concept
  budget (A11 as amended by A25), fifth-concept wording.
- STAGE2-RUNBOOK.md: the enrol-or-skip drill step is
  replaced by the note that there is no spare phrase.
- BACKUP-RESTORE-ACCEPTANCE item 12: status note now
  records the item as MOOT by removal (retained as the
  honesty spec for any future second-key design). The
  final sweep also annotated item 2's dual-recipient
  clause and the Sources line to match (both now carry
  the removed-by-A25 status).
- BOOT-ACCEPTANCE-TESTS-slice1.md: the deferred SPARE
  test bullet is marked MOOT by removal.
- DESIGN-v3-amendments.md: the A3 implementation-status
  bullet now records supersession by A25; A25 itself is
  appended as the governing record.
- OWNER-GUIDE-2026-10-15.md, the wizard and the
  Dashboard: swept — they never carried a spare claim;
  no change needed.

SWEPT AND DELIBERATELY LEFT (history and non-feature
uses, recorded so the sweep is auditable)
- Dated records: DESIGN-v2.md, the review packs,
  BOOT-CHAIN-REVIEW-2, TIMING-*, FIX-BRIEF-ENCRYPTION-
  GUARD, REBRAND-* reports, POC-RESULTS, POC-GATE1-
  RUNBOOK, and this log's own earlier entries — the
  spare appears there as what it was at the time.
- Historical slice drivers: build/boottest-slice2.py
  (spareboot mode), build/s5b-analyze.py (dual-recipient
  decrypt check), stage1/gateR-rig.sh (a comment). None
  is in the regression set; they document slices that
  ran against the feature while it existed.
- Non-feature "spare": php-fpm's pm.min/max_spare_servers
  in the golden template; build-partition.sh's "does not
  have to spare" idiom; the ci-scan 3-word rule's trigger
  vocabulary still includes the word spare (detection
  vocabulary for secret context, not a feature); the EFF
  wordlist contains the word, as it contains all words;
  the marketplace media-worker binary contains the
  string inside library text (not this feature).

TESTS — assertion changes (the only ones)
- poc/backup-proof/proof.py: the fixture's backup.json
  no longer carries a "spare": null field, modelling the
  shipped record shape. Fixture change consequent on
  the backup.json format change; no assertion touched.
- No other test file was modified. In particular the
  Review 4 batch's spare-page assertions do not exist in
  any persisted suite (task 14 shipped without a
  compiler in venue; its proof was a traced table), so
  there was nothing spare-specific left to retire.

REGRESSION (final tree)
- SMF 32/32, WordPress 39/39, DokuWiki 37/37, Gitea
  27/27, marketplace 31/31.
- gate4fix run_tests 0 failed; test_dashboard 0 failed.
- runtime-gate simulation 63/63 (stubs staged at
  /tmp/rgate/bin, as the harness requires); runtime
  dashboard harness 0 failed.
- backup-proof 20/20 against the main-only fixture.
- d8-fix p3-gitea 12/12, PHASE RESULT: PASS (proof
  machine re-staged from the current tree).
- Python syntax: all five edited Python tools compile;
  bash -n / sh -n clean on the edited shell scripts.
  (The C++ phrase viewstep cannot be compiled in this
  venue — no Calamares toolchain; its edit is deletions
  plus copy, brace-checked by eye against the sibling
  structure. The installer end-to-end re-proof is the
  rig session's, below.)
- ci-scan: the only findings on the working tree are
  the two known rig-user home-path literals in the
  UNTRACKED audit pack file (owner's briefing material,
  untouched, must never be staged). Zero findings in
  any tracked file — the tracked tree is clean,
  including every file this removal touched.

RIG LIST CONSEQUENCE
- Review 4 rig item 12 (spare-page gating) is SUPERSEDED
  — there is no spare page to gate. The pending fresh-
  install rig items now also re-prove the single-phrase
  flow end to end: no spare page in the sequence, exactly
  MAIN + KEYFILE in the role map, backup.json with the
  main recipient only, and a backup made on the box
  opening with the one paper phrase.

S13 STATUS: CLOSED by removal. The designed-not-built
gap recorded in the addendum above no longer exists,
because the feature it belonged to no longer exists.

## REPO REVIEW 5 FIX BATCH (2026-10-20)

Scope: the tree-doable half of the Fifth Review's fix brief
(the narrow pass at 0873e86; the review itself discloses that
its PRIMARY scope — the systematic network-vector
deanonymization hunt — was not completed and remains open,
routed to a human security reviewer and the hardware
session). Working-tree edits only; no git operations, no
GitHub contact. The maintainer tree and the untracked audit
pack file were not touched.

### E-1 — PHP version disclosure on the app tier: DONE (static half)

All three app nginx templates (golden/nginx-app-php,
nginx-app-native, nginx-app-native-tcp) now carry
`more_clear_headers 'X-Powered-By';` and
`more_clear_headers 'Server';` beside the existing Date
clearing, and golden/php-fpm-app.conf.tmpl sets
`php_admin_value[expose_php] = 0` in the pool, so the header
is not emitted at the source either. Check (static, run):
grep over golden/ shows both clears in all three templates
and expose_php present (previously zero hits in the whole
directory). The review's acceptance — fetch a PHP page over
the socket and confirm neither header carries a version —
needs the running stack: RIG ITEM 13 below.

### P-1 — EXIF-scrub claim scoped (copy half): DONE

site/index.html: the scrub sentence now reads "photos added
through the built-in page and journal editors", followed by
an explicit parenthetical that app uploads are published as
the app handles them, GPS included; the rig-claim sentence
now says "the built-in editors' privacy check".
OWNER-GUIDE-2026-10-15.md §3 gained a bolded warning up
front: the platform does NOT scrub app-tier uploads, a phone
photo usually carries GPS EXIF, strip before uploading or
use an app/plugin that does. Check (run): a sweep for
scrub/metadata claims across site/, outreach/ and
EXPLAINER.md finds no other public sentence; no public
sentence now states or implies platform-wide scrubbing.
No app-tier scrubbing was built — copy only, per the brief.

### B-2 — runsc-wrap unrecognised branch strips netns: DONE

The netns strip was factored into a shared _strip_netns
helper (failed write-back still fails closed) and is now
called by BOTH the website and the unrecognised branches;
the tor branch is untouched by design. Harness note: no
persisted wrapper harness existed — the Review 2 batch's
36/36 wrapper proof lived in worker scratch, the same gap
the Review 3 batch found for the gate harnesses. A harness
is now persisted at poc/runsc-wrap/run_tests.py (loads the
real wrapper as a module, captures execv, drives bundle
fixtures; .gitignore exception added beside the runtime-gate
and backup-proof ones). Pre-fix control: exactly one
failure — the new W5 case (unrecognised bundle carrying a
netns entry kept it). Post-fix: 21/21 assertions pass,
including tor-spec byte-identity and both fail-closed
cases. Whether runsc's own precedence would have overridden
the entry anyway remains a box observation: RIG ITEM 16.

### D-1 (code half) + F-P1-1 — probe decoupled; shell dropped: DONE

onionhost-update: every health judgement in main() follows
a stack restart this run performed (install, rollback,
fail-closed recovery). All three call sites now go through
health_ok_after_restart(), which first sleeps a settle drawn
per judgement from ONIONHOST_HEALTH_SETTLE_MIN..MAX
(defaults 1800..21600 s — 30 min to 6 h), then runs
health_ok() unchanged. Reasoning, recorded per the brief:
the verdict stays atomic with the install/rollback state
machine that owns the prev-debs, floors and the fail-closed
marker; splitting the verdict into a second duty would need
a cross-process state hand-off, for a correlation gain the
drawn settle already achieves (the rendezvous no longer
follows the fetch within minutes — it lands at a scattered
time). The cost matches the pre-existing republication
budget's posture: the restarted stack serves (or fails to)
during the settle, exactly as it already did while the
budget ran. The recovery path takes the settle too — a
recovering box's probe is the same rendezvous.
F-P1-1: _probe_once no longer uses shell=True; HEALTH_CMD
is shlex-split to a fixed argv (the env override still
names the command for tests, but can no longer carry shell
syntax), and an OSError from the exec is a failed probe,
logged. grep confirms no shell=True remains in the tool.
Checks (run): poc/gate4fix run_tests gains S9 (settle
pinned at 3 s; the first probe's stub-recorded epoch lands
>= 2 s after the restart epoch, and the settle wait is in
the log) and S10 (shipped defaults: floor >= 1800 s, spread
>= 3600 s); the stubs now record epochs. Existing scenarios
run with the settle pinned to 0 via the harness env, as with
the other env-tunable budget knobs. Full gate4fix suite:
0 assertion failures. D-1's circuit-isolation half is not
settleable from the tree: RIG ITEM 15 below.

### P-2 — malformed hash in audit/INTERIM-SUMMARY.md: DONE

Verified before writing: sha256 of
releases/onionhost-amd64.iso recomputed in this batch =
the value published at site/index.html (both 64 hex chars,
identical). The INTERIM-SUMMARY.md:16 token was 62 chars and
matched neither; it is corrected to the recomputed digest.
So the published download hash was always right — only the
audit record's transcription was garbled.

### P-4 — test-flavour SSH pubkey out of tracked source: DONE

build/build-iso.sh no longer embeds the operator pubkey.
The outer script resolves it from OH_TEST_SSH_PUBKEY, else
from the first line of $OH_TEST_SSH_PUBKEY_FILE (default
$HOME/.onionhost-test-pubkey, outside the tree), passes it
to the customise chroot beside OH_FLAVOUR/OH_PROBE, and the
customise step writes it under its own empty-key guard.
A FLAVOUR=test build with no key — or a malformed one —
hits a FATAL naming both supply routes and exits before
any building; the prod path never reads it. README.md's
environment table gains both variables. Checks (run):
bash -n clean; git grep finds no ssh key material anywhere
in tracked files; the resolution block exercised standalone
in four cases (env-supplied, file-supplied, prod without a
key passes, test without a key FATALs, test with a garbage
key FATALs).

### EXCLUDED from this batch (recorded, not silently dropped)

- B-1 (/run/onionhost/web at 0777): NOT changed. Whether
  nginx-under-gVisor still binds at 0770 is a rig question —
  generate-configs' own comments record a past 0755 bind
  failure — so the tightening goes to the box, not the
  tree: RIG ITEM 14 below, with the review's check.
- P-3's media-worker rebuild: belongs to the decision-3
  rebuild-from-pinned-source work, not this batch. The
  builder-username / GCP-label half of P-3 and its two
  owner questions were not tree fixes and are untouched.
- The primary network-vector deanonymization hunt: not a
  tree fix. It remains open exactly as the review left it.

### RIG-DEFERRED (additions from this batch)

13. E-1 acceptance on the box: with an app-tier site live,
    fetch a PHP page through the onion path and confirm
    neither X-Powered-By nor Server carries a version.
14. B-1: tighten /run/onionhost/web to 0770 owned by the
    website container's mapped uid (or make the http.sock
    swap a rename a non-owner cannot pre-empt). Check:
    nginx still binds under gVisor at 0770, publishing
    still rotates, and no other local uid can plant or
    replace b1.sock / http.sock.
15. D-1 on the box: confirm container U's circuit for the
    post-update self-probe is isolated from its
    package-fetch circuit, and observe that a probe no
    longer follows an update within minutes (the settle
    in effect).
16. B-2 confirmation: on a live bundle, confirm runsc
    starts classified and unclassified bundles with the
    stripped spec and no regression (the strip makes the
    precedence question moot; this is the receipt).
(Items 1–11 stand as recorded in the Review 2/3 batch
entries; item 12 was superseded by the spare removal.)

### Regression (final tree)

- poc/recipes-smf 32/32, wordpress 39/39, dokuwiki 37/37,
  gitea 27/27, marketplace 31/31.
- poc/gate4fix run_tests: 0 assertion failures (incl. the
  new S9/S10); test_dashboard: 0 failed.
- poc/runtime-gate run_sim: 63 assertions, 0 failed;
  test_runtime_dashboard: 0 failed.
- poc/runsc-wrap run_tests (new): 21/21.
- poc/backup-proof: ALL 20 CHECKS PASS (venue staging as
  in prior batches).
- poc/d8-fix p3-gitea, proof machine re-staged from the
  current tree: 12/12 PASS, PHASE RESULT: PASS.
- Edited Python compiles (onionhost-update, runsc-wrap);
  bash -n clean on build-iso.sh.
- ci-scan: PASS over the tracked file set (274 files, run
  in a scratch copy of the tracked tree). The in-repo run
  reports exactly the two known findings, both rig-user
  home-path literals in the UNTRACKED audit pack file —
  untouched, as instructed. One process note: the scan's
  phrase rule caught this batch's OWN new updater log line
  (a 5-word EFF run spanning the line pair); the line was
  reworded rather than allowlisted, and the re-scan is
  clean — the backstop working as intended on its own
  authors.


## PUBLIC TREE CHANGE (2026-10-20) — GCP APPEAL DRAFT REMOVED

By owner decision (2026-10-20, on Review 5's owner question 1):
`GCP-APPEAL-DRAFT-2026-10-14.md` is removed from the public
tree. It is process history (the project's cloud account
suspension and reinstatement appeal), accurate but quotable
out of context, and not product. The file is preserved in the
maintainer's private records; the events themselves remain
part of this log's history. The removal lands in the fourth
history rewrite together with the Review 5 fix batch; the
superseded commit joins the GitHub purge request's list
(four SHAs; the request remains drafted, not filed).


## RECIPES ARE INSTALLERS — A26 (2026-10-21)

Owner decision (Cameron, 2026-10-21): recipes are installers,
not update channels — the platform installs a recipe app once;
every future update of that app is the owner's. This closed
the question LOCAL-MODS-UPDATE-POLICY-BRIEF-2026-10-15.md had
left open (plain carryover vs surgical merge vs keep-edited-
and-flag): all three are decided against, no merge machinery
was built, and the brief is marked superseded. The design
record is amendment A26 in DESIGN-v3-amendments.md. Working-
tree changes only; nothing committed or published by this
batch.

### Rulings taken from the code's own evidence

- "INSTALLED" (the state the update path gates on) is the
  applier's state record — /var/lib/onionhost/recipes/<id>/
  state.json carrying installed=True plus the applied
  version. Every writer that completes an installation (the
  tree apply after its swap, the native apply after placing
  the binary, the install hook at verification) writes
  exactly that shape, and no writer writes it earlier, so: a
  completed install is unambiguous; a first install that
  failed before completion leaves no such record and the
  install path stays open for it; a rollback rewrites the
  same record with the restored version — still installed.
  The dpkg state of the recipe package is NOT the judge:
  the ISO's firstrun job registers every SHIPPING recipe
  package on every box, selected or not.
- Publish is not an update run. onionhost-publish calls
  apply directly; it is the first-install mechanism and the
  owner's own Go Live act, so its semantics are unchanged
  (A26 gates the update path: the updater and the package
  postinst). How the first install works is untouched.
- Recipe packages sit entirely outside the update channel:
  the updater does not refresh even an unused payload, so a
  fresh install takes the payload the box carries (the
  factory set). Standing high-water marks and floors that
  pre-A26 updaters recorded for recipe packages are simply
  never consulted again; a pre-A26 fail-closed marker that
  names recipe packages is read for its presence only, as
  before, and new markers record the platform package alone.

### What changed, per site

- onionhost/rootfs-overlay/usr/local/bin/onionhost-update:
  the managed set is the platform package alone. Recipe
  packages (discovered from dpkg as before) are observe-
  only: an observation pass records each one's candidate,
  and for an INSTALLED app with a newer package it appends
  an owner_maintained entry (package, recipe, app name,
  installed + available versions) to status.json and logs
  the state as expected, not an error. The pass installs
  nothing and cannot affect the exit code, a rollback, or
  fail-closed. Recipe packages are still unheld on entry
  and HELD across the Debian phase, so the generic upgrade
  cannot fire a recipe postinst inside an update run. The
  healthy end-of-run detail names the app when an
  owner-maintained update exists. Header records the A26
  rules beside the A6 ones.
- onionhost/rootfs-overlay/usr/local/bin/onionhost-recipe:
  new `is-installed <id>` query (exit 0 iff the state
  record carries a completed apply) — the one definition
  of installed, shared by the postinst gate; and a new
  install-time floor gate: on a FIRST install (the
  applier's own first_install judgement, both the tree and
  native paths), a payload version below the floor its own
  package declares (floor.json beside the manifest) is
  refused before the app is placed. Header rewritten where
  it described the old postinst update choreography.
- build/build-recipe-deb.sh: the generated postinst now
  gates on `onionhost-recipe is-installed` — over an
  installed app it prints the owner-maintained note and
  exits 0 (payload updated on disk, app untouched); with
  no completed install it applies as before. The control
  Description and the builder header say the same.
- wizard.py: the app-pick page states the model at the
  moment of choosing ("it installs the software once, and
  after that updating it is up to you..."), the A23 comment
  is corrected, and update_status_text appends the
  owner-maintained sentence (app named) when status.json
  carries it on a healthy state; the marker/fail-closed
  wording still wins, and the six Gate 4 Dashboard strings
  are byte-unchanged for records without the new field.
- OWNER-GUIDE-2026-10-15.md: §1's apps bullet and the
  protections scope corrected (they cover system/platform;
  the app is never touched); §2 item 6 and §5 now count
  app updates as the owner's; §3's two stale claims fixed
  (WordPress core updates are the owner's file replacement,
  not the recipe channel; the own-install paragraph no
  longer trades on a channel packaged apps also lack);
  §4 is the real section at last — the rule, what the
  Dashboard mention means, the three ways an owner updates
  inside the sealed box (the app's own upload tools;
  replacing files from the desktop with the per-app
  keep-list read off the manifests: WordPress wp-config.php
  + wp-content, DokuWiki data/ + conf/, SMF Settings.php +
  attachments/ + custom_avatar/, Gitea the one program
  file), and doing nothing — allowed, the owner's risk,
  with the sealed room's guarantee stated separately. The
  header's PENDING note is replaced by the A26 citation.

### One defect this batch introduced and the regression caught

The first cut of the floor gate shelled out to
`dpkg --compare-versions`. The d8-fix proof machine — a
minimal rootfs with a curated binary set and no dpkg —
failed its P3 applies with "No such file or directory:
'dpkg'": the applier had grown a dependency it never had.
The gate now compares versions in pure Python (dpkg's own
verrevcmp algorithm: epoch, upstream, revision; tilde and
letter ordering), verified against the real dpkg on 16
version pairs (every recipe's shipped version and floor,
oh.10 rollovers, epochs, tildes, revisions — 0 disagreements)
and pinned as standing assertions in the new proof venue.

### Tests — new, and what did not change

- NEW poc/installer-policy/run_proofs.py (26 assertions):
  builds v1/v2/v3 WordPress packages with the real builder
  (v2 = honest repackage: bumped version, one shipped
  file's bytes changed inside the archive, pin updated;
  v3 = v2 with the floor raised above its version) and
  proves, with the real applier and the real generated
  postinst run against the real absolute paths in a mount
  namespace: (A) install v1 to completion (apply + install
  hook against the fake installer), owner edits (a shipped
  file edited, a plugin added, an upload added, the config
  tweaked), then configure v2 → the postinst reports the
  app already installed and the app tree plus the recipe
  state record are BYTE-IDENTICAL, v2's changed file
  nowhere in the tree; (B) a fresh venue configuring v2
  installs at the v2 version with the v2 file content;
  (C1) the floor-raised payload is refused on a first
  install, placing nothing; (C2) the same payload over the
  completed install applies — a floor never judges an
  installed app. Plus the _debver_cmp agreement checks.
- NEW gate4fix scenarios R1–R4 (28 assertions) with the
  stubs taught recipes (per-package ctl versions, an
  apt-get call log with simulated installs, an apt-mark
  stub that records holds): R1 platform updates healthy
  while an installed app's newer recipe package is never
  installed and is reported owner_maintained; R2 fail-
  closed recovery succeeds with the recipe's floor
  standing at 99.0 above the installed app; R3 a present
  package with no installed app reports and installs
  nothing; R4 a replayed old recipe version draws no
  downgrade refusal. S1–S10 pass unchanged.
- NEW test_dashboard cases (5): the owner-maintained
  Dashboard text on up-to-date and updated, its absence
  with an empty list, no colouring of a fetch failure, and
  the marker still winning over it.
- NO existing assertion was changed. The old update-swap
  behaviour was asserted only by the 2026-10-14 rig
  acceptance runs (recorded in this log, not a persisted
  host suite); the persisted recipe suites drive the
  applier as a tool — the installer's semantics — and
  publish-style re-apply with data carryover remains its
  contract, so all five pass unmodified at their baselines.
- Venue staging recreated where /tmp had been wiped
  between sessions (harness-owned, not product): the
  runtime-gate sim's podman/systemctl/logger stubs at
  /tmp/rgate/bin (rebuilt to the contract run_sim.py
  defines, incl. stop-removes-the-container and the S14
  kill_on_stop behaviour) and backup-proof's shims at
  /tmp/backup-proof/bin; the d8 proof machine was
  re-staged from the current tree as usual.

### Regression (final tree)

- poc/recipes-smf 32/32, wordpress 39/39, dokuwiki 37/37,
  gitea 27/27, marketplace 31/31.
- poc/gate4fix run_tests: 0 assertion failures (S1–S10 +
  R1–R4); test_dashboard: 0 failed (Gate 4 six + A26 five).
- poc/installer-policy run_proofs: 26 assertions, 0 failed.
- poc/runtime-gate run_sim: 63 assertions, 0 failed;
  test_runtime_dashboard: 0 failed.
- poc/runsc-wrap run_tests: 21/21 (0 failed).
- poc/backup-proof: ALL 20 CHECKS PASS.
- poc/d8-fix p3-gitea, proof machine re-staged from the
  current tree: 12/12 PASS, PHASE RESULT: PASS.
- Edited Python compiles (onionhost-update, onionhost-
  recipe, wizard); bash -n / sh -n clean on
  build-recipe-deb.sh and the generated postinst.
- ci-scan over the working tree: the only findings are
  the two known rig-user home-path literals in the
  UNTRACKED audit pack file — untouched, as instructed;
  the tracked set is clean. (The scan's phrase rule caught
  one of this batch's own new updater comments mid-flight;
  reworded, not allowlisted, and the re-scan is clean.)

Standing rig list unchanged: the A26 behaviour is proven
host-side end to end; re-proof on a real box (an update run
against a live installed app) joins the pending rig
session's list with the other deferred items.

## DEANON AUDIT FIX BATCH (2026-10-21)

Scope: the 20-item fix brief (section 5) of the interim
deanonymization audit (~/workspace/onionhost-deanon-audit/
DEANON-AUDIT-2026-10-21.md, register R-01..R-28), authorised by
the owner 2026-10-21 and executed in brief order. Working-tree
changes only; nothing committed or published by this batch.
Rig-only proofs were NOT simulated in the sandbox: each item
below separates what the tree now does from the rig proof still
owed, and the rig additions are numbered 18-22 (the standing
list's items 1-17 are unchanged). The audit's five reserved
human-reviewer judgement calls were NOT decided; they are
restated at the end.

### Per-item verdicts

1. R-01 (Tor-class host-UDS scope) — FIXED, tree half.
   runsc-wrap now splits the tor class by the torrc path in
   the bundle args: container A (torrc) keeps --host-uds=all
   (it must CONNECT to B's http.sock); container U
   (client-torrc) gets --host-uds=create — U only binds its
   SOCKS/control listeners and host-side consumers connect,
   the pattern B's b1.sock already proves, so U loses host-UDS
   connect reach entirely. Spec untouched for both; no
   --network flag for either. poc/runsc-wrap gains case W10
   (client-tor bundle: byte-identical spec, create, no
   --network flag); suite 24/24. Whether create mode actually
   bounds the gofer on the real stack is the canary's question
   — rig item 18, now the rig list's top priority: from
   inside running A and U, attempt connects to (a) a canary
   host socket outside the containers' mounts, (b) the podman
   socket path, (c) the peer's SOCKS/control paths, and
   verify U still serves its SOCKS socket under create. If
   the canary shows U broken or the scoping illusory, the
   audit's alternative (document the mount-bounded proof)
   is the fallback — the question does not ship open in a
   release either way.
2. R-02 (SMF jQuery from Google's CDN) — FIXED. The seed
   tail now INSERTs jquery_source='local' (INSERT..ON
   DUPLICATE KEY, because the row's presence in a fresh
   install is not guaranteed), so Load.php serves the copy
   SMF ships in its own theme scripts. Sweep of the other
   visitor-side patterns in the shipped SMF tree: the
   Load.php CDN table is the only load-by-default external
   script source; the remaining external URLs in Sources/
   Who.php are credit hyperlinks (no fetch on view). One
   residual found and recorded, not fixed: Profile-Export
   .php:1877 hardcodes the Google CDN jQuery into the
   admin-only member-data export document. It is not the
   published site path and cannot be seeded away (hardcoded
   in application code, which the recipe does not patch);
   it dies at the wall in the sealed room like every other
   fetch. SMF suite 33/33 through the real seed import.
3. R-03 (RECIPE-VERSION.txt served from the docroot) —
   FIXED by relocation. The marker is now written by
   _save_state() into the recipe's state directory
   (STATE_ROOT/<id>/RECIPE-VERSION.txt, beside state.json),
   so every state writer (each apply mode, both
   rollbacks, the install hook) keeps it truthful and it
   never enters the served tree; the staging write is gone.
   Consumer check first: the only tracked-tree reference
   was the writer itself (the Dashboard and updater read
   state.json, never the marker). The two poc harnesses
   that consumed it (recipes-smf, recipes-dokuwiki) now
   read the state-dir path and each gained a check that
   the docroot does NOT contain the file. (Per-recipe fetch
   verification rides the recipe suites' normal serving
   proofs; a dedicated rig fetch per recipe is subsumed by
   rig item 18's session plan.)
4. R-04 (backup outer layer names the site + the moment) —
   FIXED. Backup FORMAT is now 3: meta.json carries only
   {format, kind, salts, recipients} — no onion address,
   no creation time — and payload.age is written with an
   explicit mtime-0 tar header (meta.json already had one;
   the ciphertext member previously leaked the creation
   moment through tar.add). The address and time live only
   in the encrypted manifest, as before. onionhost-restore
   accepts formats 1, 2 and 3 (wrapper and manifest);
   formats 1/2 restore exactly as before; at the end of a
   format-3 restore the reported address comes from the
   verified manifest. The verify comment's "four ways" is
   corrected to the three checks the code actually
   performs (manifest, bundled hostname, pubkey-recomputed)
   — the metadata copy was never compared and no longer
   exists. poc/backup-proof gains the outer-min case
   driving the REAL restore module (_read_wrapper +
   _verify) against a fixture with a self-consistent onion
   identity: outer meta carries neither the address nor a
   created key, every outer tar member has mtime 0, and
   the payload still verifies with the address recovered
   from the manifest. Suite 27/27. Copy paired in
   EXPLAINER section 4 (item 6 below).
5. R-10 (container U outside the firewall gate) — FIXED.
   onionhost-u.container now mirrors A's binding:
   BindsTo=onionhost-nft-gate.service (+ After), and
   onionhost-nft-load.service joins its Wants/After.
   onionhost-nft-gate-check stops BOTH onionhost-a and
   onionhost-u on mismatch (previously only A — the client
   container, the one that originates clearnet-bound
   traffic, kept running under a firewall the platform had
   judged wrong) and gained the house test seams
   (ONIONHOST_NFT_GATE, ONIONHOST_SYSTEMCTL).
   poc/runtime-gate run_sim gains 5 cases (mismatch stops
   A and U; match and gate-error stop nothing); sim 68/68,
   dashboard harness 0 failed.
6. R-08 (EXIF overclaim in shipped copy) — FIXED.
   EXPLAINER section 3's unscoped sentence now matches the
   site's scoped wording (scrub belongs to the built-in
   page/journal editors; app uploads are published as the
   app handles them), and both launch-post instances
   (LAUNCH-POSTS-DRAFT-2026-10-12.md) are scoped the same
   way. Sweep covered site/, outreach/, EXPLAINER.md,
   OWNER-GUIDE (already scoped) and the wizard/dashboard
   strings (sitegen's claim is about its own ingest —
   accurate). On the brief's served-anywhere question:
   EXPLAINER.md is referenced by nothing in the build or
   the shipped tree — it is a repository document only, so
   the retire/refresh branch was not triggered; its
   broader pre-app staleness (it still describes a
   static-only v1) is editorial and outside this brief.
7. R-09 (the wizard warning the docs claim exists) — BUILT.
   The Go Live page (page_s1_golive) now carries the
   warning before the button. Shipped wording, verbatim:
   "One honest warning before you go live. This system
   hides your computer's network address - it cannot hide
   when the computer is online. If being physically
   located would put you in danger, do not rely on hosting
   from your home." EXPLAINER section 2's claim ("The
   setup wizard shows this warning in plain language,
   including the sentence: if being physically located
   would put you in danger, do not rely on hosting from
   your home") and OWNER-GUIDE section 2 item 7 are now
   true of the shipped wizard.
8. R-11 (exact app versions served to visitors) — FIXED
   where a supported surface exists. DokuWiki: the recipe
   overlay now denies /VERSION, /README and /SECURITY.md
   (exact-match locations; all three files verified
   present in the shipped archive's docroot). WordPress:
   /readme.html denied in the recipe overlay, and the
   sealed must-use plugin now also suppresses the feed
   generator (the_generator -> empty on all feed formats)
   and strips the default ?ver= version parameter from
   enqueued script/style URLs (script_loader_src /
   style_loader_src). Two surfaces have NO supported
   off-switch and are recorded, not patched around: SMF's
   page footer prints SMF_FULL_VERSION via
   theme_copyright() (Sources/Subs.php:4677-4678 — a
   printf of the language string; no settings toggle
   exists), and Gitea exposes its version with no config
   surface (its footer/API version are compiled in). Both
   would need application-code or theme patches, which
   the recipe discipline does not do; the audit's Gap 4
   rig fetch remains the exposure record for both.
9. R-06 (golden ruleset's root clearnet permission) —
   MECHANICAL PART ONLY. The stale comment (it cited
   DESIGN-v2 section 7's superseded "host apt is clearnet
   HTTPS" design) is replaced with a truthful one: nothing
   shipped sends that traffic (apt is Tor-only, stock
   methods disabled), the permission is retained, and the
   narrow-vs-accept question is the reviewer's. The rule
   itself is byte-unchanged.
10. R-12 (apt User-Agent names the platform) — FIXED.
    usr/lib/apt/methods/tor+http now sends
    "Debian APT-HTTP/1.3 (3.0.3)" — the stock trixie apt
    method's agent — instead of "apt (onionhost-tor)".
    Verified on the wire in the fake-SOCKS fetch test
    (item 12).
11. R-13 (restart precedes the settle; Persistent timer) —
    FIXED. (a) On the install path the drawn settle now
    sleeps BEFORE stackctl("restart"), so the
    republication itself — not just the local probe —
    lands at a drawn time unrelated to the fetch; the
    judgement is then plain health_ok() on its existing
    probe budget (no second settle). The install-failure
    branch is byte-equivalent to before (restart, judged
    unhealthy, no probe — the old short-circuited
    expression never probed there either). The rollback
    and fail-closed-recovery paths KEEP their post-restart
    settle, with the reasoning in health_ok_after_restart's
    docstring: a rollback's restart must not wait while a
    judged-bad stack keeps serving (Y8), and recovery's
    restart returns a site that is OFF — delaying it by
    hours trades the recovery duty away, and the common
    recovery follows no same-run package fetch beyond the
    index refresh. gate4fix S9 was rewritten to assert the
    stronger property (restart starts >= the settle after
    the install; the first probe judges the restarted
    stack with no second settle) and passes; S10
    (defaults >= 1800s floor, >= 3600s spread) unchanged;
    suite 0 failed overall. (b) onionhost-update.timer
    drops Persistent=true, with the reason in its comment:
    a box off through its window polls at the next window,
    not at power-on.
12. R-14 (update-observer bound undisclosed) — FIXED in
    the Owner Guide: section 1 gains a plain paragraph
    stating what the channel's two ends can see (the
    project repository operator: that an anonymous box
    polled, and when; Debian's mirrors: which package
    versions an anonymous box fetched, and when — a bound
    on patch lag) and what they cannot (address, site,
    identity). R-19 (SOCKS streams blended across
    clients) — FIXED: both local SOCKS clients now offer
    username/password auth and authenticate under fixed
    public usernames — the apt method as "apt", the
    probe as "probe" (empty passwords; the credential is
    a circuit-partition label under Tor's default
    IsolateSOCKSAuth, not an identity) — falling back to
    no-auth if the server selects it, so the partition
    can never break the fetch or the check. Verified
    against a fake SOCKS5 server: greeting offers
    [no-auth, user/pass], the auth frame carries the
    fixed name, and the fetch completes end to end.
    Circuit-level separation is Tor-side behaviour; its
    observation rides the standing rig circuit item.
13. R-21 / R-26 / R-28 (residual fetch machinery + stale
    in-app update wording) — FIXED. R-21: Gitea's
    app.ini.tmpl gains [cron.update_checker] ENABLED =
    false (the section name and the dl.gitea.com/gitea/
    version.json endpoint both verified present in the
    shipped 1.27.3 binary's strings before relying on
    them), and wp-config gains DISABLE_WP_CRON = true
    beside the updater defines, with the trade stated in
    its comment (version-check/housekeeping noise dies;
    scheduled posts lose their trigger — no sealed-room
    equivalent exists). R-26: the SMF seed tail now
    DELETEs the two seeded package_servers rows (the
    Package Manager's upload door — the sealed update
    path — needs no server list); the language-pack
    endpoint is hardcoded in SMF's code and cannot be
    unseeded — recorded residual, dies at the wall.
    DokuWiki's {{rss>}} aggregation is documented IN
    local.protected.php as an editor-trust decision: a
    core parser mode with no supported off-switch, inert
    while the app has no network, to be revisited if a
    future platform change ever gives it one. R-28: the
    retired "platform's signed channel (recipe packages)"
    wording is corrected to the A26 owner-maintained
    model everywhere it shipped: the DokuWiki protected
    config, the WP sealed plugin (header and update-check
    comment), and the applier's wp-config defines comment
    + render_wp_config docstring.
14. R-15 (gate errors never stop anything; absent A/U
    judged clean) — NO CODE CHANGE, on evidence. The
    exit-2 error policy is one of the five reserved
    calls (below) and is untouched. The absent-container
    sub-point has no mechanical remainder: absence is a
    designed, load-bearing contract (B and the app
    container are alternatives — one is legitimately
    missing on every box — and a box before Go Live has
    no containers at all); the gate already distinguishes
    PROVEN absence (container exists -> exit 1) from
    error (exit 2), the Review 3 S9 split; and a down
    site is owner-visible where owners look — the
    Dashboard's probe-driven site card — not via the
    runtime gate. Making mere absence a gate failure
    would false-positive every pre-Go-Live boot.
15. R-24 (unbounded timestamped logs) — FIXED. Writer-
    side caps: onionhost-update's update.log and both
    writers of maintenance-log.txt (onionhost-maintenance
    and onionhost-restore) now rewrite the file to its
    newest 256 KiB (from a line boundary) behind a
    rotation note once it passes 1 MiB. A journald
    drop-in ships at etc/systemd/journald.conf.d/
    onionhost.conf: SystemMaxUse=256M,
    SystemMaxFileSize=16M, MaxRetentionSec=90day.
16. R-20 (nginx fingerprint on the app tier) — FIXED.
    The static template now clears the Server header
    outright (it already cleared Date and ran
    server_tokens off). All four templates answer
    nginx-generated errors with generic bodies (a
    plain "Not found." / "This site is not available
    right now." via error_page to named locations; 5xx
    normalises to 503) — the stock 502 body naming the
    stack when a native app is down is gone. The app
    templates clear Last-Modified (real file mtimes on
    the app tier publish install/edit timing) and the
    PHP template also sets etag off; application-
    generated errors and headers are untouched (no
    intercept_errors anywhere, by design).
17. R-16 (102 Status helper dead) — FIXED. log_status()
    in the tor+http method is now called exactly once
    per method process, when a TCP-proxy CONNECT succeeds
    — the only path on which the developer-only override
    can be honoured — recording the override's use in
    apt's own stream. Verified at function level in the
    item-12 test (fires once, not per fetch).
18. R-25 (owner copy routes identity-linked contact) —
    FIXED. The site page's contact call-to-action now
    says a project-only account, or reaching the project
    over Tor Browser, is a respectable way to say hello;
    the Owner Guide's fetch-elsewhere workflow (section
    3, covering section 4's downloads by reference) gains
    the habit in one bullet: fetch over Tor or from a
    device/account the owner doesn't mind being linked
    to the software they run.
19. R-22 / R-23 — ACCEPTED, with reasoning recorded.
    R-22 (publish timing): when a site changes IS the
    owner's publishing act; the correlation is inherent
    to running a live site at all, and an optional
    publish delay would be a product feature with its
    own design, not a patch — the platform does not
    insert itself between the owner and their own site.
    R-23 (backup stop window): SQLite-file applications
    need the cold copy for a consistent file set (the
    WAL problem); the outage is the consistency price
    of a manual, owner-timed action the owner schedules,
    and MariaDB sites — the multi-user case — already
    dump live and never stop. Accepted as designed.
20. R-07 / R-17 / R-18 / R-27 — the boot, install and
    resolver tail. R-07 (socket-dir 0777): NO tree
    change, by the register's own gating — the 0770
    landing is conditional on Gap 2's three proofs
    (live A connect, rotation's second instance, the
    setgid choice); rig item 19. R-17 (installer
    residue): tree half DONE — the Calamares cleanup
    jobmodule now removes the session-log paths
    (/var/log/Calamares, /var/log/calamares, the root
    session share) and empties the copied live journal
    directory (its shell — ownership/mode are the
    installed system's logging configuration — is
    preserved; every entry in it is install-session
    residue, since the target has never booted).
    NetworkManager profiles are deliberately NOT
    touched: whether a live-session profile may ride
    into the target is Gap 8's evidence question, and
    deleting a Wi-Fi profile the owner typed during
    install could strand a Wi-Fi-only owner — rig item
    20 decides it. R-18 (firewall load ordering): DONE —
    onionhost-nft-load.service now orders After/Wants
    network-pre.target and Before NetworkManager,
    chrony and lightdm (plus the gate and A, as before);
    the golden ruleset's default-deny output policy
    covered the residual window, and this closes the
    window itself; proof is the rig boot pcap, item 21.
    R-27 (container resolver): DONE — the A and U
    quadlets pin DNS=127.0.0.1 (B and the app container
    are Network=none and have no resolver story); Tor
    resolves internally and never consults the file, so
    the pin only removes podman's host-resolver default
    from a compromised process's reach. Rig item 22
    confirms Tor unaffected and the resolver dead.

### Reserved — still the human reviewer's calls (not decided here)

The audit reserved five judgement calls, and this batch
decided none of them: (1) R-06 — whether the golden
ruleset's root/_apt clearnet permission is narrowed or
formally accepted (only its stale comment was corrected,
item 9); (2) R-15 — whether nft-gate ERRORS (exit 2)
should fail closed (item 14 changed nothing there);
(3) gVisor gofer semantics beyond the R-01 canary's
empirical answer (item 1 scopes U; the canary measures
what the scoping is worth); (4) guard-level correlation
analysis for A/U; (5) any verdict on R-05's fleet-level
metadata exposure beyond "bounded and undisclosed"
(item 12 discloses the bound to owners; the verdict on
the exposure itself stands reserved).

### Rig additions (standing list continues)

18. R-01 canary (TOP priority): from inside running A
    and U, connect attempts to a canary host socket
    outside the mounts, the podman socket path, and the
    peer's SOCKS/control paths. Pass: U (now create-only)
    reaches none of them and still serves its SOCKS
    socket to the host probe/apt; A reaches B's http.sock
    and nothing else unexpected. Record gofer behaviour
    verbatim — it also feeds reserved call (3).
19. Gap 2 / R-07: the 0770 proofs for /run/onionhost/web
    (A connects live; a rotation's second B instance
    binds; the setgid-vs-0770 choice measured). Pass:
    all three demonstrated on the live stack, then the
    tree change (tmpfiles + generate-configs) lands.
20. Gap 8 / R-17 remainder: inventory what the installed
    target actually inherits from the live session
    (NetworkManager system-connections incl. any Wi-Fi
    profile typed during install, machine-id, SSH host
    keys if any). Pass: an itemised list with a keep/drop
    verdict per item; the cleanup jobmodule gains only
    what the evidence condemns.
21. R-18: boot pcap from power-on. Pass: zero non-Tor
    egress before the golden table loads, and the table
    loaded before NetworkManager's first connection
    attempt, chrony's first poll, and lightdm's start.
22. R-27 + Gap 11: in A and U, read /etc/resolv.conf
    (expect the 127.0.0.1 pin), attempt a lookup (expect
    failure), watch the nft input counters; confirm Tor
    bootstrap and the update fetch are unaffected.

### Regression (final tree)

- poc/recipes-smf 33/33 (32 baseline + the R-03
  docroot-absence check), wordpress 39/39, dokuwiki
  38/38 (37 + the R-03 check), gitea 27/27 (the real
  1.27.3 binary booted against the rendered app.ini —
  [cron.update_checker] accepted), marketplace 31/31.
- poc/gate4fix run_tests: 0 assertion(s) failed
  (S1-S10 + A26 R1-R4; S9 rewritten for R-13 as above);
  test_dashboard: 0 failed.
- poc/runtime-gate run_sim: 68 assertions, 0 failed
  (63 baseline + 5 R-10 cases); test_runtime_dashboard:
  0 failed.
- poc/runsc-wrap run_tests: 24/24 (21 baseline + W10's 3).
- poc/backup-proof: ALL 27 CHECKS PASS (20 baseline +
  7 format-3 outer-layer checks incl. the real restore
  round trip).
- poc/installer-policy run_proofs: 26 assertions,
  0 failed.
- poc/d8-fix p3: environment-deferred (see venue notes).
- ci-scan over the committable set: PASS except the two
  known rig-user home-path literals in the UNTRACKED
  audit pack file (owner's briefing material, untouched,
  as instructed). The scan caught three phrase-rule false
  positives on the way: one in this batch's own SMF seed
  comment (a five-word EFF run spanning the comment/SQL
  boundary) and two pre-existing in poc/installer-policy/
  run_proofs.py (a five-word run across a line pair in the
  fake installer handler, and a three-word bracketed
  segment naming a scratch dir). All three were REWORDED,
  not allowlisted - the seed comment's closing sentence,
  a scratch-dir name ("control-" -> "ctl-"), and an
  equivalent comparison form - each verified against a
  faithful reimplementation of the scanner's rule before
  the final scan, and both affected suites re-run green
  afterwards (SMF 33/33, installer-policy 26/26). The
  proof venues' extracted trees under poc/installer-policy/
  work/ (regenerated by every run_proofs run; ~27.5k
  stock-WordPress phrase false positives when present)
  were removed before the final scan - they are build
  residue of the venue, not tree content.
- Edited Python compiles (runsc-wrap, onionhost-recipe,
  onionhost-update, onionhost-backup, onionhost-restore,
  onionhost-maintenance, wizard, the Calamares cleanup
  jobmodule); bash -n clean on onionhost-nft-gate-check.
  The apt method's new handshake, stock User-Agent and
  102-Status note were verified against a fake SOCKS5
  server driving the real method module end to end.

Venue notes: the runtime-gate sim and backup-proof stubs
were already staged at /tmp/rgate/bin and
/tmp/backup-proof/bin. The d8-fix proof machine is NOT
staged in this sandbox (/tmp was wiped; its recorded
p3-gitea output in-tree stands at 12/12 PASS, PHASE
RESULT: PASS from the A26 batch's re-stage) — the applier
changes in this batch do not touch the D8 ownership
machinery (data-dir ownership, mode exceptions,
normalise), and the venue re-stages from the current
tree at the next rig session; d8 p3 is therefore
recorded as environment-deferred, not re-proven here.

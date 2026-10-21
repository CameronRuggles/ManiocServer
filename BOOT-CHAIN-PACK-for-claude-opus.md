# OnionHost OS — Boot-Chain Change: Focused Security Review Request
## For: Claude Opus · From: the OnionHost design team · 2026-10-11
## Scope: ONE engineering-forced change to the disk-encryption boot path. The rest of the design is settled (two prior reviews) — do not relitigate it.

---

# 1. The situation (all facts measured on our test rig, not assumed)

OnionHost OS is a Debian 13 system that turns a home desktop into a
sandboxed Tor onion-service host for non-technical owners. Full-disk
encryption (LUKS2) is mandatory; the disk passphrase is a
machine-generated 7-word Diceware-style phrase (~90 bits, user never
chooses it), typed at every boot. The sealed-when-powered-off state is
the product's core physical guarantee. The installer is Calamares; its
erase layout places /boot INSIDE the encrypted root volume, so the
bootloader (GRUB, loaded via Debian's signed shim → Secure Boot chain)
must unlock LUKS itself to read the kernel and initramfs.

**The problem:** our first skeleton ISO installs cleanly and reaches
the GRUB passphrase prompt — where a verified-correct passphrase is
rejected. Cause, confirmed by direct test: **Debian 13's signed GRUB
(2.12-9) cannot process argon2id key derivation**, and LUKS2 volumes
created by our installer use argon2id keyslots (both slots). GRUB
supports LUKS2 only with PBKDF2 keyslots. The passphrase is fine;
`cryptsetup open --test-passphrase` accepts it outside GRUB.

Two related design facts from the same project:
- **A18 (already decided, owner-confirmed):** the running system opens
  the volume with the keyring disabled so that a new passphrase can be
  added from the running system without the old one (lost-paper
  recovery). Trade recorded: raw volume key is root-readable in the
  device-mapper table while running.
- Boot UX target: the owner types the phrase **exactly once** per boot,
  at a console prompt (no graphical unlock in v1).

---

# 2. The candidate fixes

**Option A — dual-derivation keyslots + embedded keyfile.**
Keep /boot encrypted. Enrol the SAME generated phrase in two keyslots:
the existing argon2id slot, plus a second slot using PBKDF2 (LUKS2
allows per-keyslot PBKDF settings). Boot flow: GRUB unlocks via the
PBKDF2 slot and loads kernel+initramfs; the initramfs then opens the
root volume using an embedded keyfile (stored inside the initramfs,
which lives on the encrypted /boot — the standard KEYFILE_PATTERN
pattern), unlocking an argon2id-protected slot, so the user types the
phrase once. Our working assumption to check: because the phrase is
machine-generated at ~90 bits of entropy, the offline brute-force
resistance is bounded by the phrase entropy, not by the KDF — so a
PBKDF2 slot at feasible GRUB iteration counts does not meaningfully
weaken the disk against offline attack, the way it would for a
human-chosen password. (If this assumption is wrong, Option A falls.)

**Option B — separate unencrypted /boot (Debian installer pattern).**
GRUB needs no unlock; the initramfs (which handles argon2id natively)
prompts and unlocks. All keyslots stay argon2id; no keyfile. Cost:
kernel and initramfs sit on a plaintext partition — an attacker with
brief physical access ("evil maid") can modify the initramfs to
capture the phrase at the next boot. Secure Boot signs shim/GRUB/the
Debian kernel, but the locally generated initramfs is unsigned, so
the chain does not cover the component that asks for the phrase.

**Option C — anything else we should know about.** For example:
distributions whose signed GRUB supports argon2id (downstream
patches), signed unified kernel images without local key enrolment
(MOK enrolment is presumably a non-starter for our novice users —
confirm), LUKS detached headers, or a GRUB version/support change on
Debian's horizon that argues for waiting. If a materially better path
exists inside our constraints, name it.

---

# 3. Questions

- **Q1.** Grade Option A's core assumption (Section 2): with a
  generated ~90-bit phrase, does adding a PBKDF2 slot (say 1–5 seconds
  of GRUB-side derivation) change the offline-attack picture in any
  way that matters? Does the answer change for the SPARE phrase
  (also generated, same wordlist/length)?
- **Q2.** The embedded keyfile: it is effectively a third credential,
  protected only by /boot's encryption and GRUB's unlock. Enumerate
  the ways it can leak in practice (backups of /boot or initramfs,
  installer logs, initramfs regeneration on kernel updates copying it
  into new images, package tooling that archives initramfs files) and
  the hygiene rules that must ship with Option A if chosen.
- **Q3.** GRUB slot behaviour: with one argon2id slot and one PBKDF2
  slot present, does GRUB waste time/fail noisily on the argon2id
  slot, or does it select the PBKDF2 slot cleanly? Keyslot PRIORITY
  settings — anything we must set so the initramfs and GRUB each use
  the intended slot, including during Maintenance re-keying (A18) and
  full re-encryption?
- **Q4.** Option B's evil-maid exposure: grade it against OUR threat
  model (powered-off protection for ordinary home users; a running or
  booting machine under an attacker's hands is already partly out of
  scope). Is initramfs tampering a realistic home-user risk or a
  nation-state footnote? Does anything cheap (TPM-based measurement
  WITHOUT auto-unlock, boot-file checksums verified post-boot,
  signed-initramfs schemes available in Debian 13) close most of it?
- **Q5.** Interaction check: does either option change the A18
  analysis (keyring-disabled running open, re-key without the old
  phrase, reencrypt as the compromise cure)? In particular, under
  Option A, when Maintenance adds a new phrase to the running system,
  BOTH slots must be re-enrolled (argon2id + PBKDF2) — is that
  reliably scriptable via the volume-key path, and what happens if
  only one gets updated (does the machine become unbootable, or
  silently keep the old phrase working in GRUB)?
- **Q6.** Which option do you ship if this is your product, and what
  is the one failure story (support ticket, user report, headline)
  that most worries you about your own choice?

# 4. Constraints (violating one is a finding, not a proposal)

- The phrase is always machine-generated; users never invent or
  choose secrets. Any argument that assumes weak human passphrases
  does not apply here — say explicitly if you think it still does.
- One typing of the phrase per boot. No graphical unlock in v1.
- Secure Boot chain must remain Debian's signed shim/GRUB — no
  self-signed bootloaders, no asking novices to enrol keys.
- Non-technical owners; zero new user-facing concepts allowed.
- The sealed-when-off guarantee is the product's headline physical
  claim; arguments are weighed against it first.

# 5. Format

Verdict first (A, B, or C-with-details), then Q1–Q6 in order. For
Option A's hygiene rules (Q2) and the re-key scripting (Q5), be
concrete enough to implement from. If you believe BOTH options are
unacceptable, say so and specify what you would do instead within
Section 4.

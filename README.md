# Manioc Server

Manioc Server is a custom Debian 13 (trixie) live/installer ISO that
turns a home desktop into a Tor onion hosting server for
non-technical users: LUKS2-encrypted install, a no-network website
container reached through a Tor gateway, gVisor-sandboxed containers
(rootful Podman/Quadlet + `runsc`), and a small catalog of packaged
apps ("recipes" — a forum, a blog, a wiki, a git host) the owner
picks from a wizard. Design and history live in `DESIGN-v3-amendments.md`,
`EXPLAINER.md` and `ISO-BUILD-LOG.md`; licensing in `LICENSING.md`.

## Building the ISO

**Build entry point: `build/build-iso.sh`** — run it as root from a
plain clone of this repo. No environment variables are required for
a release build:

```sh
sudo build/build-iso.sh
```

The script is self-locating (it finds the repo through `BASH_SOURCE`):
the source tree defaults to the `onionhost/` directory of the repo
the script lives in. The ISO, its `.sha256`, logs and a `BUILD-INFO`
record land in `$WORK` (default `$HOME/iso-build-$FLAVOUR`).

Pipeline, in order: archive-keyring gate → recipe ship-list
resolution → host-dependency check → pinned `runsc` fetch/verify →
Calamares plugin + patched partition-module builds (in a pinned
mmdebstrap chroot) → container-image rootfs tarballs → rootfs
mmdebstrap from the pinned Debian snapshot → overlay + chroot
customisation → factory `.deb` packages (platform + recipes) →
squashfs → `grub-mkrescue` hybrid ISO.

Helper scripts the entry point drives (all under `build/`):

| Script | Job |
| --- | --- |
| `build/fetch-recipe-archives.sh [RECIPES_DIR]` | Fetch any missing recipe archives and verify **every** selected archive against its `recipe.json` sha256 pin. Also runnable standalone. |
| `build/build-recipe-deb.sh RECIPE_DIR VERSION OUTDIR [--floor X] [--sabotage]` | Verify one recipe's pins and build its `onionhost-recipe-<id>` package. Only the pinned `archive/<archive.file>` enters the package. |
| `build/build-onionhost-deb.sh …` | Build the platform `onionhost` package. |
| `build/ci-scan.sh` | CI leak scan over the tracked tree. |

### Host prerequisites

- A Debian/Ubuntu-family build host, run as **root** (the build
  mounts, chroots and runs mmdebstrap `--mode=root`).
- Tools: `bash`, `python3`, `gpg`, `curl`, `sha256sum`/`sha512sum`,
  `dpkg-deb`, `rsync`, `find`/`stat`/`awk`, and the ISO toolchain —
  `mmdebstrap`, `mksquashfs` (squashfs-tools), `xorriso`,
  `grub-mkrescue`. If `mmdebstrap`, `mksquashfs`, `xorriso` or
  `grub-mkrescue` are missing, the script installs them itself with
  `apt-get` (`mmdebstrap xorriso grub-common grub-pc-bin
  grub-efi-amd64-bin mtools debian-archive-keyring squashfs-tools
  curl`) using the host's configured apt repositories.
- Network access to the endpoints listed below, and enough free
  disk in `$WORK` for the rootfs, container tarballs, plugin-build
  chroot and ISO (several GB; the caches under `$WORK/cache` are
  reused across runs).

### Network endpoints the build contacts

| Endpoint | Used for |
| --- | --- |
| `https://snapshot.debian.org/archive/debian/20261023T142942Z` (the pinned snapshot; `SNAPSHOT` in `build-iso.sh`) | Every mmdebstrap tree (rootfs, container images, plugin-build chroot) and the Calamares source tarball from its `pool/main/c/calamares/` path. The chroot customisation phase's own `apt-get` calls also use this mirror, inherited from the mmdebstrap sources. |
| `https://storage.googleapis.com/gvisor/releases/release/20251006/x86_64/runsc` and the same URL + `.sha512` | The pinned gVisor `runsc` binary (`release-20251006.0`); its sha512 must equal the `RUNSC_SHA512_PIN` constant in `build-iso.sh`, not merely the served `.sha512`. |
| The host's configured apt repositories (`apt-get update`) | Only when host build dependencies are missing (see above). |
| `https://download.dokuwiki.org/src/dokuwiki/dokuwiki-2026-07-14c.tgz` | DokuWiki recipe archive (fetch step; skipped when the vendored archive already matches its pin). |
| `https://downloads.wordpress.org/release/wordpress-7.1.3.zip` | WordPress recipe archive (fetch step; same skip rule). |
| `https://dl.gitea.com/gitea/1.27.3/gitea-1.27.3-linux-amd64` | Gitea recipe archive (fetch step; same skip rule). |
| `https://github.com/SimpleMachines/SMF/archive/refs/tags/v2.1.7.zip` | SMF recipe archive (fetch step; same skip rule). **Known limitation:** GitHub regenerates this zip's container bytes, so a fresh download will *not* match the pin and the fetch step will refuse it — the vendored archive is the only pin-satisfying source. See `archive.refetch_note` in `onionhost/recipes/smf/recipe.json`. |

Recipe archive URLs are read from each recipe's
`onionhost/recipes/<id>/recipe.json` (`archive.url`); the table
above lists the current pins. The marketplace recipe is
build-from-source and is never downloaded by the fetch step (and
is not in the release ship list at all — see below).

### Environment variables the build reads

Every variable `build/build-iso.sh` and the scripts it drives
(`build/fetch-recipe-archives.sh`, `build/build-recipe-deb.sh`,
`build/build-onionhost-deb.sh`) read from the environment:

| Variable | Read by | Meaning / default |
| --- | --- | --- |
| `FLAVOUR` | `build-iso.sh` | `prod` (default) or `test`. `test` adds live-session-only test access (known live password, operator pubkey, sshd, `xdotool`); the installer strips it from installed targets in both flavours. |
| `WORK` | `build-iso.sh` | Build working directory. Default `$HOME/iso-build-$FLAVOUR` (so it also reads `HOME`). All caches, logs, `BUILD-INFO` and the finished ISO live here — nothing is written into the source tree. |
| `OH_SRC` | `build-iso.sh` | Override for the `onionhost/` source tree. Default: the `onionhost/` directory of this repo, resolved relative to the script. |
| `OH_PROBE` | `build-iso.sh` | `1` also sequences the `onionhostprobe` diagnostics Calamares module. Default `0`; the module is removed from production images entirely. |
| `OH_TEST_SSH_PUBKEY` | `build-iso.sh` | The operator SSH **public** key for `FLAVOUR=test` live-session access. Read from the environment or from `OH_TEST_SSH_PUBKEY_FILE`; it is deliberately not kept in the source tree. A test build with no key available is FATAL. Prod builds ignore it. |
| `OH_TEST_SSH_PUBKEY_FILE` | `build-iso.sh` | Path the test operator pubkey is read from when `OH_TEST_SSH_PUBKEY` is unset. Default `$HOME/.onionhost-test-pubkey` (outside the tree). |
| `OH_RECIPES` | `build-iso.sh`, `fetch-recipe-archives.sh` | Non-release recipe-selection override, e.g. `OH_RECIPES=wordpress,dokuwiki,gitea`. **FATAL unless `OH_NONRELEASE_BUILD=1` is also set.** See "Recipe ship list" below. |
| `OH_NONRELEASE_BUILD` | `build-iso.sh`, `fetch-recipe-archives.sh` | Must be exactly `1` to permit an `OH_RECIPES` override. Any build with this set is bannered NON-RELEASE and stamped `release_status=non-release` in `BUILD-INFO`. |
| `OH_OVERLAY` | `build-onionhost-deb.sh` (set by `build-iso.sh`) | The rootfs-overlay tree the platform package is built from. `build-iso.sh` sets it to `$SRC/rootfs-overlay` for its own call; standalone use defaults to a maintainer path. |
| `SOURCE_DATE_EPOCH` | `build-iso.sh` | **Set by the script itself**, not an input: `build-iso.sh` exports the pinned value `1792765782` (2026-10-23T14:29:42Z, == the Debian snapshot) and passes it into the chroot build/customise phases, so two builds of one commit can be byte-identical. Inside the chroot script a fallback to the same constant applies. |

Set internally / passed through phases (not builder inputs):
`OH_FLAVOUR` (the chroot customise script's copy of `FLAVOUR`,
exported by `build-iso.sh` when it invokes the chroot),
`DEBIAN_FRONTEND`, `LC_ALL`, `TZ` and `PATH` (pinned inside the
chroot invocations), and the standard proxy variables
(`http_proxy`/`https_proxy`/`HTTP_PROXY`/`HTTPS_PROXY`), which
`curl` and `apt-get` honour when the host environment sets them.
`build-recipe-deb.sh` reads no environment variables: its inputs
are positional arguments and the `--floor` / `--sabotage` flags.

### Archive keyring

Every installed box verifies project updates against the public
archive keyring baked into the image at
`onionhost/rootfs-overlay/usr/share/keyrings/onionhost-archive-keyring.gpg`.

- **Expected fingerprint: `38AA06376F68206F072939DE82610F8D4BEF9565`**
  (OnionHost Release Signing <release-signing@onionhost.invalid>).
- The build gates on it before doing any work: the file must
  exist, `gpg --show-keys --with-colons` must report **exactly one**
  `pub` record (one primary key), the `fpr` record **immediately
  following that `pub`** must equal the fingerprint above, and the
  file must contain **no secret material** (no `sec`/`ssb`
  records). Any violation is FATAL — apt's `Signed-By` would trust
  every key in the file, and a secret key must never ship. The gate
  deliberately does *not* count `fpr` records in total: GnuPG
  prints an `fpr` after every subkey as well as after the primary
  key, so a primary key with a signing subkey — the expected
  release shape, e.g. a hardware key — has more than one `fpr`
  and passes, as long as the single `pub` and the `fpr` that
  follows it match the pin.

### Recipe ship list and the non-release override

The tracked ship list is **`onionhost/recipes/SHIPPING`**: one
recipe id per line. A release build fetches, verifies and packages
exactly those recipes — currently:

```
smf
wordpress
dokuwiki
gitea
```

Both the fetch step and the factory-package loop in
`build-iso.sh` honour the list, so a release build cannot include
any other recipe found under `onionhost/recipes/` without a change
to `SHIPPING`. In
particular the **marketplace recipe is excluded until owner
decision 3 is met** (it ships only once it is rebuildable from a
pinned public commit); do not add it to `SHIPPING` before then.

Non-release builds are also distinguishable by name, not only by
the `BUILD-INFO` stamp: a release build produces
`maniocserver-amd64.iso` with volume label `MANIOC_LIVE`, while a
non-release build produces `maniocserver-nonrelease-amd64.iso`
(for a non-`prod` flavour, `maniocserver-nonrelease-<flavour>-amd64.iso`)
with a volume label containing `NONRELEASE` (`MANIOC_NONRELEASE`).

A local or first-time ("stranger") build may need a different set
— SMF's archive, for example, cannot be re-fetched (see the
endpoint table), so a cold clone cannot satisfy its pin. That is
what the override is for:

```sh
OH_NONRELEASE_BUILD=1 OH_RECIPES=wordpress,dokuwiki,gitea \
  build/fetch-recipe-archives.sh        # fetch step, standalone
OH_NONRELEASE_BUILD=1 OH_RECIPES=wordpress,dokuwiki,gitea \
  sudo build/build-iso.sh               # full build
```

Guardrails, by design:

- Setting `OH_RECIPES` **without** `OH_NONRELEASE_BUILD=1` is a
  **FATAL error** in both scripts, before any work happens. There
  is no silent way to change what ships.
- With `OH_NONRELEASE_BUILD=1`, the build prints a prominent
  `NON-RELEASE BUILD` banner naming the selection and its source,
  and `BUILD-INFO` is stamped `release_status=non-release` with
  `recipes_source=` and `recipes_selected=` lines (these lines are
  also in the copy of the build record that enters the image).
- The default — neither variable set — is always exactly the
  `SHIPPING` list, stamped `release_status=release`.
- Selected ids are validated: each must name an existing
  `onionhost/recipes/<id>/recipe.json`, with no duplicates.

### Forks and rebuilders: using your own signing key

A fork that wants its own update channel cannot just swap one
file: the release signing identity is named in **four coupled
places, which must change together** or the build gate (for a
mismatched keyring/pin) or installed boxes (for a mismatched repo
address) will refuse the result:

1. **The keyring file** —
   `onionhost/rootfs-overlay/usr/share/keyrings/onionhost-archive-keyring.gpg`
   (the PUBLIC key baked into every image; apt's `Signed-By`
   trusts the key(s) in this file).
2. **The pinned fingerprint constant in `build/build-iso.sh`** —
   the `ARCHIVE_KEY_FPR` constant in `build/build-iso.sh` must be
   set to your primary key's fingerprint (the `fpr` record
   immediately following the `pub` record; see "Archive keyring"
   above).
3. **The repo onion address in the apt sources template** —
   `onionhost/rootfs-overlay/usr/lib/onionhost/golden/apt-onionhost.sources.tmpl`
   must name your fork's own repository onion service instead of
   the upstream project's.
4. **`KEYID` in `build/make-onionhost-repo.sh`** — the default
   value of `KEYID` in `build/make-onionhost-repo.sh` (the key the
   repo-signing script signs the apt repository with; it can also
   be overridden per run via the `KEYID` environment variable) must
   name the same key.

To generate a fork key and put its public half in place — do this
in a maintainer keyring **outside** the checkout, never in the
tree:

```sh
export GNUPGHOME="$HOME/manioc-maintainer-gnupg"   # outside the repo
mkdir -p "$GNUPGHOME" && chmod 700 "$GNUPGHOME"
gpg --full-generate-key
# Optional, and the expected release shape: a signing subkey
# (the build gate passes it — see "Archive keyring"):
#   gpg --edit-key <your primary fingerprint> addkey
gpg --list-keys --with-colons   # primary fingerprint = the fpr after pub
gpg --export <your primary fingerprint> \
  > onionhost/rootfs-overlay/usr/share/keyrings/onionhost-archive-keyring.gpg
```

Export with plain `gpg --export` only: that exports the **public**
half. Never export secret material (`--export-secret-keys`) into
the tree — the build gate rejects a keyring containing any
`sec`/`ssb` record, and a secret signing key must never ship in an
image or a repo. Then update the other three places above (the
`ARCHIVE_KEY_FPR` pin, the repo onion address in the sources
template, and `KEYID`) to match the new key and your repo, and
rebuild: the keyring gate verifies the keyring file against the
pin before any work happens.

## Repository layout

- `onionhost/` — the OS source tree: `rootfs-overlay/` (files laid
  over the Debian rootfs), `calamares/` (installer modules, plugins
  and patches), `recipes/` (packaged apps + the `SHIPPING` list).
- `build/` — the build entry point and its helper scripts.
- `poc/` — proof-of-concept rigs and test suites for subsystems
  (most of it gitignored working bulk; the write-ups are kept).
- Top-level `*.md` — design documents, runbooks, acceptance
  records and the build log (`ISO-BUILD-LOG.md`).

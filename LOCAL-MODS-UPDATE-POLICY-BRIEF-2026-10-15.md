# OnionHost — Local-modifications vs. recipe updates: unified policy brief

SUPERSEDED 2026-10-21: Cameron decided the question this brief
posed — recipes are installers, not update channels (amendment
A26 in DESIGN-v3-amendments.md). No carryover or merge machinery
was built; an installed app is never modified by a platform
update run, so there is nothing for owner additions to survive.
Kept as the record of the options that were considered and
decided against.

Prepared 2026-10-15 from Cameron's side-chat questions (WordPress plugins,
SMF packages, owner/maintainer update responsibilities). Grounded in the
recipe files on disk today. ONE decision needed from Cameron — see §4.

## 1. The trap, verified in the recipes

A recipe update swaps the whole app tree. Only `data_dirs` and
`config_carryover` survive (`onionhost/recipes/*/recipe.json`, read today):

| App | Survives an update | Silently lost today |
|---|---|---|
| WordPress 7.1.3+oh.1 | `wp-content/uploads`, `wp-config.php` | Owner-added **plugins and themes** (settings survive in DB; files gone, plugin dead) |
| SMF 2.1.7+oh.1 | `attachments`, `custom_avatar`, `cache`, `Settings.php`(+bak) | Owner-applied **package patches/mods** (source edits reverted) — AND the uploaded package files themselves: SMF stores them in `Packages/`, which the nginx overlay already treats as an upload dir but which is **not** in `data_dirs`, so the patch file and its `Packages/backups` copy are wiped too |
| DokuWiki | `data/`, `conf/` (incl. `plugins.local.php`) | Owner-installed **plugins** (`lib/plugins`) and templates (`lib/tpl`) — same trap, not yet discussed |
| Gitea | n/a — native-slot app, different lifecycle | Out of scope for this policy |

## 2. Why the two discussed apps need different mechanics

- **WordPress plugins/themes are additions.** They live in their own
  directories and (almost) never modify shipped core files. Additions can
  persist without weakening a security update.
- **SMF packages are modifications.** A patch/mods package rewrites shipped
  source files in place. A security update *must* win those same files or
  it isn't a security update. Persistence is impossible here by definition;
  the achievable guarantee is **never silent**.

## 3. Proposed single policy

> **Owner additions persist. Shipped files win. Shipped-file removals are
> honoured. Nothing an owner did is ever reverted silently.**

Mechanics per app:

- **WordPress + DokuWiki (additions): surgical merge — option (b) from the
  chat, with one addition.** The applier already knows the payload manifest.
  On update: payload files win wherever the payload ships a file; files
  that exist only on the owner's side under `wp-content/plugins`,
  `wp-content/themes` (WP) / `lib/plugins`, `lib/tpl` (DokuWiki) persist.
  The addition: **tombstones.** If the *previous* payload shipped a file the
  new payload drops (e.g. WordPress removes a bundled plugin), that file is
  deleted even though it sits in a "persist" directory — judged against the
  previous manifest, not the directory. Without this, a removed-for-security
  bundled plugin (Akismet-class) would live forever on owner boxes, which
  is the hidden cost of the simple directory-carry option (a).
- **SMF (modifications):**
  1. Add `Packages` to `data_dirs` — uploaded package files and their
     backups persist. Cheap, no trade-off found.
  2. **Detect before swap:** the applier hashes the live tree against the
     shipped manifest it installed from (it has both). Any shipped file
     whose bytes differ = a local modification; any owner-added file
     outside data dirs is listed too.
  3. **Report, don't surprise:** the modification list is written to the
     Dashboard ("this update will undo changes you made: …") and kept in a
     post-update report on the box, so the owner can re-apply their SMF
     patch package afterwards — which they still can, because the package
     file itself now persists (point 1).

## 4. The one decision for Cameron

When a modification is detected on an SMF (or owner-modified-file) install,
what does an incoming recipe update do?

- **A. Warn-and-proceed (recommended for floor-raised security updates):**
  update applies on schedule; Dashboard shows beforehand/afterwards what
  was reverted. Fleet patch latency stays ~1 day; owner's patch is
  re-appliable from its persisted package file.
- **B. Hold-and-ask (recommended for ordinary, non-floor updates):** the
  recipe update waits until the owner acknowledges in the Dashboard.
  Protects owner work, at the cost of an unattended box sitting unpatched
  if the owner is away.
- **Proposed split:** A when the update raises the recipe's security floor,
  B otherwise. This matches the existing floor philosophy (a floor-raised
  update already fails closed rather than roll back to a vulnerable
  version — maintainer runbook, 2026-10-15).

Cameron's call is only A vs B vs the split. Everything in §3 is buildable
under any of the three.

## 5. Honest limits

- Detection covers file bytes in the app tree. A WordPress plugin that
  modifies core files (rare, discouraged upstream) would be treated like
  an SMF mod: shipped file wins, modification listed.
- DB-side state (SMF's installed-packages registry, WP's active-plugin
  list) already survives in the database; after a revert an SMF mod may
  still show as "installed" in its Package Manager while its code is
  gone. The post-update report should say re-applying the package is the
  fix; making SMF's registry agree automatically is out of scope.
- Not yet built or tested — this brief is the decision record, not an
  implementation. Build order if approved: WP/DokuWiki merge + tombstones
  first (pure additions), then `Packages` carryover (one line), then SMF
  detection + Dashboard reporting.

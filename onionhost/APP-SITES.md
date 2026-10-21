# App sites: the install contract

*For owners who chose "Your own application" as their site kind
(slice 6B, DESIGN-v3 A12/A20). This is the whole deal between you
and the platform. The Dashboard's "Application details" page shows
the live values (folder, database credentials) for your machine.*

## What the platform gives your application

- **A sealed room.** Your program runs in the app container: nginx
  + your runtime + a MariaDB database, in one gVisor sandbox with
  **no network at all**. The only way in or out is your site's
  `.onion` address, through the Tor gateway container — the same
  wiring as every other OnionHost site. A completely compromised
  application still cannot learn or reveal the computer's network
  address, reach the home network, or touch the onion key (it lives
  in a different container).
- **An app-data volume** at `/var/lib/onionhost/appdata`, with a
  **20 GB allowance**. If the data grows past it, a guard stops
  the app container (a full disk must never starve the computer
  itself) and notes it in the maintenance log; free space and the
  site starts again. Layout:
  - `www/` — your application's files (the web root), **PHP runtime**
  - `native/` — your program and its data, **native runtime**
  - `db/` — the database's own files. Never edit these by hand;
    they are the database's, and backups capture the database as a
    proper dump, not as these files.
- **Backups that understand applications.** The Dashboard's Back
  up button captures your application files plus a consistent
  database dump plus the database credentials (inside the
  encrypted backup), so a restored site comes back working, at
  the same `.onion` address. One caveat, stated plainly: the
  database is dumped when the site's runtime is **PHP**. If you
  switched the runtime to native, switch back before backing up a
  site whose database matters.

## The PHP contract

1. Copy your application's files into the **app folder**
   (`/var/lib/onionhost/appdata/www`). The Dashboard's
   "Application details" page has an "Open the folder" button.
   Whatever is there is what gets served; `index.php` is the
   front door. Each time the site starts, the platform tidies the
   folder's permissions so files you copied in become writable
   by the application (its installer needs to write its config,
   its uploads folder must accept files) and files the
   application creates stay editable by you.
2. When the application asks for its database:
   - **Host:** `localhost` — it connects over a unix socket that
     is already PHP's default, so `localhost` (not `127.0.0.1`)
     is the correct value. Socket path, if it asks:
     `/run/mysqld/mysqld.sock`.
   - **Database name, user, password:** shown on the Dashboard's
     "Application details" page. They are generated per install
     and stored only in a root-only file on the machine (and in
     your encrypted backups).
3. Know these facts before you install:
   - **No email.** The application cannot send any — there is no
     network for it and no mail server. Choose "no activation
     email" style settings in your application (admin-approved or
     immediate registration), or members can never finish signing
     up. Password resets by email cannot work either.
   - **No outbound anything.** The application cannot fetch
     updates, check versions, download remote avatars, proxy
     external images, or phone home. Such features fail quietly
     or log errors; turn them off where the application allows.
     **Updating the application means replacing its files in the
     app folder yourself** — in-app auto-updaters cannot work.
   - **Visitor addresses are not real.** Every visitor appears to
     come from `127.0.0.1` — over Tor there is no visitor address
     to pass, by design. IP bans and IP-based rate limits inside
     the application are therefore meaningless; use accounts and
     moderation instead.
   - **Uploads land in your app folder** and count toward the
     20 GB allowance. The platform's photo scrubbing applies to
     the built-in Pages/Journal editors, *not* to files your
     application accepts — your application's own upload rules
     are yours.
   - The clock is the computer's clock (kept accurate by network
     time sync), so posts and logs carry real times — a dynamic
     site cannot have the static tiers' content-derived times.

## The native contract

For a single self-contained program (the reference shape is a
static Rust binary with an embedded SQLite database):

1. Put the program in `/var/lib/onionhost/appdata/native`, named
   exactly **`app`**, executable. It takes no arguments.
2. It is started with its working directory set to that folder —
   keep its data files (e.g. its SQLite database) there; that is
   what backups capture.
3. It receives two environment variables:
   - `ONIONHOST_APP_SOCKET` — it **must listen on this unix
     socket** (value: `/run/app.sock`). nginx proxies all web
     requests to it.
   - `ONIONHOST_APP_DATA` — its folder (same as its working
     directory).
   A packaged recipe may instead declare that its program
   serves **TCP on the sandbox loopback** (manifest
   `native_serve`) — for a program that binds TCP only. nginx
   then proxies the edge to that loopback port; the program
   still has no network beyond the loopback, and the platform
   passes it `DATABASE_URL` (below) the same way.
4. By default there is no database server in this runtime; if
   the program wants SQL, it brings it (embedded SQLite is the
   proven shape). Backups pause the program briefly to copy its
   data files cold, so keep them in ordinary files it can
   reopen on restart. A packaged recipe may instead declare
   **`db.engine: "postgres"`**: the platform then runs
   PostgreSQL inside the same sandbox (its datadir beside the
   app folders, never inside one), creates the application's
   database and role from the same per-install credentials
   record the PHP runtime uses, and starts the program with
   **`DATABASE_URL`** in its environment, assembled from that
   record. Backups take a `pg_dump` of the database plus the
   cold file copy; a restore stages the dump for the app init
   to import, exactly the MariaDB contract.

## Worked example: SMF 2.1.7 (a forum)

Proven end-to-end in the slice 6 gate round and again in slice
6B against this exact slot shape.

1. In the setup wizard choose **Your own application**, then the
   **PHP** runtime, and Go Live. (This provisions the slot; the
   site answers "403/404" emptiness until the forum exists —
   that is expected.)
2. Download SMF 2.1.7 on another computer (from
   simplemachines.org), unzip it, and copy the contents into the
   app folder. (`other/` in the GitHub source archive holds the
   installer files; the release zip already has them at the top
   level.)
3. Open your `.onion` address in Tor Browser and run SMF's
   installer (`install.php`):
   - Database: server `localhost`, the name/user/password from
     the Dashboard's Application details page.
   - Forum URL: your full `http://….onion` address, no trailing
     slash.
4. **Delete `install.php` and the `*.sql` files** from the app
   folder when the installer tells you to. This is not optional
   hygiene; a leftover installer is an open door.
5. In SMF's admin panel, set the expectations the sealed room
   imposes:
   - Registration: use **immediate registration** or **admin
     approval** — never email activation (Configuration →
     Security and Moderation / Registration settings; also set
     the mail type off under Maintenance → Mail).
   - Avatars: disallow "download avatar at given URL" (members
     upload instead).
   - Turn off the server-side image proxy (it cannot fetch).
   - Expect a recurring harmless error-log line about failing to
     fetch the current SMF version — that check can never
     succeed here, and nothing depends on it.
6. Back up from the Dashboard. Restore brings back the forum,
   its members and its posts at the same address.

## Packaged recipes — the Forum (SMF), set up for you

The project also offers **packaged recipes** (amendment A23):
pre-configured, checksum-pinned installs of known applications
that the wizard sets up for you. A recipe is a convenience layer
*on top of this exact contract*, never a replacement for it:
anything a recipe can do, you can do by hand through this page,
and "install your own" remains a first-class choice (A20).

The first recipe is a **forum** — SMF 2.1.7, the same software
that runs many long-lived communities. In the setup wizard,
choosing "Your own application" and then "Forum - set up for
me" is the whole job: you pick the forum administrator's name
and password, press Go Live, and the forum is there at your
address — one board ("General Discussion") with SMF's standard
welcome topic, ready for members. What the recipe did for you:

- **Installed the exact pinned release** (the archive's SHA-256
  is in the recipe and is verified before anything is applied).
  The application's installer and upgrader scripts never reach
  the served folder — a leftover installer would be an open
  door, the warning this page gives hand installers.
- **Wrote the forum's configuration with this machine's own
  database credentials**, generated by the platform at install
  time. They exist in your forum's `Settings.php`, never in the
  recipe package; every machine's are different.
- **Seeded the database** the way SMF's own installer would,
  plus the sealed-world adjustments below, and created your
  administrator account with the name and password *you* chose
  in the wizard. Nobody else picks it, and it exists nowhere
  else. (Technical footnote: the seed stores the password in
  SMF's older hash format because the platform has no PHP
  runtime of its own to make the modern one; SMF upgrades it to
  the modern format the first time you sign in — one more
  reason to sign in once right after setup.)
- **Sealed-world settings**: new members register immediately
  and can post at once — email activation can never work here
  because the forum cannot send email (its mail setting stays
  "PHP mail", which fails instantly and cleanly rather than
  queueing mail that can never leave). The forum never fetches
  anything: remote avatars are not downloaded or measured by
  the server (members upload avatar pictures instead),
  Gravatar is off, the built-in image proxy is off (posted
  external images load in the *visitor's* browser, or not at
  all), and the version-check data files whose only job was to
  be fetched from the maker's site — failing noisily in the
  error log forever, here — are not installed. The forum
  administrator's email address starts as
  `admin@<your-onion-address>`, a placeholder nobody can write
  to; change it in the forum's admin panel if you like, knowing
  the forum still cannot send mail.
- **PHP execution is off in the directories the forum writes
  to** (attachments, uploaded avatars, cache, packages), via the
  recipe's nginx overlay: an uploaded file can never become a
  running script there. The normal case is unaffected — SMF
  serves attachments through itself, not by executing them.
- **Your forum's data is yours in the usual ways**: posts and
  members live in the database, uploads and avatars in the
  `attachments/` and `custom_avatar/` folders of the app-data
  volume, and backups (format 2) carry all of it. Switching
  site kinds and switching back works exactly as below.

**Recipe updates** arrive through the same signed update
channel as the platform itself, as their own package
(`onionhost-recipe-smf`) with their own anti-rollback floor, so
a forum security fix never waits for a platform release. An
update replaces the forum's program files with the new pinned
release, carries your `Settings.php`, attachments and avatars
over untouched, restarts the site, and health-checks it — and
if the new version fails the check, the previous recipe is put
back automatically and the forum carries on. One sharp edge to
know: if you edit the forum's program files yourself, a recipe
update will overwrite your edits (SMF's own upgrader would do
the same). Your data — the database, uploads, avatars — is
never part of what an update replaces.

How the three flags slice 6B left for the first recipe were
resolved:

1. **Permission exceptions**: the startup permission tidier's
   uniform pass now honours an exception list,
   `/etc/onionhost/normalize-exceptions`. The SMF recipe uses it
   for exactly two files: `Settings.php` and `Settings_bak.php`
   stay at `0660` (they hold the database password) instead of
   the group-shared `0664` everything else gets. SMF needs
   nothing else — proved by it running under the uniform modes
   throughout slice 6B.
2. **Upload-directory PHP execution**: the recipe's nginx
   overlay above. The platform still does not do this for
   hand-installed apps — it cannot know which of your folders
   are upload directories; a recipe knows its app.
3. **Credential substitution**: the platform renders the app's
   config at apply time from `/etc/onionhost/app-db.env`, which
   provisioning generated for this machine. The recipe package
   itself contains no credentials and no per-machine values at
   all — the same package installs correctly on every machine.

## Packaged recipes — WordPress, set up for you

The second recipe is **WordPress 7.1.3** — pages, posts,
comments and a media library: a blog or a small website rather
than a discussion board. In the setup wizard, choosing "Your
own application" and then the WordPress option is the whole
job: you pick the administrator's name and password (and you
have already chosen the site's title on an earlier page),
press Go Live, and WordPress is running at your address with
its standard first post and your administrator account ready
to sign in. What the recipe did for you:

- **Installed the exact pinned release.** The archive's
  SHA-256 is in the recipe and is verified before anything is
  applied; the contents were additionally verified file by
  file against wordpress.org's own published checksums when
  the recipe was packaged.
- **Ran WordPress's own installer** — over the site's own
  socket, with the details you staged — instead of imitating
  it. WordPress's schema and defaults live in its PHP code,
  so the honest way to seed it is to let it seed itself: the
  installer creates the tables, the default content and your
  administrator account, hashing your password itself with
  WordPress's current bcrypt. (The forum recipe above seeds
  by SQL because SMF keeps a static install script; the
  difference is the applications', not a preference.) The
  moment installation verifies, the installer and upgrader
  files are removed from the served folder, and no later
  update brings them back.
- **Wrote `wp-config.php` with this machine's own values**:
  the database credentials provisioning generated, a table
  prefix, and eight authentication salts generated fresh on
  this machine (they exist nowhere else, and not in the
  recipe package). The file is kept at `0660` by the same
  permission-exception mechanism the forum recipe uses,
  because it holds the database password.
- **Sealed-world settings**, mostly in a small must-use
  plugin the recipe maintains plus constants in the rendered
  config:
  - *All outbound HTTP is blocked inside WordPress*
    (`WP_HTTP_BLOCK_EXTERNAL`, no exceptions list). A plugin
    or theme that tries to phone anywhere gets an immediate,
    clean failure instead of a dial-out — and there is no
    dial-out to be had anyway; the container has no network.
  - *WordPress's own updater is disabled.* Updates arrive
    only as recipe packages through the signed channel
    below, and the version/plugin/theme checks are answered
    "checked just now, nothing new", so the admin screens
    show no dead update nags.
  - *Gravatar is off.* WordPress's built-in avatars are
    Gravatar URLs handed to every **visitor's** browser —
    which would tell gravatar.com who reads your site, and
    when. The default avatar is a local blank image and any
    Gravatar URL is replaced by it. Members who want a
    picture can use a local-avatar plugin; its uploads land
    in the media library like any other file.
  - *Core's emoji scripts are not loaded* — they would be
    fetched from `s.w.org` by visitors' browsers; browsers
    fall back to their own emoji.
  - *XML-RPC is off* (its pingback machinery expects the
    open internet, and it is a long-standing brute-force
    amplifier). Everything else in WordPress works without
    it; remote-publishing apps cannot reach this site except
    as visitors anyway.
  - *The theme/plugin code editor is off*: an administrator
    session must not become code execution. Manage files in
    the app folder instead.
  - *Search engines are discouraged* (the installer's
    `blog_public` is off) — an onion address has no search
    index to be in.
  - The administrator's email starts as
    `admin@<your-onion-address>`, a placeholder nobody can
    write to.
- **Comments are on**, with WordPress's own defaults: a
  first-time commenter's comment waits in the moderation
  queue until you approve it. Two sealed-room consequences
  to know: WordPress cannot email you about pending
  comments (it can send no mail at all), so check the
  Comments screen when you visit; and spam filtering that
  phones home (Akismet and friends) cannot work here —
  moderation is yours.
- **Self-registration starts closed.** WordPress registration
  completes by email — the new member is sent a "set your
  password" message — and this site can never send it, so an
  open registration form would be a door that never finishes
  opening. Create member accounts yourself under Users in
  wp-admin; if a member forgets their password, you reset it
  for them there, for the same reason. (The setting is an
  ordinary option seeded once: if you deliberately reopen
  registration knowing the caveat, the recipe will not argue
  with you afterwards.)
- **The media library works as usual** — uploads land in
  `wp-content/uploads/` in the app-data volume, count toward
  the app quota, and ride in backups. Uploaded files are
  served as files, never executed: PHP is off for the whole
  uploads tree (the recipe's nginx overlay — a prefix rule
  that outranks the PHP handler), so an uploaded script is
  inert text, exactly like the forum recipe's attachment
  directories.
- **URLs are the plain kind** (`?p=123`), and the REST API
  answers in its plain form (`?rest_route=`) — the form
  WordPress itself advertises under this permalink setting.
  Pretty permalinks (`/2026/10/my-post/`) need a platform
  change to the shared web-server configuration; it is
  recorded as future platform work, not promised here.
- **Plugins and themes**: install them by uploading the zip
  in wp-admin (Plugins → Add New → Upload) or by putting
  their files in the app folder — both work sealed. Browsing
  the wordpress.org directories from inside wp-admin cannot
  work (that is the internet again). Judge plugins by one
  rule: anything whose job needs the internet — mail
  delivery, external APIs, social embeds, most commerce —
  will fail here, cleanly and immediately. Pasting a link to
  an outside page will not expand into an embedded preview
  (WordPress would have to fetch it); the link stays a link.
- **Scheduled posts do not publish themselves.** WordPress
  runs its housekeeping (WP-Cron) by reaching back to its
  own address when visits arrive; inside the sealed room
  that loopback cannot happen, so a post scheduled for later
  will sit past its time until you publish it yourself.
  Nothing else depends on those housekeeping runs here —
  updates are the platform's job, as above.

**Recipe updates** work exactly as the forum's: the
WordPress recipe is its own package
(`onionhost-recipe-wordpress`) with its own anti-rollback
floor on the same signed channel, so a WordPress security
fix never waits for a platform release. An update replaces
the program files, carries your `wp-config.php` and
everything in `wp-content/uploads/` over untouched,
restarts the site and health-checks it; a version that
fails the check is put back automatically. Your own edits
to program files are overwritten by an update, as with any
WordPress upgrade; your posts, media and settings are data,
and are never part of what an update replaces. Recipe v1
covers patch-level WordPress updates; a future WordPress
version upgrade that needs its database upgrader will ship
as its own considered recipe step, the way the forum recipe
treats SMF major versions.

## Packaged recipes — DokuWiki, set up for you

The third recipe is **DokuWiki 2026-07-14c** — a wiki: pages
any member can read, and (as you allow) edit, with the whole
history kept. It is the choice when the site is mostly shared
writing — documentation, a community knowledge base, a
campaign notebook — rather than discussion or posts. In the
setup wizard, choosing "Your own application" and then the
wiki option is the whole job: you pick the administrator's
name and password, press Go Live, and the wiki is running at
your address with the standard start page and your
administrator account ready. What the recipe did for you:

- **Installed the exact pinned release.** The archive's
  SHA-256 is in the recipe and is verified before anything
  is applied; the archive was additionally compared against
  the maker's GitHub release copy when the recipe was
  packaged — the two are identical.
- **There is no database, at all.** DokuWiki keeps
  everything in ordinary files: pages are text files,
  pictures are picture files. For this site the platform
  does not start its database server — there is nothing
  for it to do — and a backup is simply an encrypted copy
  of the files, taken with the site briefly paused so a
  page being edited that second cannot tear. A restore
  brings the wiki back exactly, at the same address.
- **Ran DokuWiki's own installer** — over the site's own
  socket, with the details you staged — rather than
  imitating it, the same reason as the WordPress recipe:
  the administrator's password is hashed by DokuWiki
  itself with its modern bcrypt from the first moment, and
  the access rules (below) are the ones the installer
  itself writes. The moment installation verifies, the
  installer file is removed from the served folder, and no
  later update brings it back.
- **Access starts sensibly**: everyone may *read* the wiki;
  only signed-in members may edit or upload. The
  administrator (you) can loosen or tighten this in the
  admin settings — the whole wiki can be made members-only
  there.
- **Sealed-world settings**, held in protected configuration
  files the recipe maintains (see the last point):
  - *The update check is off.* The wiki never phones the
    maker's site to ask about new versions; updates arrive
    only as recipe packages through the signed channel.
  - *The remote API is off*, and *media fetching is off*:
    the wiki serves only its own media from its own files.
    A page that references an outside picture shows the
    link's text, not a fetched copy — nothing here can be
    made to fetch a visitor-supplied address.
  - *The extension manager's remote actions are disabled*,
    and the popularity-reporting plugin is off. Searching
    or downloading extensions needs the internet; installing
    a plugin means putting its files in the app folder
    yourself, like a hand install — with the caveat below.
  - *The web server never serves the wiki's insides*: the
    folders holding pages, configuration, code libraries
    and scripts answer "forbidden" to any direct web
    request. Pages and media reach visitors only through
    the wiki itself, which is what the access rules govern.
- **Self-registration starts closed** — the installer writes
  that itself when the recipe drives it. An account here is
  created by the administrator (Admin → User Manager), for
  the same reason as WordPress: registration flows that
  expect email cannot finish — the wiki can send no mail,
  and a member who forgets their password needs you to
  reset it for them there. The setting is an ordinary one:
  if you deliberately open registration in the admin
  settings, knowing the caveat, the recipe will not argue
  with you afterwards.
- **Two configuration files, two jobs.** Your settings
  (title, access rules, your user accounts) live in the
  wiki's own configuration on the app-data volume, exactly
  as a hand install would leave them. The sealed-world
  pins above live in separate *protected* files the recipe
  looks after; an update refreshes those, and never touches
  yours.
- **Plugins you add by hand live in the program tree**
  (`www/lib/plugins`), and a recipe update replaces the
  program tree — the same sharp edge as editing any
  program files under the other recipes. Plugins that ship
  with DokuWiki itself are part of the pinned release and
  always match. Your pages, media, history and settings
  are data, and are never part of what an update replaces.

**Recipe updates** work exactly as the other recipes': the
wiki recipe is its own package (`onionhost-recipe-dokuwiki`)
with its own anti-rollback floor on the same signed channel.
An update carries your pages, media and configuration over
untouched, restarts the site and health-checks it; a version
that fails the check is put back automatically.

## Packaged recipes — Gitea, set up for you

The fourth recipe is **Gitea 1.27.3** — your own small
code-hosting service: git repositories with a web front end
for browsing, issues and pull requests, for a team or a
community that wants its code on its own ground. It is also
the platform's first *native* recipe: no PHP, no web-script
interpreter at all — one self-contained program, exactly the
shape the native contract above describes. In the setup
wizard, choosing "Your own application" and then the forge
option is the whole job: you pick the administrator's name
and password, press Go Live, and the forge is running at
your address. What the recipe did for you:

- **Installed the exact pinned program.** The binary's
  SHA-256 is verified before anything is applied; when the
  recipe was packaged, the checksum was matched against
  the publisher's own signed checksum file (and the
  publisher's GPG signature on it verified), and against a
  second source. The program file is about 126 MB — large,
  but it carries its whole world with it.
- **Its database is its own.** Gitea keeps its accounts,
  repository metadata, issues and settings in a single
  SQLite database file inside the app-data volume; the
  repositories themselves are ordinary files beside it.
  The platform's database server is not started for this
  site. Backups pause the program briefly and copy its
  files cold, so a restore brings back repositories,
  accounts and history together, at the same address.
- **The administrator account is created by Gitea itself**,
  inside the sealed room, the first time the site starts —
  using Gitea's own admin tool with the name and password
  you staged in the wizard. The staged copy is shredded
  the moment the account exists, exactly as with the PHP
  recipes; the account's password hash is Gitea's, made by
  Gitea. Sign in once after setup to confirm it.
- **Sealed-world settings**, in the configuration the
  recipe generates for this machine (it also carries the
  site's own address and its own secrets, generated here,
  existing nowhere else):
  - *Self-registration is off.* Create accounts for your
    members in the admin panel (Site Administration →
    User Accounts). The forge sends no mail — that is
    switched off too — so email-based sign-up and
    password-reset mail can never complete; a member who
    forgets their password needs you to reset it for them
    in the admin panel.
  - *Repository mirroring is off.* A mirror would have to
    fetch from the internet; there is no internet to fetch
    from. Repositories get here by being pushed (below)
    or created here.
  - *Webhooks cannot deliver.* You can create them, but a
    webhook is a phone call to the internet and the room
    has no phone. Expect them to sit undelivered; nothing
    here can change that.
  - *Avatars are local.* On this version, member avatars
    are generated by the forge itself (identicon-style
    pictures) and served from it — no Gravatar fetching by
    the server, and visitors' browsers are not sent there
    either.
- **Git access is over the web address only.** Clone and
  push use the repository's `http://….onion` URL from a
  member's own machine running Tor (Tor Browser cannot do
  this; a git client configured for Tor can). **SSH git
  access is not offered** — the sealed design exposes no
  SSH port, by design, and the configuration switches it
  off. Public repositories can be browsed and cloned by
  anyone who can reach the address; private ones need an
  account, as usual.
- **Repositories, accounts and the whole state live in the
  native folder** of the app-data volume and ride in
  backups, under the native contract's rules.

**Recipe updates** work as the other recipes', with one
shape difference: the update replaces the *program file*
(the old one is kept beside it until the new one proves
healthy) and never touches the data folder. The forge
recipe is its own package (`onionhost-recipe-gitea`) with
its own anti-rollback floor on the same signed channel. The
recipe covers patch-level Gitea updates; a future
major-version step — Gitea upgrades its database when it
starts — will ship as its own considered recipe step, the
way the other recipes treat major versions.

## Packaged recipes — the Marketplace (Polyculture Markets), set up for you

The fifth recipe is **Polyculture Markets** — the project's own
marketplace: sellers list goods, buyers pay the *sellers
directly* in Monero (there is no escrow and no money ever
passes through this computer), and messages between buyers
and sellers are encrypted so only the people in a
conversation can read them. It is a native recipe like
Gitea's — one program file, no PHP — and the platform's
first **PostgreSQL** recipe: the marketplace keeps its
accounts, listings, orders and reputation in a real
database, so the platform runs PostgreSQL inside the same
sealed sandbox and hands the program its connection string
(`DATABASE_URL`, from the per-install credentials record —
the credentials themselves are never in the package). In
the setup wizard, choosing "Your own application" and then
the marketplace option is the whole job: you name the
marketplace, pick the administrator's name and password,
press Go Live, and it is running at your address. What the
recipe did for you:

- **Installed the exact pinned programs.** Two binaries,
  built from the marketplace's published source: the
  marketplace itself (its SHA-256 is verified before
  anything is applied) and the small media helper it uses
  to clean uploaded pictures, staged beside it.
- **Created the administrator through the marketplace's
  own front door.** The bare marketplace has no admin
  bootstrap — registering makes a buyer, and that is all.
  So on first start, before the site opens, the recipe
  registers your chosen account through the marketplace's
  own registration form (its own rules and password
  hashing), promotes that one account to administrator,
  and *proves it* by signing in and opening the Moderation
  page. The staged password copy is shredded the moment
  the account exists, exactly as with the other recipes.
  Your administrator name must be one the marketplace
  accepts (3–24 characters: lowercase letters, numbers,
  `_` or `-`) and your password at least 12 characters —
  the wizard checks both before it stages them.
- **Migrated the database.** The marketplace never
  migrates itself; its schema ships as numbered migrations
  inside the recipe, and a small step inside the sandbox
  applies any that are missing — in order, recorded in a
  ledger — every time the site starts, before the
  marketplace opens. An update that brings new migrations
  applies them the same way; if a migration ever failed,
  the marketplace would not start against a half-migrated
  schema (the site answers "not ready" and a bad update
  rolls back).
- **Your marketplace's settings are a file you own.** On
  first install the recipe writes `app.env` in the app
  folder from the name you chose in the wizard — display
  name, data paths, the payment and housekeeping values
  the project ships as its accepted defaults. It is never
  overwritten by updates. It holds no passwords: the
  database credentials live in the platform's own record,
  and the marketplace's master key file is generated by
  the marketplace itself in the app folder (kept at mode
  0600) and rides in backups with everything else.
- **Stagenet, deliberately.** Your marketplace runs on
  Monero's **stagenet** — test coins with no real value —
  and the recipe locks it there. The marketplace software
  refuses real funds unless it runs under its production
  profile *and* its operator has typed an exact acceptance
  sentence into its configuration; moving an instance to
  real money is a separate launch decision, made in the
  open, and this recipe does not make it for you.
- **Sellers and payments, honestly stated.** Anyone may
  register; a seller applies in the app and you approve
  them under Moderation. Sellers generate their payment
  addresses in their own wallet (the project's
  seller-helper) and upload them; when a buyer orders, the
  marketplace hands them one of the seller's addresses and
  the buyer pays the seller directly. The marketplace
  never holds keys, funds or payment proofs, charges no
  fees, and cannot take a payment back — its pages say
  exactly this to your visitors (see its Limitations and
  Payment risks pages, which show your instance's real
  settings).
- **Everything lives where backups can reach it**: the
  PostgreSQL database (backed up as a database dump, the
  MariaDB contract), the media and message-blob folders,
  the key file and `app.env`, all in the app-data volume.

**Recipe updates** work as the other recipes': the update
replaces the program files (the old ones kept beside them
until the new ones prove healthy), applies any new
migrations at the next start, and never touches the
database contents, `app.env` or the data folders. The
marketplace recipe is its own package
(`onionhost-recipe-marketplace`) with its own
anti-rollback floor on the same signed channel — the
marketplace is young software and will keep changing;
this channel is how those changes reach your instance.

## Switching site kinds

Choosing a different kind later starts a fresh site of that kind
(the wizard says so). Nothing is deleted: switching away from an
app site stops the app container and leaves the app folder, the
database and its credentials exactly as they were; switching back
resumes them. Backups restore whichever kind they were made from
and re-select the slot accordingly.

## For recipe authors (technical appendix)

A recipe is a directory `onionhost/recipes/<id>/` in the project
tree, built into its own signed package (`build/build-recipe-deb.sh`)
with its own anti-rollback floor (`floor.txt`). Everything the
platform needs to know is the manifest, `recipe.json`, rendered
into the package at `/usr/share/onionhost/recipes/<id>/manifest.json`;
the wizard offers every installed manifest, so a recipe needs no
wizard changes. The keys that exist today, and what they proved on:

- **`runtime`**: `php` or `native`. PHP recipes serve from the
  `www/` tree; native recipes stage one program file.
- **`db.required`**: `true` asks provisioning for database
  credentials (`/etc/onionhost/app-db.env`) and makes backups
  take a database dump; `false` means no credentials, no dump —
  and for native sites (or PHP sites with `db.required: false`)
  backups take the whole app tree **cold**, the app paused,
  because the files *are* the database. MariaDB is not started
  for a container whose recipe declares no database.
- **`db.engine: "postgres"`** (with `db.required: true`): the
  site's database is PostgreSQL, run by the app init inside
  the sandbox (datadir at `appdata/pgdb`, superuser by
  password over the loopback — the D2 rule). The credentials
  record is the same file in the same shape; the init creates
  the role + database from it at every start and exports
  `DATABASE_URL` (assembled there, the one place credentials
  are combined) to the recipe's boot steps and the program.
  Backups `pg_dump`; restores stage the dump as
  `appdata/db-import.sql.gz` for the init to import once,
  deleted only on success, as with MariaDB. The marketplace
  is the proving recipe.
- **`native_serve: {"type": "tcp", "port": N}`** (native): the
  program binds TCP on the sandbox loopback instead of the
  platform unix socket. `onionhost-generate-configs` reads
  the fact from the installed manifest (named by the recipe
  selection) and renders the TCP nginx variant with the port
  substituted; nothing is stamped into the site marker, so
  restores and re-renders cannot drift from it.
- **`native/migrate.sh`** (native, by convention): when a
  native program does not migrate its own schema, the recipe
  ships this step and the app init runs it at *every* start,
  after the database and before `first-boot.sh` and the
  program. It must be marker-idempotent (the marketplace's
  records a `schema_migrations` ledger, mirroring its own
  deploy tooling). A failing migrate step means the program
  is *not* started — nginx answers 502 and a bad update's
  health check fails and rolls back.
- **`app.env` by `native_config`** (native): a program
  configured only through environment variables uses the
  ordinary `native_config` render with `dst: "app.env"`;
  the app init parses that file at every start as *data*
  (literal `KEY=value` lines, never evaluated;
  platform-managed names — `ONIONHOST_*`, `PATH`, `HOME`,
  `DATABASE_URL` — cannot be set from it) and exports the
  values for the boot steps and the program. Credentials
  never travel in it: `DATABASE_URL` comes from the
  credentials record, above.
- **PHP tree archives**: `archive.format` is `zip` (SMF,
  WordPress) or `tar` (DokuWiki — tarballs carry unix
  permissions a zip loses). `archive.sha256` is verified before
  any apply; a mismatch refuses with the live site untouched.
- **`config_file` / `config_renderer`**: the per-machine config
  is rendered from the archive's sample at first install and
  carried over verbatim on updates (`config_carryover` names
  siblings carried the same way). Renderers: `smf-settings`
  (pattern substitution), `wp-config` (define() insertion +
  generated salts), `none` (no rendered config at all — the
  recipe's state lives in `data_dirs`; DokuWiki).
- **`install` (the install hook)**: for apps whose seeding
  cannot be static SQL. `type: http-form` posts one form over
  the edge socket to the app's own installer once the stack
  is up: `probe_path`/`form_marker` detect a live installer,
  `installed_marker` detects "already installed",
  `fields` templates substitute the staged admin and title
  (`{admin_user}`, `{admin_pass}`, `{site_title}`, `{onion}`,
  `{email}=admin@<onion>`), `success_marker` confirms.
  `default_title` at manifest level is the fallback title.
  Which fields to *omit* is part of the recipe's craft:
  WordPress's demand is `weblog_title`; DokuWiki's is the
  absent "allow registration" field — the installer writes
  registration-off itself. Field values are post data, never
  URLs or logs; the staged admin file is shredded after.
- **`seed/`**: optional static seeding (SMF's install SQL,
  rendered by the seed runner) and recipe-side templates:
  a native recipe's config template lives here too.
- **`extra_files`**: payload files placed from `files/` at
  apply time (SMF's tail SQL staging uses a sibling mechanism;
  WordPress's must-use plugin; DokuWiki's protected configs).
  `"after_data": true` places them *after* the `data_dirs`
  carryover, so recipe-maintained files inside data dirs are
  refreshed on every apply while owner files are carried.
- **`exclude_paths` / `install_files`**: installer/upgrader
  files never reach the served tree on an update apply;
  `install_files` may ride along on the *first* install only
  (the hook needs the installer present), and the hook's
  finish step removes them.
- **The nginx overlay rule** (`overlay/`): anything under a
  regex location in the golden template is unreachable, so
  denies for upload/data directories must be `^~` prefix
  locations. Whether PHP execution is off is only proven by
  reading the response body of a script placed there —
  source code in the reply means *served*, a denial or the
  script's output means the location never matched PHP.
- **Native recipes**: `archive.format: "file"` (one binary,
  sha256-verified), `native_files` (payload files staged
  into the native folder with modes — e.g. the first-boot
  script), `native_config {src, dst}` (a template rendered
  once — first install only, judged by the file's own
  presence — with `{onion}`, `{site_title}` and generated
  `{secret_key}`/`{internal_token}` substituted; an
  unsubstituted token is a hard error). Updates swap the
  program (`app` ↔ `.app-prev`), never the config or data.
- **`first_boot: true` (native)**: the wizard-staged admin is
  copied into the native folder as `.recipe-admin.env`
  (mode 0400, data — never executed). At container start,
  before the program starts, the app-init runs the recipe's
  `first-boot.sh` if `.first-boot-done` is absent; the script
  creates the administrator with the app's own tooling,
  shreds its env copy, and writes `.first-boot-done`.
  Meanwhile `onionhost-publish` waits for that marker
  (`onionhost-recipe await-first-boot`) and only then
  shreds the host-side staged copy — a first boot that never
  completes fails the publish with the credentials still
  staged for a retry, never half-consumed.
- **Backups follow the manifest**: the restore re-creates
  the site marker with the recipe's runtime and db mode, so
  a restored site provisions exactly what the original had.
  It also reinstates the recipe selection file from the
  restored site model before rendering configs (backups
  never captured the selection itself): without it, a
  restored TCP-serve recipe renders the unix nginx variant
  and answers 502 behind a healthy application. Publish
  likewise writes the selection BEFORE provisioning, for
  the same reason — the render at the end of provisioning
  is the one the first stack start uses.
- **Helper executables and the normaliser**: the app-init's
  uniform pass flattens every file in the app-data trees to
  0664 at every start (the owner/app sharing contract), and
  the golden init re-chmods only the archive binary
  (`native/app`) before exec. A recipe that ships a helper
  binary the application execs directly (the marketplace's
  media-worker is the first) MUST pin its mode in
  `overlay/normalize-exceptions` (e.g. `0755
  native/media-worker`), or the helper loses its exec bit at
  the first container start and fails only when the feature
  that calls it is used. The manifest's `native_files` modes
  are honoured at apply; the exceptions file is what keeps
  them true at run time.


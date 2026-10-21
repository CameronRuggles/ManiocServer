This recipe has no SQL seed and no host-rendered config,
deliberately.

DokuWiki is a flat-file application: there is no database to
seed (its manifest declares db.required=false, and the platform
provisions the site without MariaDB at all), and its
configuration is written by its own installer, in PHP -
conf/local.php, conf/users.auth.php (the administrator account,
its password hashed by DokuWiki itself with bcrypt) and
conf/acl.auth.php.

So the recipe drives the installer, exactly the way the
WordPress recipe does: the manifest's "install" stanza is an
http-form hook. onionhost-publish runs it after the app
container starts; it speaks install.php's own form over the
edge socket with the administrator details the owner staged in
the wizard - ACL on, policy "public" (visitors read, members
edit), registration left OFF (the installer's own allowreg
switch, written into local.php as an ordinary owner-changeable
option, the same posture the WordPress recipe seeds) - and the
hook removes install.php from the served tree the moment the
installation verifies.

Why not seed users.auth.php host-side, SMF-style? SMF accepts
a legacy sha1 hash and upgrades it to bcrypt at first login.
DokuWiki never upgrades a legacy hash at login (checked in the
vendored source: authplain's checkPass only verifies), so a
host-seeded legacy hash would have stayed weak for the life of
the account. Driving the installer makes DokuWiki hash the
password itself, with its configured bcrypt, from birth.

The sealed-world settings that must hold regardless of the
owner's admin choices ride in files/ as DokuWiki's protected
config cascades (conf/local.protected.php,
conf/plugins.protected.php), placed by the applier after the
data-directory carryover on every apply: update checks off,
remote-media fetching off, the remote API off, the extension
manager and the popularity reporter disabled.

See ISO-BUILD-LOG.md, "A23 RECIPES 3+4 - DOKUWIKI + GITEA",
for the full record and reasoning.

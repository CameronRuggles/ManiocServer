This recipe has no SQL seed, deliberately.

WordPress's installer is PHP (wp-admin/install.php): its schema
lives in wp-admin/includes/schema.php and its default options in
PHP code, so there is no static install SQL to substitute the way
SMF's recipe does. Replicating those writes in SQL would bake a
brittle, per-version copy of the installer's behaviour into the
recipe.

Instead, the applier renders wp-config.php at apply time (this
machine's database credentials, a per-install table prefix, and
salts generated on this machine), and after the app container
starts, onionhost-publish runs the recipe's install hook
(onionhost-recipe install-hook wordpress), which drives
WordPress's OWN installer over the edge socket with the
administrator details the owner staged in the wizard. The
installer creates the schema, the default content, and the
administrator account - hashing the password itself, with
WordPress's current bcrypt - and the hook then removes the
installer files from the served tree.

See ISO-BUILD-LOG.md, "A23 RECIPE 2 - WORDPRESS", for the full
record and reasoning.

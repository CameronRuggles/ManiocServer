<?php
/**
 * OnionHost sealed-world plugin state for DokuWiki - packaged
 * recipe (A23). This file is DokuWiki's PROTECTED plugin
 * cascade: loaded after conf/plugins.local.php, so the wiki's
 * admin pages cannot re-enable what is disabled here. The
 * recipe refreshes it on every apply.
 */

// The extension manager installs and updates plugins and
// templates by downloading them from dokuwiki.org. Downloads
// are the one thing the sealed room never does: plugins and
// templates arrive with recipe updates, or as files the owner
// copies into the app folder by hand. The manager's other job
// (seeing what is installed) goes with it - the recipe record
// and the app folder itself answer that.
$plugins['extension'] = 0;

// The popularity plugin sends anonymous usage statistics to
// dokuwiki.org. Nothing reports out of the sealed room.
$plugins['popularity'] = 0;

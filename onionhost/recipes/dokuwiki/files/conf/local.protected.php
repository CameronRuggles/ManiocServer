<?php
/**
 * OnionHost sealed-world settings for DokuWiki - packaged
 * recipe (A23). This file is DokuWiki's PROTECTED config
 * cascade: it is loaded after conf/local.php and the wiki's
 * admin pages cannot change these values. The recipe refreshes
 * it on every apply; the owner's own choices belong in
 * conf/local.php (the ordinary config the installer wrote),
 * never here.
 *
 * Each line closes a way the wiki would otherwise reach out of
 * the sealed room or invite the outside in. The container has
 * no network of its own, so every one of these would fail at
 * the wall anyway - the settings make the wiki not try, which
 * is faster, quieter, and honest.
 */

// No phoning home about new releases. DokuWiki updates arrive
// only through the platform's signed channel (the recipe
// packages), like every other packaged app's.
$conf['updatecheck'] = 0;

// fetch.php never downloads remote media server-side: a page
// that references an image by URL shows the visitor's browser
// the URL, and the wiki itself fetches nothing. (Also the
// upstream default - pinned here so a future default change
// cannot quietly open the fetch path.)
$conf['fetchsize'] = 0;

// The remote API (XML-RPC / JSON-RPC) stays off. Nothing
// outside the machine can use it as a visitor anyway, and a
// wiki's content is edited through its pages. (Also the
// upstream default, pinned for the same reason.)
$conf['remote'] = 0;

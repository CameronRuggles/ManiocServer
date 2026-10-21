<?php
/**
 * Plugin Name: OnionHost sealed-world posture
 * Description: A platform file of the packaged WordPress recipe
 * (A23). WordPress on OnionHost runs in a sealed room: no
 * outbound network, no mail, and no self-update machinery (it
 * could only work by downloading). The platform installed
 * WordPress once; updates after that are the owner's, by file
 * replacement (A26). This must-use plugin carries the parts of
 * that posture that live in WordPress options and filters
 * rather than in wp-config.php. It is (re)written by the recipe
 * on every apply; deleting it deletes the posture, not the site.
 *
 * @package OnionHost
 * License: GPL-2.0-or-later
 * License URI: https://www.gnu.org/licenses/gpl-2.0.html
 *
 * This file is distributed alongside WordPress, which is licensed
 * under GPL-2.0-or-later, and is itself licensed GPL-2.0-or-later
 * to match. See LICENSING.md at the repository root.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/*
 * Avatars: WordPress's only built-in avatar source is Gravatar -
 * the avatar URL is handed to every VISITOR's browser, which then
 * tells gravatar.com who is reading this site and when. In the
 * sealed room that is both a privacy leak and a dependency that
 * cannot work well, so: the default avatar is the local blank,
 * and any gravatar URL that would be emitted (for accounts whose
 * address has a Gravatar) is replaced by the local blank image.
 * Members who want a picture use a local-avatar plugin, whose
 * uploads land in wp-content/uploads like any other media.
 */
add_filter(
	'pre_option_avatar_default',
	function () {
		return 'blank';
	}
);
add_filter(
	'get_avatar_url',
	function ( $url ) {
		if ( is_string( $url ) && false !== strpos( $url, 'gravatar.com' ) ) {
			return includes_url( 'images/blank.gif' );
		}
		return $url;
	}
);

/*
 * Update checks: wp-config.php defines AUTOMATIC_UPDATER_DISABLED
 * and WP_HTTP_BLOCK_EXTERNAL, so WordPress cannot fetch or apply
 * updates itself - under A26 there is no platform update path
 * for an installed app at all; updating is the owner's, by file
 * replacement. These filters answer the version, plugin and
 * theme checks with "checked just now, nothing new", so wp-admin
 * shows no dead update nags - and the version-check machinery,
 * reading the same transients, finds them fresh and skips its
 * (blocked anyway) phone-home entirely.
 */
function onionhost_neutral_update_core( $value ) {
	global $wp_version;
	$value                 = is_object( $value ) ? $value : new stdClass();
	$value->last_checked   = time();
	$value->version_checked = $wp_version;
	$value->updates        = array();
	return $value;
}
function onionhost_neutral_update_list( $value ) {
	$value                = is_object( $value ) ? $value : new stdClass();
	$value->last_checked  = time();
	$value->checked       = array();
	$value->response      = array();
	$value->no_update     = array();
	return $value;
}
add_filter( 'pre_site_transient_update_core', 'onionhost_neutral_update_core' );
add_filter( 'pre_site_transient_update_plugins', 'onionhost_neutral_update_list' );
add_filter( 'pre_site_transient_update_themes', 'onionhost_neutral_update_list' );

/*
 * Visitor-side external fetches: core's emoji support loads its
 * script and images from s.w.org in every visitor's browser.
 * Disabled; browsers fall back to their own emoji, and nothing
 * about this site depends on a third-party host.
 */
remove_action( 'wp_head', 'print_emoji_detection_script', 7 );
remove_action( 'wp_print_styles', 'print_emoji_styles' );
remove_action( 'admin_print_scripts', 'print_emoji_detection_script' );
remove_action( 'admin_print_styles', 'print_emoji_styles' );
add_filter( 'emoji_svg_url', '__return_false' );

/* No version disclosure in the page head. */
remove_action( 'wp_head', 'wp_generator' );

/*
 * Version disclosure, continued (deanonymization audit R-11):
 * the head was one of three places WordPress prints its exact
 * version. Every feed carries a <generator> element naming it -
 * suppress the generator text on all feed formats. And every
 * enqueued script and style URL carries the version as its
 * default ?ver= parameter - strip the parameter; the platform
 * serves whole files and never relied on it for cache-busting.
 */
add_filter( 'the_generator', '__return_empty_string' );
function onionhost_strip_asset_version( $src ) {
	if ( is_string( $src ) && false !== strpos( $src, 'ver=' ) ) {
		$src = remove_query_arg( 'ver', $src );
	}
	return $src;
}
add_filter( 'script_loader_src', 'onionhost_strip_asset_version' );
add_filter( 'style_loader_src', 'onionhost_strip_asset_version' );

/*
 * One-time seeded defaults (owner-overridable afterwards - these
 * write ordinary options once, they are not filters):
 * self-registration starts CLOSED. WordPress registration runs on
 * email: the new member is sent a "set your password" message,
 * and this site cannot send mail, so an open registration form
 * would be a door that never finishes opening. The administrator
 * creates accounts in wp-admin instead; if they deliberately
 * reopen registration knowing the caveat, that choice stands.
 */
add_action(
	'admin_init',
	function () {
		if ( get_option( 'onionhost_sealed_seeded' ) ) {
			return;
		}
		update_option( 'users_can_register', 0 );
		update_option( 'onionhost_sealed_seeded', 1 );
	}
);

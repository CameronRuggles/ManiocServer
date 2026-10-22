#!/bin/sh
# Marketplace recipe per-install provisioning (A23) - runs
# INSIDE the app container, started by the migrate step (see
# migrate.sh) at EVERY container start, before the first-boot
# step and before the marketplace starts.
#
# Its one job: the instance's two per-install files exist.
# The application refuses to start outside its Development
# profile when either is missing (PCM audit fixes AL1 and
# HT F1): it will not mint a replacement there, because a
# silently replaced master key makes every stored TOTP
# secret and disclosure undecryptable and changes every
# buyer token, and a silently replaced marketplace id
# orphans every pinned terms statement and every configured
# helper. So the RECIPE - the installer - mints each file
# exactly once, at the paths app.env names:
#
#   KEY_FILE_PATH    64 lowercase hex chars (32 bytes from
#                    /dev/urandom): the instance master key.
#   HT_ID_FILE_PATH  "mkt_" + 32 lowercase hex chars: the
#                    instance's permanent Hidden Trades id.
#                    The id is public by design (the seller
#                    page prints it for helper setup); its
#                    INTEGRITY is what is load-bearing.
#
# Both are created mode 0600 FROM CREATION (umask in a
# subshell - no create-then-chmod window) and handed to
# www-data, the user the application runs as; the init runs
# this step as root, and a root-owned 0600 file is one the
# application cannot read.
#
# NEVER overwrite: a file that exists is left exactly as it
# is - byte-identical - whatever its contents. An existing
# file with bad contents is the application's to refuse with
# its own clear error; "repairing" it here would orphan the
# instance's secrets exactly as the application's refusal
# guards against. Mint-if-absent, never-touch-if-present is
# what makes this step safe at every start: idempotent
# across reboots, re-applies and recipe updates.
set -u

log() { echo "marketplace provision-secrets: $*"; }

DATA=/srv/appdata/native
KEY_FILE="${KEY_FILE_PATH:-$DATA/marketplace.key}"
HT_ID_FILE="${HT_ID_FILE_PATH:-$DATA/marketplace.htid}"

hex() { # hex <nbytes> -> 2*<nbytes> lowercase hex chars
    head -c "$1" /dev/urandom | od -An -tx1 | tr -d ' \n'
}

provision() { # provision <path> <kind>
    _path=$1 _kind=$2
    if [ -e "$_path" ]; then
        return 0
    fi
    case "$_kind" in
        key)  _material=$(hex 32);        _want=64 ;;
        htid) _material="mkt_$(hex 16)";  _want=36 ;;
        *)    return 1 ;;
    esac
    # A short or empty read from the random source must fail
    # the step, never land as a truncated secret.
    if [ "${#_material}" -ne "$_want" ]; then
        log "ERROR: could not generate material for $_path"
        return 1
    fi
    mkdir -p "$(dirname "$_path")" || return 1
    # umask 077 in a subshell: the file is born 0600, with no
    # window at a wider mode.
    ( umask 077; printf '%s' "$_material" > "$_path" ) \
        || return 1
    chown www-data:www-data "$_path" 2>/dev/null || true
    if [ "$(stat -c %a "$_path" 2>/dev/null || echo '?')" \
         != "600" ]; then
        log "ERROR: $_path was not created at mode 0600"
        rm -f "$_path"
        return 1
    fi
    log "created $_path (mode 0600, generated once - it is" \
        "part of the instance; back it up with it)"
    return 0
}

provision "$KEY_FILE" key || {
    log "ERROR: could not provision the marketplace key file"
    exit 1
}
provision "$HT_ID_FILE" htid || {
    log "ERROR: could not provision the HT marketplace" \
        "id file"
    exit 1
}
exit 0

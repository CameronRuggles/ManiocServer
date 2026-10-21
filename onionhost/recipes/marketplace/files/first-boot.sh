#!/bin/sh
# Marketplace recipe first boot (A23) - runs INSIDE the app
# container, started by the app init (native branch) BEFORE
# the marketplace starts, the first time only (the init gates
# on the done marker this script leaves; onionhost-recipe's
# await-first-boot confirms the marker host-side).
#
# Its one job: create the owner's administrator account. The
# marketplace has no admin bootstrap of its own - registration
# always creates a buyer, there is no CLI and no first-user
# rule (measured on the project's hosted demo, where the
# first admin had to be promoted by hand in SQL). So this
# step uses the application's own flows, in its own order:
#   1. start the application briefly (as www-data, on its
#      loopback bind - the database is already up: the init
#      ran the database leg and the migrate step first);
#   2. register the owner's chosen account through the real
#      /register form (the application's own validation,
#      password hashing and admission rules all apply);
#   3. promote that one account to admin with a single SQL
#      UPDATE (role is data; this is the same promotion the
#      project performed by hand on its demo);
#   4. prove it: log in with the chosen password and load
#      /moderation as the new admin;
#   5. stop the temporary app, shred the staged details,
#      leave the done marker.
# The administrator details are the ones the owner chose in
# the setup wizard, staged root-only on the host and copied
# onto the app-data volume by onionhost-recipe at apply time
# (.recipe-admin.env, KEY=value lines). The plaintext password
# must not linger anywhere: the volume copy is shredded here
# on success, and the host copy by await-first-boot.
#
# Idempotent by design: a retried first boot finds the
# account already registered and simply re-promotes and
# re-verifies it.
set -u
DATA=/srv/appdata/native
ENV_FILE="$DATA/.recipe-admin.env"
DONE="$DATA/.first-boot-done"
APP="$DATA/app"
BASE="http://${BIND_ADDR:-127.0.0.1:8080}"

log() { echo "marketplace first-boot: $*"; }

shred() {
    if [ -f "$1" ]; then
        sz=$(wc -c < "$1" 2>/dev/null || echo 0)
        if [ "$sz" -gt 0 ] 2>/dev/null; then
            dd if=/dev/zero of="$1" bs=1 count="$sz" \
               conv=notrunc 2>/dev/null || true
        fi
        rm -f "$1"
    fi
}

if [ ! -f "$ENV_FILE" ]; then
    log "ERROR: the staged administrator details are missing"
    exit 1
fi
if [ -z "${DATABASE_URL:-}" ]; then
    log "ERROR: DATABASE_URL is not set - the database leg" \
        "did not run, so the account cannot be created"
    exit 1
fi

RECIPE_ADMIN_USER=""
RECIPE_ADMIN_PASSWORD=""
# Read KEY=value pairs as data - the file is never sourced
# (it is input, not code).
while IFS='=' read -r k v; do
    case "$k" in
        RECIPE_ADMIN_USER) RECIPE_ADMIN_USER=$v ;;
        RECIPE_ADMIN_PASSWORD) RECIPE_ADMIN_PASSWORD=$v ;;
    esac
done < "$ENV_FILE"

if [ -z "$RECIPE_ADMIN_USER" ] || \
   [ -z "$RECIPE_ADMIN_PASSWORD" ]; then
    log "ERROR: the staged administrator details are incomplete"
    exit 1
fi

sql() { psql "$DATABASE_URL" -v ON_ERROR_STOP=1 "$@"; }
# The marketplace folds usernames to lowercase at
# registration; the account row carries the folded form.
FOLDED=$(printf '%s' "$RECIPE_ADMIN_USER" | tr 'A-Z' 'a-z')
FOLDED_SQL=$(printf '%s' "$FOLDED" | sed "s/'/''/g")
role_of() {
    sql -tAc "SELECT role FROM accounts
              WHERE username = '$FOLDED_SQL'" 2>/dev/null || true
}

# --- the temporary application instance ----------------------
mkdir -p "$DATA/home"
chown www-data:www-data "$DATA/home" 2>/dev/null || true
log "starting the application briefly to create the account"
setpriv --reuid www-data --regid www-data --clear-groups \
    /usr/bin/env HOME="$DATA/home" \
    ONIONHOST_APP_DATA="$DATA" \
    "$APP" > /run/marketplace-first-boot-app.log 2>&1 &
APP_PID=$!
cleanup() {
    kill "$APP_PID" 2>/dev/null || true
    wait "$APP_PID" 2>/dev/null || true
}
trap cleanup EXIT

up=0
for i in $(seq 1 60); do
    if curl -s -o /dev/null --max-time 2 "$BASE/" 2>/dev/null; then
        up=1; break
    fi
    kill -0 "$APP_PID" 2>/dev/null || break
    sleep 1
done
if [ "$up" != 1 ]; then
    log "ERROR: the application did not answer on $BASE;"
    log "its output follows"
    tail -20 /run/marketplace-first-boot-app.log 2>/dev/null \
        | grep -v '^$' | sed 's/^/marketplace app: /' || true
    exit 1
fi

# --- registration (the application's own form) ---------------
# The marketplace's CSRF defence is a double-submit cookie:
# the form page sets a csrf cookie and embeds the same value;
# the POST must present both. Its cookies carry the Secure
# attribute in this profile - correct for the onion (browsers
# treat .onion as a secure context) - but it means a cookie
# JAR would withhold them from this loopback HTTP call, so
# the cookies are carried explicitly, header to header.
csrf_of() {
    # csrf_of <path> -> prints the csrf cookie value the GET
    # issued (identical to the form's hidden field).
    curl -s -D - -o /dev/null --max-time 5 "$BASE$1" \
        | tr -d '\r' \
        | sed -n 's/^[Ss]et-[Cc]ookie: csrf=\([^;]*\).*/\1/p' \
        | head -1
}

if [ -z "$(role_of)" ]; then
    CSRF=$(csrf_of /register)
    if [ -z "$CSRF" ]; then
        log "ERROR: the register page issued no CSRF cookie"
        exit 1
    fi
    # The password reaches curl on STDIN (--data-urlencode
    # "password@-"), never in argv (S6): a process list during
    # first boot must not disclose it. Tested encoding: curl
    # url-encodes the stdin bytes exactly as it would a value
    # given inline.
    printf '%s' "$RECIPE_ADMIN_PASSWORD" | \
    curl -s -o /dev/null --max-time 10 \
        -H "Cookie: csrf=$CSRF" \
        --data-urlencode "username=$RECIPE_ADMIN_USER" \
        --data-urlencode "password@-" \
        --data-urlencode "csrf=$CSRF" \
        "$BASE/register" || true
fi
if [ -z "$(role_of)" ]; then
    log "ERROR: registering the administrator failed - the" \
        "marketplace accepts usernames of 3-24 characters" \
        "(lowercase letters, numbers, _ or -) and passphrases" \
        "of at least 12 characters that are not common" \
        "passwords; re-run setup with a choice it accepts"
    exit 1
fi

# --- promotion (the one SQL write) ---------------------------
if ! sql -qc "UPDATE accounts SET role = 'admin'
              WHERE username = '$FOLDED_SQL'"; then
    log "ERROR: promoting the administrator failed"
    exit 1
fi
if [ "$(role_of)" != "admin" ]; then
    log "ERROR: the account exists but is not an administrator"
    exit 1
fi

# --- proof: log in as the new admin, load /moderation --------
CSRF=$(csrf_of /login)
if [ -z "$CSRF" ]; then
    log "ERROR: the login page issued no CSRF cookie"
    exit 1
fi
SESS=$(printf '%s' "$RECIPE_ADMIN_PASSWORD" | \
    curl -s -D - -o /dev/null --max-time 10 \
    -H "Cookie: csrf=$CSRF" \
    --data-urlencode "username=$RECIPE_ADMIN_USER" \
    --data-urlencode "password@-" \
    --data-urlencode "csrf=$CSRF" \
    "$BASE/login" \
    | tr -d '\r' \
    | sed -n 's/^[Ss]et-[Cc]ookie: __Host-session=\([^;]*\).*/\1/p' \
    | head -1)
if [ -z "$SESS" ]; then
    log "ERROR: logging in as the new administrator failed"
    exit 1
fi
CODE=$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 \
    -H "Cookie: __Host-session=$SESS" "$BASE/moderation")
if [ "$CODE" != "200" ]; then
    log "ERROR: the new administrator reached /moderation" \
        "with HTTP $CODE, not 200"
    exit 1
fi

cleanup
trap - EXIT
shred "$ENV_FILE"
date -u '+%Y-%m-%dT%H:%M:%SZ' > "$DONE"
log "administrator '$RECIPE_ADMIN_USER' is ready"
exit 0

#!/bin/sh
# Gitea recipe first boot (A23) - runs INSIDE the app container,
# started by the app init (native branch) BEFORE the Gitea
# server starts, the first time only (the init gates on the
# done marker this script leaves; onionhost-recipe's
# await-first-boot confirms the marker host-side).
#
# Its one job: create the owner's administrator account with
# Gitea's own CLI. The administrator details are the ones the
# owner chose in the setup wizard, staged root-only on the host
# and copied onto the app-data volume by onionhost-recipe at
# apply time (.recipe-admin.env, KEY=value lines). They are
# consumed and SHREDDED here: the plaintext password must not
# linger anywhere.
#
# The CLI runs as www-data (the server's user - Gitea refuses
# to run as root, and the files it creates must belong to the
# server) and before the server starts, because the CLI opens
# the database directly and initialises it on first use.
#
# Idempotent by design: if the account already exists (a retry
# after a partial first run), that is success, not an error.
set -u
DATA=/srv/appdata/native
ENV_FILE="$DATA/.recipe-admin.env"
DONE="$DATA/.first-boot-done"
APP="$DATA/app"
INI="$DATA/custom/conf/app.ini"

log() { echo "gitea first-boot: $*"; }

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

RECIPE_ADMIN_USER=""
RECIPE_ADMIN_PASSWORD=""
RECIPE_ADMIN_EMAIL=""
# Read KEY=value pairs as data - the file is never sourced
# (it is input, not code).
while IFS='=' read -r k v; do
    case "$k" in
        RECIPE_ADMIN_USER) RECIPE_ADMIN_USER=$v ;;
        RECIPE_ADMIN_PASSWORD) RECIPE_ADMIN_PASSWORD=$v ;;
        RECIPE_ADMIN_EMAIL) RECIPE_ADMIN_EMAIL=$v ;;
    esac
done < "$ENV_FILE"

if [ -z "$RECIPE_ADMIN_USER" ] || [ -z "$RECIPE_ADMIN_PASSWORD" ]; then
    log "ERROR: the staged administrator details are incomplete"
    exit 1
fi
if [ -z "$RECIPE_ADMIN_EMAIL" ]; then
    RECIPE_ADMIN_EMAIL="admin@localhost.invalid"
fi

# The database must be initialised (schema migrated) before
# the first account can be created: `admin user create` opens
# the store but does not migrate it (measured on the vendored
# 1.27.3 binary: against a fresh file it fails with "no such
# table: user"). `migrate` is Gitea's own initialiser and is
# idempotent - on a retried first boot it is a no-op.
MIG=$(setpriv --reuid www-data --regid www-data --clear-groups \
        /usr/bin/env HOME="$DATA/data/home" \
        "$APP" -w "$DATA" -c "$INI" migrate 2>&1) && MRC=0 || MRC=$?
if [ $MRC -ne 0 ]; then
    echo "$MIG" | grep -v '^$' | \
        sed 's/^/gitea first-boot: /' || true
    log "ERROR: initialising the database failed"
    exit 1
fi

OUT=$(setpriv --reuid www-data --regid www-data --clear-groups \
        /usr/bin/env HOME="$DATA/data/home" \
        "$APP" -w "$DATA" -c "$INI" admin user create \
        --username "$RECIPE_ADMIN_USER" \
        --password "$RECIPE_ADMIN_PASSWORD" \
        --email "$RECIPE_ADMIN_EMAIL" \
        --admin --must-change-password=false 2>&1) && RC=0 || RC=$?
echo "$OUT" | grep -v '^$' | sed 's/^/gitea first-boot: /' || true
if [ $RC -ne 0 ]; then
    case "$OUT" in
        *"already exists"*)
            log "the administrator already exists - treating" \
                "as done (a retried first boot)"
            ;;
        *)
            log "ERROR: creating the administrator failed"
            exit 1
            ;;
    esac
fi

shred "$ENV_FILE"
date -u '+%Y-%m-%dT%H:%M:%SZ' > "$DONE"
log "administrator '$RECIPE_ADMIN_USER' is ready"
exit 0

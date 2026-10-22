#!/bin/sh
# Marketplace recipe migrate step (A23) - runs INSIDE the app
# container, started by the app init (native branch) at EVERY
# container start, before the first-boot step and before the
# application starts. The app init refuses to start the
# application when this step fails.
#
# Its job: apply the marketplace's SQL migrations
# (native/migrations/*.sql, staged by onionhost-recipe from
# the recipe payload) to the instance's PostgreSQL database.
# The marketplace binary never migrates itself - its own
# deploy tooling (deploy/deploy-demo.sh) applies the same
# files the same way, and this step mirrors it exactly:
# files in glob (filename) order, each applied once, recorded
# in a schema_migrations ledger table, never downgraded.
# DATABASE_URL arrives in the environment, assembled by the
# init from the platform's per-install credentials record;
# the connecting role OWNS this database (the init created it
# that way), so the migrations' objects are the app's own.
set -u
DATA=/srv/appdata/native

log() { echo "marketplace migrate: $*"; }

# Per-install provisioning runs first (provision-secrets.sh,
# shipped beside this step): the application's key file and
# HT id file must exist before ANY start - the application
# refuses to mint them outside its Development profile. The
# step mints each file once and never touches an existing
# one. A failure here fails this step, so the application is
# not started against an unprovisioned instance.
if ! sh "$DATA/provision-secrets.sh"; then
    log "ERROR: per-install provisioning failed - the" \
        "application will not be started"
    exit 1
fi

if [ -z "${DATABASE_URL:-}" ]; then
    log "ERROR: DATABASE_URL is not set - the database leg" \
        "did not run, so there is nothing to migrate against"
    exit 1
fi

if ! psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -q -c \
    "CREATE TABLE IF NOT EXISTS schema_migrations (
         version TEXT PRIMARY KEY,
         applied_at TIMESTAMPTZ NOT NULL DEFAULT now())" \
     >/dev/null 2>&1; then
    log "ERROR: cannot reach the database or create the" \
        "migration ledger"
    exit 1
fi

for f in "$DATA"/migrations/*.sql; do
    [ -e "$f" ] || continue
    v=$(basename "$f")
    applied=$(psql "$DATABASE_URL" -tAc \
        "SELECT 1 FROM schema_migrations WHERE version = '$v'" \
        2>/dev/null || echo "")
    if [ "$applied" = "1" ]; then
        continue
    fi
    log "applying migration $v"
    if ! psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -q -f "$f" \
            >/dev/null; then
        log "ERROR: migration $v failed - it is NOT recorded," \
            "and the application will not be started against" \
            "a half-migrated schema"
        exit 1
    fi
    if ! psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -q -c \
        "INSERT INTO schema_migrations (version) VALUES ('$v')" \
            >/dev/null; then
        log "ERROR: migration $v applied but could not be" \
            "recorded"
        exit 1
    fi
done
log "migrations are current"
exit 0

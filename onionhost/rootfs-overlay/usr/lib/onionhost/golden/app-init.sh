#!/bin/sh
# OnionHost app container init (slice 6B) - PID 1 of the combined
# app sandbox. Copied to /etc/onionhost/app-init.sh by
# onionhost-generate-configs and mounted read-only into the app
# container, whose Quadlet Exec runs it.
#
# Shape (gate-round recommendation, POC-RESULTS "SLICE 6 GATE
# ROUND"): nginx + the app runtime + MariaDB are processes in ONE
# gVisor sandbox. Service sockets are sandbox-internal (/run/*.sock);
# only the edge socket (/run/onionhost/web/b1.sock, the name
# container A's http.sock symlink points at) is shared.
#
# Runtime selection: $ONIONHOST_RUNTIME (php | native), passed by
# the Quadlet unit from /etc/onionhost/app-runtime.env, which
# onionhost-generate-configs renders from the site-kind files.
#
#   php     MariaDB (datadir on the app-data volume) + PHP-FPM +
#           nginx/fastcgi. First boot initialises the datadir,
#           creates the application database + user from the
#           credentials in /etc/onionhost/app-db.env (mounted
#           read-only, readable only by this container's root), and
#           imports /srv/appdata/db-import.sql.gz if a restore or
#           a recipe staged one (deleted only once it imports
#           cleanly - a failed import is kept and retried at the
#           next start; see start_db). A database-less site
#           (ONIONHOST_APP_DB=none - a flat-file packaged recipe)
#           skips MariaDB entirely.
#   native  The owner-supplied program /srv/appdata/native/app,
#           started with ONIONHOST_APP_SOCKET=/run/app.sock and its
#           working directory (its data) at /srv/appdata/native;
#           nginx proxies the edge to that socket. A packaged
#           native recipe may ship a first-boot step (see below),
#           run once before the app starts. A native app that
#           serves TCP on the sandbox loopback instead of the
#           socket (its recipe declares manifest "native_serve")
#           is proxied the same way by the TCP nginx variant.
#           A native site whose database is PostgreSQL
#           (ONIONHOST_APP_DB=postgres - the recipe's manifest
#           declares db.engine "postgres") gets start_pg instead
#           of MariaDB: PostgreSQL runs in this sandbox too,
#           its datadir beside the trees at /srv/appdata/pgdb.
#
# MariaDB and the runtime start in the background; nginx runs in
# the foreground as the final exec, exactly the arrangement the
# gate round's combined sandbox carried through the whole SMF
# battery. Logs go to stderr -> the container log -> the journal.
set -u
CFG=/etc/onionhost
DATA=/srv/appdata
RUNTIME="${ONIONHOST_RUNTIME:-php}"

# /run is a fresh tmpfs (Quadlet Tmpfs=/run): the sandbox-internal
# service sockets are created here by their (non-root) services.
chmod 1777 /run 2>/dev/null || true
mkdir -p /tmp/client_body /tmp/proxy /tmp/fastcgi /tmp/uwsgi \
         /tmp/scgi /tmp/php-sessions
chown www-data:www-data /tmp/php-sessions 2>/dev/null || true

# Owner/app file sharing, normalised at every start. The owner
# drops application files into the app-data trees from their
# desktop (modes arbitrary); the application (running as
# www-data) must be able to write its uploads, cache and config;
# and files the application creates must stay manageable by the
# owner. The arrangement: content is owned by www-data, the
# owner's group (ONIONHOST_OWNER_GID, provisioned) holds group
# rights everywhere, directories are setgid so new files inherit
# the group, and the unit's UMask=0000 keeps new files
# group-writable. Without this pass a forum installer cannot
# even write its own config file over the copy the owner made.
normalize_tree() {
    dir=$1
    [ -d "$dir" ] || return 0
    [ -n "${ONIONHOST_OWNER_GID:-}" ] || return 0
    find "$dir" -type d \
        -exec chown "www-data:$ONIONHOST_OWNER_GID" {} + \
        -exec chmod 2775 {} + 2>/dev/null
    find "$dir" -type f \
        -exec chown "www-data:$ONIONHOST_OWNER_GID" {} + \
        -exec chmod 0664 {} + 2>/dev/null
}

# Recipe exceptions to the uniform pass (A23; slice 6B flag 1).
# A packaged recipe may ship /etc/onionhost/normalize-exceptions
# naming files whose modes must NOT be flattened - one per line:
#   <octal mode> <path relative to the app-data volume>
# (e.g. the SMF recipe keeps its credentials-bearing Settings.php
# at 0660). Paths are confined to the volume; anything absolute
# or escaping it is ignored. Applied after every normalise pass.
apply_normalize_exceptions() {
    exc="$CFG/normalize-exceptions"
    [ -f "$exc" ] || return 0
    while read -r mode path; do
        case "$mode" in ''|\#*) continue ;; esac
        case "$path" in /*|*..*)
            echo "app-init: ignoring unsafe normalize exception:" \
                 "$path"
            continue ;;
        esac
        case "$mode" in *[!0-7]*)
            echo "app-init: ignoring bad mode in normalize" \
                 "exceptions: $mode"
            continue ;;
        esac
        if [ -e "$DATA/$path" ]; then
            chmod "$mode" "$DATA/$path" 2>/dev/null || true
        fi
    done < "$exc"
}

# MariaDB root access (D2, rig battery 2026-10-14): root's
# authentication is a per-install PASSWORD (DB_ROOT_PASSWORD in
# the credentials file, generated by onionhost-app-provision),
# never the unix_socket plugin. Socket auth judges the
# connecting process by its kernel peer credentials, and under
# gVisor those are not the credentials MariaDB expects - every
# root call in this function failed with ERROR 1698 on real
# hardware while passing in venues whose socket layer is the
# host kernel's. A password judges only what the client knows,
# which is the same in every venue. db_root runs a MariaDB
# client as root with that password (via MYSQL_PWD, so the
# password never appears in a process list).
DB_ROOT_PASS=""
db_root() {
    if [ -n "$DB_ROOT_PASS" ]; then
        MYSQL_PWD="$DB_ROOT_PASS" mariadb -u root "$@"
    else
        mariadb -u root "$@"
    fi
}

start_db() {
    mkdir -p "$DATA/db"
    chown mysql:mysql "$DATA/db" 2>/dev/null || true
    if [ ! -d "$DATA/db/mysql" ]; then
        echo "app-init: first boot - initialising MariaDB datadir"
        # "normal" root authentication: root starts with an
        # EMPTY native password (not socket auth - see above),
        # and the bridge below replaces it with this install's
        # generated DB_ROOT_PASSWORD before anything else runs.
        mariadb-install-db --defaults-file="$CFG/my-app.cnf" \
            --auth-root-authentication-method=normal \
            --skip-test-db || return 1
    fi
    echo "app-init: starting MariaDB"
    # The socket lives at the Debian default path
    # (/run/mysqld/mysqld.sock) so un-configured clients - the
    # mariadb CLI below, PHP's mysqli/PDO defaults - find it
    # without help. (A non-default path here once made every
    # provisioning call silently miss the server; see the
    # slice 6B build log.) The directory is on the /run tmpfs,
    # so it is re-created at every boot.
    mkdir -p /run/mysqld
    chown mysql:mysql /run/mysqld 2>/dev/null || true
    mariadbd --defaults-file="$CFG/my-app.cnf" &
    for i in $(seq 1 60); do
        [ -S /run/mysqld/mysqld.sock ] && break
        sleep 1
    done
    [ -S /run/mysqld/mysqld.sock ] || { echo "app-init: MariaDB did not start"; return 1; }

    # Application database + user, and any staged import.
    # The credentials file is the contract: DB_NAME / DB_USER /
    # DB_PASSWORD / DB_ROOT_PASSWORD, one KEY=value per line.
    if [ -f "$CFG/app-db.env" ]; then
        DB_NAME=$(sed -n 's/^DB_NAME=//p' "$CFG/app-db.env" | head -1)
        DB_USER=$(sed -n 's/^DB_USER=//p' "$CFG/app-db.env" | head -1)
        DB_PASS=$(sed -n 's/^DB_PASSWORD=//p' "$CFG/app-db.env" | head -1)
        DB_ROOT_PASS=$(sed -n 's/^DB_ROOT_PASSWORD=//p' "$CFG/app-db.env" | head -1)
        DB_NAME=${DB_NAME:-onionhost_app}
        # Root-auth bridge: if the generated password does not
        # authenticate yet, the datadir is fresh (root still
        # holds install-db's empty password) or pre-dates the
        # password (socket-auth root) - try one passwordless
        # login and, if it answers, set the generated password
        # so every later call and boot uses it. If neither
        # works, provisioning below fails loudly, by name.
        if [ -n "$DB_ROOT_PASS" ] && \
           ! MYSQL_PWD="$DB_ROOT_PASS" mariadb -u root \
               -e 'SELECT 1' >/dev/null 2>&1; then
            DB_ROOT_PASS_SQL=$(printf '%s' "$DB_ROOT_PASS" | sed "s/'/''/g")
            if mariadb -u root -e "ALTER USER 'root'@'localhost' IDENTIFIED BY '$DB_ROOT_PASS_SQL';" >/dev/null 2>&1; then
                echo "app-init: MariaDB root password set from" \
                     "the provisioning record"
            else
                echo "app-init: ERROR: cannot authenticate as" \
                     "MariaDB root (password not yet set, and a" \
                     "passwordless login was refused); database" \
                     "provisioning will fail"
            fi
        fi
        if [ -n "$DB_USER" ] && [ -n "$DB_PASS" ]; then
            # Escape single quotes in the password for SQL.
            DB_PASS_SQL=$(printf '%s' "$DB_PASS" | sed "s/'/''/g")
            if db_root <<SQL
CREATE DATABASE IF NOT EXISTS \`$DB_NAME\`;
CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASS_SQL';
ALTER USER '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASS_SQL';
GRANT ALL PRIVILEGES ON \`$DB_NAME\`.* TO '$DB_USER'@'localhost';
FLUSH PRIVILEGES;
SQL
            then
                echo "app-init: application database '$DB_NAME' ready"
            else
                echo "app-init: ERROR: database provisioning failed;" \
                     "the application will not be able to connect"
            fi
        fi
        if [ -f "$DATA/db-import.sql.gz" ]; then
            # A staged import (a restore's dump, a recipe's
            # seed) is applied EXACTLY ONCE, and only success
            # deletes it (D2: the first version of this branch
            # deleted the seed and logged "import done" even
            # when every import command had failed, silently
            # losing a forum's whole schema + admin seed on
            # first boot). Any failure is loud, the staged file
            # is KEPT, and the next container start retries -
            # the drop + recreate makes a retry idempotent.
            echo "app-init: importing staged database import"
            imp_tmp=/tmp/.db-import.sql
            rm -f "$imp_tmp"
            if ! gunzip -c "$DATA/db-import.sql.gz" > "$imp_tmp"; then
                echo "app-init: ERROR: the staged database import" \
                     "is not readable gzip; it is KEPT at" \
                     "$DATA/db-import.sql.gz and the database" \
                     "was NOT imported"
            elif ! db_root -e "DROP DATABASE IF EXISTS \`$DB_NAME\`; CREATE DATABASE \`$DB_NAME\`;"; then
                echo "app-init: ERROR: could not prepare database" \
                     "'$DB_NAME' for import; the staged import is" \
                     "KEPT and will be retried at the next start"
                rm -f "$imp_tmp"
            elif db_root "$DB_NAME" < "$imp_tmp"; then
                rm -f "$DATA/db-import.sql.gz" "$imp_tmp"
                echo "app-init: database import done"
            else
                echo "app-init: ERROR: database import FAILED;" \
                     "the staged import is KEPT at" \
                     "$DATA/db-import.sql.gz and will be retried" \
                     "at the next start"
                rm -f "$imp_tmp"
            fi
        fi
    else
        echo "app-init: WARNING: $CFG/app-db.env not readable; " \
             "application database not provisioned"
    fi
}

# PostgreSQL (db=postgres - a native recipe whose manifest
# declares the engine; A23 recipe 5). The second database the
# app slot can run, held to the same contract as start_db:
# per-install credentials from /etc/onionhost/app-db.env, the
# superuser (the `postgres` role) authenticating BY PASSWORD
# (DB_ROOT_PASSWORD) over the sandbox loopback - peer/socket
# credentials are the D2 trap under gVisor for this engine
# too - the application role + database created idempotently
# at every start, and a staged import applied exactly once
# (deleted only on success; kept and retried otherwise). The
# datadir lives BESIDE the app trees (appdata/pgdb), never
# inside one: the normaliser flattens the trees at every
# start, and PostgreSQL refuses a datadir it does not own
# alone at mode 0700. The application's DATABASE_URL is
# assembled here - the one place credentials are combined -
# and exported for the recipe's boot steps and the app.
PGDATA_DIR="$DATA/pgdb"
PGSOCK_DIR=/run/pgsql
pg_super() {
    # pg_super <db> [psql args...]: a psql call as the
    # superuser, password via PGPASSWORD (never argv).
    _pg_db=$1; shift
    PGPASSWORD="$DB_ROOT_PASS" psql -h 127.0.0.1 -p 5432 \
        -U postgres -d "$_pg_db" -v ON_ERROR_STOP=1 "$@"
}
start_pg() {
    if [ ! -f "$CFG/app-db.env" ]; then
        echo "app-init: WARNING: $CFG/app-db.env not readable; " \
             "PostgreSQL not started"
        return 1
    fi
    DB_NAME=$(sed -n 's/^DB_NAME=//p' "$CFG/app-db.env" | head -1)
    DB_USER=$(sed -n 's/^DB_USER=//p' "$CFG/app-db.env" | head -1)
    DB_PASS=$(sed -n 's/^DB_PASSWORD=//p' "$CFG/app-db.env" | head -1)
    DB_ROOT_PASS=$(sed -n 's/^DB_ROOT_PASSWORD=//p' \
        "$CFG/app-db.env" | head -1)
    DB_NAME=${DB_NAME:-onionhost_app}
    if [ -z "$DB_USER" ] || [ -z "$DB_PASS" ] \
       || [ -z "$DB_ROOT_PASS" ]; then
        echo "app-init: ERROR: the credentials record is" \
             "incomplete; PostgreSQL not started"
        return 1
    fi
    case "$DB_NAME$DB_USER" in
        *[!a-z0-9_]*)
            echo "app-init: ERROR: database name/user in the" \
                 "credentials record are not plain identifiers;" \
                 "PostgreSQL not started"
            return 1 ;;
    esac
    PG_BIN=$(echo /usr/lib/postgresql/*/bin)
    PG_BIN=${PG_BIN%% *}
    if [ ! -x "$PG_BIN/initdb" ]; then
        echo "app-init: ERROR: no PostgreSQL server in the image"
        return 1
    fi
    mkdir -p "$PGSOCK_DIR"
    chown postgres:postgres "$PGSOCK_DIR" 2>/dev/null || true
    chmod 2775 "$PGSOCK_DIR" 2>/dev/null || true
    # The server's log belongs to postgres from the start:
    # pg_ctl (running as postgres) appends to it, and a
    # root-owned file would refuse the server its own log.
    touch /run/postgresql.log 2>/dev/null || true
    chown postgres:postgres /run/postgresql.log \
        2>/dev/null || true
    mkdir -p "$PGDATA_DIR"
    chown postgres:postgres "$PGDATA_DIR" 2>/dev/null || true
    chmod 0700 "$PGDATA_DIR"
    if [ ! -s "$PGDATA_DIR/PG_VERSION" ]; then
        echo "app-init: first boot - initialising PostgreSQL datadir"
        # The superuser's password comes from the credentials
        # record, via a 0600 pwfile initdb reads once. The file
        # must belong to the postgres user: initdb runs AS
        # postgres and a root-owned 0600 file is unreadable to
        # it (measured in the marketplace recipe venue: initdb
        # "could not open file ... Permission denied").
        _pwf=/run/.pg-superuser.pw
        ( umask 077; printf '%s' "$DB_ROOT_PASS" > "$_pwf" )
        chown postgres:postgres "$_pwf" 2>/dev/null || true
        chmod 0600 "$_pwf" 2>/dev/null || true
        if ! setpriv --reuid postgres --regid postgres \
                --clear-groups "$PG_BIN/initdb" -D "$PGDATA_DIR" \
                -U postgres --auth=scram-sha-256 \
                --pwfile="$_pwf" >>/run/postgresql.log 2>&1; then
            rm -f "$_pwf"
            echo "app-init: ERROR: PostgreSQL initialisation" \
                 "failed; see /run/postgresql.log"
            return 1
        fi
        rm -f "$_pwf"
        {
            echo "# OnionHost (written once at initialisation;"
            echo "# the app slot's PostgreSQL contract)"
            echo "listen_addresses = '127.0.0.1'"
            echo "port = 5432"
            echo "unix_socket_directories = '$PGSOCK_DIR'"
            echo "shared_buffers = 128MB"
            echo "max_connections = 40"
            echo "# The sandbox's /dev/shm is small; file-backed"
            echo "# dynamic shared memory lives in the datadir."
            echo "dynamic_shared_memory_type = 'mmap'"
        } >> "$PGDATA_DIR/postgresql.conf"
        chown postgres:postgres "$PGDATA_DIR/postgresql.conf"
    fi
    echo "app-init: starting PostgreSQL"
    # A previous postmaster may still be shutting down when a
    # stack restart reaches this point (a smart shutdown waits
    # for the application's pooled connections to drain), or -
    # where a restart does not tear the sandbox down - may
    # still be running outright. pg_ctl start refuses on the
    # spot while postmaster.pid names a live process ("lock
    # file already exists"), and treating the database as dead
    # on that word fails an update's health check for a
    # database that is merely stopping (measured in the
    # marketplace recipe venue: the oh.2 update's restart raced
    # the oh.1 postmaster's shutdown and rolled back). So:
    # wait for a live postmaster to exit (bounded); if it is
    # still alive after the wait it IS this datadir's server -
    # adopt it and skip the start. A pid file naming a dead or
    # zombie process is stale: remove it and start normally.
    _pg_running=""
    _oldpid=""
    if [ -f "$PGDATA_DIR/postmaster.pid" ]; then
        _oldpid=$(head -1 "$PGDATA_DIR/postmaster.pid" \
            2>/dev/null || true)
        case "$_oldpid" in *[!0-9]*|"") _oldpid="" ;; esac
    fi
    if [ -n "$_oldpid" ]; then
        _state=$(cut -d' ' -f3 "/proc/$_oldpid/stat" \
            2>/dev/null || true)
        if [ "$_state" = "Z" ] \
           || ! kill -0 "$_oldpid" 2>/dev/null; then
            rm -f "$PGDATA_DIR/postmaster.pid"
            _oldpid=""
        fi
    fi
    if [ -n "$_oldpid" ]; then
        _n=0
        while [ "$_n" -lt 30 ] \
              && kill -0 "$_oldpid" 2>/dev/null; do
            sleep 1; _n=$((_n + 1))
        done
        if kill -0 "$_oldpid" 2>/dev/null; then
            echo "app-init: PostgreSQL already running" \
                 "(pid $_oldpid); adopting it"
            _pg_running=1
        else
            rm -f "$PGDATA_DIR/postmaster.pid"
        fi
    fi
    if [ -z "$_pg_running" ]; then
        if ! setpriv --reuid postgres --regid postgres \
                --clear-groups "$PG_BIN/pg_ctl" -D "$PGDATA_DIR" \
                -l /run/postgresql.log -w -t 60 start \
                >>/run/postgresql.log 2>&1; then
            echo "app-init: ERROR: PostgreSQL did not start;" \
                 "see /run/postgresql.log"
            return 1
        fi
    fi
    # Application role + database, idempotently (the bridge
    # pattern from start_db: the password is re-asserted at
    # every start, so a restored credentials record and the
    # database can never drift apart).
    _role=$(pg_super postgres -tAc \
        "SELECT 1 FROM pg_roles WHERE rolname = '$DB_USER'" \
        2>/dev/null || true)
    if [ "$_role" = "1" ]; then
        pg_super postgres -qc \
            "ALTER ROLE \"$DB_USER\" WITH LOGIN PASSWORD '$DB_PASS'" \
            >/dev/null 2>&1 \
            || echo "app-init: ERROR: could not re-assert the" \
                    "application role's password"
    else
        pg_super postgres -qc \
            "CREATE ROLE \"$DB_USER\" LOGIN PASSWORD '$DB_PASS'" \
            >/dev/null 2>&1 \
            || echo "app-init: ERROR: could not create the" \
                    "application database role"
    fi
    _db=$(pg_super postgres -tAc \
        "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" \
        2>/dev/null || true)
    if [ "$_db" != "1" ]; then
        pg_super postgres -qc \
            "CREATE DATABASE \"$DB_NAME\" OWNER \"$DB_USER\"" \
            >/dev/null 2>&1 \
            || echo "app-init: ERROR: could not create the" \
                    "application database"
    fi
    echo "app-init: application database '$DB_NAME' ready (PostgreSQL)"
    if [ -f "$DATA/db-import.sql.gz" ]; then
        # The staged-import contract, exactly as start_db
        # keeps it: applied once, deleted ONLY on success,
        # kept and retried on any failure, and a retry starts
        # from a dropped + recreated database so it cannot
        # half-apply twice.
        echo "app-init: importing staged database import (PostgreSQL)"
        imp_tmp=/tmp/.db-import-pg.sql
        rm -f "$imp_tmp"
        if ! gunzip -c "$DATA/db-import.sql.gz" > "$imp_tmp"; then
            echo "app-init: ERROR: the staged database import" \
                 "is not readable gzip; it is KEPT at" \
                 "$DATA/db-import.sql.gz and the database" \
                 "was NOT imported"
        elif ! pg_super postgres -qc \
                "DROP DATABASE IF EXISTS \"$DB_NAME\" WITH (FORCE)" \
                >/dev/null 2>&1 \
             || ! pg_super postgres -qc \
                "CREATE DATABASE \"$DB_NAME\" OWNER \"$DB_USER\"" \
                >/dev/null 2>&1; then
            echo "app-init: ERROR: could not prepare database" \
                 "'$DB_NAME' for import; the staged import is" \
                 "KEPT and will be retried at the next start"
            rm -f "$imp_tmp"
        elif PGPASSWORD="$DB_ROOT_PASS" psql -h 127.0.0.1 \
                -p 5432 -U postgres -d "$DB_NAME" \
                -v ON_ERROR_STOP=1 -q -f "$imp_tmp" \
                >>/run/postgresql.log 2>&1; then
            rm -f "$DATA/db-import.sql.gz" "$imp_tmp"
            echo "app-init: database import done"
        else
            echo "app-init: ERROR: database import FAILED;" \
                 "the staged import is KEPT at" \
                 "$DATA/db-import.sql.gz and will be retried" \
                 "at the next start"
            rm -f "$imp_tmp"
        fi
    fi
    DATABASE_URL="postgres://$DB_USER:$DB_PASS@127.0.0.1:5432/$DB_NAME"
    export DATABASE_URL
    return 0
}

case "$RUNTIME" in
    php)
        normalize_tree "$DATA/www"
        apply_normalize_exceptions
        if [ "${ONIONHOST_APP_DB:-required}" = "none" ]; then
            echo "app-init: this site has no application database;" \
                 "MariaDB not started"
        else
            start_db || echo "app-init: database problems; continuing"
        fi
        PHP_FPM=$(command -v php-fpm8.4 || command -v php-fpm || true)
        if [ -n "$PHP_FPM" ]; then
            echo "app-init: starting PHP-FPM ($PHP_FPM)"
            # -R permits a pool to run as root. The rendered pool
            # always names www-data, so this never engages in
            # production; it lets the same rendered config boot in
            # the nested-sandbox acceptance venue, where www-data
            # is aliased to uid 0 (setuid is EPERM there) and FPM
            # would otherwise refuse the pool as "root".
            "$PHP_FPM" -R -y "$CFG/php-fpm-app.conf" &
            for i in $(seq 1 20); do
                [ -S /run/php-fpm.sock ] && break
                sleep 1
            done
        else
            echo "app-init: ERROR: no php-fpm binary in the image"
        fi
        ;;
    native)
        normalize_tree "$DATA/native"
        apply_normalize_exceptions
        chmod 0775 "$DATA/native/app" 2>/dev/null || true
        # A native site may carry a database too: db=postgres
        # (the recipe's manifest declares the engine - A23
        # recipe 5). It starts before everything else in this
        # branch: the recipe's boot steps and the app all
        # connect to it.
        if [ "${ONIONHOST_APP_DB:-none}" = "postgres" ]; then
            start_pg || echo "app-init: database problems; continuing"
        fi
        # Per-install environment (A23 recipe 5): a native app
        # configured ONLY through environment variables (no
        # config file for a renderer to write) carries
        # native/app.env, rendered by onionhost-recipe from the
        # recipe's native_config template on first install -
        # the instance's display name, its data paths, the
        # application's own tuning values. Database credentials
        # are NEVER in it: DATABASE_URL is exported by start_pg
        # from the credentials record. The file is parsed as
        # DATA, line by line, never evaluated: values are taken
        # literally, and platform-managed names cannot be set
        # from it (a name the platform owns always wins).
        if [ -f "$DATA/native/app.env" ]; then
            while IFS= read -r _line || [ -n "$_line" ]; do
                case "$_line" in
                    ''|'#'*) continue ;;
                esac
                _key=${_line%%=*}
                case "$_key" in
                    ONIONHOST_*|PATH|HOME|DATABASE_URL|IFS|ENV|\
                    BASH_ENV|LD_*|SHELLOPTS)
                        echo "app-init: app.env: ignoring" \
                             "platform-managed name $_key"
                        continue ;;
                    *[!A-Za-z0-9_]*|'')
                        echo "app-init: app.env: ignoring a" \
                             "malformed line"
                        continue ;;
                esac
                export "$_line"
            done < "$DATA/native/app.env"
        fi
        # Recipe boot steps (A23). Two, in order:
        #   migrate.sh - present when the application's schema
        #     is NOT self-managing (the app neither migrates at
        #     start nor ships a CLI for it). Runs at EVERY start,
        #     before the app; the script is marker-idempotent
        #     (it records what it applied). A failure is FATAL
        #     to this start - unlike first boot below, there is
        #     no honest "start anyway": the app against an
        #     unmigrated schema corrupts or crashes, so the app
        #     is not started, nginx answers 502, and a bad
        #     update's health check fails and rolls back.
        #   first-boot.sh - a packaged native app whose
        #     administrator can only be created by the app
        #     itself ships this beside the binary. It runs ONCE
        #     (its done marker gates it), BEFORE the app starts,
        #     with the staged administrator env the applier left
        #     on the volume (.recipe-admin.env), which the
        #     script consumes and shreds. A failure is logged
        #     loudly and the app still starts:
        #     onionhost-publish's completion check is what
        #     refuses to call the site live without its admin.
        _steps_ok=1
        if [ -f "$DATA/native/migrate.sh" ]; then
            echo "app-init: running the app recipe's migrate step"
            ( cd "$DATA/native" && \
              sh "$DATA/native/migrate.sh" ) \
                || { echo "app-init: ERROR: migrate step failed;" \
                          "the application will NOT be started"
                     _steps_ok=0; }
        fi
        if [ "$_steps_ok" = 1 ] && \
           [ -f "$DATA/native/first-boot.sh" ] && \
           [ ! -f "$DATA/native/.first-boot-done" ]; then
            echo "app-init: running the app recipe's first-boot step"
            ( cd "$DATA/native" && \
              sh "$DATA/native/first-boot.sh" ) \
                || echo "app-init: ERROR: first-boot step failed;" \
                        "the app may have no administrator yet"
        fi
        if [ "$_steps_ok" = 1 ] && [ -x "$DATA/native/app" ]; then
            echo "app-init: starting native app $DATA/native/app"
            # The native program runs as www-data, like the PHP
            # runtime - never as the sandbox's root. setpriv, not
            # runuser: pure syscalls, no PAM session machinery
            # (which aborts outright under gVisor - measured in
            # the slice 6B acceptance; a sealed container has no
            # login infrastructure for PAM to talk to anyway).
            # The app also gets a HOME on its own data volume:
            # the init's HOME is root's, and an app running as
            # www-data that writes under $HOME dies on it
            # (measured with the Gitea recipe: its startup SSH
            # key sync FATALs on mkdir /root/.ssh). The home dir
            # is app state, so it lives on the volume with the
            # rest (and rides the same backups).
            mkdir -p "$DATA/native/home"
            chown www-data:www-data "$DATA/native/home" \
                2>/dev/null || true
            cd "$DATA/native" && \
                setpriv --reuid www-data --regid www-data \
                --clear-groups /usr/bin/env \
                HOME="$DATA/native/home" \
                ONIONHOST_APP_SOCKET=/run/app.sock \
                ONIONHOST_APP_DATA="$DATA/native" \
                "$DATA/native/app" &
            cd /
            # Readiness: the app answers on its unix socket
            # (the platform contract), or - a recipe that
            # declares native_serve tcp - on the BIND_ADDR its
            # app.env carries. Either way this only bounds the
            # wait before nginx starts; the edge answers 502
            # until the app is truly up.
            for i in $(seq 1 30); do
                [ -S /run/app.sock ] && break
                case "${BIND_ADDR:-}" in
                    *:*)
                        curl -s -o /dev/null --max-time 2 \
                            "http://$BIND_ADDR/" 2>/dev/null \
                            && break
                        ;;
                esac
                sleep 1
            done
        elif [ "$_steps_ok" = 1 ]; then
            echo "app-init: ERROR: no executable at $DATA/native/app"
        fi
        ;;
    *)
        echo "app-init: ERROR: unknown runtime '$RUNTIME'"
        ;;
esac

# A SIGKILLed predecessor can leave a stale edge socket that blocks
# the bind (gate-round operational finding); the name is ours alone.
rm -f /run/onionhost/web/b1.sock
# Edge splice (FIONREAD fix; the full story is in the app nginx
# templates): nginx must not read visitor requests from the
# host-backed edge socket itself. The gVisor Sentry answers
# ioctl(FIONREAD) with ENOTTY for host-file-backed endpoints, and
# nginx treats that answer as a fatal connection error - in its
# header read when a flight exactly fills the header buffer, and
# in its request-body reader on ANY body that arrives in more than
# one flight, because that reader caps its final read at exactly
# the remaining Content-Length (measured on a real install:
# one-shot requests of any size passed, the same bytes dripped in
# 500-byte writes all died). socat owns the edge socket instead:
# it copies bytes with plain reads and writes, which the Sentry
# serves correctly at any size and pacing, and hands each
# connection to nginx on the sandbox loopback (127.0.0.1:18080,
# the platform edge port), whose Sentry-native TCP endpoints
# implement FIONREAD properly. Tor, the socket name and the
# rotation story are unchanged; socat is the only process that
# touches b1.sock.
echo "app-init: starting edge splice (edge socket -> nginx loopback)"
socat UNIX-LISTEN:/run/onionhost/web/b1.sock,fork \
      TCP:127.0.0.1:18080 &
echo "app-init: starting nginx (loopback, runtime=$RUNTIME)"
exec nginx -c "$CFG/nginx-app.conf" -g "daemon off;"

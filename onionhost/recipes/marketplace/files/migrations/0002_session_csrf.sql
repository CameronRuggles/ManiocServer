-- Stage 1 addition: per-session CSRF secrets, keyed by the session token hash.
CREATE TABLE session_csrf (
    token_hash  BYTEA PRIMARY KEY,
    csrf_secret TEXT NOT NULL
);

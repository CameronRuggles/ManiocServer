-- Hidden Trades H1 (Alpha build spec §13): signed listing terms v2.
--
-- NUMBERING NOTE: the Alpha spec's §13 names this migration
-- 0014_hidden_trades.sql, but 0014 (verification fixes) and 0015
-- (disclosure message link) already exist in this tree. Per the
-- owner's build instruction the H1 migration takes the next free
-- number, 0016; existing migrations are never renamed. Later Hidden
-- Trades stages add their tables in their own later migrations.
--
-- One row per signed terms version of a listing (spec §4): the
-- exact statement bytes and detached signature the seller's helper
-- produced, verified against the seller's pinned key at submission
-- and pinned here. A superseded version stays readable for 12
-- months after supersede (§15.7) -- `superseded_at` marks it; the
-- retention job that eventually deletes old rows is not part of H1.

CREATE TABLE listing_terms_statements (
    id               BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    listing_id       BIGINT NOT NULL REFERENCES listings (id),
    version          BIGINT NOT NULL,
    statement        TEXT NOT NULL,
    signature        TEXT NOT NULL,
    statement_sha256 TEXT NOT NULL,
    terms_sha256     TEXT NOT NULL,
    transit_risk     TEXT NOT NULL CHECK (transit_risk IN ('seller', 'buyer')),
    remedy_cap_pct   INTEGER NOT NULL CHECK (remedy_cap_pct BETWEEN 0 AND 100),
    payment_timing   TEXT NOT NULL CHECK (payment_timing IN ('prepay', 'on_ship', 'on_receipt')),
    superseded_at    TIMESTAMPTZ,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (listing_id, version)
);

CREATE INDEX listing_terms_current_idx
    ON listing_terms_statements (listing_id)
    WHERE superseded_at IS NULL;

-- Initial schema (spec §16 + amendments). Stage 0: structure only.
-- Public IDs are random 128-bit values with a type prefix (Q15 patterns);
-- internal keys never appear in URLs. No table stores spending keys,
-- messaging private keys, plaintext messages, plaintext shipping details,
-- balances, raw session tokens, or txids past finality.

CREATE TABLE accounts (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    public_id   TEXT NOT NULL UNIQUE,              -- acct_<32 hex>
    username    TEXT NOT NULL UNIQUE,              -- stored case-folded
    password_hash TEXT NOT NULL,                   -- Argon2id
    role        TEXT NOT NULL DEFAULT 'buyer',     -- buyer | seller | moderator | admin
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    recovered_at TIMESTAMPTZ
);

CREATE TABLE sessions (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    token_hash  BYTEA NOT NULL UNIQUE,             -- SHA-256 of the token only
    account_id  BIGINT NOT NULL REFERENCES accounts(id),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at  TIMESTAMPTZ NOT NULL,
    revoked_at  TIMESTAMPTZ
);

CREATE TABLE recovery_codes (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    account_id  BIGINT NOT NULL REFERENCES accounts(id),
    code_hash   BYTEA NOT NULL,                    -- SHA-256
    consumed_at TIMESTAMPTZ
);

CREATE TABLE identity_keys (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    account_id  BIGINT NOT NULL REFERENCES accounts(id),
    certificate BYTEA NOT NULL,
    fingerprint TEXT NOT NULL UNIQUE,              -- uppercase hex
    version     INT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'current',   -- current | retired
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    retired_at  TIMESTAMPTZ
);

CREATE TABLE key_rotations (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    account_id  BIGINT NOT NULL REFERENCES accounts(id),
    old_fpr     TEXT NOT NULL,
    new_fpr     TEXT NOT NULL,
    statement   BYTEA NOT NULL,
    sig_old     BYTEA,
    sig_new     BYTEA,
    certified   BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE listings (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    public_id   TEXT NOT NULL UNIQUE,
    seller_id   BIGINT NOT NULL REFERENCES accounts(id),
    title       TEXT NOT NULL,
    description TEXT NOT NULL,
    price_atomic BIGINT NOT NULL CHECK (price_atomic > 0),
    pricing_module TEXT NOT NULL,
    destination_module TEXT NOT NULL,
    auto_invoice BOOLEAN NOT NULL DEFAULT FALSE,
    status      TEXT NOT NULL DEFAULT 'draft',     -- draft | published | paused | removed
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE listing_media (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    listing_id  BIGINT NOT NULL REFERENCES listings(id),
    sanitized_ref TEXT NOT NULL,                   -- media-worker output only
    width       INT NOT NULL,
    height      INT NOT NULL
);

CREATE TABLE orders (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    public_id   TEXT NOT NULL UNIQUE,              -- ord_<32 hex>
    buyer_id    BIGINT NOT NULL REFERENCES accounts(id),
    seller_id   BIGINT NOT NULL REFERENCES accounts(id),
    listing_id  BIGINT NOT NULL REFERENCES listings(id),
    state       TEXT NOT NULL DEFAULT 'Requested',
    settlement  TEXT NOT NULL DEFAULT 'direct',    -- Q9: always 'direct' in v2
    seller_fpr_pinned TEXT NOT NULL,
    terms_bytes BYTEA NOT NULL,                    -- stored exactly, never regenerated
    terms_sha256 TEXT NOT NULL,
    total_atomic BIGINT NOT NULL CHECK (total_atomic > 0),
    module_pins JSONB NOT NULL,                    -- module id+version per slot
    evidence_level TEXT NOT NULL DEFAULT 'None',
    idempotency_key TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (buyer_id, idempotency_key)
);

CREATE TABLE address_pools (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    public_id   TEXT NOT NULL UNIQUE,              -- pool_<32 hex>
    seller_id   BIGINT NOT NULL REFERENCES accounts(id),
    statement   BYTEA NOT NULL,
    signature   BYTEA NOT NULL,
    signing_fpr TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'pending',   -- pending | active | exhausted | retired
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- One global destinations table carries the uniqueness guarantee for every
-- address the system ever hands out (§3 invariant 8).
CREATE TABLE destinations (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    address     TEXT NOT NULL UNIQUE,
    seller_id   BIGINT NOT NULL REFERENCES accounts(id),
    source      TEXT NOT NULL,                     -- pool | invoice
    pool_id     BIGINT REFERENCES address_pools(id),
    pool_index  INT,
    invoice_id  BIGINT,                            -- FK added after invoices
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (pool_id, pool_index)
);

CREATE TABLE invoices (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    public_id   TEXT NOT NULL UNIQUE,              -- inv_<32 hex>
    order_id    BIGINT NOT NULL REFERENCES orders(id),
    state       TEXT NOT NULL DEFAULT 'Issued',    -- Issued|Settled|Expired|Superseded|Cancelled
    destination_id BIGINT NOT NULL REFERENCES destinations(id),
    amount_atomic BIGINT NOT NULL CHECK (amount_atomic > 0),
    expires_at  TIMESTAMPTZ NOT NULL,
    statement   BYTEA NOT NULL,
    signature   BYTEA,
    module_pin  TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE destinations
    ADD CONSTRAINT destinations_invoice_fk FOREIGN KEY (invoice_id) REFERENCES invoices(id);
-- At most one Issued invoice per order (§9).
CREATE UNIQUE INDEX one_issued_invoice_per_order
    ON invoices (order_id) WHERE state = 'Issued';
CREATE UNIQUE INDEX destinations_one_invoice
    ON destinations (invoice_id) WHERE invoice_id IS NOT NULL;

CREATE TABLE payment_evidence (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    invoice_id  BIGINT NOT NULL REFERENCES invoices(id),
    claim_kind  TEXT NOT NULL,
    submitted_by BIGINT NOT NULL REFERENCES accounts(id),
    level       TEXT NOT NULL,
    amount_atomic BIGINT,
    confirmations_bucket TEXT,
    pending_proof_enc BYTEA,                       -- encrypted w/ key file; nulled at finality
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE conversations (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    public_id   TEXT NOT NULL UNIQUE,
    order_id    BIGINT REFERENCES orders(id),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE conversation_participants (
    conversation_id BIGINT NOT NULL REFERENCES conversations(id),
    account_id  BIGINT NOT NULL REFERENCES accounts(id),
    PRIMARY KEY (conversation_id, account_id)
);

CREATE TABLE encrypted_messages (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    conversation_id BIGINT NOT NULL REFERENCES conversations(id),
    sender_id   BIGINT NOT NULL REFERENCES accounts(id),
    recipient_id BIGINT NOT NULL REFERENCES accounts(id),
    recipient_key_id TEXT NOT NULL,
    blob_ref    TEXT NOT NULL,
    length      INT NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at  TIMESTAMPTZ NOT NULL
);

CREATE TABLE reviews (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id    BIGINT NOT NULL UNIQUE REFERENCES orders(id),
    score       INT NOT NULL CHECK (score BETWEEN 1 AND 5),
    text        TEXT NOT NULL,
    seller_reply TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE reputation_facts (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    seller_id   BIGINT NOT NULL REFERENCES accounts(id),
    buyer_token BYTEA NOT NULL,                    -- HMAC, keyed from the key file
    maturity_bucket SMALLINT NOT NULL,
    evidence_level TEXT NOT NULL,
    outcome     TEXT NOT NULL,
    score       INT,
    month       TEXT NOT NULL                      -- YYYY-MM
);

CREATE TABLE disputes (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id    BIGINT NOT NULL REFERENCES orders(id),
    opened_by   BIGINT NOT NULL REFERENCES accounts(id),
    state       TEXT NOT NULL DEFAULT 'open',
    outcome     TEXT,
    resolved_by BIGINT REFERENCES accounts(id),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE disclosures (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    dispute_id  BIGINT NOT NULL REFERENCES disputes(id),
    submitted_by BIGINT NOT NULL REFERENCES accounts(id),
    content_enc BYTEA NOT NULL,                    -- encrypted w/ key file
    signature_status TEXT NOT NULL,                -- verified | unverified_claim
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE reports (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    reporter_id BIGINT NOT NULL REFERENCES accounts(id),
    target      TEXT NOT NULL,
    category    TEXT NOT NULL,
    state       TEXT NOT NULL DEFAULT 'open',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE notifications (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    account_id  BIGINT NOT NULL REFERENCES accounts(id),
    event_type  TEXT NOT NULL,
    object_ref  TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    read_at     TIMESTAMPTZ
);

CREATE TABLE admission_records (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    account_id  BIGINT NOT NULL REFERENCES accounts(id),
    module      TEXT NOT NULL,
    outcome     TEXT NOT NULL,
    inviter_id  BIGINT REFERENCES accounts(id),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE security_events (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    actor_id    BIGINT REFERENCES accounts(id),
    event_type  TEXT NOT NULL,                     -- allow-listed fields only (§3.15)
    target      TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE extension_installations (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    identifier  TEXT NOT NULL UNIQUE,
    version     TEXT NOT NULL,
    manifest    JSONB NOT NULL,
    capabilities JSONB NOT NULL
);

-- Module-owned tables live in their own migrations as mod_<id>_* (spec §4.6).

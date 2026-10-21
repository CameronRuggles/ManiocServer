-- Stage 9 (spec §13): reputation, reviews, dispute outcomes + disclosures,
-- moderation, TOTP, account closure (owner ruling 2026-10-16: closure
-- replaces suspension/banning — there is no exclusion tool).
-- Additive only; existing tables keep their Stage 0-8 shape.

-- Account lifecycle: status is active | closed. "warned" is a timestamp,
-- not a state: a warned account functions normally. Closure stamps
-- closed_at; history rows are never deleted by closure.
ALTER TABLE accounts ADD COLUMN status TEXT NOT NULL DEFAULT 'active';
ALTER TABLE accounts ADD COLUMN closed_at TIMESTAMPTZ;
ALTER TABLE accounts ADD COLUMN warned_at TIMESTAMPTZ;
-- TOTP (moderator step-up): secret is stored encrypted with the key file
-- (content_enc format of the disclosures helper), never in plaintext.
ALTER TABLE accounts ADD COLUMN totp_secret_enc BYTEA;
ALTER TABLE accounts ADD COLUMN totp_pending_enc BYTEA;
ALTER TABLE accounts ADD COLUMN totp_enabled_at TIMESTAMPTZ;

-- When the order reached a terminal state ( Stage 9 facts and the
-- "reputation stops accruing at closure" rule need the moment).
ALTER TABLE orders ADD COLUMN terminal_at TIMESTAMPTZ;

-- Reviews: edit window tracking + reply timestamp + length checks.
ALTER TABLE reviews ADD COLUMN updated_at TIMESTAMPTZ;
ALTER TABLE reviews ADD COLUMN seller_reply_at TIMESTAMPTZ;
ALTER TABLE reviews ADD CONSTRAINT reviews_text_len
    CHECK (char_length(text) <= 1000);
ALTER TABLE reviews ADD CONSTRAINT reviews_reply_len
    CHECK (seller_reply IS NULL OR char_length(seller_reply) <= 1000);

-- Reputation facts: one fact per order, idempotent by construction.
ALTER TABLE reputation_facts ADD COLUMN order_id BIGINT UNIQUE REFERENCES orders(id);

-- Disputes: outcome workflow. outcome_state: proposed (refund awaiting
-- buyer confirmation) | final. state gains 'awaiting_buyer_confirmation',
-- 'resolved', 'closed' (withdrawn) alongside 'open'.
ALTER TABLE disputes ADD COLUMN resolved_at TIMESTAMPTZ;
ALTER TABLE disputes ADD COLUMN outcome_state TEXT NOT NULL DEFAULT 'final';

-- Reports gain a free-text reason.
ALTER TABLE reports ADD COLUMN reason TEXT NOT NULL DEFAULT '';

-- Stored reputation summaries: model id + version stored with each
-- summary (spec §13).
CREATE TABLE reputation_summaries (
    seller_id          BIGINT PRIMARY KEY REFERENCES accounts(id),
    model_id           TEXT NOT NULL,
    model_version      TEXT NOT NULL,
    weighted_score     DOUBLE PRECISION,
    review_count       INT NOT NULL DEFAULT 0,
    established_buyers BIGINT NOT NULL DEFAULT 0,
    total_weight       DOUBLE PRECISION NOT NULL DEFAULT 0,
    computed_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Moderator action audit (warn / close / listing removal / report and
-- dispute outcomes). Actions, never funds: moderators have no others.
CREATE TABLE moderation_actions (
    id                BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    actor_id          BIGINT NOT NULL REFERENCES accounts(id),
    target_account_id BIGINT REFERENCES accounts(id),
    target_listing_id BIGINT REFERENCES listings(id),
    action            TEXT NOT NULL,
    reason            TEXT NOT NULL DEFAULT '',
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

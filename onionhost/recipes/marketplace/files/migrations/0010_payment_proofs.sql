-- Buyer-submitted payment proofs for direct-v1 orders (owner decision
-- 2026-10-18, amending Direct Payments v1; audit fix brief task 1,
-- expanded).
--
-- The 2026-10-15 handoff's hard rule was "the server never stores
-- txids or proofs". The owner has amended that rule for this one
-- path: a buyer who paid the order's assigned subaddress may submit
-- the Monero transaction proof (txid + proof string) as evidence.
-- The server CARRIES the proof — it never verifies it (no wallet, no
-- node; verification stays with the seller's and moderators' own
-- wallets), and it is never labelled "verified" anywhere. What is
-- stored here is a buyer assertion with evidence attached, recorded
-- with its submission timestamp: the "I've paid" report that the
-- dispute gate, the expiry sweep, and the seller-cancel guard key on.
--
-- `payment_evidence` cannot hold this (its invoice_id is NOT NULL and
-- direct-v1 orders have no invoice), so — like attestations in 0008 —
-- it gets its own table.
--
-- VISIBILITY (owner-directed, 2026-10-18): a proof row is visible
-- ONLY to the buyer who submitted it and to moderators inside the
-- dispute view. It is never shown to the seller, and no seller-facing
-- surface may reveal that a proof exists. One row per order: the
-- buyer may revise their submission while the order is open;
-- created_at keeps the FIRST submission time (the report's
-- timestamp), updated_at tracks the latest revision.

CREATE TABLE payment_proofs (
    id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id      BIGINT NOT NULL UNIQUE REFERENCES orders(id),
    pool_entry_id BIGINT NOT NULL REFERENCES payment_pool_entries(id),
    submitted_by  BIGINT NOT NULL REFERENCES accounts(id),  -- the buyer
    txid          TEXT NOT NULL,   -- 64 lowercase hex chars, validated at submission
    proof         TEXT NOT NULL,   -- proof string as submitted (outer whitespace trimmed); server-unverified
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Report index: one row per order that has ANY buyer payment report.
-- kind = 'proof' (a payment_proofs row exists) or 'manual' (the buyer
-- used the manual "I paid" fallback — evidence level BuyerReported,
-- weaker by design; owner design update #2, 2026-10-18). The dispute
-- gate for direct orders keys on this table. The expiry sweep and the
-- seller not-received declaration key on payment_proofs specifically,
-- so a manual report alone never blocks closure as unpaid — it stays
-- on the record and preserves the buyer's dispute path against a
-- seller declaration.
CREATE TABLE payment_reports (
    order_id     BIGINT PRIMARY KEY REFERENCES orders(id),
    submitted_by BIGINT NOT NULL REFERENCES accounts(id),  -- the buyer
    kind         TEXT NOT NULL,   -- 'proof' | 'manual'
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Seller not-received declarations (owner design update #2, 2026-10-18):
-- after the unpaid-expiry horizon the seller may declare, for one
-- specific order and its assigned subaddress, that no payment arrived.
-- One declaration per order. With a proof on file the declaration only
-- records the statement (and raises a contradiction flag below);
-- without a proof it closes the order as unpaid — the same end state
-- the expiry sweep produces.
CREATE TABLE payment_declarations (
    id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id      BIGINT NOT NULL UNIQUE REFERENCES orders(id),
    pool_entry_id BIGINT NOT NULL REFERENCES payment_pool_entries(id),
    declared_by   BIGINT NOT NULL REFERENCES accounts(id),  -- the seller
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Auto-review flags, surfaced in the Stage 9 moderation queue
-- (owner design update #2, 2026-10-18):
--   'proof-unconfirmed'   — a proof is on file and the seller has not
--                           confirmed payment for the order; clears
--                           automatically when the seller confirms.
--   'proof-contradiction' — a proof is on file and the seller declared
--                           not-received; moderators resolve it.
-- Moderators viewing a flag see the proof; the seller never does.
CREATE TABLE payment_review_flags (
    id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id   BIGINT NOT NULL REFERENCES orders(id),
    kind       TEXT NOT NULL,   -- 'proof-unconfirmed' | 'proof-contradiction'
    state      TEXT NOT NULL DEFAULT 'open',   -- open | cleared | resolved | dismissed
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    closed_at  TIMESTAMPTZ
);
CREATE UNIQUE INDEX payment_review_flags_one_open
    ON payment_review_flags (order_id, kind) WHERE state = 'open';

-- Direct Monero Payments v1 (2026-10-15): seller payment identities,
-- signed-subaddress batches, and the one-subaddress-per-order pool.
--
-- The handoff's hard rules shape this schema: no seeds, keys, wallet
-- files, txids, received amounts, or payment proofs are stored anywhere
-- here. Addresses, signed messages, and signatures are stored BYTE-EXACT
-- as uploaded (TEXT, never trimmed or re-encoded by any layer).
--
-- The §10 PGP invoice flow is untouched: `invoices` keeps its statement
-- contract and direct-v1 writes NO rows into it. Assignment lives in
-- these new additive tables instead.
--
-- Every pool entry's address is ALSO inserted into the global
-- `destinations` table (source 'pool'), so the existing UNIQUE(address)
-- constraint enforces the "no address is ever handed out twice, for any
-- seller, in any state" guarantee. Entries are never returned to the
-- pool: a cancelled/expired order's entry becomes 'retired' forever.

CREATE TABLE payment_identities (
    seller_id       BIGINT PRIMARY KEY REFERENCES accounts(id),
    primary_address TEXT NOT NULL,               -- standard address, byte-exact as validated
    network         TEXT NOT NULL,               -- mainnet | stagenet | testnet (instance network at set time)
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),  -- first set: "unchanged since" date
    changed_at      TIMESTAMPTZ,                 -- last primary-address CHANGE (NULL = never changed)
    status          TEXT NOT NULL DEFAULT 'active'
);

CREATE TABLE payment_batches (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    seller_id       BIGINT NOT NULL REFERENCES accounts(id),
    marketplace_id  TEXT NOT NULL,               -- as declared in the uploaded batch, byte-exact
    network         TEXT NOT NULL,               -- as declared in the uploaded batch, byte-exact
    entry_count     INT NOT NULL CHECK (entry_count > 0),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE payment_pool_entries (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    batch_id        BIGINT NOT NULL REFERENCES payment_batches(id),
    seller_id       BIGINT NOT NULL REFERENCES accounts(id),
    destination_id  BIGINT NOT NULL UNIQUE REFERENCES destinations(id),
    address         TEXT NOT NULL,               -- subaddress, byte-exact as uploaded
    message         TEXT NOT NULL,               -- signed message, byte-exact as uploaded
    signature       TEXT NOT NULL,               -- wallet signature, byte-exact as uploaded
    state           TEXT NOT NULL DEFAULT 'unused',  -- unused | assigned | retired
    order_id        BIGINT REFERENCES orders(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    assigned_at     TIMESTAMPTZ,
    retired_at      TIMESTAMPTZ
);
-- One entry per order, and an order carries at most one entry.
CREATE UNIQUE INDEX payment_pool_entries_one_per_order
    ON payment_pool_entries (order_id) WHERE order_id IS NOT NULL;
CREATE INDEX payment_pool_entries_seller_state
    ON payment_pool_entries (seller_id, state, id);

-- Seller mark-paid attestations for direct-v1 orders. `payment_evidence`
-- cannot hold these (its invoice_id is NOT NULL and direct-v1 orders
-- have no invoice), so the attestation claim is recorded here instead.
-- amount_atomic is always NULL by design: the handoff forbids recording
-- amounts received, and the claim itself carries None.
CREATE TABLE payment_attestations (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id        BIGINT NOT NULL UNIQUE REFERENCES orders(id),
    pool_entry_id   BIGINT REFERENCES payment_pool_entries(id),
    submitted_by    BIGINT NOT NULL REFERENCES accounts(id),
    claim_kind      TEXT NOT NULL,               -- 'seller-attestation'
    amount_atomic   BIGINT,                      -- always NULL for direct-v1
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Messaging Audit fix, task 6 (MM4): direct-conversation blocks.
--
-- An account can refuse DIRECT conversations from another account:
-- the blocked account can neither open a direct conversation with
-- the blocker nor send into an existing direct conversation with
-- them (messages::send_message enforces the send side;
-- messages::block_exists_either_way gates opening). Order
-- conversations are never affected: trading counterparties must stay
-- reachable for the life of an order. This is a personal reachability
-- preference, not a moderation instrument — it hides nothing, closes
-- no account, and leaves no mark on the blocked account.
CREATE TABLE conversation_blocks (
    blocker_id BIGINT NOT NULL REFERENCES accounts(id),
    blocked_id BIGINT NOT NULL REFERENCES accounts(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (blocker_id, blocked_id),
    CHECK (blocker_id <> blocked_id)
);

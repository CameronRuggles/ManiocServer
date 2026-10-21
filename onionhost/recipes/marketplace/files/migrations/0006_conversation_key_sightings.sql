-- Q16 key-history storage (owner check, gate retrofit 2026-10-13).
-- identity_keys already records each key's validity interval (created_at /
-- retired_at). This table records the other half of the Q16 rule: which
-- keys were actually SHOWN to whom inside a given conversation, so Stage 5's
-- envelope validator can answer RecipientKeyRetired vs WrongRecipient
-- without ever revealing key history from other conversations.

CREATE TABLE conversation_key_sightings (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    conversation_id BIGINT NOT NULL REFERENCES conversations(id),
    account_id      BIGINT NOT NULL REFERENCES accounts(id),   -- whose key was shown
    fingerprint     TEXT NOT NULL,                             -- primary fingerprint, uppercase hex
    key_id          TEXT NOT NULL,                             -- key ID of the (sub)key presented, uppercase hex
    shown_to        BIGINT NOT NULL REFERENCES accounts(id),   -- who was shown it
    shown_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (conversation_id, account_id, fingerprint, key_id, shown_to)
);

CREATE INDEX conversation_key_sightings_lookup
    ON conversation_key_sightings (conversation_id, account_id, fingerprint);

-- Account Security Audit fixes (2026-10-18): TOTP replay protection,
-- moderator code-guessing lockout, and session-bound step-up grants.
--
-- totp_last_step: the highest TOTP time step (unix_seconds / 30) ever
-- accepted at a verification gate (login or a step-up check) for this
-- account. A presented code whose step is <= this value is a replay
-- and is refused (audit AL3). Enrollment confirmation deliberately
-- does not record its step here: the locked Stage 9 gate suite
-- confirms enrollment and then presents the same current code at the
-- step-up gate, so the gate is the first consumer of a step.
ALTER TABLE accounts ADD COLUMN totp_last_step BIGINT;
-- Consecutive failed code verifications at any gate; reaching the
-- lockout threshold sets totp_locked_until (audit AH1: codes could be
-- guessed freely — ~330k tries on average succeeded within the hour).
ALTER TABLE accounts ADD COLUMN totp_fail_count INT NOT NULL DEFAULT 0;
ALTER TABLE accounts ADD COLUMN totp_locked_until TIMESTAMPTZ;
-- When the account was last sent an inbox notice about a lockout, so
-- one lockout episode produces exactly one notice.
ALTER TABLE accounts ADD COLUMN totp_lock_notified_at TIMESTAMPTZ;

-- A short-lived step-up grant, bound to one session: after a
-- moderator presents a fresh TOTP code, dispute disclosures render
-- for that session for a few minutes (audit AH1: a moderator session
-- alone could read every disclosure). Keyed by the session token
-- HASH (raw tokens are never stored, sessions.rs).
CREATE TABLE totp_stepup_grants (
    token_hash BYTEA NOT NULL,
    account_id BIGINT NOT NULL REFERENCES accounts(id),
    purpose    TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (token_hash, purpose)
);

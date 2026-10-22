-- Fix Verification fixes (2026-10-19): step-up failure counting.
--
-- stepup_fail_count: consecutive WRONG PASSPHRASES presented at a
-- step-up (identity-change) confirmation for this account
-- (verification-fix V6). The counter increments atomically in the
-- database; at 5 the session in use is revoked and the account is
-- notified. A successful step-up resets it. TOTP code failures are
-- NOT counted here — they have their own counter and lockout
-- (migration 0011).
ALTER TABLE accounts ADD COLUMN stepup_fail_count INT NOT NULL DEFAULT 0;

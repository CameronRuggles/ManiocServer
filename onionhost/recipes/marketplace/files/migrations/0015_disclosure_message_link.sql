-- Fix Verification fixes (2026-10-19): tie unwrap disclosures to a
-- conversation message (V4).
--
-- An unwrapped disclosure now names the conversation message it
-- claims to unwrap. The row records WHICH message (message_id,
-- nullable only for disclosures stored before this migration), the
-- time the embedded signature was created (from the signature's
-- own creation subpacket), and that message's arrival time — the
-- two times the verification rule compares (signature created no
-- more than 24h before arrival) and the dispute page displays.
ALTER TABLE disclosures ADD COLUMN message_id BIGINT;
ALTER TABLE disclosures ADD COLUMN signature_created_at TIMESTAMPTZ;
ALTER TABLE disclosures ADD COLUMN message_received_at TIMESTAMPTZ;

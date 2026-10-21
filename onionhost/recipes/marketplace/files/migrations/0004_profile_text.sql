-- Stage 3: plain-text profile field (sellers list where their fingerprint
-- is published, spec section 8). Links render as text, never anchors.
ALTER TABLE accounts ADD COLUMN profile_text TEXT NOT NULL DEFAULT '';

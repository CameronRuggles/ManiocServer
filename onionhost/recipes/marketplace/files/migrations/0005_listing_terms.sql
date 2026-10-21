-- Stage 4: per-listing delivery/refund terms, bound into order terms files.
ALTER TABLE listings ADD COLUMN delivery_terms TEXT NOT NULL DEFAULT '';
ALTER TABLE listings ADD COLUMN refund_terms TEXT NOT NULL DEFAULT '';

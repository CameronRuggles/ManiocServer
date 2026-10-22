-- Media / Content / Disputes Audit fixes (2026-10-19).
--
-- Task 1 (CH1): moderator takedown gets its OWN fields, separate
-- from the seller-controlled status. While `taken_down_at` is set,
-- the listing's status reads 'removed' (a state only moderators can
-- put a listing into or take it out of — the locked Stage 9 suite
-- pins that column value after a moderator removal), the seller's
-- status changes are refused, and `pre_takedown_status` holds the
-- seller's own status to return to on restore. The seller's own
-- removal is renamed 'withdrawn'.
--
-- Legacy 'removed' rows are ambiguous BY CONSTRUCTION (that was the
-- bug): the same value meant "a moderator removed this" and "the
-- seller withdrew this". They are mapped by the only evidence that
-- distinguishes them — the moderation action log. A row whose
-- LATEST listing action is a moderator 'remove-listing' is a
-- takedown; every other legacy 'removed' row was the seller's own
-- removal and becomes 'withdrawn'. For takedown rows the
-- pre-takedown status is unrecoverable; 'published' is used
-- because that is what the old restore produced for every restore,
-- and the seller can pause it again immediately after a restore.
ALTER TABLE listings ADD COLUMN taken_down_at TIMESTAMPTZ;
ALTER TABLE listings ADD COLUMN taken_down_by BIGINT REFERENCES accounts(id);
ALTER TABLE listings ADD COLUMN pre_takedown_status TEXT;

UPDATE listings l
   SET taken_down_at = a.created_at,
       taken_down_by = a.actor_id,
       pre_takedown_status = 'published'
  FROM (
        SELECT DISTINCT ON (target_listing_id) id, target_listing_id, actor_id, created_at
          FROM moderation_actions
         WHERE action = 'remove-listing' AND target_listing_id IS NOT NULL
         ORDER BY target_listing_id, id DESC
       ) a
 WHERE l.id = a.target_listing_id
   AND l.status = 'removed'
   AND NOT EXISTS (
        SELECT 1 FROM moderation_actions r
         WHERE r.target_listing_id = l.id
           AND r.action = 'restore-listing'
           AND r.id > a.id
       );

UPDATE listings
   SET status = 'withdrawn'
 WHERE status = 'removed' AND taken_down_at IS NULL;

-- Task 7 (CL2): the moment a refund outcome was proposed to the
-- buyer. The retention job returns proposals older than the
-- deadline to the moderator queue. Existing awaiting rows are
-- backfilled with the dispute's creation time — a floor, not the
-- exact proposal moment: those disputes have waited AT LEAST that
-- long in total, so the deadline can only bite earlier, never
-- later than it should for them.
ALTER TABLE disputes ADD COLUMN refund_proposed_at TIMESTAMPTZ;
UPDATE disputes
   SET refund_proposed_at = created_at
 WHERE state = 'awaiting_buyer_confirmation';

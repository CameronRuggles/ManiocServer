-- 0017: HT H1 audit fix task 10 (finding F14 + owner decision Q5,
-- 2026-10-21): listings published before Hidden Trades terms
-- pinning existed (stage H1) carry no pinned terms statement, so
-- they can never pass the section-4 publish gate (a current pin
-- whose hash matches the listing's text). Auto-pause every
-- currently-published listing with no current terms pin; the
-- seller re-signs terms and re-publishes to bring it back. There
-- is no grandfathering (Q5).
--
-- Taken-down listings (status 'removed') are deliberately NOT
-- touched: their pre-takedown status is preserved separately, and
-- the moderation restore path re-checks the terms gate when such
-- a listing is restored (it restores to 'paused' when the gate
-- fails) -- see moderation::set_listing_removed.
UPDATE listings
   SET status = 'paused'
 WHERE status = 'published'
   AND NOT EXISTS (
       SELECT 1
         FROM listing_terms_statements t
        WHERE t.listing_id = listings.id
          AND t.superseded_at IS NULL
   );

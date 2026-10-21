-- Stage 2: catalogue categories (operator-facing browse filter).
ALTER TABLE listings ADD COLUMN category TEXT NOT NULL DEFAULT 'general';
CREATE INDEX listings_browse_idx ON listings (status, category, created_at DESC);
CREATE INDEX listings_search_idx ON listings USING gin (to_tsvector('simple', title || ' ' || description));

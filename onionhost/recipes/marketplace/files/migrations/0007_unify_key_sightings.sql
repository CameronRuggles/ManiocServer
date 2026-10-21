-- 0007: unify conversation_key_sightings on the canonical shape
-- (migration 0006 repair, Option A, 2026-10-14).
--
-- Background: two files shared version 0006 and created this table in
-- two incompatible shapes — the canonical one kept in
-- 0006_conversation_key_sightings.sql (account_id / key_id / shown_to,
-- written by crates/app/src/keys.rs) and a Stage-5 shape
-- (key_owner_id / shown_to_id / created_at, formerly written by
-- crates/app/src/messages.rs, which now delegates to keys.rs).
-- Databases created while both files existed can hold a hand-built
-- UNION of the two shapes. This migration repairs exactly those
-- databases. On a fresh install the table is already canonical and
-- this migration is a no-op.
--
-- Safety: everything runs inside one DO block, so any failure aborts
-- the whole migration with nothing applied. A sighting row that
-- cannot be mapped into the canonical columns (no owner in either
-- shape, fingerprint too short to derive a key ID, or fingerprint not
-- present in identity_keys for its owner) aborts the migration —
-- rows are never dropped silently.

DO $$
DECLARE
    r record;
    canonical_present boolean := false;
BEGIN
    -- Fresh install / already unified: nothing to do.
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'conversation_key_sightings'
          AND column_name = 'key_owner_id'
    ) THEN
        RETURN;
    END IF;

    -- Abort if any row cannot be mapped into the canonical shape.
    IF EXISTS (
        SELECT 1 FROM conversation_key_sightings
        WHERE (account_id IS NULL AND key_owner_id IS NULL)
           OR (key_owner_id IS NOT NULL AND (
                  length(fingerprint) < 16
                  OR NOT EXISTS (
                      SELECT 1 FROM identity_keys k
                      WHERE k.account_id = key_owner_id
                        AND k.fingerprint = conversation_key_sightings.fingerprint
                  )
               ))
    ) THEN
        RAISE EXCEPTION '0007: unmappable conversation_key_sightings row(s) present; aborting without changes';
    END IF;

    -- A Stage-5 row whose mapped form already exists as a canonical
    -- row records the same sighting twice; remove those first, or
    -- the backfill below would violate the canonical UNIQUE
    -- constraint mid-update. Only exact duplicates are removed — the
    -- sighting itself survives in the canonical row.
    DELETE FROM conversation_key_sightings t
     WHERE t.key_owner_id IS NOT NULL
       AND t.account_id IS NULL
       AND EXISTS (
           SELECT 1 FROM conversation_key_sightings c
            WHERE c.account_id IS NOT NULL
              AND c.conversation_id = t.conversation_id
              AND c.account_id = t.key_owner_id
              AND c.fingerprint = t.fingerprint
              AND c.key_id = right(t.fingerprint, 16)
              AND c.shown_to = t.shown_to_id
       );

    -- Copy Stage-5-shape rows into the canonical columns.
    -- key_id = last 16 hex chars of the fingerprint (the locked
    -- blind_stage3 suite's key_id_of derivation).
    UPDATE conversation_key_sightings
       SET account_id = key_owner_id,
           shown_to   = shown_to_id,
           key_id     = right(fingerprint, 16),
           shown_at   = COALESCE(shown_at, created_at)
     WHERE key_owner_id IS NOT NULL
       AND account_id IS NULL;

    -- Nothing canonical may be NULL after the backfill.
    IF EXISTS (
        SELECT 1 FROM conversation_key_sightings
        WHERE conversation_id IS NULL OR account_id IS NULL
           OR fingerprint IS NULL OR key_id IS NULL OR shown_to IS NULL
    ) THEN
        RAISE EXCEPTION '0007: NULL in canonical columns after backfill; aborting without changes';
    END IF;

    -- Deduplicate on the canonical key (the same sighting could have
    -- been recorded in both shapes), keeping the lowest id.
    DELETE FROM conversation_key_sightings t
     USING (
        SELECT id, ROW_NUMBER() OVER (
                   PARTITION BY conversation_id, account_id, fingerprint, key_id, shown_to
                   ORDER BY id
               ) AS rn
          FROM conversation_key_sightings
     ) d
     WHERE t.id = d.id AND d.rn > 1;

    -- Drop UNIQUE constraints that are not the canonical one
    -- (name-agnostic: the union tables were hand-built).
    FOR r IN
        SELECT c.conname,
               (SELECT array_agg(a.attname::text ORDER BY a.attname)
                  FROM unnest(c.conkey) AS k(attnum)
                  JOIN pg_attribute a
                    ON a.attrelid = c.conrelid AND a.attnum = k.attnum) AS cols
          FROM pg_constraint c
         WHERE c.conrelid = 'conversation_key_sightings'::regclass
           AND c.contype = 'u'
    LOOP
        IF r.cols IS DISTINCT FROM
           ARRAY['account_id','conversation_id','fingerprint','key_id','shown_to'] THEN
            EXECUTE format(
                'ALTER TABLE conversation_key_sightings DROP CONSTRAINT %I', r.conname);
        ELSE
            canonical_present := true;
        END IF;
    END LOOP;

    -- Drop any index that still references the Stage-5-only columns.
    FOR r IN
        SELECT i.relname AS idx
          FROM pg_index x
          JOIN pg_class i ON i.oid = x.indexrelid
          JOIN pg_class t ON t.oid = x.indrelid
         WHERE t.relname = 'conversation_key_sightings'
           AND EXISTS (
               SELECT 1 FROM unnest(x.indkey) AS k(attnum)
               JOIN pg_attribute a
                 ON a.attrelid = t.oid AND a.attnum = k.attnum
               WHERE a.attname IN ('key_owner_id', 'shown_to_id', 'created_at')
           )
    LOOP
        EXECUTE format('DROP INDEX IF EXISTS %I', r.idx);
    END LOOP;

    -- Drop the Stage-5-only columns (their foreign keys go with them).
    ALTER TABLE conversation_key_sightings
        DROP COLUMN key_owner_id,
        DROP COLUMN shown_to_id,
        DROP COLUMN created_at;

    -- Restore the canonical constraint / nullability / index if the
    -- hand-built union lacked any of them.
    IF NOT canonical_present THEN
        ALTER TABLE conversation_key_sightings
            ADD CONSTRAINT conversation_key_sightings_canonical_unique
            UNIQUE (conversation_id, account_id, fingerprint, key_id, shown_to);
    END IF;

    ALTER TABLE conversation_key_sightings
        ALTER COLUMN account_id SET NOT NULL,
        ALTER COLUMN key_id SET NOT NULL,
        ALTER COLUMN shown_to SET NOT NULL;

    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'conversation_key_sightings'
          AND column_name = 'shown_at'
    ) THEN
        ALTER TABLE conversation_key_sightings
            ALTER COLUMN shown_at SET DEFAULT now(),
            ALTER COLUMN shown_at SET NOT NULL;
    END IF;

    CREATE INDEX IF NOT EXISTS conversation_key_sightings_lookup
        ON conversation_key_sightings (conversation_id, account_id, fingerprint);
END $$;

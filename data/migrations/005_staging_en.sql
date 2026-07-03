-- Staging rows carry their EN equivalent so T13 can publish concept PAIRS
-- (es row + en row sharing concept_id) instead of orphan ES terms.
ALTER TABLE seed_staging ADD COLUMN en_equiv TEXT;
ALTER TABLE seed_staging ADD COLUMN example TEXT;

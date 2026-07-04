-- Le Littré-style presentation (team reference, 2026-07-04): pronunciation
-- gets its own field/section instead of overloading ling_info.
ALTER TABLE terms ADD COLUMN pronunciation TEXT;

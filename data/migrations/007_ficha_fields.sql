-- Ficha model from the terminology team (TT_2 spreadsheet, 2026-07-04):
-- app-visible fields beyond term/definition/example. All optional.
--   subdomain     — Subdominio (finer slice of the category/domain)
--   variations    — Variaciones localizadas (regional variants of the term)
--   contrast_note — "No confundir" (false-friend / contrasentido warning)
--   ling_info     — Información lingüística (POS, gender, plural, etc.)
ALTER TABLE terms ADD COLUMN subdomain TEXT;
ALTER TABLE terms ADD COLUMN variations TEXT;
ALTER TABLE terms ADD COLUMN contrast_note TEXT;
ALTER TABLE terms ADD COLUMN ling_info TEXT;

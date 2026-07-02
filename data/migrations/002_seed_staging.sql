-- Seed staging (F5): importers write here; nothing reaches `terms` without
-- the T13 human spot-check + bulk publish step.
-- NOTE (E3 escalation, open): seed sources carry a `definition` field that the
-- published `terms` schema does not yet hold. Decide before T13 whether to add
-- terms.definition via migration 003 or map definitions into `example`.
CREATE TABLE seed_staging (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,           -- e.g. 'covenin-3661-2001', 'onsa-glosario'
    source_ref TEXT,                -- clause number / section letter in the source
    lang TEXT NOT NULL DEFAULT 'es',
    text TEXT NOT NULL,             -- the term itself
    definition TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'Protocolos',  -- recategorized by humans at T13
    register TEXT NOT NULL DEFAULT 'formal',
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source, text)
);

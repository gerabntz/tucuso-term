-- Seed staging (F5): importers write here; nothing reaches `terms` without
-- the T13 human spot-check + bulk publish step.
-- NOTE (E3, resolved): `definition` moved into the published schema via
-- migration 006; the extra ficha fields arrived in 007/008.
CREATE TABLE seed_staging (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,           -- e.g. 'unisdr-2009', 'onsa-glosario'
    source_ref TEXT,                -- clause number / section letter in the source
    lang TEXT NOT NULL DEFAULT 'es',
    text TEXT NOT NULL,             -- the term itself
    definition TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'Protocolos',  -- recategorized by humans at T13
    register TEXT NOT NULL DEFAULT 'formal',
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source, text)
);

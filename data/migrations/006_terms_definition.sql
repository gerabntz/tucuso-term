-- Resolves the E3 escalation flagged in 002_seed_staging.sql: published terms
-- now carry the definition instead of overloading `example`.
ALTER TABLE terms ADD COLUMN definition TEXT;

-- Rebuild FTS to make definitions searchable.
DROP TRIGGER terms_ai;
DROP TRIGGER terms_ad;
DROP TRIGGER terms_au;
DROP TABLE terms_fts;

CREATE VIRTUAL TABLE terms_fts USING fts5(
    text,
    definition,
    example,
    content='terms',
    content_rowid='id'
);

CREATE TRIGGER terms_ai AFTER INSERT ON terms BEGIN
    INSERT INTO terms_fts(rowid, text, definition, example)
    VALUES (new.id, new.text, new.definition, new.example);
END;

CREATE TRIGGER terms_ad AFTER DELETE ON terms BEGIN
    INSERT INTO terms_fts(terms_fts, rowid, text, definition, example)
    VALUES ('delete', old.id, old.text, old.definition, old.example);
END;

CREATE TRIGGER terms_au AFTER UPDATE ON terms BEGIN
    INSERT INTO terms_fts(terms_fts, rowid, text, definition, example)
    VALUES ('delete', old.id, old.text, old.definition, old.example);
    INSERT INTO terms_fts(rowid, text, definition, example)
    VALUES (new.id, new.text, new.definition, new.example);
END;

INSERT INTO terms_fts(terms_fts) VALUES ('rebuild');

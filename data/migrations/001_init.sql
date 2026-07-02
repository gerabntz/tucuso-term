PRAGMA foreign_keys = ON;

CREATE TABLE terms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    concept_id TEXT NOT NULL,
    lang TEXT NOT NULL,
    text TEXT NOT NULL,
    category TEXT NOT NULL,
    register TEXT NOT NULL,
    zone TEXT,
    example TEXT,
    audio_ref TEXT,
    source TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('draft', 'pending_review', 'published', 'rejected')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE revisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    term_id INTEGER NOT NULL,
    proposed_fields TEXT NOT NULL,
    reason TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('draft', 'pending_review', 'published', 'rejected')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- RESTRICT, not CASCADE: history is immutable (M8) — a term with history
    -- can never be hard-deleted out from under its revisions.
    FOREIGN KEY(term_id) REFERENCES terms(id) ON DELETE RESTRICT
);

CREATE TABLE approvals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    target_type TEXT NOT NULL CHECK(target_type IN ('term', 'revision')),
    target_id INTEGER NOT NULL,
    reviewer_id INTEGER NOT NULL,
    verdict TEXT NOT NULL CHECK(verdict IN ('approve', 'veto')),
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(reviewer_id, target_type, target_id)
);

CREATE TABLE submission_tokens (
    token TEXT PRIMARY KEY,
    target_type TEXT NOT NULL CHECK(target_type IN ('term', 'revision')),
    target_id INTEGER NOT NULL,
    expires_at TIMESTAMP NOT NULL
);

-- FTS5 Virtual Table for full-text search on terms
CREATE VIRTUAL TABLE terms_fts USING fts5(
    text,
    example,
    content='terms',
    content_rowid='id'
);

-- Sync Triggers to keep terms_fts updated
CREATE TRIGGER terms_ai AFTER INSERT ON terms BEGIN
    INSERT INTO terms_fts(rowid, text, example) VALUES (new.id, new.text, new.example);
END;

CREATE TRIGGER terms_ad AFTER DELETE ON terms BEGIN
    INSERT INTO terms_fts(terms_fts, rowid, text, example) VALUES ('delete', old.id, old.text, old.example);
END;

CREATE TRIGGER terms_au AFTER UPDATE ON terms BEGIN
    INSERT INTO terms_fts(terms_fts, rowid, text, example) VALUES ('delete', old.id, old.text, old.example);
    INSERT INTO terms_fts(rowid, text, example) VALUES (new.id, new.text, new.example);
END;

-- Indexes for performant lookups
CREATE INDEX idx_terms_concept ON terms(concept_id);
CREATE INDEX idx_terms_status_lang ON terms(status, lang);
CREATE INDEX idx_revisions_term ON revisions(term_id);
CREATE INDEX idx_approvals_target ON approvals(target_type, target_id);
CREATE INDEX idx_tokens_expires ON submission_tokens(expires_at);

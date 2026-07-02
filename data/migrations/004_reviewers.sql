-- Reviewers are the ONLY accounts in the system (N1/M10). Invite-only:
-- rows are created exclusively by the operator CLI, never by a route.
-- `handle` is a pseudonym; the schema shield forbids real_name by design.
CREATE TABLE reviewers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    handle TEXT NOT NULL UNIQUE,
    active INTEGER NOT NULL DEFAULT 1,
    invited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Single-use, short-lived login links (M10): consumed on first use,
-- worthless within minutes if intercepted.
CREATE TABLE magic_links (
    token TEXT PRIMARY KEY,
    reviewer_id INTEGER NOT NULL REFERENCES reviewers(id),
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP
);

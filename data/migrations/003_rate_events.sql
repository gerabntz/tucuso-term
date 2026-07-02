-- Anti-spam rate limiting (F2): salted daily hash of the client IP, never the
-- raw IP (M9). Rows older than the retention window are purged on every check.
CREATE TABLE rate_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_rate_events_hash ON rate_events(ip_hash, created_at);

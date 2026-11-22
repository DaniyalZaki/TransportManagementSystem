CREATE TABLE IF NOT EXISTS feedback_submissions (
    id UUID PRIMARY KEY,
    content TEXT NOT NULL,
    normalized_content TEXT NOT NULL,
    name TEXT,
    contact TEXT,
    received_at TIMESTAMPTZ NOT NULL,
    delivered_at TIMESTAMPTZ,
    retry_count INTEGER NOT NULL DEFAULT 0 CHECK (retry_count BETWEEN 0 AND 3),
    next_retry_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS feedback_duplicate_idx ON feedback_submissions (normalized_content, received_at DESC);
CREATE INDEX IF NOT EXISTS feedback_retry_idx ON feedback_submissions (next_retry_at) WHERE delivered_at IS NULL AND next_retry_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS feedback_retention_idx ON feedback_submissions (received_at);

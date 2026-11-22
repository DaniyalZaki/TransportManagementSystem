CREATE TABLE IF NOT EXISTS announcements (
    id UUID PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    published_at TIMESTAMPTZ NOT NULL,
    expires_at TIMESTAMPTZ,
    is_operational BOOLEAN NOT NULL DEFAULT FALSE,
    confirmed_at TIMESTAMPTZ,
    removed_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS announcements_public_idx ON announcements (published_at DESC) WHERE removed_at IS NULL;
CREATE INDEX IF NOT EXISTS announcements_retention_idx ON announcements (expires_at, removed_at);
CREATE TABLE IF NOT EXISTS urgent_banners (
    id UUID PRIMARY KEY,
    announcement_id UUID NOT NULL REFERENCES announcements(id),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    removed_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS urgent_banners_public_idx ON urgent_banners (created_at DESC) WHERE removed_at IS NULL AND resolved_at IS NULL;

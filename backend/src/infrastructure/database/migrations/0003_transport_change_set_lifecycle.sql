-- Slice 2: write-side lifecycle for named, versioned transport change sets.
ALTER TABLE transport_change_sets
    ADD COLUMN IF NOT EXISTS base_published_change_set_id UUID
        REFERENCES transport_change_sets(id),
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    ADD COLUMN IF NOT EXISTS expires_at TIMESTAMPTZ NOT NULL DEFAULT (now() + interval '30 days'),
    ADD COLUMN IF NOT EXISTS retired_at TIMESTAMPTZ;

CREATE TABLE IF NOT EXISTS audit_transport_publications (
    id UUID PRIMARY KEY,
    change_set_id UUID NOT NULL REFERENCES transport_change_sets(id),
    publisher_supabase_user_id TEXT NOT NULL,
    published_at TIMESTAMPTZ NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    UNIQUE (change_set_id)
);
CREATE INDEX IF NOT EXISTS audit_transport_publications_retention_idx
    ON audit_transport_publications (expires_at);

CREATE INDEX IF NOT EXISTS transport_change_sets_draft_expiry_idx
    ON transport_change_sets (expires_at) WHERE status = 'draft';

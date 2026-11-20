-- Backend-owned mapping from a self-hosted Supabase user to an application role.
-- Supabase owns credentials and sessions; this module owns authorization roles.
CREATE TABLE IF NOT EXISTS authentication_role_mappings (
    supabase_user_id UUID PRIMARY KEY,
    role TEXT NOT NULL CHECK (role IN ('transport_management', 'designated_administrator')),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deactivated_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS authentication_role_mappings_active_idx
    ON authentication_role_mappings (is_active);

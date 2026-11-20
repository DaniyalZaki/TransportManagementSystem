# Authentication module

Supabase Auth owns email/password credentials and token issuance. This module
locally validates active JWTs and resolves the authenticated Supabase subject
through the backend-owned PostgreSQL role mapping. It does not store passwords
or sessions. The first Transport Management account is manually provisioned in
Supabase and then mapped through migration-managed PostgreSQL data.

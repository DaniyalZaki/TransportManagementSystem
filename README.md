# Uzair Transport Service

Uzair Transport Service is the official public transport-information portal for the university community. Students and the public can view published departures, schedules, routes, announcements, and urgent notices without signing in. Authorized Transport Management staff and designated administrators use a separate administration application to manage and publish information.

The system is a modular monolith: two Next.js clients call one FastAPI backend, and PostgreSQL is the system of record. The approved requirements source is [PRD.md](PRD.md); architecture and implementation decisions are in [architecture.md](architecture.md) and [ADRs](docs/adr/).

## Key features

- Login-free current-departure and daily-schedule views calculated in Pakistan Standard Time (PKT).
- Published-only transport data: route, bus/service, assignment, and schedule changes are drafts until an authorized user atomically publishes a named change set.
- Recurring weekly schedules with full-day and partial date-specific overrides.
- Directly published announcements, PKT expiry, and separate persistent urgent banners with distinct remove and resolve actions.
- Anonymous feedback with a honeypot, normalized-content duplicate rejection for 10 minutes, SMTP delivery/retries, and 30-day retention.
- Mobile-focused PWA resilience: published data and announcements may be cached for 24 hours and are clearly labelled fresh, stale, offline, or service-outage. Active urgent banners are online-only.
- Backend-enforced role-based access control using self-hosted Supabase Auth and backend-owned role mappings.
- Publication-only audit history and whole-change-set recovery for 30 days.

## Technology stack

| Area | Technology |
|---|---|
| Public and admin clients | Next.js, React, TypeScript, Tailwind CSS, Headless UI |
| Public offline support | Workbox, Cache Storage, IndexedDB |
| Backend | Python 3.11+, FastAPI, handwritten asynchronous SQL/migrations |
| Data | PostgreSQL with `asyncpg` |
| Privileged identity | Self-hosted Supabase Auth, locally validated JWTs, backend-owned role mapping |
| Tests | Pytest, Cypress, Testing Library for Cypress |
| Local services | Docker Compose |

## Project structure

```text
apps/
  public-pwa/        Public, mobile-first Next.js application
  admin-web/         Privileged Next.js administration application
backend/
  src/application/   FastAPI application and authorization boundary
  src/modules/       Authentication, transport, announcements, feedback, audit, reporting
  src/infrastructure/ Database, cache, and configuration adapters
docs/
  adr/               Accepted architectural decision records
  design/            API, data, UI, component, test, and diagram artifacts
infra/local/         Local PostgreSQL and Supabase Auth Compose configuration
```

## Setup instructions

Prerequisites: Python 3.11+, Node.js 20+, npm, and Docker Compose.

1. Copy `infra/local/.env.example` to `infra/local/.env` and `.env.example` to `.env`. Set one local JWT secret in both files (`SUPABASE_JWT_SECRET` and `UTS_SUPABASE_JWT_SIGNING_KEY` must match). Never commit either `.env` file or real credentials.
2. Start PostgreSQL and self-hosted Supabase Auth:

   ```powershell
   docker compose --env-file infra/local/.env -f infra/local/compose.yaml up -d
   ```

3. Create and activate a Python virtual environment, then install backend development dependencies:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -e "backend[postgres,dev]"
   ```

4. Apply migrations, replacing `<database-url>` with the local PostgreSQL URL:

   ```powershell
   python backend/src/infrastructure/database/migrate.py <database-url>
   ```

5. Install JavaScript dependencies from the repository root:

   ```powershell
   npm install
   ```

The first Transport Management account is manually provisioned through Supabase. After applying the migration, map that account's Supabase UUID to `transport_management` in `authentication_role_mappings`; this is a one-time bootstrap action, not a public endpoint:

```sql
INSERT INTO authentication_role_mappings (supabase_user_id, role)
VALUES ('<Supabase user UUID>', 'transport_management');
```

Credentials are never stored in this repository. Subsequent role mappings and deactivation use the Transport-Management-only `/admin/accounts` API boundary.

## Run locally

Open three terminals after setup:

```powershell
# Backend (repository root)
uvicorn src.application.main:app --app-dir backend --reload

# Public PWA
npm run dev --workspace @uzair/public-pwa

# Admin app
npm run dev --workspace @uzair/admin-web
```

The public PWA runs on `http://localhost:3000`; the admin application runs on `http://localhost:3001`.

## Run tests and checks

```powershell
# Backend tests (from backend/)
python -m pytest

# Backend lint (from backend/)
python -m flake8 src tests

# Client checks (repository root)
npm run typecheck
npm run lint
npm run build

# Browser tests — start the relevant client first
npm run test:e2e
```

The foundation contains only its currently implemented test surface. Planned coverage and acceptance cases are in [docs/design/test-cases.md](docs/design/test-cases.md).

## Important documentation

| Document | Purpose |
|---|---|
| [PRD.md](PRD.md) | Validated requirements, rules, flows, acceptance criteria, and open questions |
| [architecture.md](architecture.md) | Modular-monolith rationale, boundaries, interfaces, and constraints |
| [plan.md](plan.md) | Approved vertical-slice implementation plan |
| [ADR-011](docs/adr/ADR-011.md) | Current implementation/lifecycle profile; supersedes conflicting earlier ADR language |
| [API contracts](docs/design/api-contracts.md) | Proposed REST contracts grounded in the approved source documents |
| [Data model](docs/design/data-model.md) | Proposed PostgreSQL ownership, schema, lifecycle, and integrity rules |
| [UI wireframes](docs/design/ui-wireframes.md) | Mobile-first public and administration wireframes |
| [Component design](docs/design/component-design.md) | Client and backend component responsibilities |
| [Test cases](docs/design/test-cases.md) | Traceable functional, security, lifecycle, and resilience test ideas |
| [Diagrams](docs/design/diagrams.md) | Context, publish, schedule, and cache-state diagrams |

## Scope and guardrails

The portal does not include GPS/live tracking, payments, WhatsApp integration, an AI chatbot, IP-based feedback limiting, or a feedback status dashboard. Public clients never access PostgreSQL directly. Production hosting, SMTP credentials, and backup/recovery infrastructure remain release decisions and are intentionally not committed here.

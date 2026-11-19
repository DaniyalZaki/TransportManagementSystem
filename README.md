# Uzair Transport Service

Uzair Transport Service is the university’s official public transport-information portal. The public PWA provides published departures, schedules, announcements, urgent notices, and anonymous feedback without login. A separate Admin Web App is used by Transport Management and designated administrators.

## Key features

- PKT current-departure and daily timetable views, including “No further departures today”.
- Published-only route, bus, assignment, and schedule data; named change-set drafts publish atomically.
- Weekly schedules plus full-day and partial date-specific overrides.
- Direct announcements with PKT expiry and separate persistent urgent banners.
- Anonymous feedback: honeypot, normalized 10-minute duplicate rejection, SMTP delivery/retries, 30-day retention.
- Workbox PWA resilience: 24-hour cache, clear fresh/stale/offline/outage states; active banners are online-only.
- Backend RBAC via self-hosted Supabase Auth and backend-owned role mappings.
- Publication-only audit records and whole published-change-set recovery for 30 days.

## Technology stack

| Area | Technology |
|---|---|
| Clients | Next.js, React, TypeScript, Tailwind CSS, Headless UI |
| Offline | Workbox, Cache Storage, IndexedDB |
| Backend | Python 3.11+, FastAPI, handwritten async SQL/migrations |
| Data | PostgreSQL with asyncpg |
| Identity | Self-hosted Supabase Auth and locally validated JWTs |
| Tests | Pytest, Cypress, Testing Library for Cypress |
| Local services | Docker Compose |

## Project structure

```text
apps/public-pwa/     Public mobile-first Next.js client
apps/admin-web/      Privileged Next.js administration client
backend/src/         FastAPI application, modules, infrastructure
docs/adr/            Accepted architectural decisions
docs/design/         API, data, UI, component, test, diagram documentation
infra/local/         Local PostgreSQL/Supabase Auth Compose configuration
```

## Setup instructions

Prerequisites: Python 3.11+, Node.js 20+, npm, Docker Compose.

1. Copy `infra/local/.env.example` to `infra/local/.env` and set a local JWT secret.
2. Start local services:

   ```powershell
   docker compose --env-file infra/local/.env -f infra/local/compose.yaml up -d
   ```

3. Create/activate a virtual environment and install backend development dependencies:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -e "backend[dev]"
   ```

4. Apply migrations: `python backend/src/infrastructure/database/migrate.py <database-url>`
5. Install client dependencies: `npm install`

The first Transport Management account is manually provisioned in Supabase and mapped in `authentication_role_mappings`. Never commit credentials.

## Run locally

```powershell
# from repository root
uvicorn src.application.main:app --app-dir backend --reload
npm run dev --workspace @uzair/public-pwa
npm run dev --workspace @uzair/admin-web
```

The public PWA uses port 3000 and the admin app port 3001.

## Run tests

```powershell
# backend/ directory
python -m pytest

# repository root
ruff check backend
npm run typecheck
npm run lint
npm run build
npm run test:e2e
```

Start the relevant client before Cypress. Planned coverage is documented in [test cases](docs/design/test-cases.md).

## Important documentation

- [Product requirements](PRD.md)
- [Architecture](architecture.md)
- [Implementation plan](plan.md)
- [ADR-011 implementation profile](docs/adr/ADR-011.md)
- [API contracts](docs/design/api-contracts.md)
- [Data model](docs/design/data-model.md)
- [UI wireframes](docs/design/ui-wireframes.md)
- [Component design](docs/design/component-design.md)
- [Test cases](docs/design/test-cases.md)
- [System diagrams](docs/design/diagrams.md)

The project excludes GPS/live tracking, payments, WhatsApp integration, AI chat, IP-based feedback limiting, and feedback status tracking. Clients never access PostgreSQL directly.
# Transport Management System

Students and the public can view published departures, schedules, routes, announcements, and urgent notices without signing in. Authorized Transport Management staff and designated administrators use a separate administration application to manage and publish information.

The system is a modular monolith: two Next.js clients call one FastAPI backend, and PostgreSQL is the system of record. The approved requirements source is [PRD.md](PRD.md); architecture and implementation decisions are in [architecture.md](architecture.md) and [ADRs](docs/adr/).

## Key features

- Login-free current-departure and daily-schedule views calculated in Pakistan Standard Time (PKT).
- Published-only transport data: route, bus/service, assignment, and schedule changes live in one permanent shared draft until an authorized user atomically publishes a snapshot.
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

1. Copy `infra/local/.env.example` to `infra/local/.env` and `.env.example` to `.env`.
   Set one local JWT secret in both files: `SUPABASE_JWT_SECRET` and
   `UTS_SUPABASE_JWT_SIGNING_KEY` must have the same value. Never commit either
   `.env` file or real credentials.

   ```powershell
   Copy-Item infra/local/.env.example infra/local/.env
   Copy-Item .env.example .env
   ```

2. Start PostgreSQL and self-hosted Supabase Auth:

   ```powershell
   docker compose --env-file infra/local/.env -f infra/local/compose.yaml up -d
   ```

   On a fresh local PostgreSQL volume, GoTrue may need its `auth` schema and a
   `postgres` role before it can apply its own migrations. Only run the matching
   command if the Supabase Auth logs report that the schema or role is missing:

   ```powershell
   docker compose --env-file infra/local/.env -f infra/local/compose.yaml exec -T postgres psql -U uzair_transport -d uzair_transport -c "CREATE SCHEMA IF NOT EXISTS auth;"
   docker compose --env-file infra/local/.env -f infra/local/compose.yaml exec -T postgres psql -U uzair_transport -d uzair_transport -c "CREATE ROLE postgres WITH LOGIN SUPERUSER;"
   docker compose --env-file infra/local/.env -f infra/local/compose.yaml up -d supabase-auth
   ```

   Check service state with:

   ```powershell
   docker compose --env-file infra/local/.env -f infra/local/compose.yaml ps
   ```

3. Create and activate a Python virtual environment, then install the backend
   dependencies and the local ASGI server:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -e "backend[postgres,dev]" "uvicorn>=0.30,<1.0"
   ```

   When `python -m venv` was run with MSYS2 Python, use this activation command
   instead of `Scripts\\Activate.ps1`:

   ```powershell
   . .\.venv\bin\Activate.ps1
   ```

4. Load the local backend settings into the PowerShell session and apply
   migrations:

   ```powershell
   Get-Content .env | ForEach-Object {
     if ($_ -match '^\s*([^#=]+)=(.*)$') {
       Set-Item -Path "Env:$($matches[1].Trim())" -Value $matches[2].Trim()
     }
   }
   python backend/src/infrastructure/database/migrate.py $env:UTS_DATABASE_URL
   ```

5. Install JavaScript dependencies from the repository root:

   ```powershell
   npm install
   ```

## Configure SMTP feedback delivery

The backend sends public feedback to the configured Transport Management
mailbox using SMTP. Before starting the backend, set these values in the root
`.env` file (copied from `.env.example` during setup):

```dotenv
UTS_SMTP_HOST=smtp.example.com
UTS_SMTP_PORT=587
UTS_SMTP_USERNAME=transport@example.com
UTS_SMTP_PASSWORD=replace-with-an-app-password-or-smtp-password
UTS_SMTP_SENDER=transport@example.com
UTS_FEEDBACK_RECIPIENT=transport-management@example.com
```

`UTS_SMTP_HOST` and `UTS_FEEDBACK_RECIPIENT` are required for feedback
delivery. `UTS_SMTP_SENDER` is optional and defaults to the recipient address.
When `UTS_SMTP_USERNAME` is set, the backend uses STARTTLS and authenticates
with the supplied username and password; leave both username and password
empty only for an SMTP relay that does not require authentication. Port `587`
is the default. Use provider-issued app passwords where required, and keep
real SMTP credentials only in the uncommitted `.env` file.

## Bootstrap the first Transport Management account

The first management account is a one-time local bootstrap action. Public
signup remains disabled, and the normal admin account-management routes only
work after one account already has the `transport_management` role.

The process has two parts:

1. Create an email/password user through the local Supabase Auth admin API on
   port `9999`. The request is authenticated with a short-lived service-role
   JWT signed from `infra/local/.env`; the token is held only in the shell
   process and is never saved to the repository.
2. Insert the returned Supabase user UUID into the backend-owned
   `authentication_role_mappings` table with the `transport_management` role.

Run the following from the repository root after Docker and backend migrations
are ready. Replace the example email and password before running it. Do not use
the example password outside local development.

```powershell
$bootstrapEmail = "transport@example.test"
$bootstrapPassword = "replace-with-a-strong-local-password"

$localConfig = @{}
Get-Content infra/local/.env | ForEach-Object {
  if ($_ -match '^\s*([^#=]+)=(.*)$') {
    $localConfig[$matches[1].Trim()] = $matches[2].Trim().Trim('"').Trim("'")
  }
}

$env:UTS_SUPABASE_JWT_SIGNING_KEY = $localConfig['SUPABASE_JWT_SECRET']
$env:BOOTSTRAP_EMAIL = $bootstrapEmail
$env:BOOTSTRAP_PASSWORD = $bootstrapPassword

$bootstrapUser = @'
import json
import os
from datetime import UTC, datetime, timedelta

import httpx
import jwt

token = jwt.encode(
    {
        "aud": "authenticated",
        "exp": datetime.now(UTC) + timedelta(minutes=5),
        "iss": "supabase",
        "role": "service_role",
    },
    os.environ["UTS_SUPABASE_JWT_SIGNING_KEY"],
    algorithm="HS256",
)
response = httpx.post(
    "http://localhost:9999/admin/users",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "email": os.environ["BOOTSTRAP_EMAIL"],
        "password": os.environ["BOOTSTRAP_PASSWORD"],
        "email_confirm": True,
    },
    timeout=10,
)
response.raise_for_status()
user = response.json()
print(json.dumps({"id": user["id"], "email": user["email"]}))
'@ | python | ConvertFrom-Json

docker compose --env-file infra/local/.env -f infra/local/compose.yaml exec -T postgres psql -U uzair_transport -d uzair_transport -v ON_ERROR_STOP=1 -c "INSERT INTO authentication_role_mappings (supabase_user_id, role) VALUES ('$($bootstrapUser.id)', 'transport_management');"
```

The script confirms the email in local Supabase Auth and prints the returned
UUID. It does not print the password or the temporary service-role token.

If `UTS_SUPABASE_JWT_SIGNING_KEY` in `.env` differs from
`SUPABASE_JWT_SECRET` in `infra/local/.env`, update the local files so they
match before starting the backend. GoTrue signs login tokens with the latter,
and the backend must validate those tokens with the same key.

After the bootstrap mapping exists, Transport Management can create and
deactivate other privileged role mappings through `/admin/accounts`. Do not
create additional accounts by inserting passwords or sessions directly into the
database.

For reference, the role-mapping SQL used by the bootstrap is:

```sql
INSERT INTO authentication_role_mappings (supabase_user_id, role)
VALUES ('<Supabase user UUID>', 'transport_management');
```

Credentials are never stored in this repository.

## Run locally

Open three terminals after setup. The first terminal must have the virtual
environment active and the `.env` variables loaded:

```powershell
# Backend (repository root)
.\.venv\Scripts\Activate.ps1
Get-Content .env | ForEach-Object {
  if ($_ -match '^\s*([^#=]+)=(.*)$') {
    Set-Item -Path "Env:$($matches[1].Trim())" -Value $matches[2].Trim()
  }
}
python -m uvicorn src.application.main:app --app-dir backend --reload --port 8000 --limit-concurrency 500

# Public PWA (second terminal)
npm run dev --workspace @uzair/public-pwa

# Admin app (third terminal)
npm run dev --workspace @uzair/admin-web
```

When using an MSYS2-created virtual environment, replace the first backend
command with `. .\.venv\bin\Activate.ps1`.

The backend runs on `http://localhost:8000`, the public PWA on
`http://localhost:3000`, and the admin application on `http://localhost:3001`.
Check that the API is ready at `http://localhost:8000/health`.

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

Slice 0 and Slice 1 test coverage is implemented. Planned and executed acceptance
evidence is maintained in [docs/design/test-cases.md](docs/design/test-cases.md).

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

The portal does not include GPS/live tracking, payments, WhatsApp integration, an AI chatbot, IP-based feedback limiting, or a feedback status dashboard. Public clients never access PostgreSQL directly. The single Uvicorn worker is started with a hard 500-concurrency cap; requests beyond that cap receive Uvicorn's overload response. Production SMTP credentials and backup/recovery infrastructure remain release decisions and are intentionally not committed here.

# Implementation Plan

- **Version:** 1.6
- **Status:** S0, S1, S2, and S3 complete
- **Source of truth:** `PRD.md`, `architecture.md`, `AGENTS.md`, ADR-011, and ADR-014
- **History:** Git preserves every revision. A frozen copy of each accepted
  version is stored in `docs/plan-versions/`.

## 1. Implementation objective

Deliver Transport Service as a modular monolith: a public Next.js PWA,
a separate Next.js admin application, and a single-worker FastAPI backend
backed by PostgreSQL. The release supplies published schedules/current
departures, announcements and urgent banners, controlled transport publishing,
SMTP feedback, protected public API admission, and offline public access while
preserving the documented draft/publish and recovery rules.

## 2. Vertical slices

| Slice | Outcome | Primary modules |
|---|---|---|
| S0 — Foundation | Runnable local system with repeatable database and auth integration boundaries | Platform, Authentication |
| S1 — Published transport | Public users can read current departures and today’s schedule from published data only | Transport Data, Public PWA |
| S2 — Managed transport publishing | Authorized users create, validate, publish, retire, and recover atomic transport change sets | Transport Data, Audit, Authentication, Admin Web App |
| S3 — Announcements and urgent operations | Public announcements and online-only urgent banners have the defined direct-publish lifecycle | Announcement, Public PWA, Admin Web App |
| S4 — Feedback delivery | Public feedback is validated, delivered by SMTP, retried, and retained safely | Feedback |
| S5 — Public API overload protection | A production deployment edge protects the API and database from excess public-read traffic and fails visibly | Platform, Public PWA |
| S6 — Resilient PWA | Public data remains clearly labelled through fresh, stale, offline, and outage states | Public PWA |
| S7 — Verification and release readiness | Functional, security, performance, overload, and recovery evidence supports release acceptance | All modules |

## 3. Sequence and dependencies

```text
S0 Foundation
 ├── S1 Published transport ──┬── S3 Announcements ──┬── S6 Resilient PWA ──┐
 ├── S2 Managed publishing ──┤                     └── S5 Public API overload protection ─┤
 └── S4 Feedback             ┘                                                       └── S7 Verification
```

S0 is required before all implementation. S1 requires the published-read data
model. S2 requires S0 authentication and S1 transport primitives. S3 and S4
can proceed after S0/S1 boundaries exist. S5 requires a production hosting
decision and stable public-read endpoints from S1 and S3. S6 depends on stable
public APIs from S1 and S3. S7 spans every slice and is complete only after a
production hosting decision enables overload and RTO/RPO verification.

## 4. Tasks

### S0 — Foundation [HITL]

1. Propose the initial repository structure and obtain approval before creating
   implementation files, as required by `AGENTS.md`.
2. Establish FastAPI, raw asynchronous PostgreSQL access, SQL migrations,
   environment configuration, structured error handling, and OpenAPI.
3. Establish separate Next.js TypeScript public/admin applications with
   Tailwind and accessible headless components.
4. Configure local PostgreSQL and self-hosted Supabase Auth to share the
   approved PostgreSQL deployment without exposing database access to clients.
5. Implement email/password login integration, locally validated active JWTs,
   and the backend-owned role mapping. Manually bootstrap the first Transport
   Management account.
6. Restrict account-management endpoints to Transport Management; deactivation
   blocks fresh login while active JWTs remain usable to expiry.
7. Set up Pytest and Cypress test foundations and the single-worker in-process
   read-cache boundary.

### S1 — Published transport [AFK]

1. Model versioned routes, free-text origin/destination/direction, buses,
   assignments, recurring departures, date overrides, and published pointers.
2. Implement PKT service-date/current-departure calculations; surface every
   published Route–Bus assignment pair and “No further departures today” where
   required.
3. Support full-day overrides and partial overrides; partial matching uses
   Route, Bus, and time, while a time change is remove/add.
4. Create public REST endpoints that only return published records and never
   expose drafts.
5. Build the public current-departure and today-only schedule experience.
6. Test PKT boundaries, no-service overrides, current-departure selection,
   published-only reads, and incomplete/conflicting data display rules.

### S2 — Managed transport publishing [HITL]

1. Implement named change sets, draft creation/update, 30-day draft expiry,
   optimistic stale-change-set detection, and rebase workflow.
2. Implement warnings plus explicit “Publish anyway” confirmation for
   incomplete/conflicting schedules.
3. Publish complete change sets atomically: new versions, published pointers,
   synchronous cache invalidation, and one publication record containing
   publisher and publication time.
4. Implement retirement and physical deletion 30 days after retirement.
5. Implement 30-day whole-change-set recovery; prohibit recovery of drafts or
   announcements.
6. Build authorized admin views and tests for RBAC, optimistic concurrency,
   draft isolation, recovery, retention, and cache freshness.

### S3 — Announcements and urgent operations [HITL]

1. Implement direct announcement publication, PKT expiry, newest-first order,
   manual removal, and 30-day removed/expired-record retention.
2. Implement urgent announcements with a separate persistent banner; removal
   hides only the banner, while resolution records resolution and stops banner
   display.
3. Keep urgent and routine publications on one pipeline; ensure confirmed
   operational changes publish within one minute.
4. Do not create announcement-version, edit, or login/logout audit records.
5. Build public/admin experiences and lifecycle tests, including multiple
   banners and announcement-expiry/banner independence.

### S4 — Feedback delivery [AFK]

1. Build the anonymous feedback form with optional name/contact, hidden
   honeypot, and receipt/error UI.
2. Normalize case, outer whitespace, and repeated internal whitespace before
   the 10-minute database duplicate check; never use IP limiting.
3. Send accepted feedback by SMTP to the configured Transport Management
   mailbox. On initial failure, store it, show an error, and retry at 1, 5,
   and 30 minutes.
4. Return the neutral already-received response for a retry-pending duplicate;
   do not provide feedback status tracking.
5. Delete feedback after 30 days and test delivery, retry, duplicate, honeypot,
   anonymous, and retention behavior.

### S5 — Public API overload protection [HITL]

1. Select the production reverse proxy or load balancer and document its
   configuration outside the repository; do not commit provider credentials.
2. Route public and administrative API traffic through health checks for the
   single FastAPI worker. Configure finite connection, request, and idle
   timeouts, maximum request-body size, and a bounded pending-request queue.
3. Configure per-client admission limits only for unauthenticated public read
   endpoints. Exclude feedback from IP-based limiting and preserve its approved
   honeypot and duplicate-detection policy.
4. Set the backend PostgreSQL connection-pool ceiling below the verified safe
   database capacity. Add operational alerts for health-check failure, queue
   saturation, overload responses, worker saturation, and pool exhaustion.
5. Test prompt `429`/`503` overload rejection and the Public PWA outage and
   unavailable-first-use responses. Do not add a second FastAPI worker, shared
   cache, or edge API-response cache.

### S6 — Resilient PWA [HITL]

1. Implement Workbox with Cache Storage/IndexedDB and a single snapshot
   timestamp for cached public data and announcements.
2. Cache published transport data and announcements for 24 hours; never cache
   active urgent banners.
3. Display PKT last-successful-sync time and distinguish fresh, stale, offline,
   outage, and unavailable-first-use states.
4. Synchronize while the public application is open every minute, on
   reconnection, and by manual refresh; never advance the timestamp on failure.
5. Test browser behavior for cache expiry, refresh failure, reconnection, and
   public data isolation.

### S7 — Verification and release readiness [HITL]

1. Run formatter, linting, type checks, unit/integration tests, Cypress suites,
   build checks, and API-contract checks.
2. Measure publish-to-visible latency at 500 concurrent users and 2,000
   scheduled departures; at least 95% must complete within five seconds.
3. Verify urgent publication completes within one minute and public read paths
   remain unauthenticated.
4. Load-test the production edge and database pool at and above the approved
   baseline. Verify overload requests are rejected promptly without exhausting
   the FastAPI worker or PostgreSQL connections.
5. Select production hosting, backup, and recovery configuration, then run and
   record RTO <= 4 hours / RPO <= 1 hour recovery testing.
6. Evaluate every documented acceptance criterion; at least 95% must pass with
   no critical defects before release.

## 5. Acceptance criteria

- Public endpoints return published transport data only; drafts are never
  visible.
- Current departure uses PKT and identifies the next departure for every
  published Route–Bus assignment pair, or “No further departures today.”
- A named change set is published atomically, stale drafts are rebased, and
  recovery restores a whole published change set within 30 days.
- Transport publication records contain only publisher and publication time;
  no edit, announcement-version, or login/logout audit history is created.
- Only Transport Management manages accounts; both privileged roles are
  backend-authorized for documented transport and announcement operations.
- Announcements follow PKT expiry, urgent banners remain online-only, and
  banner removal/resolution behavior stays distinct.
- Feedback meets honeypot, normalized duplicate, SMTP retry, anonymous, and
  retention rules without status tracking or IP limiting.
- The production edge health-checks the backend, bounds public-read work before
  it reaches the API/database, and returns prompt overload responses while the
  PWA preserves its labelled outage/unavailable behavior.
- Workbox PWA behavior correctly labels and preserves the single snapshot
  timestamp through fresh/stale/offline/outage states.
- Verification meets the performance, urgent-publication, recovery, and
  release-acceptance thresholds in the PRD.

## 6. Progress / status

| Slice | Status | Evidence / next gate | Human Decision |
|---|---|---|---|
| S0 | Complete | Reviewed and pushed: FastAPI/auth/cache, local PostgreSQL/Supabase boundaries, separate Next.js clients, and Pytest/Cypress foundations; all current checks pass | Accept |
| S1 | Complete | Published-only PostgreSQL read model, PKT schedule/current-departure API, responsive public views, and automated verification are complete | Accept |
| S2 | Complete | Authorized change-set editing, validation/confirmation, atomic pointer + Audit publication writes, retention cleanup, recovery, and admin workflow complete; backend unit/API-contract and admin type/lint checks pass | Accept |
| S3 | Complete | Reviewed and pushed: direct PKT announcement publication, independent urgent-banner lifecycle, public/admin APIs and experiences; backend, type/lint, and Cypress checks passed | Accept |
| S4 | Not started | Depends on S0 SMTP configuration boundary | |
| S5 | Not started | ADR-014 requires a deployment edge, bounded admission controls, database-pool limits, monitoring, and overload testing | Select provider and capacity limits |
| S6 | Not started | Depends on stable public APIs | |
| S7 | Not started | Production hosting, overload-capacity, and RTO/RPO choices are deferred | |

## 7. Constraints

- Keep one modular-monolith backend; clients access only its API.
- Use PostgreSQL only as the relational system of record; no extra databases
  or deployable services without an approved architectural decision.
- Use one FastAPI worker while the cache is in-process; do not scale to
  multiple workers without selecting a shared-cache approach.
- Put a health-checked production deployment edge in front of the API. Bound
  public-read work before it reaches the worker/database and do not apply
  IP-based limits to feedback. Do not add edge API response caching without a
  reviewed synchronous-invalidation design.
- Use self-hosted Supabase Auth, backend-owned role mapping, and local active
  JWT validation. Do not build in-house credentials or sessions.
- Use PKT for service dates, current departures, timestamps, and announcement
  expiry.
- Exclude GPS/live tracking, payments, WhatsApp integration, AI chat, and
  feedback dashboards/status tracking.
- Production hosting, SMTP credentials/recipient value, and backup/recovery
  infrastructure are configuration/release prerequisites and must not be
  committed to Git.

## Plan versioning procedure

When this plan changes, update `plan.md`, copy its complete approved content
to `docs/plan-versions/plan-v<N>.md`, and commit both in the same Git commit.
Git history and the immutable per-version copies must agree.

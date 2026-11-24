# Test Cases and Release Evidence

## Test strategy

Use Pytest for domain, adapter, authorization, and API-contract checks. Use
Cypress for Public PWA and Admin Web App workflows. Use a deployment load tool
for the required publish-to-visible benchmark. Test data must be synthetic.
Planned cases define expected behavior; the verification record only claims
results from completed runs.

## Slice 1 - public transport information

| ID | Layer | Scenario | Expected result |
|---|---|---|---|
| TD-01 | Unit | 14:00 PKT with departures at 14:00 and 15:00 | The 14:00 departure is selected; comparison is inclusive. |
| TD-02 | Unit | All Route-Bus departures have passed | `no_further_departures_today` is returned. |
| TD-03 | Integration | Full-day no-service override | Base recurring departures are suppressed. |
| TD-04 | Integration | Partial Route-Bus-time override | Only the matching departure changes; a time change uses remove plus add. |
| TD-05 | API | Public read while a draft exists | Only the current published change set is returned. |
| TD-11 | Unit | UTC instant maps to a different PKT date | Service date uses `Asia/Karachi`, never server local time. |
| TD-12 | Unit | Request occurs exactly at a departure | That departure remains next-upcoming. |
| TD-13 | Unit | Published assignments include exhausted pairs | Every pair is represented; exhausted pairs have `no_further_departures_today`. |
| TD-14 | Unit | Partial override adds or removes one match | Only the matching entry changes. |
| TD-15 | API | Public departure and schedule reads | Both are unauthenticated, published-only, and return PKT ISO timestamps. |
| TD-16 | API | Assignment has no timetable rows | It remains in current departures as `no_further_departures_today`; no internal warning is exposed. |
| PW-08 | Cypress | Successful published-data response | Departures and schedule show route details, buses, and exhausted state without sign-in. |

## Slice 2 - shared draft, publication, authorization, and audit

| ID | Layer | Scenario | Expected result |
|---|---|---|---|
| TD-06 | API | Incomplete or conflicting draft | Save succeeds with warnings; publish needs explicit confirmation. |
| TD-07 | Integration | Concurrent stale draft operation | The stale operation conflicts; the shared draft is not silently overwritten. |
| TD-08 | Transaction | Successful publish or recovery | Pointer, immutable snapshot, and audit record commit together; cache invalidates after commit. |
| TD-09 | Transaction | Publish fails before commit | No public pointer or audit record becomes visible. |
| TD-10 | Retention | Permanent working draft lifecycle | Retention does not expire or delete the draft. |
| AU-01 | API | Missing or invalid privilege credentials | `401` or `403`; no mutation occurs. |
| AU-02 | API | Both privileged roles manage transport | Both roles can use the authorized transport workflow. |
| AU-03 | API | Designated administrator manages accounts | `403`; Transport Management alone manages accounts. |
| AU-04 | Integration | Deactivated account with valid JWT | New login is blocked; token remains valid until expiry. |
| AD-01 | Integration | Transport publication | Audit stores publisher and time only; records expire after 30 days. |
| AD-02 | Integration | Recover eligible publication | A whole published change set is recovered. |
| AD-03 | Security | Recover a draft or announcement | The request is rejected. |

## Slice 3 - announcements and persistent urgent banners

| ID | Layer | Scenario | Expected result |
|---|---|---|---|
| AN-01 | API/UI | PKT announcement expiry | It is hidden after expiry; record remains for 30 days. |
| AN-02 | API/UI | Urgent announcement | Direct-published announcement and separate persistent banner are created without operational-change or confirmation state. |
| AN-03 | API/UI | Remove urgent banner | Banner is hidden and remains unresolved. |
| AN-04 | API/UI | Resolve urgent banner | Banner is hidden and resolution state is retained. |
| AN-05 | Integration | Associated announcement expires | Banner remains until an authorized remove or resolve action. |
| AN-06 | API/UI | Title-only announcement | Message/body may be omitted and is returned as an empty string. |

## Slice 4 - feedback delivery and retention

| ID | Layer | Scenario | Expected result |
|---|---|---|---|
| FB-01 | API | Anonymous content, empty honeypot, SMTP success | Receipt returned. |
| FB-02 | API | Populated honeypot | Rejected without delivery. |
| FB-03 | API | Normalized duplicate within 10 minutes | Rejected, or neutral already-received while retry is pending. |
| FB-04 | API | Equivalent content outside 10 minutes | Accepted by duplicate rule. |
| FB-05 | Integration | Initial SMTP failure | Retained, error returned, retry due after one minute. |
| FB-06 | Integration | Repeated SMTP failures | Retries at 1, 5, and 30 minutes only; no later user notification. |
| FB-07 | Privacy | Schema and route review | No IP limiting or feedback status dashboard exists. |
| FB-08 | Unit | Duplicate exactly 10 minutes after receipt | Accepted because the window is the preceding 10 minutes. |
| FB-09 | API | Retry-pending normalized duplicate | Neutral response; no second record or SMTP send. |
| FB-10 | Unit | Later retry succeeds | Delivery is complete without browser notification or status endpoint. |
| FB-11 | Integration | Feedback older than 30 days | Cleanup removes it, including undelivered and exhausted records. |
| FB-12 | Cypress | Anonymous submission | Optional identity fields may be empty and receipt is shown. |
| FB-13 | Cypress | Immediate SMTP failure | Error is shown with no tracking or later-success notice. |

## Slice 5 - Public PWA cache, freshness, and accessibility

| ID | Layer | Scenario | Expected result |
|---|---|---|---|
| PW-01 | Cypress | Successful sync | PKT last-successful-sync is saved and fresh through five minutes. |
| PW-02 | Cypress | Failed refresh from cache | Timestamp is unchanged; data becomes stale after five minutes. |
| PW-03 | Cypress | Offline inside 24 hours | Cached content and offline warning appear; active banners are absent. |
| PW-04 | Cypress | Online backend outage | Cached content and service/data-outage warning appear. |
| PW-05 | Cypress | No cache and unavailable service | Unavailable state appears; no empty schedule is fabricated. |
| PW-06 | Cypress | Cache older than 24 hours | Offline content is unavailable. |
| PW-07 | Cypress | Browser reconnects | A sync is attempted; warnings clear only after success. |
| PW-09 | Cypress | First successful public sync | One complete cacheable snapshot is stored with one PKT timestamp. |
| PW-10 | Cypress | Cached snapshot older than five minutes | Original timestamp is retained and stale warning appears. |
| PW-11 | Cypress | Online API failure with valid cache | Cached content and outage warning appear; offline does not. |
| PW-12 | Cypress | Offline with valid cache | Cached content and original timestamp appear; network-only banners do not. |
| PW-13 | Cypress | First use or expired cache while offline/outage | Only unavailable state appears. |
| PW-14 | Cypress | Snapshot reaches exactly 24 hours | It is expired; younger snapshots remain available. |
| PW-15 | Cypress | Reconnect after offline use | Only successful full retrieval replaces data, advances time, and clears warnings. |
| PW-16 | Cypress | Manual refresh | Success replaces payloads; failure preserves data, time, and warning. A successful manual refresh disables the control for five seconds to prevent request spamming. |
| PW-17 | Cypress | App remains open for one minute | A sync is attempted every 60 seconds without advancing time on failure. |
| PW-18 | Cypress | Service-worker policy | Published transport and announcements cache for 24 hours; banners, privileged routes, and drafts do not. |
| UX-01 | Cypress/a11y | Mobile, keyboard, and semantic workflow | Core public and admin workflows are usable and accessible. |

## Slice 6 - release, performance, and operational validation

| ID | Layer | Scenario | Expected result |
|---|---|---|---|
| RV-01 | API contract | Release OpenAPI surface | Public reads and feedback remain unauthenticated; privileged operations retain authorization. |
| RV-02 | Unit | Approved runtime profile | One Uvicorn worker with `limit_concurrency=500`. |
| RV-03 | Unit/performance guard | 2,000 derived departures and 500 simultaneous readers | Every reader gets 2,000 results in under five seconds. This is a service guard, not the deployed benchmark. |
| RV-04 | Deployment benchmark | 500 concurrent users and 2,000 departures | At least 95% of publish-to-public-read measurements finish inside five seconds; record environment, command, timings, and p95. |
| RV-05 | Integration/timing | Confirmed urgent publication | Public announcement and banner are visible within one minute. |
| RV-06 | Deployment load | At and above 500 concurrent connections | Requests through cap work; excess requests get Uvicorn overload responses without process failure. |
| RV-07 | Review | Acceptance-criteria traceability | At least 95% of applicable criteria pass and no critical defect remains. |
| RV-08 | Deferred HITL | Production restore drill | After hosting, backup, and recovery are approved, demonstrate RTO <=4h and RPO <=1h. |

## Automated verification record

| Slice | Evidence | Latest recorded result |
|---|---|---|
| Slice 1 | `backend/tests/unit/test_transport_schedule.py`, `backend/tests/integration/test_public_transport_api.py`, `apps/public-pwa/tests/transport-home.cy.ts` | Passed in prior recorded runs; repeat for every release validation. |
| Slice 2 | `backend/tests/unit/test_transport_change_sets.py`, `backend/tests/integration/test_transport_change_set_api_contract.py`, `backend/tests/unit/test_authorization.py` | Passed in prior recorded runs; transaction evidence remains part of release validation. |
| Slice 3 | `backend/tests/unit/test_announcements.py`, `backend/tests/integration/test_announcement_api_contract.py`, `apps/admin-web/tests/announcements.cy.ts` | Passed after the announcement-state removal: 11 focused backend tests and 2 Cypress tests, 2026-11-24. |
| Slice 4 | `backend/tests/unit/test_feedback.py`, `backend/tests/integration/test_feedback_api_contract.py`, `apps/public-pwa/tests/feedback.cy.ts` | Passed in prior recorded runs. |
| Slice 5 | `apps/public-pwa/tests/resilience.cy.ts` | Passed in prior recorded runs; covers cache, outage, offline, reconnect, and banner exclusion. |
| Slice 6 | Architecture, runtime, performance, client checks, and Cypress suites | Full backend suite passed: 59 tests in 3.70 seconds, 2026-11-24. A previous performance-guard run took 7.78 seconds, so deployed p95 evidence remains required. |

## Required release commands

```powershell
# Backend, from backend/
..\.venv\bin\python.exe -m pytest
..\.venv\bin\python.exe -m flake8 src tests

# Clients, from repository root
npm run typecheck
npm run lint
$env:NEXT_DIST_DIR = ".next-verify"
npm run build
Remove-Item Env:NEXT_DIST_DIR

# Browser suites, after both applications are running
npm run test:e2e
```

## Deferred production evidence

RV-04, RV-05, RV-06 live timing and RV-08 recovery need an authorized
deployment environment and a selected production backup configuration. No
local result substitutes for that evidence.

## Performance follow-up for RV-03 and RV-04

The current deterministic RV-03 guard resolves the same 2,000-departure
snapshot independently for 500 readers in one Python event loop. It passed in
3.70 seconds on the latest run, but an earlier run on 2026-11-24 took 7.78
seconds. The following changes are compatible with the approved single-worker,
in-process-cache design and should be evaluated with a benchmark before
adoption.

1. Cache the immutable published snapshot in the application read cache and
   invalidate it synchronously after publish or recovery. This removes four
   PostgreSQL reads and object reconstruction from each public request.
2. Build immutable indexes when the published snapshot enters the cache:
   routes by code, assignments by route, weekly departures by weekday, and
   date overrides by service date. `daily_schedule` then avoids rebuilding
   these dictionaries and sets for every reader.
3. Cache the resolved daily schedule by `(published_change_set_id,
   service_date)` and invalidate it on transport publication or recovery.
   Date-specific overrides remain correct because the key includes service
   date and the snapshot is immutable.
4. Derive a next-departure index from the cached daily schedule. Bucket its
   refresh by PKT minute, or calculate only affected Route-Bus entries as time
   advances. The cache key must include the published change set and PKT date.
5. Measure the resulting HTTP path with a real 500-client benchmark. The
   existing RV-03 unit guard detects CPU regressions; it does not prove the
   NFR-01 p95 publish-to-visible requirement, which includes PostgreSQL,
   cache invalidation, and network handling.

Do not add workers or a shared cache as a performance shortcut. The accepted
architecture fixes one FastAPI worker and an in-process cache; either change
requires an approved architectural decision.

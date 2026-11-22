# Test Ideas and Acceptance Cases

## Strategy

Use Pytest for domain/repository/API integration; Cypress for public/admin workflows and PWA behavior; a load tool selected during S6 for the approved benchmark. Synthetic data only. These are planned cases, not passed-check evidence. S1 implementation evidence is recorded beside its cases after the relevant checks have run.

| ID | Layer | Scenario | Expected result |
|---|---|---|---|
| TD-01 | Unit | 14:00 PKT with departures 14:00/15:00 | 14:00 selected; comparison inclusive. |
| TD-02 | Unit | All Route–Bus departures passed | `No further departures today`. |
| TD-03 | Integration | Full-day no-service override | Base weekly departures suppressed. |
| TD-04 | Integration | Partial Route/Bus/time override | Only matching departure changes; time is remove/add. |
| TD-05 | API | Public read during drafts | Only active published change set returned. |
| TD-06 | API | Incomplete/conflicting draft | Warnings; save works; publish needs confirmation. |
| TD-07 | Integration | One of two same-base drafts publishes | Other receives stale conflict until rebase. |
| TD-08 | Transaction | Successful publish/recovery | Pointer, snapshot, and audit row commit together; cache invalidates after commit. |
| TD-09 | Transaction | Publish fails before commit | No public pointer/audit record leaks. |
| TD-10 | Retention | Draft reaches 30 days | Expires; cannot publish/recover. |
| TD-11 | Unit | A UTC instant crosses into a different PKT calendar date | Service-date selection uses `Asia/Karachi`, never the server local zone. |
| TD-12 | Unit | Exactly at a scheduled departure | That departure is next-upcoming (inclusive comparison). |
| TD-13 | Unit | Multiple published route–bus assignments, including one with no remaining time | Every assignment pair is represented; exhausted pairs use `no_further_departures_today`. |
| TD-14 | Unit | Partial override adds/removes a Route–Bus–time match | Only its matching entry changes; a time change is represented by remove plus add. |
| TD-15 | API | Public current-departures and schedule reads | Both are unauthenticated, only use the current published snapshot, and return PKT ISO timestamps. |
| TD-16 | API | Published data contains no timetable entries for an assignment | It remains visible in current departures as `no_further_departures_today`; no incomplete/conflict warning is exposed publicly. |
| PW-08 | Cypress | Public transport page with successful published-read responses | Current-departure cards and today-only schedule render route, bus, separately maintained route information, and the no-further state without a sign-in prompt. |
| AU-01 | API | Public/unauthenticated privileged request | `401`/`403`; no mutation. |
| AU-02 | API | Both privileged roles publish | Succeed within documented roles. |
| AU-03 | API | Designated admin manages account | `403`; Transport Management only. |
| AU-04 | Integration | Deactivated user with valid active JWT | New login blocked; token valid to expiry. |
| AD-01 | Integration | Transport publication | Audit has publisher/time only and 30-day expiry. |
| AD-02 | Integration | Recover eligible publication | Whole published set only. |
| AD-03 | Security | Recover draft/announcement | Rejected. |
| AN-01 | API/UI | PKT announcement expiry | Hidden after expiry; record kept 30 days. |
| AN-02 | API/UI | Urgent operational change | Announcement and separate banner exist. |
| AN-03 | API/UI | Remove banner | Hidden, unresolved. |
| AN-04 | API/UI | Resolve banner | Hidden, resolution retained. |
| AN-05 | Integration | Associated announcement expires | Banner remains until explicit action. |
| FB-01 | API | Anonymous, empty honeypot, SMTP success | Receipt returned. |
| FB-02 | API | Populated honeypot | Rejected without delivery. |
| FB-03 | API | Normalized duplicate within 10 minutes | Rejected/neutral already-received when retry pending. |
| FB-04 | API | Equivalent content outside 10 minutes | Accepted by duplicate rule. |
| FB-05 | Integration | Initial SMTP failure | Retained, error returned, retry at 1 minute. |
| FB-06 | Integration | Repeated SMTP failures | Only 1, 5, 30-minute retries; no later user notification. |
| FB-07 | Privacy | Schema/routes inspection | No IP limiting/status dashboard exists. |
| FB-08 | Unit | Duplicate exactly 10 minutes after the first receipt | Accepted: the duplicate window is the preceding 10 minutes, not an inclusive ten-minute boundary. |
| FB-09 | API | Retry-pending normalized duplicate | Neutral `already received` response; no second feedback record or SMTP send. |
| FB-10 | Unit | Retry later succeeds | Delivery is marked complete with no browser notification or status endpoint. |
| FB-11 | Integration | Feedback older than 30 days | Cleanup deletes the record, including undelivered/exhausted records. |
| FB-12 | Cypress | Anonymous form submission | Hidden honeypot remains empty, optional name/contact can be omitted, and a receipt is shown. |
| FB-13 | Cypress | Immediate SMTP failure | Error is shown immediately; the form offers neither tracking nor later-success notification. |
| PW-01 | Cypress | Successful sync | PKT timestamp saved; fresh through 5 minutes. |
| PW-02 | Cypress | Failed refresh from cache | Timestamp unchanged; stale at >5 min. |
| PW-03 | Cypress | Offline inside 24 hours | Cached data + offline warning; no cached active banners. |
| PW-04 | Cypress | Online backend outage | Cached data + outage, not offline, warning. |
| PW-05 | Cypress | No cache + unavailable service | Unavailable, no fabricated empty schedule. |
| PW-06 | Cypress | Cache >24 hours | Unavailable offline. |
| PW-07 | Cypress | Reconnection | Sync attempts; warnings clear only after success. |
| UX-01 | Cypress/a11y | Mobile/keyboard/semantic check | Core workflows usable and accessible. |

## S1 verification record

| ID | Automated evidence | Result |
|---|---|---|
| TD-01, TD-02, TD-03, TD-04, TD-11, TD-12, TD-13, TD-14 | `backend/tests/unit/test_transport_schedule.py` | Passed — 6 tests, 2026-11-20 |
| TD-05, TD-15, TD-16 | `backend/tests/integration/test_public_transport_api.py` | Passed — 2 tests, 2026-11-20 |
| PW-08 | `apps/public-pwa/tests/transport-home.cy.ts` | Passed — Cypress, 2026-11-20 |

## S2 implementation verification record

| ID | Automated evidence | Result |
|---|---|---|
| TD-06 | `backend/tests/unit/test_transport_change_sets.py` | Passed — warning detection and explicit publish confirmation, 2026-11-20 |
| TD-07 | `backend/tests/unit/test_transport_change_sets.py` | Passed — stale publication rejection and rebase baseline replacement, 2026-11-20 |
| TD-08 | `backend/tests/unit/test_transport_change_sets.py` | Passed at service boundary — pointer advance, publication-record invocation, cache invalidation, 2026-11-20 |
| AU-01, AU-02 | `backend/tests/integration/test_transport_change_set_api_contract.py` | Passed — privileged route contract is present; full HTTP authorization integration remains pending, 2026-11-20 |
| TD-06, TD-07, TD-10, AD-02, AD-03 | `backend/tests/unit/test_transport_change_sets.py` | Passed — optimistic draft save, expiry rejection, rebase, whole-published-snapshot recovery, and role gate, 2026-11-20 |
| API contract | `backend/tests/integration/test_transport_change_set_api_contract.py` | Passed — draft read/update, publication history, recovery, confirmation, and versioned-save schemas, 2026-11-20 |

Database transaction behavior is implemented in the PostgreSQL adapter: Audit
joins the Transport Data transaction for both normal publication and recovery.
The repository-level database integration remains part of Slice 6 release
verification alongside the required performance benchmark.

## S4 implementation verification record

| ID | Automated evidence | Result |
|---|---|---|
| FB-01, FB-02, FB-03, FB-04, FB-05, FB-06, FB-08, FB-09, FB-10, FB-11 | `backend/tests/unit/test_feedback.py` | Passed — 9 domain scenarios, 2026-11-22. |
| FB-01, FB-05, FB-09 | `backend/tests/integration/test_feedback_api_contract.py` | Passed — public OpenAPI contract and receipt/error/neutral response behavior, 2026-11-22. |
| FB-12, FB-13 | `apps/public-pwa/tests/feedback.cy.ts` | Passed — anonymous receipt and immediate delivery-error UI, 2026-11-22. |

## Release evidence

1. At 500 concurrent users and 2,000 scheduled departures, measure publish receipt to a subsequent public read; 95% must become visible within 5 seconds.
2. Confirmed urgent operational change reaches public availability within one minute.
3. After production hosting/backup selection, recovery evidence demonstrates RTO ≤4h and RPO ≤1h.
4. PRD release acceptance requires at least 95% passing criteria and no critical defects.

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
| PW-09 | Cypress | First successful public sync | Persist the complete published transport and announcement snapshot with one PKT last-successful-sync time; show it and no stale warning through exactly five minutes. |
| PW-10 | Cypress | Cached snapshot is older than five minutes | Retain its original PKT timestamp and show “Information may be outdated”; a failed reload or interval refresh does not change either. |
| PW-11 | Cypress | Online API failure with a valid cached snapshot | Show cached transport/announcements, a distinct service/data-outage warning, and (when applicable) the stale warning; never show offline. |
| PW-12 | Cypress | Offline with a valid cached snapshot | Show cached transport/announcements, offline and (when applicable) stale warnings, the original timestamp, and no urgent banner. |
| PW-13 | Cypress | First use or expired cache while offline/outage | Show unavailable state only; do not fabricate an empty or current-looking schedule. |
| PW-14 | Cypress | Snapshot reaches exactly 24 hours | Treat it as expired and unavailable for offline display; snapshots younger than 24 hours remain available. |
| PW-15 | Cypress | Browser reconnects after offline use | Attempt refresh immediately; only a successful full retrieval replaces the snapshot, advances its timestamp, clears warnings, and may render freshly fetched banners. |
| PW-16 | Cypress | Manual refresh | Attempt refresh; success replaces all cacheable public payloads and advances the timestamp, while failure retains the prior snapshot/time and warning. |
| PW-17 | Cypress | Application remains open for one minute | Perform a synchronization attempt every 60 seconds; failure must not advance the persisted timestamp or clear a warning. |
| PW-18 | Cypress | Service-worker cache policy | A Workbox service worker caches only public published transport and announcement API reads for at most 24 hours; it never caches `/public/urgent-banners`, privileged routes, or draft data. |
| UX-01 | Cypress/a11y | Mobile/keyboard/semantic check | Core workflows usable and accessible. |
| RV-01 | API contract | Release OpenAPI surface | All public reads and feedback remain unauthenticated; privileged transport, announcement, and account mutation paths remain protected by backend dependencies. |
| RV-02 | Unit | Approved server runtime profile | The executable backend launcher starts exactly one Uvicorn worker with `limit_concurrency=500`; neither setting is documentation-only. |
| RV-03 | Unit/performance guard | Baseline data shape: 2,000 derived scheduled departures and 500 simultaneous public readers | Every reader receives all 2,000 Route–Bus current-departure results within five seconds in the deterministic service-level guard. This detects algorithmic regressions; it is not the required deployed publish-to-visible measurement. |
| RV-04 | Deployment benchmark | 500 concurrent users and 2,000 scheduled departures | In the selected deployment, measure publish receipt to a subsequent public schedule/current-departure read. At least 95% of measurements complete within five seconds. Record environment, command, raw timings, p95, and result. |
| RV-05 | Integration/timing | Confirmed urgent operational publication | From confirmed timestamp to unauthenticated public announcement/banner visibility is at most one minute; record the observed elapsed time. |
| RV-06 | Deployment load | Uvicorn at exactly 500 and above 500 held concurrent connections | The single-worker process accepts work through the approved cap and requests above it receive Uvicorn's overload response without process failure; record command and status distribution. |
| RV-07 | Review | Acceptance-criteria traceability | Evaluate every applicable PRD acceptance criterion against automated/manual evidence; release passes only with at least 95% passing and no critical defect. ADR-011/012/013 supersede conflicting older PRD/ADR clauses. |
| RV-08 | Deferred HITL | Production restore drill | After human selection of production hosting, backup, and recovery configuration, run and record recovery evidence showing RTO <= 4 hours and RPO <= 1 hour. This case is intentionally not runnable locally. |

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

## S5 implementation verification record

| ID | Automated evidence | Result |
|---|---|---|
| PW-01, PW-02, PW-04, PW-05, PW-07, PW-09, PW-10, PW-11, PW-13, PW-15, PW-16, PW-17 | `apps/public-pwa/tests/resilience.cy.ts` | Passed — one successful PKT snapshot timestamp; failed refresh and one-minute retry retain cache/timestamp; outage, unavailable-first-use, manual refresh, and reconnect behaviors, 2026-11-23. |
| PW-03, PW-12 | `apps/public-pwa/tests/resilience.cy.ts` | Passed — offline state keeps the published snapshot and removes online-only urgent banners, 2026-11-23. |
| PW-06, PW-14 | `apps/public-pwa/tests/resilience.cy.ts` | Passed — exactly five minutes remains fresh and a snapshot is expired at exactly 24 hours, 2026-11-23. |
| PW-18 | `apps/public-pwa/public/sw.js`, `apps/public-pwa/src/lib/public-data.ts` | Implemented — Workbox matches only cacheable public transport/announcement reads; snapshot storage writes no urgent-banner data, 2026-11-23. |

## S6 implementation verification record

| ID / check | Automated evidence | Result |
|---|---|---|
| RV-01 | `backend/tests/integration/*_api_contract.py` and `backend/tests/architecture/test_module_boundaries.py` | Passed — 58 backend tests total, including public/privileged contract and module-boundary checks, 2026-11-24. |
| RV-02, RV-06 configuration | `backend/src/infrastructure/runtime/server.py`, `backend/tests/unit/test_runtime_profile.py` | Passed — executable launcher fixes Uvicorn at one worker and `limit_concurrency=500`; deployed at/above-cap response testing remains deployment evidence. |
| RV-03 | `backend/tests/unit/test_release_performance.py` | Passed — 2,000 derived departures for 500 concurrent service-level readers completed below five seconds, 2026-11-24. |
| PW-12 / offline-banner regression | `apps/public-pwa/tests/resilience.cy.ts` | Passed — manual offline refresh removes active network-only banners while preserving the valid snapshot, 2026-11-24. |
| Public/admin browser workflows | `npm run test:e2e` | Passed — 23 Cypress scenarios (15 public, 8 admin), 2026-11-24. |
| Backend lint | `python -m flake8 src tests` from `backend/` | Passed, 2026-11-24. |
| Client type/lint/build | `npm run typecheck`, `npm run lint`, `NEXT_DIST_DIR=.next-verify npm run build` | Passed, 2026-11-24. The alternate generated-output directory avoided a pre-existing OneDrive `.next` reparse-point error. |
| RV-04, RV-05, RV-06 live timing | Production/deployment environment | Deferred — needs the later hosting decision and an authorized deployed environment; no result is claimed. |
| RV-08 | Production restore drill | Deferred by approved scope — select production hosting, backup, and recovery configuration, then run and record RTO <= 4 hours / RPO <= 1 hour testing. |

## Release evidence

1. At 500 concurrent users and 2,000 scheduled departures, measure publish receipt to a subsequent public read; 95% must become visible within 5 seconds.
2. Confirmed urgent operational change reaches public availability within one minute.
3. After production hosting/backup selection, recovery evidence demonstrates RTO ≤4h and RPO ≤1h.
4. PRD release acceptance requires at least 95% passing criteria and no critical defects.

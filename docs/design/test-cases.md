# Test Cases

Executed 26 November 2026 (PKT). Each row records committed tests with the same result; where a spec has different outcomes, its cases are recorded separately.

| **Slice / Requirement** | **Test Type** | **Input / Condition** | **Expected Result** | **Actual Result** | **Pass / Fail** |
| ----------------------- | ------------- | --------------------- | ------------------- | ----------------- | --------------- |
| S0 - Configuration (`test_configuration.py`, 3 tests) | Basic functional testing | Safe defaults and local JWT configuration; non-PostgreSQL URL. | Valid settings are accepted; invalid database URL is rejected. | All 3 tests passed. | Pass |
| S0 - Module boundary (`test_module_boundaries.py`) | Basic functional testing | Inspect backend module directories. | Audit, feedback, reporting, announcement, authentication, and transport-data modules exist. | Passed. | Pass |
| S0 - JWT (`test_jwt_verifier.py`, 2 tests) | Negative testing | Verify correctly and incorrectly audience-scoped locally signed tokens. | Correct audience is accepted; another audience is rejected. | Both tests passed. | Pass |
| S1 / FR-01--FR-03 (`test_transport_schedule.py`, 7 tests) | Boundary Value Analysis (BVA) | PKT date conversion; weekly schedules; assignments; overrides; equal-time and exhausted departures. | PKT schedule and next-departure rules are applied, including boundary and no-service cases. | All 7 tests passed. | Pass |
| S1 / FR-01, FR-14a (`test_public_transport_api.py`, 2 tests) | Negative testing | Read public endpoints while a draft exists. | Public reads are unauthenticated and use published snapshot data only. | Both tests passed. | Pass |
| S1 UI / FR-01--FR-03 (`transport-home.cy.ts`) | Basic functional testing | Display public current departures and published daily schedule. | Route, buses, schedule, and exhausted state show without login. | Passed. | Pass |
| S2 / FR-06 (`test_transport_change_sets.py`, 6 tests) | Negative testing | Create, save, compare, publish, and concurrently update the shared draft. | One permanent draft is serialised, persists, warns on incomplete data, and prevents silent overwrite. | All 6 tests passed. | Pass |
| S2 / FR-03, FR-06 (`test_transport_change_set_api_contract.py`, 2 tests) | Boundary Value Analysis (BVA) | Inspect draft routes, weekday range, and fixed direction values. | Single-draft API, weekdays 1--7, and directions are documented. | Both tests passed. | Pass |
| S2 / FR-14a (`test_authorization.py`, 3 tests) | Negative testing | Account-management requests from Transport Management, administrator, and deactivated account. | Only Transport Management is authorized; prohibited/deactivated access is denied. | All 3 tests passed. | Pass |
| S2 / FR-14a (`test_session_policy.py`, 4 tests) | Equivalence Partitioning (EP) | Active/deactivated mappings and tokens issued before/after deactivation. | Active login works; new deactivated login/token fails; prior token remains valid until expiry. | All 4 tests passed. | Pass |
| S2 / Authentication (`test_authentication_api_contract.py`) | Basic functional testing | Inspect authentication OpenAPI contract. | Login, session, and account-management routes are exposed. | Passed. | Pass |
| S2 / Publication cache (`test_read_cache.py`, 2 tests) | Negative testing | Read before invalidation and after cache clear. | Cache serves until invalidated and is never a source of truth after clear. | Both tests passed. | Pass |
| S2 UI / FR-14a (`login.cy.ts`, 6 tests) | Basic functional testing | Sign-in boundary; history; shared-draft expand/collapse; save conflict; disabled publish. | Privileged UI presents correct draft, history, and error/disabled states. | All 6 tests passed. | Pass |
| S3 / FR-04--FR-08 (`test_announcements.py`, 8 tests) | Equivalence Partitioning (EP) | Routine/urgent publication, expiry, remove/resolve, edit, PKT expiry, and title-only message. | Lifecycle and banner state remain distinct; public visibility follows requirements. | All 8 tests passed. | Pass |
| S3 / FR-04--FR-05 (`test_announcement_api_contract.py`, 3 tests) | Negative testing | Inspect contracts and request public data after expiry/removal. | Lifecycle routes are documented; omitted messages are accepted; hidden records are excluded. | All 3 tests passed. | Pass |
| S3 UI / FR-04--FR-07 (`apps/admin-web/tests/announcements.cy.ts`, 2 tests) | Basic functional testing | Load lifecycle card and publish urgent announcement. | Admin view separates lifecycle; urgent announcement publishes directly. | Both tests passed. | Pass |
| S3 UI / FR-04--FR-05 (`apps/public-pwa/tests/announcements.cy.ts`) | Basic functional testing | Load announcements and active urgent banners. | Independent banners and newest-first announcements display. | Passed. | Pass |
| S4 / FR-09 (`test_feedback.py`, 9 tests) | Boundary Value Analysis (BVA) | Anonymous submission, normalized duplicate, exactly 10 minutes, honeypot, SMTP retries, and 30-day cleanup. | Valid feedback delivers; invalid/duplicate conditions follow the specified retention and retry rules. | All 9 tests passed. | Pass |
| S4 / FR-09 (`test_feedback_api_contract.py`, 2 tests) | Equivalence Partitioning (EP) | Inspect public form and receipt/error/pending-duplicate response contracts. | Public API documents each permitted response class. | Both tests passed. | Pass |
| S4 UI / FR-09 (`feedback.cy.ts`, 2 tests) | Negative testing | Submit anonymous feedback with SMTP success and failure responses. | Receipt appears on success; failure has no status-tracking option. | Both tests passed. | Pass |
| S5 UI / FR-01 (`home.cy.ts`) | Basic functional testing | Open the public PWA. | Public transport entry point displays without login. | Passed. | Pass |
| S5 / FR-10--FR-13 (`resilience.cy.ts`: freshness and cache age) | Boundary Value Analysis (BVA) | Evaluate exactly five minutes and exactly 24 hours. | Data remains fresh at five minutes; cache expires at 24 hours. | Passed. | Pass |
| S5 / FR-10 (`resilience.cy.ts`: successful snapshot) | Basic functional testing | Synchronize complete published data. | One PKT last-successful-sync timestamp is stored and displayed. | Passed. | Pass |
| S5 / FR-13 (`resilience.cy.ts`: HTTP cache bypass) | Basic functional testing | Synchronize published data through browser/service-worker path. | Request bypasses stale browser and service-worker responses. | Passed. | Pass |
| S5 / FR-10--FR-12 (`resilience.cy.ts`: failed online refresh) | Negative testing | Refresh fails while a valid snapshot exists. | Cached content and original timestamp remain with outage indication. | Passed. | Pass |
| S5 / FR-13 (`resilience.cy.ts`: pending refresh) | Basic functional testing | Delay manual refresh response. | Refresh shows disabled, busy state. | Passed. | Pass |
| S5 / FR-13 (`resilience.cy.ts`: refresh cooldown) | Boundary Value Analysis (BVA) | Advance clock to 4,999 ms then 5,000 ms after refresh. | Control enables only at the five-second boundary. | Passed. | Pass |
| S5 / FR-12 (`resilience.cy.ts`: first-use outage) | Negative testing | First request fails with no cache. | Unavailable state appears; no schedule is fabricated. | Passed. | Pass |
| S5 / FR-13 (`resilience.cy.ts`: banner exclusion) | Negative testing | Fail refresh after syncing a network-only urgent banner. | Banner is absent while cached announcement remains visible. | Passed after narrowing the assertion to the visible announcement title. | Pass |
| S5 / FR-13 (`resilience.cy.ts`: offline snapshot) | Negative testing | Go offline after a valid snapshot with network-only banner. | Offline warning and cached announcement show; urgent banner is absent. | Passed after narrowing the assertion to the visible announcement title. | Pass |
| S5 / FR-13 (`resilience.cy.ts`: reconnect) | Basic functional testing | Dispatch online event with successful new response. | Snapshot is replaced only after successful synchronization. | Passed. | Pass |
| S5 / FR-13 (`resilience.cy.ts`: periodic refresh) | Boundary Value Analysis (BVA) | Advance open-app clock one minute during failed refresh. | A sync is attempted and timestamp does not advance. | Passed. | Pass |
| S6 / Health (`test_health_api.py`, 2 tests) | Basic functional testing | Call health endpoint and retrieve OpenAPI document. | Ready response and API description are returned. | Both tests passed. | Pass |
| S6 / ADR-011 (`test_runtime_profile.py`) | Basic functional testing | Inspect runtime configuration. | One worker and hard 500-connection cap are configured. | Passed. | Pass |
| S6 / NFR-01 (`test_release_performance.py`) | Basic functional testing | Resolve 2,000 departures for 500 concurrent readers. | Deterministic workload remains within target. | Passed. | Pass |

## Execution record

| **Slice / Requirement** | **Test Type** | **Input / Condition** | **Expected Result** | **Actual Result** | **Pass / Fail** |
| ----------------------- | ------------- | --------------------- | ------------------- | ----------------- | --------------- |
| Backend suite | Basic functional testing | `python -m pytest` from `backend/`. | All backend automated tests pass. | 59 passed in 5.56 seconds. | Pass |
| Client static checks | Basic functional testing | `npm run typecheck` and `npm run lint`. | Type and lint checks pass for both clients. | Both commands passed. | Pass |
| Public Cypress suite | Basic functional testing | Run all five public-PWA specs locally. | All public tests pass. | 16 passed in 21 seconds. | Pass |
| Admin Cypress suite | Basic functional testing | Run both admin-web specs locally. | All admin tests pass. | 8 passed. | Pass |

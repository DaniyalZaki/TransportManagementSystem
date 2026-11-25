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

### Automated test inventory and slice association

The following inventory records every committed automated test file. Test names
in a row are the executable test cases in that file; the final column links
them to the planned cases above. A mapped case is evidence for that slice, not
a claim that an unrun deployment test has passed.

| Slice | Executable file and test cases | Planned case IDs |
|---|---|---|
| S0 | `test_configuration.py`: `test_settings_accepts_local_safe_defaults`, `test_settings_rejects_non_postgres_database_url`, `test_settings_accepts_the_local_jwt_verification_configuration` | S0 platform/configuration coverage |
| S0 | `test_jwt_verifier.py`: `test_verifier_accepts_a_locally_signed_supabase_token`, `test_verifier_rejects_a_token_for_another_audience`; `test_module_boundaries.py`: `test_backend_declares_the_required_logical_modules` | AU-01, RV-01 |
| S1 | `test_transport_schedule.py`: `test_pkt_service_date_uses_pakistan_timezone_not_server_timezone`, `test_daily_schedule_uses_weekly_departures_for_service_weekday`, `test_route_schedule_expands_to_every_assigned_bus`, `test_full_day_no_service_override_suppresses_weekly_schedule`, `test_partial_overrides_remove_and_add_exact_route_bus_time_matches`, `test_current_departure_selects_equal_time_and_then_no_further_departures`, `test_current_departures_include_assignment_without_a_timetable_entry` | TD-01--TD-04, TD-11--TD-14, TD-16 |
| S1 | `test_public_transport_api.py`: `test_public_transport_endpoints_are_documented_without_authentication`, `test_public_schedule_and_current_departures_use_only_the_injected_published_snapshot`; `transport-home.cy.ts`: `shows public current departures and today's published schedule` | TD-05, TD-15, PW-08 |
| S2 | `test_transport_change_sets.py`: `test_open_draft_creates_once_and_never_expires`, `test_save_persists_for_next_account_and_returns_execution_order`, `test_publish_warning_only_for_route_missing_schedule_and_preserves_draft`, `test_publish_does_not_require_a_rebase_when_the_current_pointer_changes`, `test_simultaneous_saves_are_processed_in_order_without_silent_overwrite`, `test_draft_reports_changes_only_when_it_differs_from_current_publication` | TD-06--TD-10 |
| S2 | `test_transport_change_set_api_contract.py`: `test_single_draft_routes_are_documented`, `test_schedule_contract_uses_weekdays_one_through_seven_and_fixed_directions`; `login.cy.ts`: `loads publication history through the authenticated admin API`, `expands the single shared draft from its initially visible control`, `keeps a save error visible in the open draft editor`, `disables Publish until a changed draft has been saved and when it matches published data`, `collapses and re-expands the open draft editor` | TD-06, TD-07, AD-01--AD-03 |
| S2 | `test_authorization.py`: `test_transport_management_is_authorized_for_account_management`, `test_designated_administrator_cannot_manage_accounts`, `test_deactivated_account_is_rejected_for_newly_validated_token`; `test_session_policy.py`: `test_active_mapping_allows_new_login`, `test_deactivation_rejects_a_new_login`, `test_token_issued_before_deactivation_remains_usable_until_expiry`, `test_token_issued_after_deactivation_is_rejected` | AU-01--AU-04 |
| S2 | `login.cy.ts`: `shows the privileged sign-in boundary`; `test_authentication_api_contract.py`: `test_openapi_exposes_login_session_and_transport_management_account_routes`; `test_read_cache.py`: `test_cache_returns_value_until_explicit_invalidation`, `test_cache_is_not_a_source_of_truth_after_clear` | AU-01--AU-03, TD-08 |
| S3 | `test_announcements.py`: `test_routine_announcements_publish_directly_and_are_newest_first`, `test_urgent_announcement_creates_a_separate_banner_without_operational_state`, `test_expiry_hides_announcement_but_does_not_hide_its_banner`, `test_remove_only_hides_banner_while_resolve_records_resolution`, `test_announcement_edit_replaces_content_without_creating_a_version`, `test_manual_removal_hides_an_announcement_without_touching_its_banner`, `test_naive_expiry_is_interpreted_as_pakistan_standard_time`, `test_announcement_message_can_be_empty` | AN-01--AN-06 |
| S3 | `test_announcement_api_contract.py`: `test_announcement_routes_document_public_reads_and_privileged_lifecycle`, `test_announcement_request_allows_an_omitted_message`, `test_public_announcement_response_never_exposes_removed_or_expired_records`; `announcements.cy.ts` (admin): `loads current announcements and banners into a separate lifecycle card`, `publishes an urgent announcement directly without operational state`; `announcements.cy.ts` (public): `shows announcements and independent active urgent banners newest first` | AN-01--AN-06, RV-05 |
| S4 | `test_feedback.py`: `test_anonymous_feedback_is_delivered_and_returns_a_receipt`, `test_normalization_collapses_case_outer_and_internal_whitespace_for_duplicate_checking`, `test_duplicate_at_exactly_ten_minutes_is_not_rejected`, `test_populated_honeypot_is_rejected_without_persistence_or_delivery`, `test_initial_smtp_failure_is_retained_and_schedules_first_retry`, `test_pending_duplicate_gets_neutral_already_received_response_without_a_second_send`, `test_failed_delivery_retries_at_one_five_and_thirty_minutes_then_stops`, `test_successful_retry_marks_delivered_without_a_user_notification_channel`, `test_retention_removes_feedback_after_thirty_days` | FB-01--FB-11 |
| S4 | `test_feedback_api_contract.py`: `test_feedback_route_is_public_and_documents_the_form_contract`, `test_feedback_route_returns_receipt_delivery_error_and_neutral_pending_duplicate`; `feedback.cy.ts`: `submits anonymous feedback and shows a receipt`, `shows an immediate delivery error without offering status tracking` | FB-01--FB-03, FB-09, FB-12, FB-13 |
| S5 | `resilience.cy.ts`: `keeps exactly-five-minute data fresh and expires a snapshot at exactly 24 hours`, `persists one PKT last-successful-sync timestamp for a complete successful snapshot`, `bypasses browser and service-worker response caches during synchronization`, `retains cached content and its original timestamp when an online refresh fails`, `shows a pending state while manual refresh is in progress`, `enforces a five-second cooldown after a manual refresh`, `shows unavailable instead of fabricated data on first use during an outage` | PW-01, PW-02, PW-05, PW-06, PW-09, PW-10, PW-11, PW-13, PW-14, PW-16 |
| S5 | `resilience.cy.ts`: `does not persist urgent banners with the offline snapshot`, `labels a valid snapshot offline and removes network-only urgent banners`, `reconnects by replacing cached data only after a successful synchronization`, `attempts automatic synchronization every minute without advancing the timestamp on failure`; `home.cy.ts`: `shows the public transport information entry point without authentication` | PW-03, PW-07, PW-12, PW-15, PW-17, PW-18, UX-01 |
| S6 | `test_health_api.py`: `test_health_endpoint_reports_ready`, `test_openapi_describes_the_api`; `test_runtime_profile.py`: `test_runtime_profile_uses_one_worker_and_hard_500_connection_cap`; `test_release_performance.py`: `test_baseline_read_workload_resolves_2000_departures_for_500_readers_within_target` | RV-01--RV-03 |

| Slice | Evidence | Latest recorded result |
|---|---|---|
| Slice 1 | `backend/tests/unit/test_transport_schedule.py`, `backend/tests/integration/test_public_transport_api.py`, `apps/public-pwa/tests/transport-home.cy.ts` | Passed in prior recorded runs; repeat for every release validation. |
| Slice 2 | `backend/tests/unit/test_transport_change_sets.py`, `backend/tests/integration/test_transport_change_set_api_contract.py`, `backend/tests/unit/test_authorization.py` | Passed in prior recorded runs; transaction evidence remains part of release validation. |
| Slice 3 | `backend/tests/unit/test_announcements.py`, `backend/tests/integration/test_announcement_api_contract.py`, `apps/admin-web/tests/announcements.cy.ts` | Passed after the announcement-state removal: 11 focused backend tests and 2 Cypress tests, 2026-11-24. |
| Slice 4 | `backend/tests/unit/test_feedback.py`, `backend/tests/integration/test_feedback_api_contract.py`, `apps/public-pwa/tests/feedback.cy.ts` | Passed in prior recorded runs. |
| Slice 5 | `apps/public-pwa/tests/resilience.cy.ts` | Passed in prior recorded runs; covers cache, outage, offline, reconnect, and banner exclusion. |
| Slice 6 | Architecture, runtime, performance, client checks, and Cypress suites | Full backend suite passed: 59 tests in 7.00 seconds, 2026-11-25. A previous performance-guard run took 7.78 seconds, so deployed p95 evidence remains required. |

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
7.00 seconds for the full-suite run on 2026-11-25, and an earlier isolated run
on 2026-11-24 took 7.78 seconds. The following changes are compatible with the approved single-worker,
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

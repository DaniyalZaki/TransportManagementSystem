# Test Ideas and Acceptance Cases

## Strategy

Use Pytest for domain/repository/API integration; Cypress for public/admin workflows and PWA behavior; a load tool selected during S6 for the approved benchmark. Synthetic data only. These are planned cases, not passed-check evidence.

| ID | Layer | Scenario | Expected result |
|---|---|---|---|
| TD-01 | Unit | 14:00 PKT with departures 14:00/15:00 | 14:00 selected; comparison inclusive. |
| TD-02 | Unit | All Route–Bus departures passed | `No further departures today`. |
| TD-03 | Integration | Full-day no-service override | Base weekly departures suppressed. |
| TD-04 | Integration | Partial Route/Bus/time override | Only matching departure changes; time is remove/add. |
| TD-05 | API | Public read during drafts | Only active published change set returned. |
| TD-06 | API | Incomplete/conflicting draft | Warnings; save works; publish needs confirmation. |
| TD-07 | Integration | One of two same-base drafts publishes | Other receives stale conflict until rebase. |
| TD-08 | Transaction | Successful publish | Pointer, snapshot, audit row, cache invalidation are atomic. |
| TD-09 | Transaction | Publish fails before commit | No public pointer/audit record leaks. |
| TD-10 | Retention | Draft reaches 30 days | Expires; cannot publish/recover. |
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
| PW-01 | Cypress | Successful sync | PKT timestamp saved; fresh through 5 minutes. |
| PW-02 | Cypress | Failed refresh from cache | Timestamp unchanged; stale at >5 min. |
| PW-03 | Cypress | Offline inside 24 hours | Cached data + offline warning; no cached active banners. |
| PW-04 | Cypress | Online backend outage | Cached data + outage, not offline, warning. |
| PW-05 | Cypress | No cache + unavailable service | Unavailable, no fabricated empty schedule. |
| PW-06 | Cypress | Cache >24 hours | Unavailable offline. |
| PW-07 | Cypress | Reconnection | Sync attempts; warnings clear only after success. |
| UX-01 | Cypress/a11y | Mobile/keyboard/semantic check | Core workflows usable and accessible. |

## Release evidence

1. At 500 concurrent users and 2,000 scheduled departures, measure publish receipt to a subsequent public read; 95% must become visible within 5 seconds.
2. Confirmed urgent operational change reaches public availability within one minute.
3. After production hosting/backup selection, recovery evidence demonstrates RTO ≤4h and RPO ≤1h.
4. PRD release acceptance requires at least 95% passing criteria and no critical defects.

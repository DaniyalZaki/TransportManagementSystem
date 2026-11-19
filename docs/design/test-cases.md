# Test Ideas and Acceptance Cases

Use Pytest for domain/repository/API integration, Cypress for public/admin/PWA workflows, and a selected load tool for release performance evidence. These are planned cases, not passed-check evidence.

| Area | Cases |
|---|---|
| Transport | PKT boundary inclusive current departure; no-more-today; weekly/full-day/partial override; drafts never public; stale base/rebase; warnings plus explicit publish confirmation; atomic pointer/audit/cache behavior; 30-day expiry. |
| Authorization/audit | Unauthenticated/unauthorized writes fail; both privileged roles operate where allowed; accounts are Transport Management only; deactivated new login blocked while valid active JWT lasts to expiry; audit has publisher/time only; recovery excludes drafts/announcements. |
| Announcement | PKT expiry and retention; urgent item creates announcement plus banner; remove is not resolve; expired announcement does not end banner; newest-first banners. |
| Feedback | Anonymous success; populated honeypot rejected; normalized duplicates rejected within 10 minutes; outside window accepted; initial SMTP failure persists/retries at 1/5/30 minutes; no IP/status dashboard. |
| PWA | Fresh through 5 minutes; failed refresh preserves timestamp; 24-hour offline cache without banners; online outage distinct from offline; unavailable first use; expiry/reconnect. |
| UX | Mobile viewport, keyboard, semantic/accessibility checks. |

Release evidence: at 500 concurrent users and 2,000 departures, 95% of publish-to-visible reads must be within 5 seconds; confirmed urgent changes within 1 minute; selected production recovery proves RTO ≤4h and RPO ≤1h; PRD acceptance requires 95% passing with no critical defects.

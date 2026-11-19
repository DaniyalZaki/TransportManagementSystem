# API Contracts

## Status
Proposed REST contract derived from PRD, architecture, plan, and ADR-011. It does not supersede them. Writes require a locally validated Supabase JWT and backend RBAC. Public reads and feedback are unauthenticated.

## Public endpoints
| Method/path | Outcome |
|---|---|
| GET /api/v1/public/transport/current-departures?service_date=YYYY-MM-DD | Published next departure per Route–Bus group, or `no_further_departures_today`; PKT. |
| GET /api/v1/public/transport/schedule?service_date=YYYY-MM-DD | Published schedule after override resolution. |
| GET /api/v1/public/transport/routes | Published route metadata. |
| GET /api/v1/public/announcements | Active nonexpired/nonremoved announcements, newest first. |
| GET /api/v1/public/urgent-banners | Active banners, newest first; never offline cached. |
| POST /api/v1/public/feedback | Anonymous/identified feedback; honeypot and normalized duplicate checks. |

Current departures never imply GPS location. Feedback has optional name/contact and a hidden `website` honeypot. Duplicate comparison lowercases, trims, and collapses repeated internal whitespace for the prior 10 minutes. No IP limiting is used.

## Privileged endpoints
| Method/path | Outcome |
|---|---|
| POST, GET, PATCH /api/v1/admin/transport/change-sets | Create/read/save named drafts. |
| POST /{id}/validate, /{id}/rebase, /{id}/publish | Validate warnings, rebase stale draft, atomically publish. |
| GET /api/v1/admin/transport/publications | 30-day publisher/time-only history. |
| POST /api/v1/admin/transport/publications/{id}/recover | Whole published change-set recovery only. |
| POST/PATCH /api/v1/admin/announcements | Direct announcement publication/edit; no version history. |
| POST /api/v1/admin/urgent-banners and /{id}/remove or /{id}/resolve | Separate persistent-banner lifecycle. |
| GET/POST/PATCH /api/v1/admin/accounts | Transport Management only. |

A publish request carries `expected_base_published_change_set_id` and `publish_anyway`; a stale base returns 409 and must rebase. Successful publication writes one audit record and synchronously invalidates cache. Removal of a banner does not resolve it; banner expiry is independent of announcement expiry.

## Error envelope
```json
{"error":{"code":"stale_change_set","message":"Rebase before publishing.","details":[]}}
```
Codes include `unauthenticated`, `forbidden`, `validation_failed`, `stale_change_set`, `draft_expired`, `duplicate_feedback`, `honeypot_rejected`, and `service_unavailable`.

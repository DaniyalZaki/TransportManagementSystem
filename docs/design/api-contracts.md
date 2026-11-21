# API Contracts

## Status and conventions

This proposed REST contract is derived from `PRD.md`, `architecture.md`, `plan.md`, and ADR-011. It records an implementation target; it does not supersede those sources. All write endpoints require a locally validated Supabase JWT and backend RBAC. Public read and feedback endpoints are unauthenticated.

- Base path: `/api/v1`; JSON uses `snake_case`; timestamps are RFC 3339 UTC instants rendered by clients in PKT.
- `401` means missing/invalid authentication; `403` means authenticated but unauthorized; `409` is stale/duplicate conflict; `422` is input or business-rule validation failure.
- Public transport responses contain only the active published change set. A cache is never a source of truth.

## Public contracts

| Method and path | Purpose | Success |
|---|---|---|
| `GET /public/transport/current-departures?service_date=YYYY-MM-DD` | Next published departure per Route–Bus pair for a PKT service date; defaults to today. | `200 CurrentDeparturesResponse` |
| `GET /public/transport/schedule?service_date=YYYY-MM-DD` | Published daily schedule after date override resolution. | `200 ScheduleResponse` |
| `GET /public/transport/routes` | Published route metadata. | `200 Route[]` |
| `GET /public/announcements` | Active nonexpired/nonremoved announcements, newest first. | `200 Announcement[]` |
| `GET /public/urgent-banners` | Active urgent banners, newest first; not offline-cacheable. | `200 UrgentBanner[]` |
| `POST /public/feedback` | Submit anonymous or identified feedback. | `201 FeedbackReceipt`; `202` on queued retry |

`CurrentDeparturesResponse` has an item for every published Route–Bus grouping. Each item is either `status: "scheduled"` with a departure or `status: "no_further_departures_today"`; it never implies GPS location or motion.

```json
{
  "service_date": "2026-11-19",
  "departures": [{"route_id":"R-01","bus_identifier":"C-12","status":"scheduled","scheduled_departure_at":"2026-11-19T14:30:00+05:00"}],
  "published_at": "2026-11-19T08:00:00Z"
}
```

`ScheduleResponse` includes `service_date`, `service_status` (`operating` or `no_service`), `entries`, and `published_at`. Each entry contains a route ID, separately maintained origin/destination and `RETURN`/`PICK-UP` direction, every assigned bus identifier in `bus_identifiers`, and a PKT scheduled departure. Draft `weekly_departures` use weekday 1–7, Route, and departure time only; the backend derives buses from assignments.

```json
// POST /public/feedback
{"content":"The afternoon pickup sign needs clarity.","name":"Optional","contact":"Optional","website":""}
```

`website` is the hidden honeypot; a nonempty value is rejected. Content is lowercased, outer whitespace trimmed, and repeated internal whitespace collapsed before comparing the prior 10 minutes. No IP-based limit is applied. A retry-pending duplicate receives a neutral `200 {"status":"already_received"}` response.

## Privileged transport contracts

Both privileged roles may manage transport data; only `transport_management` may manage accounts.

| Method and path | Purpose | Rules |
|---|---|---|
| `POST /admin/transport/change-sets` | Create named draft. | Starts at current published baseline. |
| `GET/PATCH /admin/transport/change-sets/{id}` | Read/save draft routes, buses, assignments, schedules, overrides. | Routes accept only `RETURN` or `PICK-UP`; schedules use weekday 1–7, Route, and time and derive all buses from assignments. Carries `base_published_change_set_id`; never public. |
| `GET /admin/transport/change-sets?query=` | Search active draft change sets by name. | Returns matching drafts only; opening a result loads its private snapshot. |
| `POST /admin/transport/change-sets/{id}/validate` | Calculate incomplete/conflict warnings. | Warnings do not block publication. |
| `POST /admin/transport/change-sets/{id}/rebase` | Rebase stale draft. | Required before stale publish. |
| `POST /admin/transport/change-sets/{id}/publish` | Atomically publish. | Explicit `publish_anyway` needed with warnings; one audit record + synchronous cache invalidation. |
| `GET /admin/transport/publications` | List recent publications. | Publisher/time only; 30-day window. |
| `POST /admin/transport/publications/{id}/recover` | Recover eligible published set. | Whole change set only; never draft/announcement. |

Publish request: `{"expected_base_published_change_set_id":"cs_01","publish_anyway":false}`. A changed base returns `409 stale_change_set`; success returns the new published change-set ID and publication time.

### Slice 2 delivery

Slice 2 exposes authenticated draft create/read/update, validation, rebase,
publication history, direct whole-change-set recovery, and publication
endpoints. A draft update contains the complete snapshot and its
`expected_version`; a stale write returns `409`. Publication and recovery write
the current pointer and Audit publication record in one PostgreSQL transaction,
then invalidate the single-worker read cache synchronously. The hourly
single-worker lifecycle job expires drafts and physically deletes retired
published snapshots after their respective 30-day periods.

## Announcements, banners, and accounts

| Method and path | Purpose |
|---|---|
| `POST/PATCH /admin/announcements[/{id}]` | Directly publish/edit announcement; `expires_at_pkt` is supplied or null for manual removal. No version history. |
| `POST /admin/announcements/{id}/remove` | Hide announcement. |
| `POST /admin/announcements/{id}/confirm-operational-change` | Confirm operational change before publication. |
| `POST /admin/urgent-banners` | Create separate persistent banner linked to urgent announcement. |
| `POST /admin/urgent-banners/{id}/remove` | Hide banner without resolving it. |
| `POST /admin/urgent-banners/{id}/resolve` | Mark banner resolved and stop public display. |
| `GET /admin/me` | Return current privileged user and backend-mapped role. |
| `GET/POST /admin/accounts`, `PATCH /admin/accounts/{supabase_user_id}` | Transport Management only: role mappings/activation. |

An urgent operational change is both an announcement and independent banner. The banner remains active if its announcement expires, until an authorized user removes or resolves it. Deactivation blocks new login but does not revoke an otherwise valid active token.

## Error envelope

```json
{"error":{"code":"duplicate_feedback","message":"An equivalent submission was received recently.","details":[{"field":"content","reason":"duplicate_within_10_minutes"}]}}
```

Stable codes include `unauthenticated`, `forbidden`, `validation_failed`, `stale_change_set`, `draft_expired`, `duplicate_feedback`, `honeypot_rejected`, `resource_not_found`, and `service_unavailable`.

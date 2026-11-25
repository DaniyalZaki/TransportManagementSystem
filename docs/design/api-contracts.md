# API Contracts

## Status and conventions

This implemented REST contract is derived from `PRD.md`, `architecture.md`, ADR-011, ADR-012, and ADR-013. It describes the current FastAPI surface; the PRD and accepted ADRs remain authoritative. All write endpoints require a locally validated Supabase JWT and backend RBAC. Public read and feedback endpoints are unauthenticated.

- Base path: `/api/v1`; JSON uses `snake_case`; timestamps are RFC 3339 UTC instants rendered by clients in PKT.
- `401` means missing/invalid authentication; `403` means authenticated but unauthorized; `409` is stale/duplicate conflict; `422` is input or business-rule validation failure.
- Public transport responses contain only the active published change set. A cache is never a source of truth.

## Public contracts

| Method and path | Purpose | Success |
|---|---|---|
| `GET /public/transport/current-departures?service_date=YYYY-MM-DD` | Next published departure per Route–Bus pair for a PKT service date; defaults to today. | `200 CurrentDeparturesResponse` |
| `GET /public/transport/schedule?service_date=YYYY-MM-DD` | Published daily schedule after date override resolution. | `200 ScheduleResponse` |
| `GET /public/announcements` | Active nonexpired/nonremoved announcements, newest first. | `200 Announcement[]` |
| `GET /public/urgent-banners` | Active urgent banners, newest first; not offline-cacheable. | `200 UrgentBanner[]` |
| `POST /public/feedback` | Submit anonymous or identified feedback. | `201 FeedbackReceipt`; `503` when initial SMTP delivery fails; `202` for a retry-pending duplicate |

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
{"content":"The afternoon pickup sign needs clarity.","name":"Optional","contact":"Optional","honeypot":""}
```

`honeypot` is the hidden form field; a nonempty value is rejected. Content is lowercased, outer whitespace trimmed, and repeated internal whitespace collapsed before comparing the prior 10 minutes. No IP-based limit is applied. A retry-pending duplicate receives a neutral `202 {"message":"Feedback was already received."}` response.

## Privileged transport contracts

Both privileged roles may manage transport data; only `transport_management` may manage accounts.

| Method and path | Purpose | Rules |
|---|---|---|
| `GET /admin/transport/draft` | Open the permanent shared draft. | Creates it from the published baseline only if it does not yet exist. |
| `PATCH /admin/transport/draft` | Save routes, buses, assignments, schedules, and overrides. | Complete snapshot with `expected_version`; serial execution returns `operation_order`. |
| `POST /admin/transport/draft/publish` | Atomically snapshot and publish the shared draft. | The draft remains editable; it may publish against the current pointer without a rebase. Explicit `publish_anyway` is needed only when a route has no recurring schedule entry. Returns `operation_order`. |
| `GET /admin/transport/publications` | List recent publications. | Publisher/time only; 30-day window. |
| `POST /admin/transport/publications/{change_set_id}/recover` | Recover eligible published set. | Whole change set only; never draft/announcement. |

Publish request: `{"publish_anyway":false}`. Publishing always snapshots the current permanent draft; a stale save still returns `409 stale_change_set`, so the user reloads before saving again. Success returns the new published change-set ID and publication time.

### Slice 2 delivery

Slice 2 exposes authenticated shared-draft open/update, publication history,
direct whole-change-set recovery, and publication endpoints. A draft update
contains the complete snapshot and its `expected_version`; a stale write
returns `409`. Save and publish serialize in the one worker and return a
temporary numeric `operation_order`. Publication snapshots the permanent draft,
writes the current pointer and Audit record in one PostgreSQL transaction, then
invalidates the read cache synchronously. Retired published snapshots are
physically deleted after 30 days; the working draft is never expired or deleted.

## Announcements, banners, and accounts

| Method and path | Purpose |
|---|---|
| `GET /admin/announcements/current` | List current announcements and active banners for the privileged lifecycle view. |
| `POST/PATCH /admin/announcements[/{id}]` | Directly publish/edit announcement; `expires_at` is a PKT-aware RFC 3339 instant or null for manual removal. No version history. |
| `POST /admin/announcements/{id}/remove` | Hide announcement. |
| `POST /admin/urgent-banners/{id}/remove` | Hide banner without resolving it. |
| `POST /admin/urgent-banners/{id}/resolve` | Mark banner resolved and stop public display. |
| `POST /auth/login` | Start a privileged Supabase email/password session after backend role checks. |
| `GET /auth/session` | Return the authenticated user's backend-mapped role. |
| `POST /admin/accounts`, `POST /admin/accounts/{supabase_user_id}/deactivate` | Transport Management only: create role mapping or deactivate an account. |

An urgent announcement is both an announcement and an independent banner. The
request has no operational-change or confirmation state, and the service does
not store either. `content` is optional and defaults to an empty string. The
banner remains active if its announcement expires, until an authorized user
removes or resolves it. Deactivation blocks new login but does not revoke an
otherwise valid active token.

## Error envelope

FastAPI returns its standard `detail` body. For example, a stale draft save
returns `409` with `detail.code` set to `stale_change_set` and the temporary
`operation_order`; a publish warning returns `422` with
`detail.code` set to `publish_confirmation_required`. The implementation does
not expose a `draft_expired` workflow because ADR-013 makes the shared draft
permanent.

# Data Model and Schema Design

## Status

This proposed PostgreSQL model preserves approved modular-monolith ownership boundaries. It is a design artifact, not a migration. Each module accesses only its own tables; cross-module use is through documented services. All business-date calculations use PKT (`Asia/Karachi`); persisted instants use `timestamptz`.

## Ownership map

| Module | Tables owned | Lifecycle |
|---|---|---|
| Authentication | `authentication_role_mappings` | One mapped role per Supabase user; deactivation blocks new login. |
| Transport Data | `transport_change_sets`, versioned `routes`, `buses`, `assignments`, `weekly_departures`, `date_overrides`, `published_change_sets` | One permanent working draft; retired published records delete at 30 days. |
| Audit | `transport_publications`, `recovery_requests` | Publication actor/time only; 30 days. |
| Announcement | `announcements`, `urgent_banners` | Removed/expired announcements retained 30 days; banner lifecycle independent. |
| Feedback | `feedback_submissions`, `feedback_delivery_attempts` | Normalized duplicate check, delivery retry state, 30 days. |
| Reporting | no owned write tables | Read-only module interfaces only. |

```mermaid
erDiagram
  TRANSPORT_CHANGE_SETS ||--o{ ROUTES : versions
  TRANSPORT_CHANGE_SETS ||--o{ BUSES : versions
  TRANSPORT_CHANGE_SETS ||--o{ ASSIGNMENTS : versions
  TRANSPORT_CHANGE_SETS ||--o{ WEEKLY_DEPARTURES : versions
  TRANSPORT_CHANGE_SETS ||--o{ DATE_OVERRIDES : versions
  TRANSPORT_CHANGE_SETS ||--|| PUBLISHED_CHANGE_SETS : becomes
  PUBLISHED_CHANGE_SETS ||--|| TRANSPORT_PUBLICATIONS : creates
  ANNOUNCEMENTS ||--o| URGENT_BANNERS : may_have
  FEEDBACK_SUBMISSIONS ||--o{ FEEDBACK_DELIVERY_ATTEMPTS : delivery
```

## Core tables

`authentication_role_mappings`: `supabase_user_id uuid primary key`, `role` constrained to `transport_management`/`designated_administrator`, `is_active`, `created_at`, `deactivated_at`. Supabase owns credentials and sessions, so neither passwords nor tokens belong here.

`transport_change_sets`: `id`, unique `name`, `status` (`draft`, `published`, `retired`, `expired`), `base_published_change_set_id`, `created_at`, `updated_at`, and `expires_at`. Exactly one row has `status = 'draft'`; it is the permanent working draft and its expiry is never processed. Publishing copies its snapshot into a new published row and advances its base pointer. Every versioned transport record has `id`, `change_set_id`, `version`, `status`, `created_at`, `retired_at`; public queries join only the current `published_change_sets` record and `status = 'published'`.

| Table | Domain columns | Key constraint |
|---|---|---|
| `routes` | `route_code`, `origin`, `destination`, `direction` (`RETURN` or `PICK-UP`) | unique `(change_set_id, route_code)` |
| `buses` | `bus_identifier` | unique `(change_set_id, bus_identifier)` |
| `assignments` | `route_id`, `bus_id` | assignment belongs to one change set |
| `weekly_departures` | ISO `weekday` (1–7), `local_departure_time`, `route_id` | one row per change set/weekday/route/time; it expands to all Route-to-bus assignments |
| `date_overrides` | `service_date`, `scope` (`full_day`, `partial`), `no_service`, route/bus/time references | partial match is Route + Bus + time; time changes are remove/add |
| `published_change_sets` | `change_set_id`, `published_at`, `is_current` | exactly one current pointer |

An incomplete entry is saveable but warned at publish when it lacks weekday, time, Route, or an assignment for that Route. Schedule rows do not carry a bus reference: each one applies to all buses assigned to its Route. Later published sets take precedence.

`transport_publications`: `id`, `published_change_set_id`, `publisher_supabase_user_id`, `published_at`, `expires_at`. It deliberately excludes edits, login/logout, announcements, and announcement version history. Recovery creates a new change set from an eligible whole published snapshot.

`announcements`: `id`, `title`, `body`, `category`, `is_operational_change`, `confirmed_at`, `published_by`, `published_at`, `expires_at`, `removed_at`, `retention_delete_at`, `updated_at`; no version table. `urgent_banners`: `id`, `announcement_id`, `message`, `created_by`, `created_at`, `removed_at`, `resolved_at`, `resolved_by`. Publicly active requires both end fields null; announcement expiry never changes this.

`feedback_submissions`: `id`, optional `name`/`contact`, `content`, `normalized_content`, `received_at`, `delivery_state` (`pending`, `delivered`, `retry_pending`, `exhausted`), `next_retry_at`, `expires_at`. `feedback_delivery_attempts`: `id`, `feedback_id`, `attempt_number`, `attempted_at`, `outcome`, `failure_reason`. Index `(normalized_content, received_at DESC)` supports 10-minute duplicate checks; index `(delivery_state, next_retry_at)` supports retry. No IP or status-tracking field exists.

## Transaction and lifecycle invariants

1. Publication checks/locks its base, writes new published versions and pointer, retires the prior pointer, writes exactly one publication record, and invalidates cache synchronously before success returns.
2. Public reads select only active published records; drafts cannot appear.
3. Recovery uses only a nonexpired whole published snapshot and normal publish rules; drafts and announcements are never recovered.
4. PKT date conversion precedes weekly/override resolution. Weekly rows use weekday 1–7 and expand to Route assignments. Full-day no-service wins; partial overrides match Route, Bus, time.
5. Retention jobs delete only records at their approved 30-day boundaries.

# Component Design

| Component | Responsibility |
|---|---|
| Public PWA | Published departures/schedules/announcements, feedback, cache state, online-only banners. |
| Admin Web App | Privileged draft, publish, recovery, announcement/banner, and account UI. |
| FastAPI API | Validation, auth boundary, routing, OpenAPI/errors. |
| Authentication | Local Supabase JWT validation and backend role mapping; no credentials/sessions. |
| Transport Data | Change sets, PKT schedule calculations, validation, published projections. |
| Announcement | Direct announcements and independent banner lifecycle. |
| Feedback | Honeypot, normalized duplicate check, SMTP/retries, retention. |
| Audit | Publication records and eligible published-set recovery. |
| Read cache | Single-worker hot-read cache; synchronous invalidation on publish. |

```text
Public shell
├─ SyncStatus
├─ UrgentBannerList (network only)
├─ CurrentDeparturesPanel
├─ DailyScheduleTable
├─ AnnouncementFeed
└─ FeedbackForm

Admin shell
├─ ChangeSetWorkspace
├─ PublicationHistoryAndRecovery
├─ AnnouncementEditor / UrgentBannerLifecyclePanel
└─ AccountManagement (Transport Management only)
```

The PWA repository uses Workbox, Cache Storage, and IndexedDB; refresh runs every minute only while open, plus reconnection/manual refresh, and never advances the timestamp on failure. Backend modules expose DTOs/services rather than querying each other’s private tables. Transport publication verifies role/base/warnings, promotes the snapshot and pointer, writes one audit record, then invalidates cache before success is returned.

# System Diagrams

## Container view
```mermaid
flowchart TB
  Public --> PWA[Public Next.js PWA]
  Staff --> Admin[Admin Next.js app]
  PWA --> API[FastAPI modular monolith]
  Admin --> API
  API --> Auth
  API --> Transport
  API --> Announcement
  API --> Feedback
  API --> Audit
  Auth --> Supabase[Self-hosted Supabase Auth]
  Transport --> DB[(PostgreSQL)]
  Announcement --> DB
  Feedback --> DB
  Audit --> DB
  Transport --> Cache[Single-worker in-process cache]
  PWA --> Local[Workbox + Cache Storage + IndexedDB]
```

## Publication sequence
```mermaid
sequenceDiagram
  participant A as Admin
  participant T as Transport API
  participant DB as PostgreSQL
  participant AU as Audit
  participant C as Cache
  A->>T: publish(change set, expected base)
  T->>DB: verify role/draft/base
  alt stale
    T-->>A: 409 rebase required
  else eligible
    T->>DB: promote snapshot/current pointer
    T->>AU: write publisher/time event
    T->>C: invalidate synchronously
    T-->>A: published
  end
```

## PKT schedule and PWA state
```mermaid
flowchart TD
  Now[Current PKT] --> Date[Derive service date]
  Date --> Override{Full-day override?}
  Override -->|no service| None[No service]
  Override -->|no| Weekly[Published weekly departures]
  Weekly --> Partial[Apply Route + Bus + time overrides]
  Partial --> Current[Earliest departure >= now or no further today]
```

Freshness is based only on the saved successful synchronization timestamp (fresh through 5 minutes). Offline and service outage are distinct connectivity states. Cached core data/announcements expire at 24 hours; active urgent banners are never cached.

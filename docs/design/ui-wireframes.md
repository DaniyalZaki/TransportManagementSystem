# UI Wireframes

These low-fidelity wireframes describe required content and behavior, not final styling. They prioritize mobile public use. All dates and times are PKT.

## Public PWA — home / departures

```text
┌──────────────────────────────────────┐
│ Uzair Transport Service     [Refresh] │
│ Last synced: 19 Nov, 13:05 PKT        │
├──────────────────────────────────────┤
│ [Offline] [Information may be outdated]│  ← only when applicable
├──────────────────────────────────────┤
│ URGENT                                │
│ [Banner 1: Road closure…]             │  ← online only; newest first
│ [Banner 2: …]                         │
├──────────────────────────────────────┤
│ Next departures — Wed, 19 Nov         │
│ R-01 · C-12          14:30            │
│ Lahore → Campus      Scheduled         │
│ R-02 · C-08          No further        │
│                       departures today │
├──────────────────────────────────────┤
│ [Today's schedule] [Announcements]    │
│ [Send feedback]                       │
└──────────────────────────────────────┘
```

The timestamp is the original successful synchronization time; cache display and failed refreshes do not change it. Offline and service-outage warnings use distinct labels and can coexist conceptually with stale state. No label suggests GPS/live tracking.

## Public PWA — schedule, announcements, feedback

```text
┌──────────────────────────────────────┐
│ ← Today’s schedule                    │
│ Wed, 19 Nov 2026 · PKT                │
├──────────────────────────────────────┤
│ 08:00  R-01  C-12                     │
│        Lahore → Campus · Inbound      │
│ 14:30  R-01  C-12                     │
│        Campus → Lahore · Outbound     │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ Send feedback                          │
│ Name (optional)     [               ] │
│ Contact (optional)  [               ] │
│ Feedback *          [               ] │
│ Website (hidden honeypot)             │
│ [Submit feedback]                     │
│ Receipt / immediate delivery error    │
└──────────────────────────────────────┘
```

Announcements are newest first. Cached announcements are identified when required; active banners are deliberately absent from offline cache. Feedback has no status-tracking dashboard; retry-pending duplicates receive a neutral already-received message.

## Admin — transport change set

```text
┌────────────────────────────────────────────────────────────┐
│ Admin / Transport                       User menu           │
├───────────────┬────────────────────────────────────────────┤
│ Change sets   │ Spring timetable [Draft]                    │
│ Routes        │ Base: Published set #18                     │
│ Buses         │ [Routes] [Buses] [Assignments] [Schedule]  │
│ Assignments   │ Editable, accessible data table             │
│ Schedule      │                                             │
│ Publications  │ Warnings: 1 incomplete entry                │
│ Announcements │ [Save draft] [Validate] [Publish…]          │
│ Accounts*     │                                             │
└───────────────┴────────────────────────────────────────────┘
* Transport Management only
```

Publish shows a confirmation summary and requires an explicit “Publish anyway” when validation finds incomplete/conflicting entries. A stale draft shows the current baseline and rebase action; it cannot publish first.

## Admin — announcement / urgent lifecycle

```text
┌──────────────────────────────────────┐
│ New announcement                     │
│ Title [                             ] │
│ Body  [                             ] │
│ [ ] Operational change  [ ] Urgent   │
│ Expiry: (•) PKT date/time ( ) Manual │
│ [Confirm change] [Publish]           │
└──────────────────────────────────────┘

Published urgent item
┌──────────────────────────────────────┐
│ Announcement: active / expired/removed│
│ Banner: active                        │
│ [Remove banner] [Resolve banner]      │
└──────────────────────────────────────┘
```

The UI makes clear that removal is not resolution. An urgent operational change requires both a published announcement and a separate banner.

# UI Wireframes

These low-fidelity wireframes describe required content and behavior, not final styling. They prioritize mobile public use. All dates and times are PKT.

## Public PWA — home / departures

```text
┌──────────────────────────────────────┐
│ Transport Service           [Refresh] │
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
│ 08:00  R-01  C-12, C-14              │
│        Lahore → Campus · PICK-UP      │
│ 14:30  R-01  C-12, C-14              │
│        Campus → Lahore · RETURN       │
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
│ Working draft │ Working draft [Draft]                       │
│ Routes        │ Base: Current published snapshot            │
│ Buses         │ [Routes] [Buses] [Assignments] [Schedule]  │
│ Assignments   │ Editable, accessible data table             │
│ Schedule      │                                             │
│ Publications  │ Warnings: 1 incomplete entry                │
│ Announcements │ [Save draft] [Publish…]                     │
└───────────────┴────────────────────────────────────────────┘
```

Schedule rows contain weekday 1–7, Route, all buses assigned to that Route, and departure time; there is no per-schedule bus selector. Route direction is a `RETURN`/`PICK-UP` select. The launcher contains one styled **Open Draft** action for the permanent shared draft. The desktop grid places Audit History beside the Working Copy (or Draft Editor once open), with Protected Publication below across both columns; its grid gap remains constant while history is expanded or collapsed. Publish is greyed out until the displayed snapshot has no unsaved changes; Publish warns only when a route has no recurring schedule entry and requires explicit “Publish anyway” in that case. The editor does not display a draft version; save/publish completion and errors remain visible within the editor.

## Admin — announcement / urgent lifecycle

```text
┌──────────────────────────────────────┐
│ New announcement                     │
│ Title [                             ] │
│ Body  [                             ] │
│ [ ] Urgent                           │
│ Expiry: (•) PKT date/time ( ) Manual │
│ [Publish]                            │
└──────────────────────────────────────┘

Published urgent item
┌──────────────────────────────────────┐
│ Announcement: active / expired/removed│
│ Banner: active                        │
│ [Remove banner] [Resolve banner]      │
└──────────────────────────────────────┘
```

The UI makes clear that removal is not resolution. An urgent announcement requires both a published announcement and a separate banner; the form has no operational-change or confirmation control.

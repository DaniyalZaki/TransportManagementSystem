# UI Wireframes

Low-fidelity requirements wireframes; not final visual styling. All times are PKT.

## Public PWA
```text
┌──────────────────────────────────────┐
│ Uzair Transport Service     [Refresh] │
│ Last synced: 19 Nov, 13:05 PKT        │
├──────────────────────────────────────┤
│ [Offline] [Information may be outdated]│
├──────────────────────────────────────┤
│ URGENT (online only; newest first)    │
│ [Road closure…]                       │
├──────────────────────────────────────┤
│ Next departures — Wed, 19 Nov         │
│ R-01 · C-12    14:30  Scheduled       │
│ R-02 · C-08    No further departures  │
├──────────────────────────────────────┤
│ [Today's schedule] [Announcements]    │
│ [Send feedback]                       │
└──────────────────────────────────────┘
```
The original successful-sync timestamp never changes on cache display or failed refresh. Offline and outage labels are distinct; stale can coexist. There is no live/GPS implication.

## Feedback
```text
Name (optional)     [             ]
Contact (optional)  [             ]
Feedback *          [             ]
Website (hidden honeypot)
[Submit feedback]  Receipt / immediate delivery error
```
No status dashboard exists; retry-pending duplicates receive a neutral already-received message.

## Admin
```text
Admin / Transport
Change sets | Routes | Buses | Assignments | Schedule | Publications
Spring timetable [Draft]  Base: Published set #18
Warnings: 1 incomplete entry
[Save draft] [Validate] [Publish…]
```
Publish requires explicit confirmation when warnings exist; stale drafts require rebase. Announcement editor provides operational/urgent flags and PKT expiry. Urgent view explicitly separates Remove banner from Resolve banner. Account management is Transport Management only.

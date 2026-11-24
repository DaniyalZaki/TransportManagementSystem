# Product Requirements Document

## 0. Approved implementation decisions and precedence

The decisions in this section are approved product and implementation
requirements. They supersede conflicting wording elsewhere in this PRD
and in older ADRs. ADR-011 records their architectural rationale.

- The backend is Python/FastAPI with handwritten asynchronous PostgreSQL
  SQL and migrations. The Public PWA and Admin Web App are separate
  Next.js/TypeScript applications. The public client uses Workbox,
  Cache Storage, and IndexedDB; refresh runs every minute while the app
  is open, on reconnection, and on manual refresh.
- PostgreSQL is the system of record. A single FastAPI worker uses an
  in-process read cache. One permanent shared transport draft publishes
  atomically as a new published snapshot. Save and publish requests execute
  serially and report a temporary numeric execution-order identifier.
- Supabase Auth is self-hosted on the PostgreSQL deployment. Privileged
  users use email/password. Roles are mapped in backend-owned PostgreSQL
  data; only Transport Management manages accounts. Deactivation blocks
  new login but does not invalidate an already active token.
- The audit log records only successful transport publications, with the
  publisher and publication time, and is retained for 30 days. It does
  not record edits, login/logout activity, announcements, or prior
  announcement versions. Recovery restores an entire previously
  published change set within 30 days. Published records are physically
  deleted 30 days after retirement.
- Feedback is sent by backend SMTP to the configured Transport
  Management mailbox, retained for 30 days, and deduplicated using
  normalized content (case, outer whitespace, and repeated internal
  whitespace). Failed delivery is retried after 1, 5, and 30 minutes;
  the submitter sees an immediate error on the initial failure and is
  not later notified of retry success.
- Announcements use PKT expiry. Removed and expired announcement records
  are retained for 30 days. Active urgent banners are online-only;
  their associated announcements may be cached.

## 1. Product / Feature Overview

The Transport Information Web Application is intended for students and transport administration. Students can access daily coaster timings, route information, and announcements from Transport Management through a dedicated web application. Transport Management and designated administrators can update coaster routes, timings, and announcements, and gather Feedback from users.

The application provides a centralized channel for transport information and Feedback. For the first release, announcements published by Transport Management may cover transport-related and non-transport-related notices.

## 2. Problem and User Need

A Computer Engineering student commutes daily via Uzair Transport. Transport updates and bus timings are shared mainly through a WhatsApp channel. Critical schedule updates get lost among irrelevant announcements. The student has difficulty finding timely departure schedules, risks missing coasters/buses on the return journey, and experiences stress arranging costly alternative transport. The client selected a dedicated web application.

The user wants to stay up to date with daily coaster timings, routes and announcements through a web app that is easy to use and access, and wants a Feedback page to inform Transport Management of any issues.

## 3. Goals

### User Goals

- **UG-01 | Student:** Ease of accessibility and usage
- **UG-02 | Student:** Daily coaster timings, routes and announcements
- **UG-03 | Transport Management:** Deliver daily Schedule / Timetable, Route information and announcements through the web app and gather Feedback from users

### Product Goals

- **G-01:** Ensuring ease of use (supports UG-01); the target is that at least 80% of surveyed students report that transport information is easy to access.
- **G-02:** Keeping users updated with relevant information (supports UG-02)
- **G-03:** Providing a way of communication between students and Transport Management (supports UG-02, UG-03)

## 4. Non-Goals / Out of Scope

- **NG-01:** Fee payment management
- **NG-02:** Student portal
- **NG-03:** AI chatbot

## 5. Users and Stakeholders

| Stakeholder | Role | Concern |
|---|---|---|
| Student (Day Scholar) | End-user relying on daily transport | Needs accurate, easily accessible bus timings and announcements. |
| Transport Management | Service provider | Needs an efficient channel to publish clear updates, manage Schedule / Timetable information, and receive Feedback. |
| Driver / Bus Operators | Operational execution | Operate according to published routes and schedules. No direct interaction with the application. |

## 6. Ubiquitous Language / Glossary

| Term | Definition |
|---|---|
| Schedule / Timetable / Departure Schedule | Equivalent terms for departure-time information. The "current departure-time table" and "that specific day's departure times" are the two schedule views from D-18. |
| Recurring weekly schedule | A schedule pattern identified by weekday **1–7** (Monday through Sunday), Route, and departure time. Each entry applies to every Bus/Service Identifier currently assigned to that Route. |
| Date-specific override | A schedule change applying to one specified service date; it takes precedence over the recurring weekly schedule for that date. It may specify a no-service day. |
| Draft transport data | The one saved shared Route, Bus/Service Identifier, assignment, and Schedule / Timetable workspace; it is not visible to students until separately published and never expires. |
| Announcement expiry | The optional date/time selected by an authorized publisher for an announcement to stop being displayed. An announcement may instead remain visible until manually removed. |
| Announcement version history | The retained prior versions of an announcement when its published content is edited. |
| Service date | The calendar date, in Pakistan Standard Time (PKT), on which a scheduled departure is assigned to operate. |
| Departure instance | One scheduled service derived from a schedule row and a Bus/Service Identifier assigned to its Route, uniquely identified by service date, scheduled departure date/time, Route, and Bus/Service Identifier. |
| Current departure | For each Route and Bus/Service Identifier, the earliest departure instance scheduled for the current service date whose scheduled departure time is at or after the current PKT time. It is a next-upcoming departure, not a GPS/live-location status. |
| Last successful synchronization | The time at which the application most recently completed a successful retrieval of the relevant published transport data from the service. Cached display or page reload does not change this time. |
| Cached information | Previously retrieved transport information retained on the user's device for offline or outage viewing. |
| Fresh information | Information whose last successful synchronization is no more than 5 minutes old. |
| Stale information | Information whose last successful synchronization is more than 5 minutes old. |
| Route | A unique route identifier. Route locations and direction are maintained separately rather than being embedded in the Route identifier. |
| Bus/Service Identifier | Identifies an individual physical coaster. |
| Coaster-to-route assignment | Associates an individual physical coaster with a Route. A schedule row automatically applies to all buses assigned to that Route; it does not select an individual bus. |
| Incomplete schedule entry | A departure entry missing weekday, departure time, Route, or at least one coaster-to-route assignment for its Route. |
| Conflicting assignment | Two different coaster-to-route assignments recorded for the same departure instance. |
| Cache retention period | The period cached core transport information remains available for offline viewing after its last successful synchronization. |
| Official transport information channel | The designated authoritative channel through which transport information is published to students and the public. |
| Announcement | A distinct mechanism from a persistent alert banner. Urgent changes use both. |
| Persistent alert banner | A distinct mechanism from an Announcement. An urgent-change banner remains visible until an authorized user manually removes or resolves it. |
| Removed urgent announcement | An urgent announcement manually hidden from public display; removal does not mean it was resolved. |
| Resolved urgent announcement | An urgent announcement manually marked as resolved, with its resolution state retained. |
| Feedback | A separate category from complaint and contact. |
| Complaint | A separate category from Feedback and contact. |
| Contact | A separate category from Feedback and complaint. |
| Receipt confirmation | A simple on-screen success message shown after a Feedback submission is successfully delivered. |
| Honeypot field | A hidden form field used for basic spam prevention; a Feedback submission that populates it is rejected. |
| Status tracking | Reports progress on a Feedback submission; not included in this release. |
| Outdated information / stale information | Equivalent terms for information considered outdated or stale. |
| Service/data outage | A situation distinct from offline use and outdated information, with separately specified behavior. |
| Offline use | A situation distinct from service/data outage and outdated information, with separately specified behavior. |
| the public | People who view transport information without Login. |
| Transport Management | Owns and verifies transport data. |
| Designated administrators | A distinct role with privileged access. |
| Login / authentication | Equivalent terms. |
| Individual account | A separate concept from Login / authentication. |
| Publication | Release of information. |
| Visibility | Student access to information. |
| Audit record / audit log / administrative change record | Equivalent terms. |
| Backup / recovery | Equivalent terms in the glossary; backups and recovery testing remain separate requirements. |
| RTO | Maximum acceptable recovery time. |
| RPO | Maximum acceptable data-loss window. |
| Data loss | The observed outcome. |
| Acceptance / release acceptance | Equivalent terms. |
| Acceptance criteria | Conditions used to judge the release. |
| Refresh | General term; automatic refresh and manual refresh are distinct. |
| Automatic refresh | A distinct type of Refresh. |
| Manual refresh | A distinct type of Refresh. |
| Mobile-focused | Mobile-prioritized with laptop/desktop compatibility retained. |

## 7. Functional Requirements

- **FR-01:** The system shall display departure-time information to students and the public without requiring Login.
- **FR-02:** The system shall display the next-upcoming departure instance for each Route and Bus/Service Identifier for the current service date. Each departure instance shall be identified by service date, scheduled departure date/time, Route, and Bus/Service Identifier. The system shall not imply that a departure is currently in motion or GPS-tracked. If no later departure exists for a Route and Bus/Service Identifier on that service date, the system shall display “No further departures today” for that service grouping.
- **FR-03:** The system shall display the daily Schedule / Timetable with weekday values 1–7 (Monday–Sunday), a unique Route identifier, the complete set of Bus/Service Identifiers assigned to that Route, and a PKT departure time. A schedule row shall automatically apply to every bus assigned to its Route; operators shall not select a bus separately while defining the schedule. Route locations and direction shall be maintained separately from the Route identifier, and direction shall be one of `RETURN` or `PICK-UP`. The schedule shall be based on a recurring weekly schedule, with date-specific overrides taking precedence for the dates to which they apply. A date-specific override may specify that no service operates on that date.
- **FR-04:** The system shall display announcements published by Transport Management and designated administrators to students and the public, including transport-related and non-transport-related notices. An announcement has a required title and optional body. Announcements shall be ordered newest first. At publication, the authorized publisher shall choose either a PKT expiry date/time or that the announcement remains visible until manually removed. Published announcements may be edited; prior versions are not retained. Removed and expired records are retained for 30 days. Announcements do not store operational-change or confirmation state. For urgent announcements, the persistent banner follows FR-05 and FR-08 regardless of announcement expiry.
- **FR-05:** The system shall allow Transport Management and designated administrators to mark an announcement as urgent and shall display each urgent announcement through a separate persistent alert banner and an announcement. Each banner shall remain visible until manually removed or resolved by an authorized user. Multiple urgent banners shall be displayed separately, newest first.
- **FR-06:** The system shall allow Transport Management and designated administrators to open and save one shared permanent draft containing unique Route identifiers, separately maintained route locations and fixed `RETURN`/`PICK-UP` direction, physical Bus/Service Identifiers, Route-to-bus assignments, and Schedule / Timetable information. A schedule row contains weekday 1–7, Route, and departure time and uses all buses assigned to that Route. Saving preserves changes for every privileged account; a separate Publish action is required before the changes become visible to students.
- **FR-07:** The system shall allow Transport Management and designated administrators to publish announcements, including urgent and non-transport-related notices. An announcement is published through its Publish action without a separate draft-publication workflow.
- **FR-08:** The system shall allow Transport Management and designated administrators to remove or resolve urgent announcements manually. Removal shall hide the banner from public display without marking the change as resolved. Resolution shall mark the urgent announcement as resolved and retain that resolution state. Neither action shall occur automatically.
- **FR-09:** The system shall allow students and the public to submit Feedback through a simple form that sends submissions to the configured Transport Management mailbox using SMTP. Name and contact details shall be optional, and anonymous submissions shall be permitted. The system shall apply a hidden honeypot field and reject normalized-content duplicates received within the preceding 10 minutes. No IP-based submission limit shall be applied. On immediate SMTP failure it shall show an error, retain the submission, and retry after 1, 5, and 30 minutes without later user notification. Feedback is retained for 30 days; a dashboard and status tracking are out of scope.
- **FR-10:** The system shall display, for each displayed transport-data set, the timestamp of its last successful synchronization with the service. The timestamp shall represent when the data was successfully retrieved, not when cached data was displayed, the page was opened, or a refresh was attempted. It shall be displayed in PKT.
- **FR-11:** The system shall treat transport information as fresh for up to and including 5 minutes after its last successful synchronization. After 5 minutes, it shall mark the information as stale and display a visible “Information may be outdated” warning with the last successful synchronization timestamp. A successful synchronization resets the freshness age.
- **FR-12:** If a request for current transport information fails because the service/data source is unavailable, the system shall display the last successfully synchronized cached information, if available and still within its 24-hour cache-retention period, with an outage warning and its original timestamp. If no cached information exists, it shall display an unavailable message and shall not fabricate or display an empty schedule as if it were current.
- **FR-13:** The system shall retain previously loaded core transport information and announcements for offline use for 24 hours after its last successful synchronization; active urgent banners are not cached. After this retention period, cached information shall no longer be available offline. While the public app is open and online, it shall attempt synchronization every 1 minute, on reconnection, and on manual refresh. It shall distinguish offline connectivity from a service/data outage, show the appropriate warning and original shared snapshot timestamp, and never present cached information as newly updated.
- **FR-14a:** The system shall allow only Transport Management and designated administrators to publish transport information. Route, Bus/Service Identifier, assignment, and Schedule / Timetable edits shall require a separate Publish action after being saved as drafts. Announcements shall be published directly through their Publish action.
- **FR-15:** The portal shall be the official transport information channel for students and the public, replacing the existing WhatsApp channel for official transport information. Official transport schedules, route assignments, and announcements shall be published through the portal.
- **FR-14b:** The system shall record successful transport publication events only, identifying the publisher and publication time, and retain these records for 30 days. It shall not retain edit, login/logout, announcement-publication, or announcement-version audit records. If an accidental change is identified by Transport Management or a designated administrator, recovery restores the complete previously published transport change set within 30 days. Unpublished drafts and announcements are never recoverable.

## 8. Non-Functional Requirements

- **NFR-01 (Performance):** The system shall make published transport information visible to students within 5 seconds, measured from the server receiving the publish request/update to the published information becoming visible to students. The performance test shall focus on the current departure table and daily Schedule / Timetable, using a baseline workload of 500 concurrent users and 2,000 scheduled departures. At least 95% of measured publication operations shall make the relevant information visible within 5 seconds.
- **NFR-02 (Compatibility):** The system shall remain usable on mobile devices, laptops, and desktop computers, with mobile access prioritized.
- **NFR-03 (Reliability):** The system shall keep previously loaded core information available during offline use for 24 hours after its last successful synchronization, identify cached data as cached, preserve its last successful synchronization timestamp, and attempt automatic synchronization every 1 minute while online and after reconnection. Manual refresh shall also be available when connectivity permits.
- **NFR-04 (Reliability):** The system shall support backups and recovery testing. Recovery shall meet an RTO of no more than 4 hours and an RPO of no more than 1 hour. A recovery test passes when recovery time is no more than 4 hours and data loss is no more than 1 hour. Overall release acceptance is governed by the release-acceptance criterion in Section 12.

## 9. Business Rules and Constraints

### 9.1 Business Rules

- **BR-01:** Transport Management owns and verifies transport data.
- **BR-02:** Transport Management and designated administrators are the roles permitted to perform privileged functions.
- **BR-03:** Drivers do not interact directly with the application.
- **BR-04:** An urgent announcement shall be published directly without a draft-publication workflow.
- **BR-05:** Urgent announcements must be communicated through both a persistent alert banner and an announcement. Transport Management and designated administrators may mark an announcement as urgent.
- **BR-06:** When published transport information conflicts, the latest published update takes effect, and the change is recorded.
- **BR-07:** Publishing shall warn the publisher only when one or more configured Routes have no recurring schedule entry. The warning shall not block publication after explicit confirmation. Students shall see only the latest published version and shall not see a separate warning.
- **BR-08:** Transport Management and designated administrators authenticate using individual accounts and passwords.
- **BR-09:** Current departure is evaluated separately for each Route and Bus/Service Identifier using PKT and the current service date. The selected departure is the earliest scheduled departure at or after the current time. Once all departures for that grouping have passed, the system displays “No further departures today”; it does not continue to label the final past departure as current.
- **BR-10:** Freshness is based only on the last successful synchronization timestamp. Data is fresh at an age of 5 minutes or less and stale at an age greater than 5 minutes.
- **BR-11:** Offline status means the user's device has no network connectivity. Service/data outage means connectivity exists but the application cannot retrieve current data from its service/data source. Both may show cached data, but the warning shall identify the applicable condition. If cached data is more than 5 minutes old, the stale warning shall also be shown; the connectivity warning and stale warning are not mutually exclusive.
- **BR-12:** Cached data remains available only within the 24-hour cache-retention period and retains its original last successful synchronization timestamp. Opening, reloading, displaying, or reading cached data shall not change that timestamp or clear a stale/outage warning. While the public app is open, reconnection triggers automatic synchronization; warnings clear only after successful synchronization. If synchronization fails, cached data and its warning remain.
- **BR-13:** The system shall create a 30-day transport-publication record for each successful transport publication, containing only its publisher and publication time. It shall not record edits, login/logout activity, announcement publication, or announcement version history. Recovery may restore only a whole previously published transport change set within 30 days; drafts and announcements are not recoverable.
- **BR-14:** Name and contact details on the Feedback form are optional. Users may submit Feedback anonymously.
- **BR-15:** Transport Management may publish both transport-related and non-transport-related announcements. An announcement title is required and its body is optional.
- **BR-16:** Announcements do not record operational-change or confirmation state.
- **BR-17:** At least 80% of surveyed students shall report that transport information is easy to access for the product's ease-of-use improvement target.
- **BR-18:** The Feedback form shall include a hidden honeypot field. A submission that populates the honeypot field shall be rejected. The system shall reject a submission whose normalized content (case, outer whitespace, and repeated internal whitespace) duplicates a previous submission in the preceding 10 minutes. No IP-based submission limit shall be applied.
- **BR-19:** Release acceptance requires at least 95% of defined acceptance criteria to pass, with no critical defects.
- **BR-20:** The daily Schedule / Timetable shall use a recurring weekly schedule as its base. A date-specific override takes precedence over the recurring schedule for that service date. A date-specific override may explicitly specify that no service operates on that date.
- **BR-21:** Transport Management and designated administrators may mark an announcement as urgent before publication.
- **BR-22:** Each urgent change shall have its own persistent banner. Banners remain visible until manually removed or resolved by Transport Management or a designated administrator and are ordered newest first. Removal hides the banner without recording the change as resolved; resolution records that the issue has been resolved.
- **BR-23:** Each announcement shall be configured at publication either to expire at a selected PKT date/time or to remain visible until manually removed. Announcements are ordered newest first. Published announcements may be edited without retaining previous versions; removed/expired records are retained for 30 days. An urgent banner remains governed by BR-22 even if its associated announcement reaches display expiry.
- **BR-24:** Changes to Routes, route locations/direction, Bus/Service Identifiers, Route-to-bus assignments, and schedules are saved in one permanent shared draft and require a separate Publish action before becoming visible. Save Draft and Publish execute one request at a time and return a temporary numeric execution-order identifier. Schedule rows use weekday 1–7 and every bus assigned to the selected Route. Announcements are published directly through their Publish action.
- **BR-25:** The portal is the official transport information channel and replaces the existing WhatsApp channel for official transport information. The portal is the authoritative source for published schedules, route assignments, and announcements.

### 9.2 Constraints

- **C-01:** Viewing transport information shall not require Login.
- **C-02:** Only Transport Management and designated administrators shall have privileged access to edit or publish transport information.
- **C-03:** The application shall prioritize mobile access while remaining usable on laptops and desktop computers.
- **C-04:** Direct driver interaction with the application shall be outside the project scope.
- **C-05:** Below the header, the page shall show the current departure-time table with coaster-to-route assignments, then announcements, then that specific day's departure times; Feedback/contact shall be placed in the footer. [Traces: D-17, D-18]
- **C-06:** The portal shall replace WhatsApp as the official channel for transport information. No WhatsApp integration or parallel official transport-information publication workflow is required by this release.

## 10. Main User Flows / Scenarios

#### MF-01 | Linked FR: FR-01
Trigger: Student seeks departure-time information.
Actors: Student
Normal sequence:
1. Student accesses the transport information.
2. The system displays departure-time information.
3. The system provides departure-time information without requiring Login.

Successful outcome: Departure-time information is displayed to students without requiring Login.

#### MF-02 | Linked FR: FR-02
Trigger: Student seeks the current/next departure assignments.
Actors: Student
Normal sequence:
1. Student accesses the transport information.
2. The system obtains the current date and time in PKT.
3. For each Route and Bus/Service Identifier, the system selects the earliest departure instance for the current service date whose scheduled departure time is at or after the current time.
4. The system displays each selected departure with its service date, scheduled departure time, Route, and Bus/Service Identifier.
5. For any grouping with no remaining departure that day, the system displays “No further departures today”.

Successful outcome: The page identifies the next-upcoming departure for each service grouping, or explicitly states that no further departure remains that day.

Boundary case: After the final scheduled departure for a grouping, no past departure is labelled current; “No further departures today” is displayed.

#### MF-03 | Linked FR: FR-03
Trigger: Student seeks the daily Schedule / Timetable.
Actors: Student
Normal sequence:
1. Student accesses the transport information for a service date.
2. The system retrieves the recurring weekly schedule applicable to that day.
3. If a date-specific override exists, the system applies it in place of the recurring schedule for that date.
4. If the override specifies no service, the system displays that no service is scheduled; otherwise, it displays departures identified by Route and the physical Bus/Service Identifier assigned to each departure.

Successful outcome: The applicable daily Schedule / Timetable is displayed using the recurring schedule or the date-specific override.

Boundary case: When a date-specific override specifies no service, the system does not display the recurring departures for that date.

#### MF-04 | Linked FR: FR-04
Trigger: Student seeks announcements.
Actors: Student
Normal sequence:
1. Student accesses the transport information.
2. The system retrieves published transport-related and non-transport-related announcements.
3. The system orders announcements newest first and displays each according to its selected expiry or manual-removal lifetime.
4. If a published announcement has been edited, the current version is displayed; prior versions are not retained.

Successful outcome: Published announcements are displayed newest first with their configured lifetime.

#### MF-05 | Linked FR: FR-05
Trigger: An announcement needs to be identified as urgent.
Actors: Transport Management, designated administrators, Student
Normal sequence:
1. Transport Management or a designated administrator marks an announcement as urgent.
2. The system displays the urgent announcement through the announcement and its own persistent alert banner.
3. The system displays multiple active urgent banners separately, newest first.
5. The banner remains visible until Transport Management or a designated administrator manually removes or resolves it.

Successful outcome: Each urgent change is displayed through an announcement and a separate persistent banner.

#### MF-06 | Linked FR: FR-06
Trigger: Transport Management or a designated administrator needs to update transport data.
Actors: Transport Management, designated administrators
Normal sequence:
1. The authorized user accesses the transport information management function.
2. The user edits a Route (with `RETURN` or `PICK-UP` direction), route locations, Bus/Service Identifier, Route-to-bus assignment, or a weekday-1–7 Schedule / Timetable row.
3. The system saves the successful edit as draft transport data; edits are not audit-recorded.
4. The authorized user reviews the draft and selects Publish as a separate action.
5. The system makes the published transport data visible to students and records publisher and publication time for 30 days.

Successful outcome: Transport data changes are not visible to students until the separate Publish action succeeds.

Boundary case: Saving a draft without selecting Publish does not change the information visible to students.

#### MF-07 | Linked FR: FR-07
Trigger: An announcement needs to be published.
Actors: Transport Management, designated administrators, Student
Normal sequence:
1. The authorized user prepares a transport-related or non-transport-related announcement.
2. The authorized user enters an optional message body and selects the announcement's expiry date/time or chooses that it remains visible until manually removed.
3. The authorized user selects Publish; announcements are published directly and do not require a separate draft-publication workflow.
4. The system displays the announcement newest first. If edited after publication, the latest version replaces the prior content without retaining prior versions.

Successful outcome: Authorized users can publish announcements directly with the selected lifetime.

#### MF-08 | Linked FR: FR-08
Trigger: An urgent announcement needs to be removed or resolved.
Actors: Transport Management, designated administrators
Normal sequence:
1. An authorized user selects an active urgent announcement.
2. The user chooses either Remove or Resolve.
3. If Remove is selected, the system hides the banner from public display without marking the issue as resolved.
4. If Resolve is selected, the system records the resolved state and stops displaying the active banner.

Successful outcome: Removal and resolution have distinct recorded outcomes and are performed manually.

#### MF-09 | Linked FR: FR-09
Trigger: A student wants to submit feedback.
Actors: Student, Transport Management
Normal sequence:
1. Student accesses the Feedback form.
2. The user enters Feedback and may optionally provide a name and contact details; the user may leave those fields blank to submit anonymously.
3. The system applies basic spam prevention and duplicate-submission detection.
4. If accepted, the system sends the feedback submission to Transport Management and displays the on-screen success confirmation.

Successful outcome: Feedback is submitted to Transport Management and the user receives an on-screen success confirmation. The application does not provide a management dashboard or feedback status tracking in this release.

#### MF-10 | Linked FR: FR-10
Trigger: Student wants to check when transport information was last synchronized.
Actors: Student
Normal sequence:
1. Student accesses the transport information.
2. The system retrieves the last successful synchronization timestamp for each displayed transport-data set.
3. The system displays that timestamp, clearly labelled as the last successful update/synchronization.

Successful outcome: The displayed timestamp reflects the last successful retrieval, not the time cached data was displayed.

#### MF-11 | Linked FR: FR-11
Trigger: Transport information passes the freshness threshold.
Actors: Student
Normal sequence:
1. Student accesses transport information.
2. The system compares the current PKT time with the last successful synchronization timestamp.
3. If the age is greater than 5 minutes, the system marks the information stale and displays “Information may be outdated” with the timestamp.
4. If a successful synchronization occurs, the system updates the timestamp and removes the stale warning while the data remains within the freshness threshold.

Successful outcome: Freshness status and warning are derived from the age of the last successful synchronization.

Boundary case: At exactly 5 minutes old, information remains fresh; immediately after 5 minutes, it is stale and warned.

#### MF-12 | Linked FR: FR-12
Trigger: A service/data outage prevents retrieval of current transport information.
Actors: Student
Normal sequence:
1. Student accesses transport information while the device has network connectivity.
2. The system fails to retrieve current data from its service/data source.
3. If cached data exists, the system displays it with an outage warning and its original last successful synchronization timestamp.
4. If no cached data exists, the system displays that current transport information is unavailable and does not present a fabricated or blank schedule as current.

Successful outcome: An outage is clearly identified; cached data is visibly historical, or unavailability is stated when no cache exists.

#### MF-13 | Linked FR: FR-13
Trigger: Student accesses transport information offline, or connectivity returns after offline use.
Actors: Student
Normal sequence:
1. If the device is offline and cached core information exists and is within 24 hours of its last successful synchronization, the system displays the cached information with an offline warning and its original synchronization timestamp. If 24 hours have elapsed, the cached information is no longer available for offline display.
2. If the device is offline and no cached core information exists, the system displays that information is unavailable until a connection is restored and a successful synchronization completes.
3. While online, the system attempts automatic synchronization every 1 minute. When connectivity returns, the system indicates that it is refreshing and attempts automatic synchronization.
4. Only after successful synchronization does the system replace the cached data, update the timestamp, and clear the offline/stale warning as applicable.
5. If automatic synchronization fails, the system retains the cached data, original timestamp, and warning, provided the cache is still within its 24-hour retention period. The user may also request a manual refresh when connectivity permits.

Successful outcome: Previously loaded information remains available offline without being misrepresented as current; reconnection refreshes it only after a successful retrieval.

#### MF-14a | Linked FR: FR-14a
Trigger: Transport data or an announcement needs to be published.
Actors: Transport Management, designated administrators
Normal sequence:
1. The user accesses the publishing function.
2. The system verifies that the user is Transport Management or a designated administrator.
3. For Route, Bus/Service Identifier, assignment, or Schedule / Timetable changes, the user selects Publish after saving the changes as a draft.
4. For announcements, the user publishes directly through the announcement Publish action.
5. The system rejects publication attempts by unauthorized users and records successful publication events.

Successful outcome: Only authorized users can publish; transport-data drafts require a separate Publish action, while announcements are published directly.

#### MF-14b | Linked FR: FR-14b
Trigger: An administrative change is made to transport information.
Actors: Transport Management, designated administrators
Normal sequence:
1. An authorized user makes an administrative change to transport information.
2. On successful transport publication, the system records only publisher and publication time.
3. If Transport Management or a designated administrator identifies the change as accidental, the system can recover a whole previously published transport change set within 30 days. Unpublished drafts and announcements are not recoverable.

Successful outcome: Administrative changes can be traced to the responsible user for 30 days; only previously published transport information can be recovered if an accidental change is identified.

## 11. Edge Cases and Failure Conditions

EC-01 | FR-01 | Situation: A student attempts to view departure-time information without logging in. | Status: COVERED | Behaviour or open question: "public viewing without Login" (D-01).

EC-02 | FR-02 | Situation: More than one service grouping has departures at different times. | Status: COVERED | Behaviour: Select the next-upcoming departure independently for each Route and Bus/Service Identifier using PKT.

EC-03 | FR-02 | Situation: The final departure for a Route and Bus/Service Identifier has already passed. | Status: COVERED | Behaviour: Display “No further departures today”; do not label the last past departure as current.

EC-04 | FR-02 | Situation: A coaster-to-route assignment is displayed. | Status: COVERED | Behaviour: Route is a unique identifier, Bus/Service Identifier identifies a physical coaster, and the assignment links that coaster to a Route for a particular departure.

EC-05 | FR-03, BR-07 | Situation: The Schedule / Timetable contains incomplete or conflicting information. | Status: COVERED | Behaviour: An entry is incomplete if service date, departure time, Route, Bus/Service Identifier, or assignment is missing. A conflict is two different assignments for the same departure instance. Warn the publisher but allow publication; students see only the latest published version, without a separate conflict warning.

EC-06 | FR-03 | Situation: A service date has a recurring weekly schedule and/or a date-specific override. | Status: COVERED | Behaviour: Use the recurring weekly schedule unless a date-specific override exists; the override takes precedence and may specify no service.

EC-07 | FR-03 | Situation: A service must be identified in the Schedule / Timetable. | Status: COVERED | Behaviour: Show weekday 1–7, Route, every Bus/Service Identifier assigned to that Route, and departure time; maintain route locations and `RETURN`/`PICK-UP` direction separately.

EC-08 | FR-04 | Situation: The system encounters announcements of different types. | Status: COVERED | Behaviour: Display all announcements published by Transport Management and designated administrators, including transport-related and non-transport-related notices.

EC-09 | FR-04 | Situation: Announcements have different publication times and configured lifetimes. | Status: COVERED | Behaviour: Order newest first; each announcement either expires at its configured date/time or remains until manually removed.

EC-10 | FR-04 | Situation: An announcement is published, but the relationship between publication and the latest published update is unclear. | Status: COVERED | Behaviour or open question: "latest published update takes effect and the change is recorded" (D-21).

EC-11 | FR-05 | Situation: An urgent change needs to be displayed to users. | Status: COVERED | Behaviour or open question: "urgent changes use a persistent alert banner plus an announcement" (D-08).

EC-12 | FR-05 | Situation: An announcement must be identified as urgent. | Status: COVERED | Behaviour: Transport Management and designated administrators may mark an announcement as urgent.

EC-13 | FR-05, FR-08 | Situation: An urgent banner must be removed or resolved, or multiple urgent changes are active. | Status: COVERED | Behaviour: Each urgent change has a separate newest-first banner; manual removal hides it without resolving the issue, while manual resolution records its resolved state.

EC-14 | FR-10, FR-11, FR-12, FR-13 | Situation: Cached information is displayed after the freshness threshold. | Status: COVERED | Behaviour: Preserve the original last successful synchronization timestamp and display the stale warning; displaying or reloading the cache does not reset its age.

EC-15 | FR-12 | Situation: A service/data outage occurs before this device has cached any transport information. | Status: COVERED | Behaviour: Display a clear unavailable message; do not fabricate a schedule or imply that no service is scheduled.

EC-16 | FR-13 | Situation: The device is offline on first use and has no cached information. | Status: COVERED | Behaviour: State that information cannot be loaded until connectivity returns and synchronization succeeds.

EC-17 | FR-13 | Situation: Connectivity returns but automatic synchronization fails. | Status: COVERED | Behaviour: Retain cached information, its original timestamp, and the relevant warning; do not clear the warning until synchronization succeeds.

EC-18 | FR-11 | Situation: Data age is exactly 5 minutes or just over 5 minutes. | Status: COVERED | Behaviour: Exactly 5 minutes is fresh; greater than 5 minutes is stale and warned.

EC-19 | FR-03 | Situation: A date-specific schedule override exists. | Status: COVERED | Behaviour: The date-specific override takes precedence over the recurring weekly schedule.

EC-20 | FR-03 | Situation: A date-specific override specifies no service. | Status: COVERED | Behaviour: Display no service for that date and do not display the recurring weekly departures.

EC-21 | FR-05, FR-08 | Situation: Several urgent changes are active simultaneously. | Status: COVERED | Behaviour: Display a separate banner for each, newest first; each remains until manually removed or resolved.

EC-22 | FR-08 | Situation: An authorized user removes an urgent banner but the issue has not been resolved. | Status: COVERED | Behaviour: Hide the banner without marking the issue resolved.

EC-23 | FR-04 | Situation: An announcement reaches its configured expiry time. | Status: COVERED | Behaviour: Stop displaying the announcement. Its audit history remains; an associated urgent banner follows its separate manual lifecycle.

EC-24 | FR-04, FR-14b | Situation: A published announcement is edited. | Status: COVERED | Behaviour: Display the latest version; prior versions are not retained.

EC-25 | FR-06, FR-14a | Situation: An administrator saves transport-data changes but does not publish them. | Status: COVERED | Behaviour: Keep the changes as drafts; students continue to see the previous published data.

EC-26 | FR-07, FR-14a | Situation: An announcement is ready to publish. | Status: COVERED | Behaviour: Publish directly through its Publish action; a separate draft-publication step is not required.

EC-27 | FR-13, NFR-03 | Situation: Cached core transport information reaches 24 hours since its last successful synchronization. | Status: COVERED | Behaviour: The cached information is no longer available for offline display; the system must not present it as current.

EC-28 | FR-13, NFR-03 | Situation: The portal is online and transport information is being displayed. | Status: COVERED | Behaviour: The system attempts automatic synchronization every 1 minute; a failed attempt does not advance the timestamp or clear warnings.

EC-29 | FR-14b, BR-13 | Situation: An audit record reaches 30 days old. | Status: COVERED | Behaviour: The record is no longer required to be retained. Recovery is limited to previously published transport information; drafts and announcements are excluded.

EC-30 | FR-15, BR-25 | Situation: A user looks for official transport information on WhatsApp. | Status: COVERED | Behaviour: The portal is the official transport information channel; WhatsApp is not an official parallel publication channel under this release.

## 12. Acceptance Criteria

## Part A: Functional Requirements

### FR-01
- AC-FR-01-1 (verifies FR-01): Given a Student is not logged in, when the Student requests departure-time information, then the system displays it.
- AC-FR-01-2 (verifies FR-01): Given a member of the public is not logged in, when they request departure-time information, then the system displays it.
- AC-FR-01-3 (verifies FR-01): Given any viewer who is not logged in, when they view departure-time information, then the system does not require Login (D-01).

### FR-02
- AC-FR-02-1 (verifies FR-02): Given the current PKT date/time and a service grouping with at least one departure remaining today, when transport information is accessed, then the system selects the earliest departure for that service date at or after the current time.
- AC-FR-02-2 (verifies FR-02): Given a selected departure instance, when it is displayed, then its service date, scheduled departure time, Route, and Bus/Service Identifier are all shown.
- AC-FR-02-3 (verifies FR-02): Given a service grouping has no departure at or after the current PKT time on the current service date, when the current departure table is displayed, then it shows “No further departures today” for that grouping and does not label a past departure as current.
- AC-FR-02-4 (verifies FR-02): Given multiple Routes or Bus/Service Identifiers have different departure times, when the current departure table is displayed, then the next-upcoming departure is selected independently for each grouping.
- AC-FR-02-5 (verifies FR-02): Given the page is displayed, when it is viewed, then the current departure-time table appears below the header and before announcements (D-18).

### FR-03
- AC-FR-03-1 (verifies FR-03): Given the daily Schedule / Timetable is available, when transport information is accessed, then the system displays it.
- AC-FR-03-2 (verifies FR-03): Given the daily Schedule / Timetable is displayed, when it is viewed, then each departure is identified by its unique Route identifier and the physical Bus/Service Identifier assigned to that particular departure.
- AC-FR-03-3 (verifies FR-03): Given the page is displayed, when it is viewed, then that specific day's departure times appear after the announcements (D-18).
- AC-FR-03-4 (verifies FR-03 and BR-20): Given a service date has no date-specific override, when its Schedule / Timetable is displayed, then the applicable recurring weekly schedule is used.
- AC-FR-03-5 (verifies FR-03 and BR-20): Given a date-specific override exists, when that service date is displayed, then the override takes precedence over the recurring weekly schedule.
- AC-FR-03-6 (verifies FR-03 and BR-20): Given a date-specific override specifies no service, when that date is displayed, then no recurring departures are shown for that date.

### FR-04
- AC-FR-04-1 (verifies FR-04): Given announcements are available, when a Student accesses transport information, then the system displays them.
- AC-FR-04-2 (verifies FR-04): Given announcements are available, when a member of the public accesses transport information, then the system displays them.
- AC-FR-04-3 (verifies FR-04): Given Transport Management has published a non-transport-related notice, when a viewer accesses announcements, then the notice is displayed.
- AC-FR-04-4 (verifies FR-04 and BR-23): Given multiple announcements are published, when they are displayed, then they are ordered newest first.
- AC-FR-04-5 (verifies FR-04 and BR-23): Given an announcement is published with an expiry date/time, when that time passes, then it is no longer displayed.
- AC-FR-04-6 (verifies FR-04 and BR-23): Given an announcement is published with no expiry, when no authorized user has removed it, then it remains displayed.
- AC-FR-04-7 (verifies FR-04 and BR-23): Given a published announcement is edited, when the edit is saved, then the updated version is displayed and the previous version remains in the audit history.

### FR-05
- AC-FR-05-1 (verifies FR-05): Given an urgent change has been published, when a viewer accesses transport information, then the urgent change is displayed through both a persistent alert banner and an announcement (D-08).
- AC-FR-05-2 (verifies FR-05): Given an urgent announcement is displayed, when nobody has manually removed or resolved it, then it is not removed automatically (D-12).
- AC-FR-05-3 (verifies FR-05 and BR-21): Given either Transport Management or a designated administrator marks an announcement as urgent, when it is published, then a separate persistent banner and announcement are displayed.
- AC-FR-05-4 (verifies FR-05 and BR-22): Given multiple urgent changes are active, when the page is displayed, then each has a separate banner and the banners are ordered newest first.

### FR-06
- AC-FR-06-1 (verifies FR-06): Given Transport Management or a designated administrator, when they update Route, Bus/Service Identifier, coaster-to-route assignments or Schedule / Timetable information, then the system accepts the update.
- AC-FR-06-2 (verifies FR-06): Given a user who is neither Transport Management nor a designated administrator, when they attempt to edit this information, then the system does not allow the edit (D-20).
- AC-FR-06-3 (verifies FR-06 and BR-24): Given an authorized user saves a Route, Bus/Service Identifier, assignment, or Schedule / Timetable edit as a draft, when the user has not selected Publish, then students continue to see the previously published information.
- AC-FR-06-4 (verifies FR-06 and BR-24): Given an authorized user selects Publish for a saved transport-data draft, when publication succeeds, then the updated data becomes visible to students.

### FR-07
- AC-FR-07-1 (verifies FR-07): Given an authorized user prepares a transport-related or non-transport-related notice, when they publish it, then the system makes the announcement available.
- AC-FR-07-2 (verifies FR-07 and BR-15): Given an authorized user publishes an announcement with only a title, when publication succeeds, then the public response contains an empty body.
- AC-FR-07-3 (verifies FR-07 and BR-16): Given an announcement is published, when its persisted record and public response are inspected, then neither contains operational-change or confirmation state.
- AC-FR-07-4 (verifies FR-07): Given an unauthorized user, when they attempt to publish an announcement, then the system does not allow it (D-20).

### FR-08
- AC-FR-08-1 (verifies FR-08): Given an urgent announcement is displayed, when Transport Management or a designated administrator manually removes it, then it is no longer displayed as an urgent announcement (D-12).
- AC-FR-08-2 (verifies FR-08): Given an urgent announcement is displayed, when Transport Management or a designated administrator manually resolves it, then it is recorded as resolved (D-12).
- AC-FR-08-3 (verifies FR-08 and BR-22): Given an urgent banner is active, when an authorized user removes it, then it is hidden without being marked resolved.
- AC-FR-08-4 (verifies FR-08 and BR-22): Given an urgent banner is active, when an authorized user resolves it, then the system records the resolved state and stops displaying it as active.

### FR-09
- AC-FR-09-1 (verifies FR-09): Given a Student submits valid Feedback, when the submission succeeds, then it is delivered to Transport Management.
- AC-FR-09-2 (verifies FR-09): Given a member of the public submits valid Feedback, when the submission succeeds, then it is delivered to Transport Management.
- AC-FR-09-3 (verifies FR-09): Given a Feedback submission is successfully delivered, when the submission completes, then the user sees an on-screen success confirmation.
- AC-FR-09-4 (verifies FR-09 and BR-14): Given a user submits Feedback without a name or contact details, when the submission is otherwise valid, then the system accepts it anonymously.
- AC-FR-09-5 (verifies FR-09 and BR-14): Given a user chooses to provide a name or contact details, when the submission is otherwise valid, then the system accepts the optional details.
- AC-FR-09-6 (verifies FR-09 and BR-18): Given a Feedback submission populates the hidden honeypot field, when it is submitted, then the system rejects it and does not deliver it to Transport Management.
- AC-FR-09-7 (verifies FR-09 and BR-18): Given a Feedback submission is identical in content to a previous submission received within the preceding 10 minutes, when it is submitted, then the system rejects it and does not deliver it to Transport Management.
- AC-FR-09-8 (verifies FR-09 and BR-18): Given multiple Feedback submissions are made from the same IP address, when none populates the honeypot field and none duplicates a submission within the 10-minute period, then the system does not reject them solely because they share an IP address.
- AC-FR-09-9 (verifies FR-09): Given Feedback has been submitted, when the user expects follow-up, then the system does not imply that status tracking or a management dashboard is available in this release.

### FR-10
- AC-FR-10-1 (verifies FR-10): Given transport information has been successfully retrieved, when it is displayed, then the last successful synchronization timestamp is shown for the relevant data set in PKT.
- AC-FR-10-2 (verifies FR-10): Given cached information is displayed offline or during an outage, when it is viewed, then its original last successful synchronization timestamp is shown.
- AC-FR-10-3 (verifies FR-10): Given cached information is displayed or the page is reloaded, when no successful retrieval occurs, then the last successful synchronization timestamp does not change.

### FR-11
- AC-FR-11-1 (verifies FR-11): Given the last successful synchronization occurred no more than 5 minutes ago, when information is displayed, then it is treated as fresh and no stale warning is shown.
- AC-FR-11-2 (verifies FR-11): Given the last successful synchronization occurred more than 5 minutes ago, when information is displayed, then it is marked stale and the “Information may be outdated” warning and original timestamp are shown.
- AC-FR-11-3 (verifies FR-11): Given information is exactly 5 minutes old, when freshness is evaluated, then it remains fresh; when it is older than 5 minutes, it is stale.
- AC-FR-11-4 (verifies FR-11): Given stale cached information is displayed, when it is reloaded without a successful synchronization, then the timestamp and stale warning remain unchanged.

### FR-12
- AC-FR-12-1 (verifies FR-12): Given a service/data outage occurs and cached information exists within its 24-hour retention period, when transport information is accessed, then the last successfully synchronized information is displayed with an outage warning and its original timestamp; if it is also more than 5 minutes old, the stale warning is shown as well.
- AC-FR-12-2 (verifies FR-12): Given a service/data outage occurs and no cached information exists, when transport information is accessed, then an unavailable message is displayed and no fabricated/current-looking schedule is shown.
- AC-FR-12-3 (verifies FR-12): Given a service/data outage occurs while the device remains online, when the status is displayed, then it is identified as a service/data outage rather than offline device connectivity.

### FR-13
- AC-FR-13-1 (verifies FR-13): Given core information was previously loaded and remains within its 24-hour retention period, when the device is offline, then cached information remains available with an offline warning and its original synchronization timestamp; if it is also more than 5 minutes old, the stale warning is shown as well.
- AC-FR-13-2 (verifies FR-13): Given the device is offline on first use and no cache exists, when transport information is requested, then an unavailable message is displayed until connectivity returns and synchronization succeeds.
- AC-FR-13-3 (verifies FR-13): Given connectivity returns after offline use, when automatic synchronization succeeds, then the current published information replaces the cache, the timestamp is updated, and applicable offline/stale warnings are cleared.
- AC-FR-13-4 (verifies FR-13): Given connectivity returns but automatic synchronization fails, when the refresh attempt ends, then cached information, its original timestamp, and its warning remain.
- AC-FR-13-5 (verifies FR-13): Given connectivity permits, when the user requests manual refresh and retrieval succeeds, then the displayed information and timestamp are updated.
- AC-FR-13-6 (verifies FR-13): Given a refresh is attempted but does not successfully retrieve current data, when the attempt ends, then the timestamp is not advanced and cached information is not presented as newly updated.
- AC-FR-13-7 (verifies FR-13): Given cached core information was last synchronized less than 24 hours ago, when the device is offline, then the cached information remains available for offline viewing.
- AC-FR-13-8 (verifies FR-13): Given cached core information reaches 24 hours since its last successful synchronization, when the device is offline, then the cached information is no longer available for offline display.
- AC-FR-13-9 (verifies FR-13): Given the portal is online, when 1 minute elapses, then the system attempts automatic synchronization; a failed attempt does not update the timestamp or clear warnings.

### FR-14a
- AC-FR-14a-1 (verifies FR-14a): Given Transport Management or a designated administrator, when they publish transport information, then publication succeeds.
- AC-FR-14a-2 (verifies FR-14a): Given any other user, when they attempt to publish transport information, then the system does not allow it (D-20).
- AC-FR-14a-3 (verifies FR-14a and BR-24): Given transport-data changes are saved as a draft, when no separate Publish action has succeeded, then the changes are not visible to students.
- AC-FR-14a-4 (verifies FR-14a and BR-24): Given an authorized user publishes an announcement, when the Publish action succeeds, then the announcement becomes visible without a separate draft-publication step.


### FR-15
- AC-FR-15-1 (verifies FR-15): Given official transport schedules, route assignments, or announcements are published, when students or the public seek official transport information, then the portal is the authoritative source.
- AC-FR-15-2 (verifies FR-15): Given the release is operating, when official transport information is distributed, then the portal is used as the official channel and WhatsApp is not maintained as a parallel official publication channel.

### FR-14b
- AC-FR-14b-1 (verifies FR-14b): Given an authorized user makes an administrative edit, when the edit is successfully saved, then an audit record identifies the responsible user.
- AC-FR-14b-2 (verifies FR-14b): Given an authorized user successfully publishes transport information, when publication completes, then an audit record identifies the responsible user.
- AC-FR-14b-3 (verifies FR-14b): Given an accidental administrative change is identified, when correction or recovery is requested, then an authorized user may correct the information; recovery is limited to previously published transport information.
- AC-FR-14b-4 (verifies FR-14b): Given an accidental change is identified by Transport Management or a designated administrator, when recovery is requested, then only previously published transport information can be recovered; unpublished drafts and announcements cannot be recovered through this function.
- AC-FR-14b-5 (verifies FR-14b and BR-13): Given an audit record is created, when 30 days have elapsed, then the record is no longer required to be retained.

## Part B: Business rules with decided behaviour

- AC-BR-06-1 (verifies BR-06): Given two conflicting published updates, when both have been published, then the latest published update takes effect and the change is recorded (D-21).
- AC-BR-07-1 (verifies BR-07): Given a schedule entry is missing service date, departure time, Route, Bus/Service Identifier, or assignment, when it is submitted for publication, then the publisher is warned and may proceed with publication.
- AC-BR-07-2 (verifies BR-07): Given two different assignments exist for the same departure instance, when the schedule is submitted for publication, then the publisher is warned and may proceed with publication.
- AC-BR-07-3 (verifies BR-07): Given conflicting schedule information has been published, when students view the schedule, then only the latest published version is displayed and no separate conflict warning is shown.
- AC-BR-13-1 (verifies BR-13): Given an authorized user successfully saves an administrative edit, when the change is committed, then an audit record identifies that user.
- AC-BR-13-2 (verifies BR-13): Given an authorized user successfully publishes transport information, when publication completes, then an audit record identifies that user.
- AC-BR-16-1 (verifies BR-16): Given an announcement is published, when its persisted record is inspected, then it has no operational-change or confirmation field.
- AC-BR-17-1 (verifies BR-17): Given the student experience survey is conducted, when responses are evaluated, then at least 80% of surveyed students report that transport information is easy to access.
- AC-BR-20-1 (verifies BR-20): Given a recurring weekly schedule exists and no date-specific override applies, when a service date is displayed, then the recurring schedule is used.
- AC-BR-20-2 (verifies BR-20): Given a date-specific override exists, when its service date is displayed, then the override takes precedence over the recurring schedule.
- AC-BR-21-1 (verifies BR-21): Given an authorized Transport Management user or designated administrator marks an announcement as urgent, when it is published, then either role is permitted to make that determination.
- AC-BR-22-1 (verifies BR-22): Given multiple urgent changes are active, when banners are displayed, then each appears separately and newest first.
- AC-BR-22-2 (verifies BR-22): Given an active urgent banner, when an authorized user removes it, then it is hidden but not marked resolved.
- AC-BR-22-3 (verifies BR-22): Given an active urgent banner, when an authorized user resolves it, then its resolved state is recorded and the active banner is no longer displayed.
- AC-BR-23-1 (verifies BR-23): Given announcements have different publication times, when displayed, then newest announcements appear first.
- AC-BR-23-2 (verifies BR-23): Given an announcement is configured to expire, when its expiry time passes, then it is no longer displayed.
- AC-BR-23-3 (verifies BR-23): Given a published announcement is edited, when the new version is saved, then the latest content is displayed and the prior version is not retained.
- AC-BR-25-1 (verifies BR-25): Given official transport information is published, when students or the public access the authoritative source, then the portal provides it and WhatsApp is not used as a parallel official channel.
- AC-BR-24-1 (verifies BR-24): Given a transport-data edit is saved as a draft, when it has not been separately published, then students continue to see the previous published version.
- AC-BR-24-2 (verifies BR-24): Given an announcement is ready for publication, when an authorized user selects Publish, then it is published directly without a separate draft-publication step.

## Part C: Non-Functional Requirements

### Overall release acceptance
- AC-REL-01: Given the release acceptance review is performed, when all defined acceptance criteria are evaluated, then at least 95% pass and there are no critical defects.

### NFR-01
- AC-NFR-01-1 (verifies NFR-01): Given the server receives a publish request/update, when the published transport information becomes visible to students, then the elapsed time is no more than 5 seconds.
- AC-NFR-01-2 (verifies NFR-01): Given the performance test is run, when results are judged, then the baseline workload includes 500 concurrent users and 2,000 scheduled departures.
- AC-NFR-01-3 (verifies NFR-01): Given the performance test is run, when publication visibility is measured for the current departure table and daily Schedule / Timetable, then at least 95% of measured publication operations make the relevant information visible within 5 seconds.

### NFR-02
- AC-NFR-02-1 (verifies NFR-02): Given a mobile device, when a Student views departure-time information, views announcements and submits Feedback, then each task can be completed (D-15).
- AC-NFR-02-2 (verifies NFR-02): Given a laptop or desktop computer, when the same three tasks are performed, then each task can be completed (D-15).

### NFR-03
- AC-NFR-03-1 (verifies NFR-03): Given core information was previously loaded, when the system is offline, then it remains available with its original timestamp and an offline warning.
- AC-NFR-03-2 (verifies NFR-03): Given connectivity returns and automatic or manual refresh succeeds, when the refresh completes, then current information replaces cached information and the timestamp advances.
- AC-NFR-03-3 (verifies NFR-03): Given refresh fails, when the attempt completes, then cached data retains its original timestamp and warning.

### NFR-04
- AC-NFR-04-1 (verifies NFR-04): Given a recovery test is run in a test environment, when it finishes, then recovery time and data loss are recorded (D-29, D-30).
- AC-NFR-04-2 (verifies NFR-04): Given a recovery test is completed, when the results are evaluated, then recovery time is no more than 4 hours and data loss is no more than 1 hour. These two thresholds determine recovery-test acceptance.

## 13. Assumptions

- Students can access a browser on smartphones and/or computers.
- Transport Management will actively maintain the platform.
- Management owns and verifies transport data.
- Previously loaded core information can be retained for offline viewing.

## 14. Open Questions / Unresolved Decisions

- **OQ-01:** RESOLVED. Feedback submissions are delivered to Transport Management. A management dashboard and post-submission workflow/status tracking are out of scope for this release. [Related: FR-09]
- **OQ-02:** RESOLVED. Live GPS tracking is not included in the current release; departure selection is schedule-based and does not report a vehicle's live location. [Related: FR-02, FR-03]
- **OQ-03:** RESOLVED. The 5-second interval is measured from the server receiving the publish request/update until the published information becomes visible to students. Performance testing focuses on the current departure table and daily Schedule / Timetable, uses a baseline of 500 concurrent users and 2,000 scheduled departures, and requires at least 95% of measured publication operations to meet the 5-second target. [Related: NFR-01]
- **OQ-04:** RESOLVED. Record successful administrative edits and successful publication events, identifying the responsible individual account. Warning-only events and failed publication attempts are not required audit events for this release. [Related: FR-14b, BR-13]
- **OQ-05:** RESOLVED. After a successful Feedback submission, display a simple on-screen success confirmation. A unique submission/reference number is not required. [Related: FR-09]
- **OQ-06:** RESOLVED. Name and contact details are optional. Users may submit Feedback anonymously. [Related: FR-09, BR-14]
- **OQ-07:** RESOLVED. The first release supports all announcements published by Transport Management or designated administrators, including transport-related and non-transport-related notices. Announcement bodies are optional and operational-change state is not stored. [Related: FR-04, FR-07, BR-15, BR-16]
- **OQ-08:** RESOLVED. At least 80% of surveyed students shall report that transport information is easy to access. [Related: UG-01, G-01, BR-17]
- **OQ-09:** RESOLVED. Announcements publish directly and do not have an operational-change confirmation step. [Related: FR-07, BR-04, BR-16]
- **OQ-10:** RESOLVED. Adopt RTO of no more than 4 hours and RPO of no more than 1 hour. [Related: NFR-04]
- **OQ-11:** RESOLVED. Use a baseline performance-test scale of 500 concurrent users and 2,000 scheduled departures. The remaining performance-test details are resolved under OQ-03. [Related: NFR-01]
- **OQ-12:** RESOLVED. A recovery test passes when recovery time is no more than 4 hours and data loss is no more than 1 hour. [Related: NFR-04]
- **OQ-13:** RESOLVED. At least 95% of defined acceptance criteria must pass, with no critical defects. [Related: Section 12, NFR-03, NFR-04]
- **OQ-14:** RESOLVED. Use a hidden honeypot field for basic spam prevention and reject submissions identical in content to a previous submission received within the preceding 10 minutes. Do not apply an IP-based submission limit. [Related: FR-09, BR-18]
- **OQ-15:** RESOLVED. Route is a unique identifier; route locations and direction (`RETURN` or `PICK-UP`) are maintained separately. Bus/Service Identifier identifies an individual physical coaster. A Route-to-bus assignment associates that physical coaster with a Route, and each schedule row automatically applies to every assigned bus. [Related: FR-02, FR-03, FR-06]
- **OQ-16:** RESOLVED. “Current departure” means the next-upcoming departure instance selected independently for each Route and Bus/Service Identifier for the current service date in PKT. It is identified by service date, scheduled departure date/time, Route, and Bus/Service Identifier. After the final departure for a grouping, show “No further departures today”. This is schedule-based, not GPS/live tracking. [Related: FR-02]
- **OQ-17:** RESOLVED. The Schedule / Timetable uses a recurring weekly schedule as its base. A date-specific override takes precedence for the date it covers and may specify a no-service day. Future dates use the recurring weekly schedule unless an override exists. [Related: FR-03, BR-20]
- **OQ-18:** RESOLVED. Both Transport Management and designated administrators may mark an announcement as urgent before publication. [Related: FR-05, BR-05, BR-21]
- **OQ-19:** RESOLVED. Each urgent change has a separate banner. Banners remain until manually removed or resolved by Transport Management or a designated administrator and are ordered newest first. Removal hides the banner without marking the change resolved; resolution records the resolved state. [Related: FR-05, FR-08, BR-05, BR-22]
- **OQ-20:** RESOLVED. At publication, the authorized user chooses a PKT expiry date/time or that the announcement remains visible until manually removed. Announcements are ordered newest first. Published announcements may be edited without retaining prior versions; an urgent banner remains governed by its separate manual-removal/resolution rule. [Related: FR-04, FR-07, FR-14b, BR-23]
- **OQ-21:** RESOLVED. Route, Bus/Service Identifier, assignment, and Schedule / Timetable changes are saved as drafts and require a separate Publish action. Announcements are published directly through their Publish action without a separate draft-publication workflow. [Related: FR-06, FR-07, FR-14a, BR-24]
- **OQ-22:** RESOLVED. A schedule entry is incomplete if service date, departure time, Route, Bus/Service Identifier, or coaster-to-route assignment is missing. A conflict exists when two different assignments are recorded for the same departure instance. The publisher is warned but may proceed. Students see only the latest published version, without a separate conflict warning. [Related: FR-03, BR-06, BR-07]
- **OQ-23:** RESOLVED (5-minute default adopted in this PRD): Information is fresh for 5 minutes after the last successful synchronization and stale after 5 minutes. The timestamp advances only on successful retrieval. Stale, offline, and service/data-outage states have distinct warnings; cached data always retains its original timestamp. [Related: FR-10, FR-11, FR-12, FR-13]
- **OQ-24:** RESOLVED. Previously loaded core transport information is retained for offline viewing for 24 hours after its last successful synchronization. While online, automatic synchronization is attempted every 1 minute. First use without cache displays an unavailable message; reconnection triggers automatic refresh and manual refresh is also available. [Related: FR-13, NFR-03]
- **OQ-25:** RESOLVED. Only previously published transport information is recoverable after an accidental change. Transport Management or a designated administrator may identify the change as accidental. Audit records, including retained announcement versions, are kept for 30 days. Unpublished drafts and announcements are excluded from recovery. [Related: FR-14b, BR-13]
- **OQ-26:** RESOLVED. The portal replaces WhatsApp as the official transport information channel. The portal is the authoritative channel for schedules, route assignments, and announcements; a parallel official WhatsApp publication channel or WhatsApp integration is not part of this release. [Related: FR-15, BR-25, C-06]

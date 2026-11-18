# AGENTS.md

## Project

Uzair Transport Service is a public transport-information portal for
students and the wider university community. It provides published route
and schedule information, current departures, announcements, urgent
notices, and a public feedback channel. Privileged transport-management
functions are available only to authorized Transport Management
personnel and designated administrators.

Before implementation, read the approved `PRD.md` (the validated source
currently supplied as `Validated PRD.md`), `architecture.md`, and
relevant project documentation. The PRD defines product requirements;
`architecture.md` describes the system architecture and its rationale.
This file contains operational instructions for coding agents and does
not replace either document.

## Before implementation

-   Identify the requirements and architectural constraints relevant to
    the requested change.
-   Identify the module(s), interfaces, and data ownership affected.
-   Follow the existing repository structure, naming, tooling, and
    testing conventions. Do not invent a new structure when one already
    exists.
-   If the initial codebase does not exist, propose a small project
    structure based on the documented modules and obtain human approval
    before creating implementation files.
-   Raise missing requirements or conflicting documentation before
    making assumptions that affect security, data integrity, or system
    behaviour.

## Architecture and module boundaries

Use the **modular monolith** described in `architecture.md`:

-   **Public PWA** and **Admin Web App** are separate clients.
-   Both clients communicate with the **Backend API**. Neither client
    may access the database directly.
-   The backend contains the following logical modules:
    -   **Authentication:** Self-hosted Supabase Auth for individual
        privileged accounts, with backend authorization for Transport
        Management and designated administrators.
    -   **Transport Data:** Routes, route locations and directions,
        bus/service identifiers, assignments, schedules, draft and
        published versions, and current-departure calculation.
    -   **Announcement:** Announcement and urgent-notice content,
        direct publication, PKT expiry/removal, 30-day record retention,
        and persistent urgent-banner lifecycle. It does not retain prior
        announcement versions or audit history.
    -   **Feedback:** Public feedback intake, honeypot validation,
        duplicate detection, and delivery to the configured Transport
        Management destination.
    -   **Audit:** Owns the persisted append-only transport-publication
        log (publisher and publication time only), its 30-day retention,
        and recovery of previously published transport data. It does not
        record edits, announcement revisions, or login/logout events.
    -   **Reporting:** Read-only administrative views only if required
        and approved; it must not own or modify other modules' data.

Modules must communicate through documented public interfaces. A module
must not access another module's private tables, persistence adapters,
or internal implementation. Keep each module responsible for its own
data and business rules.

## Architectural constraints

-   Keep the backend as one modular-monolith application; do not
    introduce microservices or additional deployment units without human
    approval.
-   Use **PostgreSQL** as the relational system of record.
-   Represent route, schedule, and assignment draft/published data as
    versioned records using `status` and `version`. Public reads must
    return published versions only.
-   Transport changes must be saved as drafts and require a separate
    publish action. Publishing must create a new version, write the
    audit record, and synchronously invalidate relevant cache entries.
-   Recovery is limited to previously published transport data; drafts
    must never be restored through this function.
-   Announcements publish directly; they do not use the transport
    draft/publish workflow.
-   An urgent operational change requires both an announcement and a
    separate persistent banner. Removing a banner is distinct from
    resolving it.
-   Public transport reads do not require authentication. All privileged
    operations must be authorized by the backend.
-   Use Pakistan Standard Time (PKT) for service-date and departure
    calculations. Do not rely on the server's local timezone.
-   The client cache is not a source of truth. Preserve the last
    successful synchronization time when refresh fails or cached data is
    displayed.
-   Feedback must support anonymous submissions, honeypot validation,
    normalized-content duplicate detection within the preceding 10
    minutes, SMTP delivery, and 30-day retention. Do not introduce
    IP-based limiting or a feedback status-tracking dashboard.
-   Do not introduce GPS/live tracking, payments, WhatsApp integration,
    or an AI chatbot; these are outside the documented scope.

## Implementation and verification

-   Make changes consistent with the existing codebase and keep module
    names and responsibilities clear.
-   Add or update tests for changed behaviour, especially authorization,
    draft/publication isolation, versioning, audit consistency, schedule
    calculations, urgent-banner lifecycle, feedback validation, and
    offline/freshness behaviour where relevant.
-   Run the repository's applicable formatter, linter, type checks,
    tests, and build. Use the commands defined by the actual project; do
    not assume a package manager or framework.
-   Never report a check as passed unless it was actually run
    successfully.
-   Use synthetic data in tests and examples. Do not commit credentials,
    secrets, production data, or private keys.
-   Do not run destructive operations against shared, staging, or
    production environments without explicit human approval.

## Human approval required

Obtain human approval before:

-   Changing the modular-monolith architecture, module ownership, or a
    documented cross-module interface.
-   Selecting an undecided technology, database engine, hosting
    provider, or external service.
-   Adding infrastructure, a new database, a deployment unit, or a
    third-party integration.
-   Changing authentication or authorization policy, data-retention
    rules, recovery behaviour, or draft/publication semantics.
-   Making destructive data changes or deploying to a shared or
    production environment.

## Handling decisions and conflicts

Follow the PRD for product behaviour, `architecture.md` for
architectural structure, and accepted ADRs for recorded architectural
decisions. An accepted ADR takes precedence over an earlier conflicting
architectural description where it explicitly records a later decision.
Do not invent missing decisions or silently resolve contradictions;
pause the affected work and ask the developer.

The current project decisions include self-hosted Supabase Auth,
PostgreSQL as the relational system of record, versioned transport
records, FastAPI with handwritten async SQL/migrations, separate Next.js
clients, and a single-worker in-process read cache. ADR-011 records the
approved implementation and policy profile and supersedes conflicting
older ADR clauses. Review the complete ADR collection before changing
affected architecture or behaviour.

## Completion report

After completing a requested change, briefly report:

-   What was changed and which requirements it addresses.
-   Which tests and checks were run, with their actual results.
-   Any unresolved questions, limitations, or architectural deviations.

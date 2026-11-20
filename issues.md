# Encountered Issues

This log records verified implementation and local-development issues encountered
while delivering Slice 2. It distinguishes product-code fixes from machine-local
environment problems.

| Slice | Issue | Summary |
|---|---|---|
| S2 | Incomplete change-set workflow | The initial Slice 2 work only created, validated, rebased, and published drafts; draft updates, publication history, recovery, retention cleanup, and transaction-joining Audit writes were added to complete the slice. |
| S2 | Draft-create endpoint returned 404 | The admin application was calling the correct URL, but an old FastAPI process was still running and its OpenAPI document did not include the Slice 2 router. Restarting the backend with current source restored the route; unauthenticated requests now correctly return `401`. |
| S2 | Tailwind directives were not compiled | The admin app lacked an effective monorepo PostCSS configuration, so the browser received literal `@tailwind` directives and TSX utility classes had no effect. Root and app PostCSS configuration now compile Tailwind utilities. |
| S2 | Next.js cache failures under OneDrive | Stale `.next` cache entries caused `EINVAL`/`readlink` errors and a missing generated chunk, leading to HTTP 500 responses and failed browser tests. Restarting after moving the regenerable admin cache aside restored the admin server; the cache remains an environment risk. |
| S2 | Cypress browser verification blocked | Cypress could not load the public PWA because the stale local Next.js server returned HTTP 500 before test execution. Backend, lint, type-check, and production-build checks succeeded; rerun Cypress after rebuilding its `.next` cache. |
| S2 | Local Git credential helper could not push | Git Credential Manager waited for unavailable interactive credentials and non-interactive push reported no password. The GitHub connector created and advanced the remote branch instead. |

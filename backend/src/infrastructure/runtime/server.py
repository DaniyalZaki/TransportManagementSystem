"""Approved Uvicorn runtime profile.

The in-process read cache is safe only with one worker.  Keep these values in
one importable location so the release configuration is testable rather than a
README-only convention.
"""

HOST = "0.0.0.0"
PORT = 8000
WORKERS = 1
LIMIT_CONCURRENCY = 500
APP_IMPORT = "src.application.main:app"


def run(uvicorn_run) -> None:
    """Start the approved single-worker Uvicorn process.

    ``uvicorn_run`` is injected to keep this operational boundary testable
    without starting a server in the unit suite.
    """
    uvicorn_run(
        APP_IMPORT,
        app_dir="backend",
        host=HOST,
        port=PORT,
        workers=WORKERS,
        limit_concurrency=LIMIT_CONCURRENCY,
    )

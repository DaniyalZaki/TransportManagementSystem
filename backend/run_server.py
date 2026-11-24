"""Start the backend with the approved single-worker Uvicorn profile."""

import uvicorn

from src.infrastructure.runtime.server import run


if __name__ == "__main__":
    run(uvicorn.run)

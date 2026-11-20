from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any


@asynccontextmanager
async def open_connection(database_url: str) -> AsyncIterator[Any]:
    """Open a short-lived raw async PostgreSQL connection for a module-owned query."""
    try:
        import asyncpg
    except ImportError as error:
        raise RuntimeError(
            "Install the backend postgres extra before using PostgreSQL persistence"
        ) from error
    connection = await asyncpg.connect(database_url)
    try:
        yield connection
    finally:
        await connection.close()

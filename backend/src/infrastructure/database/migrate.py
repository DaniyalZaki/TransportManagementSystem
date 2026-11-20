import argparse
import asyncio
from pathlib import Path

import asyncpg


async def apply_migrations(database_url: str) -> None:
    """Apply handwritten SQL migrations in lexical order."""
    connection = await asyncpg.connect(database_url)
    try:
        for migration in sorted(Path(__file__).with_name("migrations").glob("*.sql")):
            await connection.execute(migration.read_text(encoding="utf-8"))
    finally:
        await connection.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("database_url")
    args = parser.parse_args()
    asyncio.run(apply_migrations(args.database_url))

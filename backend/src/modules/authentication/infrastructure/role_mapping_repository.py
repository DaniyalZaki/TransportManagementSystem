from src.application.authorization.roles import Role
from src.infrastructure.database.connection import open_connection
from src.modules.authentication.domain.role_mapping import RoleMapping


class PostgresRoleMappingRepository:
    """Authentication's raw-SQL persistence adapter; no other module owns this table."""

    def __init__(self, database_url: str) -> None:
        self._database_url = database_url

    async def get(self, supabase_user_id: str) -> RoleMapping | None:
        async with open_connection(self._database_url) as connection:
            row = await connection.fetchrow(
                """
                SELECT supabase_user_id, role, is_active, deactivated_at
                FROM authentication_role_mappings
                WHERE supabase_user_id = $1
                """,
                supabase_user_id,
            )
        return self._to_mapping(row) if row else None

    async def create(self, supabase_user_id: str, role: Role) -> RoleMapping:
        async with open_connection(self._database_url) as connection:
            row = await connection.fetchrow(
                """
                INSERT INTO authentication_role_mappings (supabase_user_id, role)
                VALUES ($1, $2)
                RETURNING supabase_user_id, role, is_active, deactivated_at
                """,
                supabase_user_id,
                role.value,
            )
        return self._to_mapping(row)

    async def deactivate(self, supabase_user_id: str) -> None:
        async with open_connection(self._database_url) as connection:
            await connection.execute(
                """
                UPDATE authentication_role_mappings
                SET is_active = FALSE, deactivated_at = now()
                WHERE supabase_user_id = $1
                """,
                supabase_user_id,
            )

    @staticmethod
    def _to_mapping(row: object) -> RoleMapping:
        record = row  # asyncpg.Record supports mapping-style indexed access.
        return RoleMapping(
            supabase_user_id=str(record["supabase_user_id"]),  # type: ignore[index]
            role=Role(record["role"]),  # type: ignore[index]
            active=bool(record["is_active"]),  # type: ignore[index]
            deactivated_at=record["deactivated_at"],  # type: ignore[index]
        )

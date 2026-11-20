from typing import Protocol

from src.modules.transport_data.domain.schedule import PublishedTransportSnapshot


class PublishedSnapshotRepository(Protocol):
    """Transport Data's public-read persistence boundary."""

    async def get_current(self) -> PublishedTransportSnapshot | None: ...

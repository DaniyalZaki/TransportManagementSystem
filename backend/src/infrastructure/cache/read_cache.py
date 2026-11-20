from typing import TypeVar


T = TypeVar("T")


class InMemoryReadCache:
    """A single-worker cache; it is never the source of truth."""

    def __init__(self) -> None:
        self._values: dict[str, object] = {}

    def get(self, key: str) -> T | None:
        return self._values.get(key)  # type: ignore[return-value]

    def set(self, key: str, value: T) -> None:
        self._values[key] = value

    def invalidate(self, key: str) -> None:
        self._values.pop(key, None)

    def clear(self) -> None:
        self._values.clear()

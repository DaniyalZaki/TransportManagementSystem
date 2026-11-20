from src.infrastructure.cache.read_cache import InMemoryReadCache


def test_cache_returns_value_until_explicit_invalidation() -> None:
    cache = InMemoryReadCache()
    cache.set("published:routes", {"version": 1})

    assert cache.get("published:routes") == {"version": 1}

    cache.invalidate("published:routes")

    assert cache.get("published:routes") is None


def test_cache_is_not_a_source_of_truth_after_clear() -> None:
    cache = InMemoryReadCache()
    cache.set("published:schedules", ["08:00"])

    cache.clear()

    assert cache.get("published:schedules") is None

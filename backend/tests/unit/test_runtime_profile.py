from src.infrastructure.runtime.server import (
    APP_IMPORT,
    HOST,
    LIMIT_CONCURRENCY,
    PORT,
    WORKERS,
    run,
)


def test_runtime_profile_uses_one_worker_and_hard_500_connection_cap() -> None:
    calls = []

    run(lambda *args, **kwargs: calls.append((args, kwargs)))

    assert calls == [
        (
            (APP_IMPORT,),
            {
                "app_dir": "backend",
                "host": HOST,
                "port": PORT,
                "workers": 1,
                "limit_concurrency": 500,
            },
        )
    ]
    assert WORKERS == 1
    assert LIMIT_CONCURRENCY == 500

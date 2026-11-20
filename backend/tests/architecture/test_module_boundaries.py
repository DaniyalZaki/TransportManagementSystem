from pathlib import Path


def test_backend_declares_the_required_logical_modules() -> None:
    modules = Path("src/modules")
    expected = {
        "announcement",
        "audit",
        "authentication",
        "feedback",
        "reporting",
        "transport_data",
    }

    assert expected <= {path.name for path in modules.iterdir() if path.is_dir()}

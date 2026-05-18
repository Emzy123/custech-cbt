"""Minimal smoke tests for current backend track."""


def test_project_imports():
    """Ensure core package imports in test environment."""
    from src.cbt.main import app

    assert app is not None

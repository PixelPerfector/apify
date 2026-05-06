"""Shared pytest fixtures for moldova_bank_rates tests."""
from __future__ import annotations

from pathlib import Path

import pytest

FIXTURE_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixture_bytes():
    """Return a function that loads a fixture file as raw bytes."""

    def _load(relative_path: str) -> bytes:
        return (FIXTURE_DIR / relative_path).read_bytes()

    return _load


@pytest.fixture
def fixture_text():
    """Return a function that loads a fixture file as decoded text."""

    def _load(relative_path: str, encoding: str = "utf-8") -> str:
        return (FIXTURE_DIR / relative_path).read_text(encoding=encoding)

    return _load

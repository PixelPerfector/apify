"""Tests for shared parsing normalizers."""
from __future__ import annotations

import pytest

from moldova_bank_rates.normalizers import normalize_number, normalize_pair


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("19,45", 19.45),
        ("1 945,32", 1945.32),
        ("19.4500", 19.45),
        ("  19,4500  ", 19.45),
        ("1,945.32", 1945.32),
    ],
)
def test_normalize_number(raw, expected):
    assert normalize_number(raw) == pytest.approx(expected)


def test_normalize_number_returns_none_on_empty():
    assert normalize_number("") is None
    assert normalize_number("—") is None
    assert normalize_number(None) is None


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("EUR/MDL", ("EUR", "MDL")),
        ("eur-mdl", ("EUR", "MDL")),
        ("EURMDL", ("EUR", "MDL")),
        ("usd_mdl", ("USD", "MDL")),
    ],
)
def test_normalize_pair(raw, expected):
    assert normalize_pair(raw) == expected


def test_normalize_pair_rejects_invalid():
    with pytest.raises(ValueError):
        normalize_pair("EU/MDL")
    with pytest.raises(ValueError):
        normalize_pair("EURMDLX")

"""Tests for Pydantic models."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from moldova_bank_rates.models import Rate


def _base_kwargs(**overrides):
    kwargs = dict(
        pair="EUR/MDL",
        base="EUR",
        quote="MDL",
        bank="maib",
        bank_display_name="Moldova Agroindbank",
        rate_type="cash",
        buy=19.45,
        sell=19.85,
        currency_unit=1,
        timestamp=datetime(2026, 5, 6, 14, 30, tzinfo=timezone.utc),
        bank_updated_at=None,
        source_url="https://maib.md/en/exchange-rates",
        available=True,
    )
    kwargs.update(overrides)
    return kwargs


def test_rate_computes_mid_and_spread():
    rate = Rate(**_base_kwargs())
    assert rate.mid == pytest.approx(19.65)
    assert rate.spread_pct == pytest.approx(((19.85 - 19.45) / 19.65) * 100)


def test_rate_mid_is_none_when_either_leg_missing():
    rate = Rate(**_base_kwargs(buy=None))
    assert rate.mid is None
    assert rate.spread_pct is None


def test_rate_pair_must_match_base_quote():
    with pytest.raises(ValidationError):
        Rate(**_base_kwargs(pair="USD/MDL"))


def test_rate_currency_codes_must_be_iso_4217_shape():
    with pytest.raises(ValidationError):
        Rate(**_base_kwargs(base="EU", pair="EU/MDL"))


def test_rate_marks_unavailable_when_sell_lower_than_buy():
    rate = Rate(**_base_kwargs(buy=20.0, sell=19.0))
    assert rate.available is False


def test_rate_timestamp_must_be_timezone_aware():
    with pytest.raises(ValidationError):
        Rate(**_base_kwargs(timestamp=datetime(2026, 5, 6, 14, 30)))

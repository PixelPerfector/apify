"""Offline parser test for BNM XML."""
from __future__ import annotations

from datetime import datetime, timezone

from moldova_bank_rates.banks.bnm import parse_bnm
from moldova_bank_rates.models import Rate


def test_parse_bnm_returns_rates(fixture_bytes):
    xml = fixture_bytes("bnm/rates.xml")
    fetched_at = datetime(2026, 5, 6, 14, 30, tzinfo=timezone.utc)

    rates = parse_bnm(xml, fetched_at=fetched_at)

    assert len(rates) >= 5
    assert all(isinstance(r, Rate) for r in rates)
    eur = next(r for r in rates if r.base == "EUR")
    assert eur.quote == "MDL"
    assert eur.rate_type == "card"  # BNM publishes a single reference rate; we tag it as card
    assert eur.bank == "bnm"
    assert eur.buy == eur.sell  # reference rate has no spread
    assert eur.timestamp == fetched_at

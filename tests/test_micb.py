"""Offline parser test for MICB."""
from __future__ import annotations

from datetime import datetime, timezone

from moldova_bank_rates.banks.micb import parse_micb
from moldova_bank_rates.models import Rate


FETCHED_AT = datetime(2026, 5, 6, 14, 30, tzinfo=timezone.utc)


def test_parse_micb_returns_cash_and_card(fixture_bytes):
    rates = parse_micb(fixture_bytes("micb/rates.html"), fetched_at=FETCHED_AT)
    assert all(isinstance(r, Rate) for r in rates)
    assert all(r.bank == "micb" for r in rates)

    cash = [r for r in rates if r.rate_type == "cash"]
    card = [r for r in rates if r.rate_type == "card"]
    assert len(cash) == 7, f"expected 7 cash rows, got {len(cash)}"
    assert len(card) == 2, f"expected 2 card rows, got {len(card)}"


def test_parse_micb_eur_cash_known_values(fixture_bytes):
    rates = parse_micb(fixture_bytes("micb/rates.html"), fetched_at=FETCHED_AT)
    eur_cash = next(r for r in rates if r.base == "EUR" and r.rate_type == "cash")
    assert eur_cash.buy == 20.10
    assert eur_cash.sell == 20.29
    assert eur_cash.available is True


def test_parse_micb_eur_card_known_values(fixture_bytes):
    rates = parse_micb(fixture_bytes("micb/rates.html"), fetched_at=FETCHED_AT)
    eur_card = next(r for r in rates if r.base == "EUR" and r.rate_type == "card")
    assert eur_card.buy == 20.00
    assert eur_card.sell == 20.50


def test_parse_micb_marks_uah_and_rub_cash_unavailable(fixture_bytes):
    rates = parse_micb(fixture_bytes("micb/rates.html"), fetched_at=FETCHED_AT)
    for code in ("UAH", "RUB"):
        match = next(r for r in rates if r.base == code and r.rate_type == "cash")
        assert match.buy is None, f"{code} cash buy should be None"
        assert match.sell is None, f"{code} cash sell should be None"
        assert match.available is False, f"{code} cash should be unavailable"


def test_parse_micb_card_currencies_are_usd_eur(fixture_bytes):
    """The card panel exposes only USD and EUR — order in source HTML is USD first."""
    rates = parse_micb(fixture_bytes("micb/rates.html"), fetched_at=FETCHED_AT)
    card_codes = [r.base for r in rates if r.rate_type == "card"]
    assert set(card_codes) == {"USD", "EUR"}

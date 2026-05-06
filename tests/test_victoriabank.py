"""Offline parser test for Victoriabank."""
from __future__ import annotations

from datetime import datetime, timezone

from moldova_bank_rates.banks.victoriabank import parse_victoriabank
from moldova_bank_rates.models import Rate


FETCHED_AT = datetime(2026, 5, 6, 14, 30, tzinfo=timezone.utc)


def test_parse_victoriabank_returns_cash_and_card(fixture_bytes):
    rates = parse_victoriabank(
        fixture_bytes("victoriabank/rates.html"), fetched_at=FETCHED_AT
    )
    assert all(isinstance(r, Rate) for r in rates)
    assert all(r.bank == "victoriabank" for r in rates)

    cash = [r for r in rates if r.rate_type == "cash"]
    card = [r for r in rates if r.rate_type == "card"]
    assert len(cash) == 5, f"expected 5 cash rows, got {len(cash)}"
    assert len(card) == 4, f"expected 4 card rows, got {len(card)}"


def test_parse_victoriabank_eur_cash_known_values(fixture_bytes):
    rates = parse_victoriabank(
        fixture_bytes("victoriabank/rates.html"), fetched_at=FETCHED_AT
    )
    eur_cash = next(r for r in rates if r.base == "EUR" and r.rate_type == "cash")
    assert eur_cash.buy == 20.07
    assert eur_cash.sell == 20.32
    assert eur_cash.available is True


def test_parse_victoriabank_card_includes_rub_excludes_gbp_and_chf(fixture_bytes):
    rates = parse_victoriabank(
        fixture_bytes("victoriabank/rates.html"), fetched_at=FETCHED_AT
    )
    card_codes = {r.base for r in rates if r.rate_type == "card"}
    assert card_codes == {"EUR", "USD", "RON", "RUB"}


def test_parse_victoriabank_skips_header_rows(fixture_bytes):
    """The header `.tr` (with `.th` cells) must not produce a Rate."""
    rates = parse_victoriabank(
        fixture_bytes("victoriabank/rates.html"), fetched_at=FETCHED_AT
    )
    assert all(r.base.isalpha() and len(r.base) == 3 for r in rates)

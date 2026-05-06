"""Offline parser test for MAIB."""
from __future__ import annotations

from datetime import datetime, timezone

from moldova_bank_rates.banks.maib import parse_maib
from moldova_bank_rates.models import Rate


FETCHED_AT = datetime(2026, 5, 6, 14, 30, tzinfo=timezone.utc)


def test_parse_maib_returns_cash_and_card(fixture_bytes):
    rates = parse_maib(fixture_bytes("maib/rates.html"), fetched_at=FETCHED_AT)
    assert all(isinstance(r, Rate) for r in rates)

    cash = [r for r in rates if r.rate_type == "cash"]
    card = [r for r in rates if r.rate_type == "card"]
    assert cash, "expected cash rates from MAIB branches"
    assert card, "expected card rates from MAIB"
    assert all(r.bank == "maib" for r in rates)


def test_parse_maib_eur_cash_known_values(fixture_bytes):
    rates = parse_maib(fixture_bytes("maib/rates.html"), fetched_at=FETCHED_AT)
    eur_cash = next(r for r in rates if r.base == "EUR" and r.rate_type == "cash")
    assert eur_cash.buy == 20.10
    assert eur_cash.sell == 20.30
    assert eur_cash.available is True


def test_parse_maib_eur_card_known_values(fixture_bytes):
    rates = parse_maib(fixture_bytes("maib/rates.html"), fetched_at=FETCHED_AT)
    eur_card = next(r for r in rates if r.base == "EUR" and r.rate_type == "card")
    assert eur_card.buy == 19.98
    assert eur_card.sell == 20.42


def test_parse_maib_marks_unavailable_when_dash(fixture_bytes):
    rates = parse_maib(fixture_bytes("maib/rates.html"), fetched_at=FETCHED_AT)
    rub_cash_candidates = [r for r in rates if r.base == "RUB" and r.rate_type == "cash"]
    # RUB cash is published as "-" in the fixture; we expect either:
    #   (a) a Rate with buy=None, sell=None, available=False, OR
    #   (b) the row is skipped entirely (no RUB cash record).
    if rub_cash_candidates:
        rub = rub_cash_candidates[0]
        assert rub.buy is None
        assert rub.sell is None
        assert rub.available is False


def test_parse_maib_only_emits_branches_and_card_sections(fixture_bytes):
    """Customs-agency tables (three-*-new) should NOT be emitted in v1."""
    rates = parse_maib(fixture_bytes("maib/rates.html"), fetched_at=FETCHED_AT)
    # Cash should only have branch entries (EUR, USD, GBP, RON, UAH, CHF — RUB may
    # appear as unavailable). At most 7 cash rows.
    cash = [r for r in rates if r.rate_type == "cash"]
    assert len(cash) <= 7
    # Card should be small set (EUR, USD only in fixture).
    card = [r for r in rates if r.rate_type == "card"]
    assert len(card) == 2

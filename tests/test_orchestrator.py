"""Tests for per-bank error isolation in the orchestrator."""
from __future__ import annotations

from datetime import datetime, timezone

import httpx
import pytest

from moldova_bank_rates.models import Rate
from moldova_bank_rates.orchestrator import gather_all_rates


class _OkFetcher:
    slug = "ok"
    display_name = "OK Bank"
    source_url = "https://example.com/ok"

    async def fetch(self, client: httpx.AsyncClient) -> list[Rate]:
        return [
            Rate(
                pair="EUR/MDL",
                base="EUR",
                quote="MDL",
                bank="ok",
                bank_display_name="OK Bank",
                rate_type="card",
                buy=19.0,
                sell=19.5,
                currency_unit=1,
                timestamp=datetime(2026, 5, 6, tzinfo=timezone.utc),
                source_url=self.source_url,
            )
        ]


class _BoomFetcher:
    slug = "boom"
    display_name = "Boom Bank"
    source_url = "https://example.com/boom"

    async def fetch(self, client: httpx.AsyncClient) -> list[Rate]:
        raise RuntimeError("boom")


@pytest.mark.asyncio
async def test_one_bank_failure_does_not_break_others():
    async with httpx.AsyncClient() as client:
        rates, errors = await gather_all_rates(
            client=client,
            fetchers=[_OkFetcher(), _BoomFetcher()],
            wanted_pairs={"EUR/MDL"},
            wanted_rate_types={"card"},
        )

    assert len(rates) == 1
    assert rates[0].bank == "ok"
    assert errors == [("boom", "boom")]


@pytest.mark.asyncio
async def test_filters_by_pair_and_rate_type():
    """Even when a fetcher returns extra pairs/types, the orchestrator drops them."""

    class _NoisyFetcher:
        slug = "noisy"
        display_name = "Noisy Bank"
        source_url = "https://example.com/noisy"

        async def fetch(self, client: httpx.AsyncClient) -> list[Rate]:
            common = dict(
                bank="noisy",
                bank_display_name="Noisy Bank",
                currency_unit=1,
                timestamp=datetime(2026, 5, 6, tzinfo=timezone.utc),
                source_url=self.source_url,
            )
            return [
                Rate(pair="EUR/MDL", base="EUR", quote="MDL", rate_type="cash",
                     buy=19.0, sell=19.5, **common),
                Rate(pair="EUR/MDL", base="EUR", quote="MDL", rate_type="card",
                     buy=19.1, sell=19.4, **common),
                Rate(pair="USD/MDL", base="USD", quote="MDL", rate_type="cash",
                     buy=17.0, sell=17.3, **common),
            ]

    async with httpx.AsyncClient() as client:
        rates, errors = await gather_all_rates(
            client=client,
            fetchers=[_NoisyFetcher()],
            wanted_pairs={"EUR/MDL"},
            wanted_rate_types={"cash"},
        )

    assert errors == []
    assert len(rates) == 1
    assert rates[0].pair == "EUR/MDL"
    assert rates[0].rate_type == "cash"

"""Parallel per-bank fetch with error isolation and timing."""
from __future__ import annotations

import asyncio
import time
from typing import Iterable

import httpx
from apify import Actor

from moldova_bank_rates.banks.base import BankFetcher
from moldova_bank_rates.models import Rate


async def _run_one(
    fetcher: BankFetcher,
    client: httpx.AsyncClient,
    wanted_pairs: set[str],
    wanted_rate_types: set[str],
) -> tuple[str, list[Rate], float, str | None]:
    t0 = time.perf_counter()
    try:
        rates = await fetcher.fetch(client)
    except Exception as exc:  # noqa: BLE001 — isolate per bank
        return fetcher.slug, [], time.perf_counter() - t0, str(exc)
    kept = [
        r for r in rates
        if r.pair in wanted_pairs and r.rate_type in wanted_rate_types
    ]
    return fetcher.slug, kept, time.perf_counter() - t0, None


async def gather_all_rates(
    *,
    client: httpx.AsyncClient,
    fetchers: Iterable[BankFetcher],
    wanted_pairs: set[str],
    wanted_rate_types: set[str],
) -> tuple[list[Rate], list[tuple[str, str]]]:
    """Fetch all banks in parallel. Returns (collected_rates, [(slug, error_msg)])."""
    results = await asyncio.gather(
        *(_run_one(f, client, wanted_pairs, wanted_rate_types) for f in fetchers)
    )
    all_rates: list[Rate] = []
    errors: list[tuple[str, str]] = []
    for slug, kept, elapsed, error in results:
        if error is not None:
            Actor.log.warning(f"{slug}: failed in {elapsed:.2f}s: {error}")
            errors.append((slug, error))
            continue
        Actor.log.info(f"Fetched {slug}: {len(kept)} pairs in {elapsed:.2f}s")
        all_rates.extend(kept)
    return all_rates, errors

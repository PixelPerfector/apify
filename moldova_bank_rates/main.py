"""Apify actor entry point: fetch Moldovan bank exchange rates."""
from __future__ import annotations

import time

import httpx
from apify import Actor

from moldova_bank_rates.banks.bnm import BnmFetcher
from moldova_bank_rates.models import InputConfig


async def main() -> None:
    async with Actor:
        raw_input = await Actor.get_input() or {}
        config = InputConfig.model_validate(raw_input)
        Actor.log.info(f"Resolved input: {config.model_dump()}")

        proxy_url = await _resolve_proxy_url(config.use_apify_proxy)

        fetchers = [BnmFetcher()]  # MAIB / MICB / Victoriabank wired in later phases.
        async with httpx.AsyncClient(timeout=15.0, proxy=proxy_url) as client:
            for fetcher in fetchers:
                if fetcher.slug not in config.banks:
                    continue
                t0 = time.perf_counter()
                try:
                    rates = await fetcher.fetch(client)
                except Exception as exc:  # bank-isolation: log and continue
                    Actor.log.exception(f"{fetcher.slug}: fetch failed: {exc}")
                    continue
                kept = [
                    r for r in rates
                    if r.pair in config.pairs and r.rate_type in config.rate_types
                ]
                elapsed = time.perf_counter() - t0
                Actor.log.info(
                    f"Fetched {fetcher.slug}: {len(kept)} pairs in {elapsed:.2f}s"
                )
                for rate in kept:
                    await Actor.push_data(rate.model_dump(mode="json"))


async def _resolve_proxy_url(use_apify_proxy: bool) -> str | None:
    """Return an Apify-Proxy URL when available; tolerate local runs without credentials."""
    if not use_apify_proxy:
        return None
    try:
        proxy_configuration = await Actor.create_proxy_configuration()
    except Exception as exc:  # noqa: BLE001 — local runs without APIFY_TOKEN are fine
        Actor.log.warning(f"Could not create Apify proxy configuration: {exc}; running without proxy")
        return None
    if proxy_configuration is None:
        return None
    return await proxy_configuration.new_url()

"""Apify actor entry point: fetch Moldovan bank exchange rates."""
from __future__ import annotations

import httpx
from apify import Actor

from moldova_bank_rates.banks.bnm import BnmFetcher
from moldova_bank_rates.banks.maib import MaibFetcher
from moldova_bank_rates.banks.micb import MicbFetcher
from moldova_bank_rates.banks.victoriabank import VictoriabankFetcher
from moldova_bank_rates.models import InputConfig
from moldova_bank_rates.orchestrator import gather_all_rates

ALL_FETCHERS = {
    "bnm": BnmFetcher,
    "maib": MaibFetcher,
    "micb": MicbFetcher,
    "victoriabank": VictoriabankFetcher,
}


async def main() -> None:
    async with Actor:
        raw_input = await Actor.get_input() or {}
        config = InputConfig.model_validate(raw_input)
        Actor.log.info(f"Resolved input: {config.model_dump()}")

        proxy_url = await _resolve_proxy_url(config.use_apify_proxy)

        fetchers = [
            ALL_FETCHERS[slug]()
            for slug in config.banks
            if slug in ALL_FETCHERS
        ]
        async with httpx.AsyncClient(timeout=15.0, proxy=proxy_url) as client:
            rates, errors = await gather_all_rates(
                client=client,
                fetchers=fetchers,
                wanted_pairs=set(config.pairs),
                wanted_rate_types=set(config.rate_types),
            )

        for rate in rates:
            await Actor.push_data(rate.model_dump(mode="json"))

        Actor.log.info(
            f"Run summary: {len(rates)} records, {len(errors)} bank failures"
        )


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

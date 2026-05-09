"""Victoriabank HTML rate fetcher."""
from __future__ import annotations

from datetime import datetime

import httpx
from selectolax.lexbor import LexborHTMLParser, LexborNode

from moldova_bank_rates.models import Rate, RateType
from moldova_bank_rates.normalizers import normalize_number

SLUG = "victoriabank"
DISPLAY_NAME = "Victoriabank"
SOURCE_URL = "https://www.victoriabank.md/curs-valutar"

# (panel id in source -> rate_type emitted)
_PANELS: tuple[tuple[str, RateType], ...] = (
    ("numerar", "cash"),
    ("carduri", "card"),
)


def parse_victoriabank(html: bytes, fetched_at: datetime) -> list[Rate]:
    tree = LexborHTMLParser(html)
    rates: list[Rate] = []
    for panel_id, rate_type in _PANELS:
        panel = tree.css_first(f"#{panel_id}")
        if panel is None:
            continue
        rates.extend(_parse_panel(panel, rate_type=rate_type, fetched_at=fetched_at))
    return rates


def _parse_panel(
    panel: LexborNode, *, rate_type: RateType, fetched_at: datetime
) -> list[Rate]:
    out: list[Rate] = []
    for row in panel.css(".vb-table .tr"):
        cells = [c.text(strip=True) for c in row.css(".td")]
        if len(cells) < 3:
            # Header row (`.th` cells) or empty layout row — skip.
            continue
        code = cells[0].upper()
        if len(code) != 3 or not code.isalpha():
            continue
        buy = normalize_number(cells[1])
        sell = normalize_number(cells[2])
        available = buy is not None and sell is not None
        out.append(
            Rate(
                pair=f"{code}/MDL",
                base=code,
                quote="MDL",
                bank=SLUG,
                bank_display_name=DISPLAY_NAME,
                rate_type=rate_type,
                buy=buy,
                sell=sell,
                currency_unit=1,
                timestamp=fetched_at,
                bank_updated_at=None,
                source_url=SOURCE_URL,
                available=available,
            )
        )
    return out


class VictoriabankFetcher:
    slug = SLUG
    display_name = DISPLAY_NAME
    source_url = SOURCE_URL

    async def fetch(self, client: httpx.AsyncClient) -> list[Rate]:
        from moldova_bank_rates.banks.base import utcnow

        now = utcnow()
        response = await client.get(SOURCE_URL)
        response.raise_for_status()
        return parse_victoriabank(response.content, fetched_at=now)

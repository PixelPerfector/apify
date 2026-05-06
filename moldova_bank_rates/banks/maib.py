"""MAIB (Moldova Agroindbank) HTML rate fetcher."""
from __future__ import annotations

from datetime import datetime

import httpx
from selectolax.lexbor import LexborHTMLParser, LexborNode

from moldova_bank_rates.models import Rate
from moldova_bank_rates.normalizers import normalize_number

SLUG = "maib"
DISPLAY_NAME = "Moldova Agroindbank (MAIB)"
SOURCE_URL = "https://www.maib.md/en/curs-valutar"

# Map (container id in the source HTML) -> (rate_type emitted, columns).
# Only branch-cash and card; customs-agency variants are out of scope for v1.
_SECTIONS: tuple[tuple[str, str], ...] = (
    ("one-one-new", "cash"),
    ("two-new", "card"),
)


def parse_maib(html: bytes, fetched_at: datetime) -> list[Rate]:
    tree = LexborHTMLParser(html)
    rates: list[Rate] = []
    for section_id, rate_type in _SECTIONS:
        container = tree.css_first(f"#{section_id}")
        if container is None:
            continue
        table = container.css_first("table")
        if table is None:
            continue
        for row in table.css("tbody tr"):
            rate = _parse_row(row, rate_type=rate_type, fetched_at=fetched_at)
            if rate is not None:
                rates.append(rate)
    return rates


def _parse_row(
    row: LexborNode, *, rate_type: str, fetched_at: datetime
) -> Rate | None:
    cells = [c.text(strip=True) for c in row.css("td")]
    if len(cells) < 3:
        return None
    code = cells[0].upper()
    if len(code) != 3 or not code.isalpha():
        return None
    buy = normalize_number(cells[1])
    sell = normalize_number(cells[2])
    available = buy is not None and sell is not None
    return Rate(
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


class MaibFetcher:
    slug = SLUG
    display_name = DISPLAY_NAME
    source_url = SOURCE_URL

    async def fetch(self, client: httpx.AsyncClient) -> list[Rate]:
        from moldova_bank_rates.banks.base import utcnow

        now = utcnow()
        # Default httpx User-Agent passes Incapsula; adding a browser UA actually
        # triggers a 212-byte bot-challenge response from datacenter IPs.
        response = await client.get(SOURCE_URL)
        response.raise_for_status()
        return parse_maib(response.content, fetched_at=now)

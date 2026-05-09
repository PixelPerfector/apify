"""MICB (Moldova-Investiții-Comerțiale Bank) HTML rate fetcher."""
from __future__ import annotations

import re
from datetime import datetime

import httpx
from selectolax.lexbor import LexborHTMLParser, LexborNode

from moldova_bank_rates.models import Rate, RateType
from moldova_bank_rates.normalizers import normalize_number

SLUG = "micb"
DISPLAY_NAME = "Moldova-Investiții-Comerțiale Bank (MICB)"
SOURCE_URL = "https://micb.md/en/"

_TRAILING_CODE = re.compile(r"[A-Z]{3}$")
_TABS: tuple[RateType, ...] = ("cash", "card")


def parse_micb(html: bytes, fetched_at: datetime) -> list[Rate]:
    tree = LexborHTMLParser(html)
    rates: list[Rate] = []
    for tab in _TABS:
        panel = tree.css_first(f'div[data-exchangetab="{tab}"]')
        if panel is None:
            continue
        rates.extend(_parse_panel(panel, rate_type=tab, fetched_at=fetched_at))
    return rates


def _parse_panel(
    panel: LexborNode, *, rate_type: RateType, fetched_at: datetime
) -> list[Rate]:
    table = panel.css_first(".exchange-table")
    if table is None:
        return []
    currency_codes = _extract_currency_codes(table)
    rows = _extract_value_rows(table)
    if not currency_codes or not rows or len(currency_codes) != len(rows):
        return []

    out: list[Rate] = []
    for code, values in zip(currency_codes, rows, strict=True):
        if len(values) < 2:
            continue
        buy = normalize_number(values[0])
        sell = normalize_number(values[1])
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


def _extract_currency_codes(table: LexborNode) -> list[str]:
    codes: list[str] = []
    for node in table.css(".currency-list .currency"):
        text = node.text(strip=True).upper()
        match = _TRAILING_CODE.search(text)
        if match:
            codes.append(match.group(0))
    return codes


def _extract_value_rows(table: LexborNode) -> list[list[str]]:
    rows: list[list[str]] = []
    table_div = table.css_first(".table")
    if table_div is None:
        return rows
    for row in table_div.css(".row"):
        cells = [n.text(strip=True) for n in row.iter(include_text=False) if n.text(strip=True)]
        rows.append(cells)
    return rows


class MicbFetcher:
    slug = SLUG
    display_name = DISPLAY_NAME
    source_url = SOURCE_URL

    async def fetch(self, client: httpx.AsyncClient) -> list[Rate]:
        from moldova_bank_rates.banks.base import utcnow

        now = utcnow()
        response = await client.get(SOURCE_URL)
        response.raise_for_status()
        return parse_micb(response.content, fetched_at=now)

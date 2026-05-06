"""BNM (Banca Națională a Moldovei) XML reference-rate fetcher."""
from __future__ import annotations

from datetime import datetime
from xml.etree import ElementTree as ET

import httpx

from moldova_bank_rates.models import Rate
from moldova_bank_rates.normalizers import normalize_number

SLUG = "bnm"
DISPLAY_NAME = "National Bank of Moldova (BNM)"
SOURCE_URL_TEMPLATE = (
    "https://www.bnm.md/en/official_exchange_rates?get_xml=1&date={date}"
)


def _build_url(now: datetime) -> str:
    return SOURCE_URL_TEMPLATE.format(date=now.strftime("%d.%m.%Y"))


def parse_bnm(xml_bytes: bytes, fetched_at: datetime) -> list[Rate]:
    root = ET.fromstring(xml_bytes)
    out: list[Rate] = []
    for valute in root.findall("Valute"):
        code = (valute.findtext("CharCode") or "").strip().upper()
        nominal_raw = valute.findtext("Nominal") or "1"
        value_raw = valute.findtext("Value")
        if not code or value_raw is None:
            continue
        value = normalize_number(value_raw)
        nominal = int(normalize_number(nominal_raw) or 1)
        if value is None:
            continue
        out.append(
            Rate(
                pair=f"{code}/MDL",
                base=code,
                quote="MDL",
                bank=SLUG,
                bank_display_name=DISPLAY_NAME,
                rate_type="card",
                buy=value,
                sell=value,
                currency_unit=nominal,
                timestamp=fetched_at,
                bank_updated_at=None,
                source_url=_build_url(fetched_at),
                available=True,
            )
        )
    return out


class BnmFetcher:
    slug = SLUG
    display_name = DISPLAY_NAME

    @property
    def source_url(self) -> str:
        return _build_url(datetime.now())

    async def fetch(self, client: httpx.AsyncClient) -> list[Rate]:
        from moldova_bank_rates.banks.base import utcnow

        now = utcnow()
        url = _build_url(now)
        response = await client.get(url)
        response.raise_for_status()
        return parse_bnm(response.content, fetched_at=now)

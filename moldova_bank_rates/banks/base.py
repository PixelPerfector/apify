"""Shared bank-fetcher protocol and HTTP helper."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Protocol

import httpx

from moldova_bank_rates.models import Rate


class BankFetcher(Protocol):
    slug: str
    display_name: str
    source_url: str

    async def fetch(self, client: httpx.AsyncClient) -> list[Rate]: ...


def utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)

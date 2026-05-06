"""Pydantic models for actor input and output."""
from __future__ import annotations

import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, computed_field, field_validator, model_validator

CURRENCY_CODE = re.compile(r"^[A-Z]{3}$")
RateType = Literal["cash", "card"]


class Rate(BaseModel):
    """One row in the actor dataset. Schema documented in CONTEXT.md §4."""

    pair: str
    base: str
    quote: str
    bank: str
    bank_display_name: str
    rate_type: RateType
    buy: float | None = None
    sell: float | None = None
    currency_unit: int = 1
    timestamp: datetime
    bank_updated_at: datetime | None = None
    source_url: str
    available: bool = True

    @field_validator("base", "quote")
    @classmethod
    def _currency_shape(cls, value: str) -> str:
        if not CURRENCY_CODE.fullmatch(value):
            raise ValueError(f"currency code must be 3 uppercase letters, got {value!r}")
        return value

    @field_validator("timestamp", "bank_updated_at")
    @classmethod
    def _require_tzaware(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("datetime must be timezone-aware (UTC ISO 8601)")
        return value

    @model_validator(mode="after")
    def _check_pair_and_availability(self) -> "Rate":
        expected = f"{self.base}/{self.quote}"
        if self.pair != expected:
            raise ValueError(f"pair {self.pair!r} does not match base/quote {expected!r}")
        if self.buy is not None and self.sell is not None and self.sell < self.buy:
            object.__setattr__(self, "available", False)
        return self

    @computed_field
    @property
    def mid(self) -> float | None:
        if self.buy is None or self.sell is None:
            return None
        return (self.buy + self.sell) / 2

    @computed_field
    @property
    def spread_pct(self) -> float | None:
        if self.mid is None or self.mid == 0:
            return None
        return ((self.sell - self.buy) / self.mid) * 100  # type: ignore[operator]


from moldova_bank_rates.normalizers import normalize_pair  # noqa: E402

SUPPORTED_BANKS = ("bnm", "maib", "micb", "victoriabank")
DEFAULT_PAIRS = ("EUR/MDL", "USD/MDL", "RON/MDL", "GBP/MDL", "CHF/MDL")
DEFAULT_RATE_TYPES = ("cash", "card")


class InputConfig(BaseModel):
    """Validated actor input."""

    banks: list[str] = Field(default_factory=lambda: list(SUPPORTED_BANKS))
    pairs: list[str] = Field(default_factory=lambda: list(DEFAULT_PAIRS))
    rate_types: list[RateType] = Field(default_factory=lambda: list(DEFAULT_RATE_TYPES))
    use_apify_proxy: bool = True

    @field_validator("banks")
    @classmethod
    def _check_banks(cls, value: list[str]) -> list[str]:
        for slug in value:
            if slug not in SUPPORTED_BANKS:
                raise ValueError(
                    f"unknown bank {slug!r}; supported: {SUPPORTED_BANKS}"
                )
        return value

    @field_validator("pairs")
    @classmethod
    def _normalise_pairs(cls, value: list[str]) -> list[str]:
        out: list[str] = []
        for raw in value:
            base, quote = normalize_pair(raw)
            out.append(f"{base}/{quote}")
        return out

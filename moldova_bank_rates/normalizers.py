"""Pure helpers for cleaning raw bank input."""
from __future__ import annotations

import re

_PAIR_SEPARATORS = re.compile(r"[\s/_\-]+")
_NUMBER_NOISE = re.compile(r"[^\d,.\-]")


def normalize_number(raw: str | None) -> float | None:
    """Parse a localized numeric string to float.

    Handles: thousands separators (space, comma, dot), decimal commas, decimal dots.
    Returns ``None`` for empty / placeholder values.
    """
    if raw is None:
        return None
    cleaned = _NUMBER_NOISE.sub("", raw).strip()
    if not cleaned:
        return None
    has_comma = "," in cleaned
    has_dot = "." in cleaned
    if has_comma and has_dot:
        # The rightmost separator is the decimal one.
        if cleaned.rfind(",") > cleaned.rfind("."):
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    elif has_comma:
        # Treat comma as decimal unless it appears as a thousands separator
        # (i.e. exactly 3 digits follow the last comma and the value has 5+ digits).
        last = cleaned.rsplit(",", 1)[-1]
        if len(last) == 3 and len(cleaned.replace(",", "")) >= 5:
            cleaned = cleaned.replace(",", "")
        else:
            cleaned = cleaned.replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


def normalize_pair(raw: str) -> tuple[str, str]:
    """Parse 'EUR/MDL', 'eur-mdl', 'EURMDL' into ('EUR', 'MDL')."""
    if raw is None:
        raise ValueError("pair cannot be None")
    upper = raw.strip().upper()
    parts = [p for p in _PAIR_SEPARATORS.split(upper) if p]
    if len(parts) == 2 and all(len(p) == 3 for p in parts):
        base, quote = parts
    elif len(parts) == 1 and len(parts[0]) == 6:
        base, quote = parts[0][:3], parts[0][3:]
    else:
        raise ValueError(f"cannot parse pair: {raw!r}")
    if not (base.isalpha() and quote.isalpha()):
        raise ValueError(f"pair contains non-letters: {raw!r}")
    return base, quote

# Moldova Bank Exchange Rates Actor — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build, deploy and publish an Apify Actor that scrapes commercial buy/sell exchange rates from four Moldovan banks (BNM, MAIB, MICB, Victoriabank), emits one normalized record per (bank × currency-pair × rate-type), and satisfies every box in CONTEXT.md §5 Faza 0–3 plus the §9 final pre-publish gate.

**Architecture:** Single Python Apify actor. Async HTTPX client fetches all four sources in parallel; per-bank parser modules return Pydantic-validated `Rate` records; an orchestrator isolates failures so one broken bank does not crash the run; output goes to the default dataset. Parsers are pure functions over HTML/XML strings — fixtures captured to disk drive offline unit tests; live URLs are hit only by the actor itself and by a single optional smoke test.

**Tech Stack:** Python 3.14, Apify SDK (`apify`), `httpx` (async), `selectolax` (lexbor HTML parser), Pydantic v2, `pytest` + `pytest-asyncio` for tests. No browser engine, no Crawlee.

---

## File Structure

Files to create (path → responsibility):

| Path | Responsibility |
|---|---|
| `moldova_bank_rates/__init__.py` | Package marker (empty) — replaces `my_actor/` |
| `moldova_bank_rates/__main__.py` | `python -m moldova_bank_rates` entry — moved from template |
| `moldova_bank_rates/main.py` | Apify entry: load input, run orchestrator, push records |
| `moldova_bank_rates/models.py` | Pydantic `Rate` and `InputConfig` models with §4 invariants |
| `moldova_bank_rates/normalizers.py` | `normalize_number`, `normalize_pair` pure helpers |
| `moldova_bank_rates/orchestrator.py` | `gather` parallel fetches, isolate per-bank errors, time logging |
| `moldova_bank_rates/banks/__init__.py` | Bank registry: slug → fetcher callable |
| `moldova_bank_rates/banks/base.py` | `BankFetcher` protocol + shared HTTP helper |
| `moldova_bank_rates/banks/bnm.py` | BNM XML fetcher + parser |
| `moldova_bank_rates/banks/maib.py` | MAIB HTML fetcher + parser |
| `moldova_bank_rates/banks/micb.py` | MICB HTML fetcher + parser |
| `moldova_bank_rates/banks/victoriabank.py` | Victoriabank HTML fetcher + parser |
| `tests/__init__.py` | Empty |
| `tests/conftest.py` | Shared pytest fixtures |
| `tests/fixtures/bnm/rates.xml` | Saved BNM XML response |
| `tests/fixtures/maib/rates.html` | Saved MAIB rates page |
| `tests/fixtures/micb/rates.html` | Saved MICB rates page |
| `tests/fixtures/victoriabank/rates.html` | Saved Victoriabank rates page |
| `tests/test_normalizers.py` | Unit tests for normalizers |
| `tests/test_models.py` | Unit tests for `Rate` invariants |
| `tests/test_bnm.py` | Offline parser test (uses fixture) |
| `tests/test_maib.py` | Offline parser test |
| `tests/test_micb.py` | Offline parser test |
| `tests/test_victoriabank.py` | Offline parser test |
| `tests/test_orchestrator.py` | Per-bank error isolation test |
| `requirements-dev.txt` | pytest, pytest-asyncio, respx |
| `pytest.ini` | pytest config (asyncio_mode=auto) |
| `CHANGELOG.md` | Version history |
| `docs/legal-notes.md` | ToS skim notes per bank (Faza 0 DoD item) |

Files to modify:

| Path | Change |
|---|---|
| `.actor/actor.json` | Slug, name, version, `generatedBy`, package path |
| `.actor/input_schema.json` | Banks/pairs/rate_types/proxy fields per §3 |
| `.actor/output_schema.json` | Map dataset URL output |
| `.actor/dataset_schema.json` | Field definitions and Overview view per §4 |
| `Dockerfile` | Reference new package name; install deps |
| `requirements.txt` | Replace `beautifulsoup4` with `selectolax` + `pydantic` |
| `README.md` | Replace template README with full Apify Store listing |
| `.gitignore` | Add `.venv/`, `.pytest_cache/`, `__pycache__/` if missing |

Files to delete:

- `my_actor/` (entire directory, after package rename in Phase 0)

---

## Phase 0 — Setup, BNM scraper, foundations (CONTEXT §5 Faza 0)

### Task 0.1: Update `.actor/actor.json` with locked metadata

**Files:**
- Modify: `.actor/actor.json`

- [ ] **Step 1: Replace placeholder fields**

Open `.actor/actor.json` and replace its full contents with:

```json
{
    "$schema": "https://apify.com/schemas/v1/actor.ide.json",
    "actorSpecification": 1,
    "name": "moldova-bank-rates",
    "title": "Moldova Bank Exchange Rates",
    "description": "Live commercial cash and card exchange rates from MAIB, MICB, Victoriabank and the National Bank of Moldova (BNM). One normalized record per bank, currency pair and rate type.",
    "version": "0.1",
    "buildTag": "latest",
    "meta": {
        "templateId": "python-start",
        "generatedBy": "Claude Code with Claude Opus 4.7"
    },
    "input": "./input_schema.json",
    "output": "./output_schema.json",
    "storages": {
        "dataset": "./dataset_schema.json"
    },
    "dockerfile": "../Dockerfile"
}
```

- [ ] **Step 2: Commit**

```bash
git add .actor/actor.json
git commit -m "chore: lock actor slug, name, and metadata for moldova-bank-rates"
```

---

### Task 0.2: Rename Python package `my_actor` → `moldova_bank_rates`

Rename the package once, before any code is written into it. Renaming after `apify push` is painful because the Dockerfile path is part of the build.

**Files:**
- Create: `moldova_bank_rates/__init__.py`, `moldova_bank_rates/__main__.py`
- Delete: `my_actor/`
- Modify: `Dockerfile`

- [ ] **Step 1: Move package**

```bash
git mv my_actor moldova_bank_rates
```

- [ ] **Step 2: Update Dockerfile**

In `Dockerfile`, replace both occurrences of `my_actor` with `moldova_bank_rates`. The two affected lines are:

```dockerfile
RUN python -m compileall -q moldova_bank_rates/
```

```dockerfile
CMD ["python", "-m", "moldova_bank_rates"]
```

- [ ] **Step 3: Verify package still imports**

Run: `python -c "import moldova_bank_rates"`
Expected: no output, exit 0.

- [ ] **Step 4: Commit**

```bash
git add Dockerfile moldova_bank_rates/ my_actor/
git commit -m "refactor: rename package my_actor -> moldova_bank_rates"
```

---

### Task 0.3: Replace runtime dependencies and add dev requirements

**Files:**
- Modify: `requirements.txt`
- Create: `requirements-dev.txt`, `pytest.ini`

- [ ] **Step 1: Rewrite `requirements.txt`**

Replace its full contents with:

```text
apify >= 3.0.0, < 4.0.0
httpx >= 0.28.0, < 1.0.0
selectolax >= 0.3.21, < 1.0.0
pydantic >= 2.6.0, < 3.0.0
```

- [ ] **Step 2: Create `requirements-dev.txt`**

```text
-r requirements.txt
pytest >= 8.0.0, < 9.0.0
pytest-asyncio >= 0.23.0, < 1.0.0
respx >= 0.21.0, < 1.0.0
```

- [ ] **Step 3: Create `pytest.ini`**

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
addopts = -ra -q
```

- [ ] **Step 4: Install into a local venv**

```bash
python3.14 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
```

Expected: install completes, no errors. If Python 3.14 is unavailable locally, use the latest available 3.x; the Dockerfile still pins 3.14 for the Apify build.

- [ ] **Step 5: Commit**

```bash
git add requirements.txt requirements-dev.txt pytest.ini
git commit -m "build: switch to selectolax + pydantic, add pytest dev deps"
```

---

### Task 0.4: Create test scaffolding

**Files:**
- Create: `tests/__init__.py`, `tests/conftest.py`, `tests/fixtures/.gitkeep`

- [ ] **Step 1: Create empty `tests/__init__.py`**

Write an empty file at `tests/__init__.py`.

- [ ] **Step 2: Create `tests/conftest.py`**

```python
"""Shared pytest fixtures for moldova_bank_rates tests."""
from __future__ import annotations

from pathlib import Path

import pytest

FIXTURE_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixture_bytes():
    """Return a function that loads a fixture file as raw bytes."""

    def _load(relative_path: str) -> bytes:
        return (FIXTURE_DIR / relative_path).read_bytes()

    return _load


@pytest.fixture
def fixture_text():
    """Return a function that loads a fixture file as decoded text."""

    def _load(relative_path: str, encoding: str = "utf-8") -> str:
        return (FIXTURE_DIR / relative_path).read_text(encoding=encoding)

    return _load
```

- [ ] **Step 3: Create `tests/fixtures/.gitkeep`**

Empty file so the directory is committed.

- [ ] **Step 4: Verify pytest finds zero tests cleanly**

Run: `.venv/bin/pytest`
Expected: "no tests ran" with exit code 5 (acceptable — directory is empty).

- [ ] **Step 5: Commit**

```bash
git add tests/ pytest.ini
git commit -m "test: scaffold pytest with fixture loader helpers"
```

---

### Task 0.5: Implement Pydantic `Rate` model with §4 invariants

**Files:**
- Create: `moldova_bank_rates/models.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_models.py`:

```python
"""Tests for Pydantic models."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from moldova_bank_rates.models import Rate


def _base_kwargs(**overrides):
    kwargs = dict(
        pair="EUR/MDL",
        base="EUR",
        quote="MDL",
        bank="maib",
        bank_display_name="Moldova Agroindbank",
        rate_type="cash",
        buy=19.45,
        sell=19.85,
        currency_unit=1,
        timestamp=datetime(2026, 5, 6, 14, 30, tzinfo=timezone.utc),
        bank_updated_at=None,
        source_url="https://maib.md/en/exchange-rates",
        available=True,
    )
    kwargs.update(overrides)
    return kwargs


def test_rate_computes_mid_and_spread():
    rate = Rate(**_base_kwargs())
    assert rate.mid == pytest.approx(19.65)
    assert rate.spread_pct == pytest.approx(((19.85 - 19.45) / 19.65) * 100)


def test_rate_mid_is_none_when_either_leg_missing():
    rate = Rate(**_base_kwargs(buy=None))
    assert rate.mid is None
    assert rate.spread_pct is None


def test_rate_pair_must_match_base_quote():
    with pytest.raises(ValidationError):
        Rate(**_base_kwargs(pair="USD/MDL"))


def test_rate_currency_codes_must_be_iso_4217_shape():
    with pytest.raises(ValidationError):
        Rate(**_base_kwargs(base="EU", pair="EU/MDL"))


def test_rate_marks_unavailable_when_sell_lower_than_buy():
    rate = Rate(**_base_kwargs(buy=20.0, sell=19.0))
    assert rate.available is False


def test_rate_timestamp_must_be_timezone_aware():
    with pytest.raises(ValidationError):
        Rate(**_base_kwargs(timestamp=datetime(2026, 5, 6, 14, 30)))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_models.py -v`
Expected: import error or 6 failures (`Rate` does not exist yet).

- [ ] **Step 3: Implement the model**

Create `moldova_bank_rates/models.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify pass**

Run: `.venv/bin/pytest tests/test_models.py -v`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add moldova_bank_rates/models.py tests/test_models.py
git commit -m "feat(models): add Rate model enforcing §4 schema invariants"
```

---

### Task 0.6: Implement `InputConfig` model

**Files:**
- Modify: `moldova_bank_rates/models.py`
- Modify: `tests/test_models.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_models.py`:

```python
from moldova_bank_rates.models import InputConfig


def test_input_config_defaults_match_context_section_3():
    config = InputConfig()
    assert set(config.banks) == {"bnm", "maib", "micb", "victoriabank"}
    assert "EUR/MDL" in config.pairs
    assert "USD/MDL" in config.pairs
    assert set(config.rate_types) == {"cash", "card"}


def test_input_config_rejects_unknown_bank():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        InputConfig(banks=["unknown-bank"])


def test_input_config_normalises_pair_strings():
    config = InputConfig(pairs=["eur-mdl", "USD/MDL", "ronmdl"])
    assert config.pairs == ["EUR/MDL", "USD/MDL", "RON/MDL"]
```

- [ ] **Step 2: Run tests to verify failure**

Run: `.venv/bin/pytest tests/test_models.py -v`
Expected: 3 new failures on `InputConfig` (model not defined yet).

- [ ] **Step 3: Add `InputConfig` to `moldova_bank_rates/models.py`**

Append to the file (and add the import for `normalize_pair`):

```python
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
```

`normalize_pair` will be defined in Task 0.7. Tests will fail at import time until then — that is expected and resolved in the next task.

- [ ] **Step 4: Commit**

```bash
git add moldova_bank_rates/models.py tests/test_models.py
git commit -m "feat(models): add InputConfig with bank allowlist and pair normalisation"
```

---

### Task 0.7: Implement `normalizers.py` with tests

**Files:**
- Create: `moldova_bank_rates/normalizers.py`
- Create: `tests/test_normalizers.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_normalizers.py`:

```python
"""Tests for shared parsing normalizers."""
from __future__ import annotations

import pytest

from moldova_bank_rates.normalizers import normalize_number, normalize_pair


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("19,45", 19.45),
        ("1 945,32", 1945.32),
        ("19.4500", 19.45),
        ("  19,4500  ", 19.45),
        ("1,945.32", 1945.32),
    ],
)
def test_normalize_number(raw, expected):
    assert normalize_number(raw) == pytest.approx(expected)


def test_normalize_number_returns_none_on_empty():
    assert normalize_number("") is None
    assert normalize_number("—") is None
    assert normalize_number(None) is None


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("EUR/MDL", ("EUR", "MDL")),
        ("eur-mdl", ("EUR", "MDL")),
        ("EURMDL", ("EUR", "MDL")),
        ("usd_mdl", ("USD", "MDL")),
    ],
)
def test_normalize_pair(raw, expected):
    assert normalize_pair(raw) == expected


def test_normalize_pair_rejects_invalid():
    with pytest.raises(ValueError):
        normalize_pair("EU/MDL")
    with pytest.raises(ValueError):
        normalize_pair("EURMDLX")
```

- [ ] **Step 2: Run tests to verify failure**

Run: `.venv/bin/pytest tests/test_normalizers.py -v`
Expected: import error (module not yet created).

- [ ] **Step 3: Implement `normalizers.py`**

Create `moldova_bank_rates/normalizers.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify pass**

Run: `.venv/bin/pytest tests/test_normalizers.py tests/test_models.py -v`
Expected: all pass (normalizers tests + InputConfig tests from Task 0.6).

- [ ] **Step 5: Commit**

```bash
git add moldova_bank_rates/normalizers.py tests/test_normalizers.py
git commit -m "feat(normalizers): add number and pair normalisation helpers"
```

---

### Task 0.8: Capture BNM XML fixture and document URL

The BNM publishes today's reference rates as XML. Verify the URL by visiting <https://www.bnm.md/en/official_exchange_rates>.

**Files:**
- Create: `tests/fixtures/bnm/rates.xml`
- Create: `docs/legal-notes.md` (start ToS skim file — appended in later tasks)

- [ ] **Step 1: Fetch a live BNM XML response into the fixture**

```bash
curl -sS "https://www.bnm.md/en/official_exchange_rates?get_xml=1&date=$(date +%d.%m.%Y)" -o tests/fixtures/bnm/rates.xml
```

Expected: file exists, ≥1 KB, contains `<ValCurs>` root element.

If the URL has changed, find the current XML link in browser dev tools on the BNM rates page and substitute. Record the live URL in `docs/legal-notes.md`.

- [ ] **Step 2: Begin `docs/legal-notes.md`**

```markdown
# Legal & ToS skim notes

30-min ToS / robots.txt skim per CONTEXT.md §5 Faza 0. Update before publishing.

## bnm.md

- Page: https://www.bnm.md/en/official_exchange_rates
- XML endpoint used: https://www.bnm.md/en/official_exchange_rates?get_xml=1&date=DD.MM.YYYY
- Skim date: <FILL IN BEFORE PUBLISH>
- robots.txt: <FILL IN — paste relevant rules>
- ToS notes: <FILL IN — explicit prohibitions, attribution requirements>
- Decision: <PROCEED / BLOCK / NEEDS LEGAL REVIEW>
```

- [ ] **Step 3: Commit**

```bash
git add tests/fixtures/bnm/rates.xml docs/legal-notes.md
git commit -m "test: add BNM XML fixture; start legal notes log"
```

---

### Task 0.9: Implement BNM parser (TDD)

**Files:**
- Create: `moldova_bank_rates/banks/__init__.py`, `moldova_bank_rates/banks/base.py`, `moldova_bank_rates/banks/bnm.py`
- Create: `tests/test_bnm.py`

- [ ] **Step 1: Write the failing parser test**

Open `tests/fixtures/bnm/rates.xml` and read 2–3 specific currency entries (e.g. EUR, USD) to copy their published values. Encode them as `expected` in the test below — replace the placeholder numbers with what is actually in your fixture.

Create `tests/test_bnm.py`:

```python
"""Offline parser test for BNM XML."""
from __future__ import annotations

from datetime import datetime, timezone

from moldova_bank_rates.banks.bnm import parse_bnm
from moldova_bank_rates.models import Rate


def test_parse_bnm_returns_rates(fixture_bytes):
    xml = fixture_bytes("bnm/rates.xml")
    fetched_at = datetime(2026, 5, 6, 14, 30, tzinfo=timezone.utc)

    rates = parse_bnm(xml, fetched_at=fetched_at)

    assert len(rates) >= 5
    assert all(isinstance(r, Rate) for r in rates)
    eur = next(r for r in rates if r.base == "EUR")
    assert eur.quote == "MDL"
    assert eur.rate_type == "card"  # BNM publishes a single reference rate; we tag it as card
    assert eur.bank == "bnm"
    assert eur.buy == eur.sell  # reference rate has no spread
    assert eur.timestamp == fetched_at
```

- [ ] **Step 2: Run test to verify failure**

Run: `.venv/bin/pytest tests/test_bnm.py -v`
Expected: ImportError (`parse_bnm` undefined).

- [ ] **Step 3: Add the bank base abstractions**

Create `moldova_bank_rates/banks/__init__.py`:

```python
"""Per-bank fetchers."""
```

Create `moldova_bank_rates/banks/base.py`:

```python
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
```

- [ ] **Step 4: Implement BNM parser + fetcher**

Create `moldova_bank_rates/banks/bnm.py`:

```python
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
```

- [ ] **Step 5: Run test to verify pass**

Run: `.venv/bin/pytest tests/test_bnm.py -v`
Expected: PASS. If it fails because the EUR/USD values you encoded do not match the fixture, re-read the fixture and update the assertion. Do not weaken assertions to match buggy code.

- [ ] **Step 6: Commit**

```bash
git add moldova_bank_rates/banks/ tests/test_bnm.py
git commit -m "feat(bnm): parse BNM XML reference rates"
```

---

### Task 0.10: Wire BNM into the actor entry point and run end-to-end

**Files:**
- Modify: `moldova_bank_rates/main.py` (replace template content)

- [ ] **Step 1: Replace `moldova_bank_rates/main.py` contents**

```python
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

        proxy_configuration = (
            await Actor.create_proxy_configuration() if config.use_apify_proxy else None
        )
        proxy_url = await proxy_configuration.new_url() if proxy_configuration else None
        proxies = {"all://": proxy_url} if proxy_url else None

        fetchers = [BnmFetcher()]  # MAIB / MICB / Victoriabank wired in later phases.
        async with httpx.AsyncClient(timeout=15.0, proxies=proxies) as client:
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
```

Note: this duplicates the per-bank loop logic that Task 1.5 will extract into the orchestrator. Accept the duplication for now — it lets you verify BNM end-to-end before introducing more abstractions (YAGNI).

- [ ] **Step 2: Run the actor locally**

```bash
.venv/bin/python -m apify run --purge
```

Or, if `apify` CLI is the auth-installed system one: `apify run --purge`.

Expected log lines:
- `Resolved input: {...}`
- `Fetched bnm: N pairs in 0.Xs` where N ≥ 5
- Records written to `storage/datasets/default/`

- [ ] **Step 3: Manual sanity check**

Open `storage/datasets/default/000000001.json` (or similar) and pick three currencies (EUR, USD, RON). Open <https://www.bnm.md/en/official_exchange_rates> in a browser and confirm the three values match what is in the dataset.

- [ ] **Step 4: Commit**

```bash
git add moldova_bank_rates/main.py
git commit -m "feat: actor runs end-to-end with BNM source"
```

---

### Task 0.11: Replace the template README with a placeholder

The full Apify-Store README is built in Phase 3. For now leave a clear in-progress marker so search engines (and future you) do not see "Scrape single-page in Python template".

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Overwrite `README.md`**

```markdown
# Moldova Bank Exchange Rates

Apify actor that returns live commercial cash and card exchange rates from BNM, MAIB, MICB and Victoriabank.

> **Status:** in development. Full README, input/output examples and pricing notes land in v0.1.0.

## What this actor will do

For a configurable list of Moldovan banks and currency pairs, this actor scrapes today's published buy/sell rates and emits one normalized JSON record per (bank × pair × rate type). See `CONTEXT.md` for the full product brief.

## Local development

```bash
python3.14 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/pytest
apify run
```
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: replace template README with in-progress placeholder"
```

---

### Faza 0 DoD verification (manual checklist before moving on)

Confirm each is true in your environment, then proceed:

- Repo on GitHub, public, first commit pushed (already true per `git log`).
- Apify CLI authenticated (`apify info` shows your account).
- `apify run` exits cleanly.
- BNM XML fetched (HTTP 200 in logs).
- ≥5 pairs parsed.
- Three rates compared against bnm.md and matching.
- Per-source log line "Fetched bnm: N pairs in X.Ys" visible.
- README has name + 2-sentence description.
- `docs/legal-notes.md` created (will be filled per bank as you go).
- Apify payout method note: add a sentence to `README.md` (or a `docs/operations.md`) recording that the actor is owned by Perlog SRL with PayPal Business as the configured payout. Capture this even if PayPal application is still pending — see CONTEXT.md §5 Pre-Faza 0.

---

## Phase 1 — Two commercial banks + isolation infra (CONTEXT §5 Faza 1)

### Task 1.1: Capture MAIB HTML fixture

**Files:**
- Create: `tests/fixtures/maib/rates.html`

- [ ] **Step 1: Identify the live MAIB rates URL**

Open <https://maib.md/> and navigate to the personal-banking exchange-rates page (typical URL: <https://www.maib.md/en/exchange-rates>; verify before saving).

- [ ] **Step 2: Save the page**

```bash
curl -sS -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)" "<MAIB_URL>" -o tests/fixtures/maib/rates.html
```

Expected: ≥10 KB, opens in a browser and shows a rate table.

If `curl` is blocked, save via browser ("Save Page As → Web Page, HTML Only") into the same path.

- [ ] **Step 3: Note the URL in `docs/legal-notes.md`**

Append a `## maib.md` section with the same template used for bnm.md.

- [ ] **Step 4: Commit**

```bash
git add tests/fixtures/maib/rates.html docs/legal-notes.md
git commit -m "test: add MAIB HTML fixture"
```

---

### Task 1.2: Implement MAIB parser (TDD)

**Files:**
- Create: `moldova_bank_rates/banks/maib.py`
- Create: `tests/test_maib.py`

- [ ] **Step 1: Inspect the fixture and identify selectors**

Open `tests/fixtures/maib/rates.html` and locate the rates table. Use Chrome DevTools or `selectolax` REPL to settle on a CSS selector that yields rows with currency code, buy, sell, and rate-type (cash vs card) cells. Record the selectors here in this task before continuing.

- [ ] **Step 2: Write the failing test**

Create `tests/test_maib.py`:

```python
"""Offline parser test for MAIB."""
from __future__ import annotations

from datetime import datetime, timezone

from moldova_bank_rates.banks.maib import parse_maib
from moldova_bank_rates.models import Rate


def test_parse_maib_returns_cash_and_card(fixture_bytes):
    html = fixture_bytes("maib/rates.html")
    rates = parse_maib(html, fetched_at=datetime(2026, 5, 6, 14, 30, tzinfo=timezone.utc))

    assert all(isinstance(r, Rate) for r in rates)
    eur_cash = [r for r in rates if r.base == "EUR" and r.rate_type == "cash"]
    eur_card = [r for r in rates if r.base == "EUR" and r.rate_type == "card"]
    assert eur_cash, "expected at least one EUR cash rate"
    assert eur_card, "expected at least one EUR card rate"
    assert eur_cash[0].sell > eur_cash[0].buy > 0
```

If MAIB does not publish both cash and card on a single page, adjust the test to assert only what the fixture contains and document the omission in `docs/legal-notes.md`.

- [ ] **Step 3: Run test to verify failure**

Run: `.venv/bin/pytest tests/test_maib.py -v`
Expected: ImportError (`parse_maib` undefined).

- [ ] **Step 4: Implement `moldova_bank_rates/banks/maib.py`**

```python
"""MAIB (Moldova Agroindbank) HTML rate fetcher."""
from __future__ import annotations

from datetime import datetime

import httpx
from selectolax.lexbor import LexborHTMLParser

from moldova_bank_rates.models import Rate
from moldova_bank_rates.normalizers import normalize_number

SLUG = "maib"
DISPLAY_NAME = "Moldova Agroindbank (MAIB)"
SOURCE_URL = "https://www.maib.md/en/exchange-rates"  # verify against fixture URL

# Replace selectors below with what you confirmed in Step 1.
_TABLE_SELECTOR = "table.rates-table tr"
_CODE_SELECTOR = "td:nth-child(1)"
_BUY_SELECTOR = "td:nth-child(2)"
_SELL_SELECTOR = "td:nth-child(3)"


def parse_maib(html: bytes, fetched_at: datetime) -> list[Rate]:
    tree = LexborHTMLParser(html)
    rates: list[Rate] = []
    for section_rate_type in ("cash", "card"):
        for row in tree.css(_TABLE_SELECTOR):
            code_node = row.css_first(_CODE_SELECTOR)
            buy_node = row.css_first(_BUY_SELECTOR)
            sell_node = row.css_first(_SELL_SELECTOR)
            if not (code_node and buy_node and sell_node):
                continue
            code = code_node.text(strip=True).upper()
            if len(code) != 3 or not code.isalpha():
                continue
            buy = normalize_number(buy_node.text(strip=True))
            sell = normalize_number(sell_node.text(strip=True))
            if buy is None or sell is None:
                continue
            rates.append(
                Rate(
                    pair=f"{code}/MDL",
                    base=code,
                    quote="MDL",
                    bank=SLUG,
                    bank_display_name=DISPLAY_NAME,
                    rate_type=section_rate_type,
                    buy=buy,
                    sell=sell,
                    currency_unit=1,
                    timestamp=fetched_at,
                    bank_updated_at=None,
                    source_url=SOURCE_URL,
                    available=True,
                )
            )
    return rates


class MaibFetcher:
    slug = SLUG
    display_name = DISPLAY_NAME
    source_url = SOURCE_URL

    async def fetch(self, client: httpx.AsyncClient) -> list[Rate]:
        from moldova_bank_rates.banks.base import utcnow

        now = utcnow()
        response = await client.get(SOURCE_URL)
        response.raise_for_status()
        return parse_maib(response.content, fetched_at=now)
```

The selectors and `section_rate_type` loop above are the *first cut*. The MAIB page may have separate tables or tabs for cash vs card — adjust the parser to walk those distinct sections and assign the correct `rate_type`. The test from Step 2 is the contract.

- [ ] **Step 5: Run test to verify pass**

Run: `.venv/bin/pytest tests/test_maib.py -v`
Expected: PASS. Iterate on selectors until it does.

- [ ] **Step 6: Commit**

```bash
git add moldova_bank_rates/banks/maib.py tests/test_maib.py
git commit -m "feat(maib): parse MAIB cash and card rates"
```

---

### Task 1.3: Capture MICB HTML fixture

Same shape as Task 1.1, for MICB.

**Files:**
- Create: `tests/fixtures/micb/rates.html`

- [ ] **Step 1: Identify URL on <https://micb.md/>**

Typical URL: <https://www.micb.md/en/private/exchange-rates>; confirm before saving.

- [ ] **Step 2: Save fixture**

```bash
curl -sS -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)" "<MICB_URL>" -o tests/fixtures/micb/rates.html
```

- [ ] **Step 3: Append `## micb.md` section to `docs/legal-notes.md`**

- [ ] **Step 4: Commit**

```bash
git add tests/fixtures/micb/rates.html docs/legal-notes.md
git commit -m "test: add MICB HTML fixture"
```

---

### Task 1.4: Implement MICB parser (TDD)

**Files:**
- Create: `moldova_bank_rates/banks/micb.py`
- Create: `tests/test_micb.py`

Mirror Task 1.2:

- [ ] **Step 1: Inspect fixture and identify selectors**
- [ ] **Step 2: Write `tests/test_micb.py`** asserting EUR and USD rates parse with `sell > buy > 0`. Use the same shape as `test_maib.py`, importing `parse_micb`.
- [ ] **Step 3: Run test to verify failure** (`pytest tests/test_micb.py -v`).
- [ ] **Step 4: Implement `moldova_bank_rates/banks/micb.py`** following the MAIB skeleton; constants `SLUG = "micb"`, `DISPLAY_NAME = "Moldova-Investiții-Comerțiale Bank (MICB)"`, `SOURCE_URL = "<from fixture>"`. Replace selectors with those from Step 1.
- [ ] **Step 5: Run test to verify pass.**
- [ ] **Step 6: Commit.**

```bash
git add moldova_bank_rates/banks/micb.py tests/test_micb.py
git commit -m "feat(micb): parse MICB cash and card rates"
```

---

### Task 1.5: Build orchestrator with per-bank error isolation

Extract the per-bank loop in `main.py` into `orchestrator.py` and add a regression test that confirms one bank failing does not lose the others' results.

**Files:**
- Create: `moldova_bank_rates/orchestrator.py`
- Create: `tests/test_orchestrator.py`
- Modify: `moldova_bank_rates/main.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_orchestrator.py`:

```python
"""Tests for per-bank error isolation in the orchestrator."""
from __future__ import annotations

from datetime import datetime, timezone

import httpx
import pytest

from moldova_bank_rates.models import InputConfig, Rate
from moldova_bank_rates.orchestrator import gather_all_rates


class _OkFetcher:
    slug = "ok"
    display_name = "OK Bank"
    source_url = "https://example.com/ok"

    async def fetch(self, client: httpx.AsyncClient) -> list[Rate]:
        return [
            Rate(
                pair="EUR/MDL",
                base="EUR",
                quote="MDL",
                bank="ok",
                bank_display_name="OK Bank",
                rate_type="card",
                buy=19.0,
                sell=19.5,
                currency_unit=1,
                timestamp=datetime(2026, 5, 6, tzinfo=timezone.utc),
                source_url=self.source_url,
            )
        ]


class _BoomFetcher:
    slug = "boom"
    display_name = "Boom Bank"
    source_url = "https://example.com/boom"

    async def fetch(self, client: httpx.AsyncClient) -> list[Rate]:
        raise RuntimeError("boom")


@pytest.mark.asyncio
async def test_one_bank_failure_does_not_break_others():
    config = InputConfig(banks=["bnm"], pairs=["EUR/MDL"], rate_types=["card"])
    # InputConfig validates against SUPPORTED_BANKS, so we override on the orchestrator
    # call directly rather than via config.
    async with httpx.AsyncClient() as client:
        rates, errors = await gather_all_rates(
            client=client,
            fetchers=[_OkFetcher(), _BoomFetcher()],
            wanted_pairs={"EUR/MDL"},
            wanted_rate_types={"card"},
        )

    assert len(rates) == 1
    assert rates[0].bank == "ok"
    assert errors == [("boom", "boom")]
```

- [ ] **Step 2: Run test to verify failure**

Run: `.venv/bin/pytest tests/test_orchestrator.py -v`
Expected: ImportError (`gather_all_rates` undefined).

- [ ] **Step 3: Implement `moldova_bank_rates/orchestrator.py`**

```python
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
```

`Actor.log` is imported at module top — that's fine because pytest tests do not exercise the orchestrator's logging path through Actor (the log calls run, but `Actor.log` is a module-level logger that works without `Actor.init()`).

- [ ] **Step 4: Update `moldova_bank_rates/main.py`**

Replace its body with:

```python
"""Apify actor entry point: fetch Moldovan bank exchange rates."""
from __future__ import annotations

import httpx
from apify import Actor

from moldova_bank_rates.banks.bnm import BnmFetcher
from moldova_bank_rates.banks.maib import MaibFetcher
from moldova_bank_rates.banks.micb import MicbFetcher
from moldova_bank_rates.models import InputConfig
from moldova_bank_rates.orchestrator import gather_all_rates

ALL_FETCHERS = {
    "bnm": BnmFetcher,
    "maib": MaibFetcher,
    "micb": MicbFetcher,
    # "victoriabank": added in Phase 2
}


async def main() -> None:
    async with Actor:
        raw_input = await Actor.get_input() or {}
        config = InputConfig.model_validate(raw_input)
        Actor.log.info(f"Resolved input: {config.model_dump()}")

        proxy_configuration = (
            await Actor.create_proxy_configuration() if config.use_apify_proxy else None
        )
        proxy_url = await proxy_configuration.new_url() if proxy_configuration else None
        proxies = {"all://": proxy_url} if proxy_url else None

        fetchers = [
            ALL_FETCHERS[slug]()
            for slug in config.banks
            if slug in ALL_FETCHERS
        ]
        async with httpx.AsyncClient(timeout=15.0, proxies=proxies) as client:
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
```

- [ ] **Step 5: Run all tests**

Run: `.venv/bin/pytest -v`
Expected: all pass.

- [ ] **Step 6: Run end-to-end**

Run: `apify run --purge`
Expected: per-bank "Fetched X: N pairs in Ys" lines for bnm, maib, micb. Run completes ≤ 10 s.

Manual sanity check: open the bank pages and compare 3 rates per bank with the dataset. Record any discrepancies and fix selectors.

- [ ] **Step 7: Commit**

```bash
git add moldova_bank_rates/orchestrator.py moldova_bank_rates/main.py tests/test_orchestrator.py
git commit -m "feat(orchestrator): parallel fetch with per-bank error isolation"
```

---

### Faza 1 DoD verification (manual checklist)

- Two of {MAIB, MICB} have functional local scrapers (true after Tasks 1.2, 1.4).
- Pydantic Rate model rejects invalid input (Task 0.5 tests).
- Number/pair normalizers (Task 0.7 tests).
- Cash and card emitted as separate records (Task 1.2 test).
- HTML fixtures saved (`tests/fixtures/{maib,micb}/`).
- ≥3 normalizer tests (Task 0.7 has 11+).
- 3 rates per bank visually match live site (manual after Step 6).
- Per-bank error isolation (`tests/test_orchestrator.py`).
- Per-bank fetch time visible in logs.

---

## Phase 2 — Fourth scraper + Apify deploy (CONTEXT §5 Faza 2)

### Task 2.1: Capture Victoriabank HTML fixture

**Files:**
- Create: `tests/fixtures/victoriabank/rates.html`

- [ ] **Step 1: Identify URL on <https://www.victoriabank.md/>** (typical: <https://www.victoriabank.md/en/curs-valutar>).
- [ ] **Step 2: Save fixture** with `curl` (same UA flag as Task 1.1).
- [ ] **Step 3: Append `## victoriabank.md` to `docs/legal-notes.md`.**
- [ ] **Step 4: Commit.**

```bash
git add tests/fixtures/victoriabank/rates.html docs/legal-notes.md
git commit -m "test: add Victoriabank HTML fixture"
```

---

### Task 2.2: Implement Victoriabank parser (TDD)

**Files:**
- Create: `moldova_bank_rates/banks/victoriabank.py`
- Create: `tests/test_victoriabank.py`

Same five-step pattern as Task 1.4 (inspect, write failing test, run-fail, implement, run-pass, commit).

- [ ] **Step 1: Identify selectors in fixture.**
- [ ] **Step 2: Write `tests/test_victoriabank.py`** mirroring `test_maib.py`, using `parse_victoriabank`.
- [ ] **Step 3: Run test → verify import error.**
- [ ] **Step 4: Implement `moldova_bank_rates/banks/victoriabank.py`** following the MAIB skeleton with constants `SLUG = "victoriabank"`, `DISPLAY_NAME = "Victoriabank"`, and the URL/selectors from Steps 1.
- [ ] **Step 5: Run test → pass.**
- [ ] **Step 6: Wire into `ALL_FETCHERS` in `moldova_bank_rates/main.py`:**

```python
from moldova_bank_rates.banks.victoriabank import VictoriabankFetcher

ALL_FETCHERS = {
    "bnm": BnmFetcher,
    "maib": MaibFetcher,
    "micb": MicbFetcher,
    "victoriabank": VictoriabankFetcher,
}
```

- [ ] **Step 7: Run end-to-end**

Run: `apify run --purge`
Expected: 4 "Fetched ..." log lines, ≥15 records produced, total run < 30 s.

- [ ] **Step 8: Commit.**

```bash
git add moldova_bank_rates/banks/victoriabank.py moldova_bank_rates/main.py tests/test_victoriabank.py
git commit -m "feat(victoriabank): parse Victoriabank rates and wire into actor"
```

---

### Task 2.3: Update `.actor/input_schema.json`

**Files:**
- Modify: `.actor/input_schema.json`

- [ ] **Step 1: Replace contents with v1 schema**

```json
{
    "$schema": "https://apify.com/schemas/v1/input.ide.json",
    "title": "Moldova Bank Exchange Rates — Input",
    "type": "object",
    "schemaVersion": 1,
    "properties": {
        "banks": {
            "title": "Banks",
            "type": "array",
            "description": "Which banks to scrape on this run.",
            "editor": "select",
            "items": {
                "type": "string",
                "enum": ["bnm", "maib", "micb", "victoriabank"],
                "enumTitles": ["BNM (reference)", "MAIB", "MICB", "Victoriabank"]
            },
            "default": ["bnm", "maib", "micb", "victoriabank"],
            "uniqueItems": true,
            "minItems": 1
        },
        "pairs": {
            "title": "Currency pairs",
            "type": "array",
            "description": "Currency pairs in BASE/QUOTE form (always vs MDL in v1).",
            "editor": "stringList",
            "items": {"type": "string"},
            "default": ["EUR/MDL", "USD/MDL", "RON/MDL", "GBP/MDL", "CHF/MDL"],
            "uniqueItems": true,
            "minItems": 1
        },
        "rate_types": {
            "title": "Rate types",
            "type": "array",
            "description": "Cash (in-branch) or card (transfer / account) rates.",
            "editor": "select",
            "items": {
                "type": "string",
                "enum": ["cash", "card"],
                "enumTitles": ["Cash", "Card / transfer"]
            },
            "default": ["cash", "card"],
            "uniqueItems": true,
            "minItems": 1
        },
        "use_apify_proxy": {
            "title": "Use Apify proxy",
            "type": "boolean",
            "description": "Route requests through Apify Proxy (datacenter). Recommended.",
            "default": true
        }
    },
    "required": ["banks", "pairs", "rate_types"]
}
```

- [ ] **Step 2: Commit**

```bash
git add .actor/input_schema.json
git commit -m "feat(schema): real input_schema.json for v1"
```

---

### Task 2.4: Update output and dataset schemas

**Files:**
- Modify: `.actor/output_schema.json`
- Modify: `.actor/dataset_schema.json`

- [ ] **Step 1: Rewrite `.actor/output_schema.json`**

```json
{
    "$schema": "https://apify.com/schemas/v1/output.ide.json",
    "actorOutputSchemaVersion": 1,
    "title": "Moldova Bank Exchange Rates — Output",
    "properties": {
        "rates": {
            "type": "string",
            "title": "Rates dataset",
            "template": "{{links.apiDefaultDatasetUrl}}/items"
        }
    }
}
```

- [ ] **Step 2: Rewrite `.actor/dataset_schema.json`**

```json
{
    "$schema": "https://apify.com/schemas/v1/dataset.ide.json",
    "actorSpecification": 1,
    "fields": {
        "type": "object",
        "properties": {
            "pair": {"type": "string"},
            "base": {"type": "string"},
            "quote": {"type": "string"},
            "bank": {"type": "string"},
            "bank_display_name": {"type": "string"},
            "rate_type": {"type": "string", "enum": ["cash", "card"]},
            "buy": {"type": ["number", "null"]},
            "sell": {"type": ["number", "null"]},
            "mid": {"type": ["number", "null"]},
            "spread_pct": {"type": ["number", "null"]},
            "currency_unit": {"type": "integer"},
            "timestamp": {"type": "string", "format": "date-time"},
            "bank_updated_at": {"type": ["string", "null"], "format": "date-time"},
            "source_url": {"type": "string"},
            "available": {"type": "boolean"}
        },
        "required": [
            "pair", "base", "quote", "bank", "bank_display_name", "rate_type",
            "currency_unit", "timestamp", "source_url", "available"
        ]
    },
    "views": {
        "overview": {
            "title": "Overview",
            "transformation": {
                "fields": [
                    "bank_display_name", "pair", "rate_type",
                    "buy", "sell", "mid", "spread_pct",
                    "timestamp", "source_url"
                ]
            },
            "display": {
                "component": "table",
                "properties": {
                    "bank_display_name": {"label": "Bank", "format": "text"},
                    "pair": {"label": "Pair", "format": "text"},
                    "rate_type": {"label": "Type", "format": "text"},
                    "buy": {"label": "Buy", "format": "number"},
                    "sell": {"label": "Sell", "format": "number"},
                    "mid": {"label": "Mid", "format": "number"},
                    "spread_pct": {"label": "Spread %", "format": "number"},
                    "timestamp": {"label": "Fetched at", "format": "date"},
                    "source_url": {"label": "Source", "format": "link"}
                }
            }
        }
    }
}
```

- [ ] **Step 3: Commit**

```bash
git add .actor/output_schema.json .actor/dataset_schema.json
git commit -m "feat(schema): real output and dataset schemas matching §4"
```

---

### Task 2.5: Verify Docker build is clean

**Files:**
- Modify: `Dockerfile` (only if needed)

- [ ] **Step 1: Run a local docker build**

```bash
docker build -t moldova-bank-rates .
```

Expected: build completes; no errors. Critical-warning lines (`ERROR`, missing wheel, segfault during compile) must be addressed; benign `pip` deprecation warnings can stay.

If the build fails because of a missing system dep (e.g. `selectolax` needs build tools), update `Dockerfile` to install only what is actually missing — do not pre-emptively bloat the image.

- [ ] **Step 2: Commit any Dockerfile changes**

```bash
git add Dockerfile
git commit -m "build: ensure docker image builds cleanly"
```

(Skip if no changes were needed.)

---

### Task 2.6: First Apify platform deploy

⚠ **Confirm with the user before pushing — `apify push` deploys to the Cloud account.**

- [ ] **Step 1: `apify push`**

```bash
apify push
```

Expected: build started, build completes successfully (status `SUCCEEDED` in the Apify Console build log).

- [ ] **Step 2: Trigger one platform run from the Apify Console**

Open the actor in <https://console.apify.com/actors>, click "Start", accept default input, click "Save & start".

Expected:
- Run finishes with status `SUCCEEDED`.
- Dataset has ≥ 15 rows (4 banks × ~4 pairs).
- Run duration < 30 s.
- Compute units / cost visible in "Run details".

- [ ] **Step 3: Click "Export → JSON" and "Export → CSV"** from the dataset tab; both downloads succeed.

- [ ] **Step 4: Copy the run URL, open it in an incognito window** (logged out). The "Public link" version of the run should display.

- [ ] **Step 5: No code commit** for this task — verification only. Note the run ID in `docs/operations.md` (create the file if missing) for later reference.

```bash
mkdir -p docs && touch docs/operations.md
```

```markdown
# Operations log

## First successful platform run
- Run ID: <fill-in>
- Date: <fill-in>
- Records produced: <fill-in>
- Compute units used: <fill-in>
```

```bash
git add docs/operations.md
git commit -m "docs: log first successful platform run"
```

---

### Faza 2 DoD verification (manual checklist)

- All four banks functional locally.
- `.actor/actor.json` has slug `moldova-bank-rates` (Task 0.1).
- `input_schema.json` renders in Console (manual check Task 2.6).
- Dataset & output schemas aligned with §4 (Task 2.4).
- `docker build` clean (Task 2.5).
- First Apify build SUCCEEDED.
- One platform run produced ≥15 records.
- JSON & CSV exports work.
- Total run time < 30 s.
- Compute cost visible.
- Run page shareable in incognito.

---

## Phase 3 — Publishing readiness (CONTEXT §5 Faza 3)

### Task 3.1: Write the full Apify Store README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Replace the placeholder README**

Use the structure required by AGENTS.md ("Actor README" section): H2 only, ≥300 words, sections in order. Include the disclaimer text from CONTEXT.md §5 Faza 3 verbatim.

```markdown
# Moldova Bank Exchange Rates

## What does Moldova Bank Exchange Rates do?

This actor scrapes **live commercial exchange rates** from the four largest banks in Moldova — **MAIB**, **MICB**, **Victoriabank** — plus the **National Bank of Moldova (BNM)** reference rate. For each (bank × currency pair × rate type) it returns one normalized JSON record with buy, sell, mid and spread fields, ready to plug into a comparison page, fintech app, or dashboard. There is no public aggregator API for Moldovan bank rates — this actor is the simplest way to get them.

Try a one-click run from the Apify Console, then export results as JSON, CSV, Excel or HTML, or call the Apify API to run on demand.

## Why use Moldova Bank Exchange Rates?

- **Commercial rates, not just the central-bank reference.** BNM publishes a daily reference rate; bank counter rates can differ by 1–4%.
- **Cash vs card rates as separate records.** Useful for buyers comparing in-branch tourist rates against card / transfer rates.
- **One JSON shape across all banks.** No per-bank quirks to handle downstream.
- **Apify-managed schedule, monitoring, proxy rotation.** Run every 6 hours out of the box; if a selector breaks, you'll see it in the run log.
- **Use cases:**
  - Remittance / fintech firms showing "where to exchange best."
  - Travel and booking platforms that price in MDL.
  - Personal-finance comparison sites in Moldova and Romania.

## How to use Moldova Bank Exchange Rates

1. Open the Actor in the Apify Console.
2. (Optional) Edit the input — by default all four banks and the five most common pairs are scraped.
3. Click **Start**.
4. When the run finishes (~10 s), open the **Dataset** tab.
5. Export as JSON / CSV, or call the Dataset API URL shown in the run summary.

## Input

The input is a small JSON object. All fields are optional and have defaults that produce ~30–40 records per run.

```json
{
    "banks": ["bnm", "maib", "micb", "victoriabank"],
    "pairs": ["EUR/MDL", "USD/MDL", "RON/MDL", "GBP/MDL", "CHF/MDL"],
    "rate_types": ["cash", "card"],
    "use_apify_proxy": true
}
```

See the **Input** tab for the full form-rendered schema.

## Output

Each record is one (bank × pair × rate type). You can download the dataset as JSON, CSV, Excel or HTML.

```json
{
    "pair": "EUR/MDL",
    "base": "EUR",
    "quote": "MDL",
    "bank": "maib",
    "bank_display_name": "Moldova Agroindbank (MAIB)",
    "rate_type": "cash",
    "buy": 19.45,
    "sell": 19.85,
    "mid": 19.65,
    "spread_pct": 2.04,
    "currency_unit": 1,
    "timestamp": "2026-05-06T14:30:00Z",
    "bank_updated_at": null,
    "source_url": "https://www.maib.md/en/exchange-rates",
    "available": true
}
```

## Data fields

| Field | Type | Notes |
|---|---|---|
| pair | string | "EUR/MDL" |
| base, quote | string | ISO 4217 codes |
| bank | string | Slug: bnm / maib / micb / victoriabank |
| bank_display_name | string | Human-readable bank name |
| rate_type | string | "cash" or "card" |
| buy | number/null | Price the bank pays for 1 unit base |
| sell | number/null | Price the bank charges for 1 unit base |
| mid | number/null | (buy + sell) / 2 |
| spread_pct | number/null | ((sell − buy) / mid) × 100 |
| currency_unit | integer | Quote unit; e.g. 100 for JPY |
| timestamp | string (ISO 8601) | When the actor fetched the data |
| bank_updated_at | string/null | Bank's own publish time, if available |
| source_url | string | Page or feed scraped |
| available | boolean | False if the bank does not quote that pair / type |

## Pricing — How much does it cost to scrape Moldovan bank rates?

Pay-per-result, **$0.50 per 1000 records** ($0.0005 / record). A typical run produces 30–40 records, so each run costs roughly **$0.015–$0.02**. Running every 6 hours for a month: about **$2.40**. The default Apify free tier covers many runs.

## Tips

- Narrow `banks` and `pairs` to cut record count and cost.
- Schedule every 6 hours rather than every hour — bank rates do not move that fast.
- Use `use_apify_proxy: true` (the default) to avoid rate-limiting from any single IP.

## FAQ, disclaimers and support

> Exchange rates are scraped from public bank websites and may lag the bank's quoted rate by several minutes. Always verify with the bank before transacting. This actor is not affiliated with, endorsed by, or sponsored by any of the banks listed.

- **Selector broke?** Open an Issue on the actor's GitHub repo. Selector fixes typically ship within 24 hours.
- **Need another bank or pair?** Open an Issue describing the use case.
- **Custom integration?** Contact the maintainer via the Apify Store profile.
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: write full Apify Store README per CONTEXT §5 Faza 3"
```

---

### Task 3.2: Add `CHANGELOG.md`

**Files:**
- Create: `CHANGELOG.md`

- [ ] **Step 1: Create the file**

```markdown
# Changelog

All notable changes to this actor will be documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] — Unreleased

### Added
- BNM XML reference-rate fetcher.
- MAIB, MICB, Victoriabank HTML cash/card scrapers.
- Pydantic `Rate` model enforcing CONTEXT.md §4 invariants.
- Per-bank error isolation in the orchestrator.
- Apify input, output, and dataset schemas.
```

- [ ] **Step 2: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs: add CHANGELOG with 0.1.0 entry"
```

---

### Task 3.3: Bump version, redeploy, and verify auto-deploy

⚠ **Confirm with the user before pushing.**

- [ ] **Step 1: Bump version**

In `.actor/actor.json` change `"version": "0.1"` → `"version": "0.1"` (Apify uses `<major>.<minor>` here; patch level lives only in CHANGELOG / Git tags).

If you have already shipped 0.1, bump to `"0.2"` and update CHANGELOG accordingly.

- [ ] **Step 2: `apify push`** — confirm a fresh build SUCCEEDED.

- [ ] **Step 3: Configure GitHub auto-deploy in the Apify Console**

In the actor's "Source" tab, link the GitHub repo and enable build-on-push for branch `main`. Confirm with a trivial commit (e.g. typo in `CHANGELOG.md`) that a build is triggered automatically.

- [ ] **Step 4: Configure 6-hour schedule**

In Apify Console → Schedules, create one named "moldova-bank-rates: every 6h" with cron `0 */6 * * *`, target = this actor, default input. Save and enable.

- [ ] **Step 5: Configure run-failure alerts**

In the actor's Settings → Notifications, enable "Run failed" email alerts to your account.

- [ ] **Step 6: Smoke-test from a non-owner account**

Either ask a friend to log into Apify and run the actor, or use a second personal Apify account. Compare the dataset output against your own run from Task 2.6 — should be identical (modulo timestamp).

- [ ] **Step 7: Record results in `docs/operations.md`**

```markdown
## v0.1 production cutover
- Auto-deploy commit verified: <SHA>
- 6h schedule ID: <fill-in>
- Alerting: email confirmed for run failures
- External smoke test by: <name / account>
```

```bash
git add docs/operations.md .actor/actor.json
git commit -m "chore: bump version, configure auto-deploy + schedule + alerts"
```

---

### Task 3.4: Apify Store listing assets and pricing

These steps are configured **in the Apify Console UI**, not in code. Each box must be ticked manually before the actor can flip Public.

- [ ] **Step 1: Open the actor's "Publication" tab.**

- [ ] **Step 2: Pricing**

Select **pay-per-result**, set **$0.50 per 1000 results** ($0.0005 / record).

- [ ] **Step 3: Categories & tags**

Categories: **Business**, **Finance**.
Tags: `Moldova`, `exchange rate`, `bank rates`, `currency`, `MDL`.

- [ ] **Step 4: Upload listing assets**

- Hero / banner image: 1280×640 (or per the spec shown in the upload UI). Use a simple branded image with the actor title and an MDL ↔ EUR/USD motif.
- At least one screenshot: open the most recent run's dataset → "View as JSON", screenshot a clean 5–10 record sample.

- [ ] **Step 5: Disclaimer**

Paste this verbatim into the listing description (right after the "What does ... do?" intro):

> Exchange rates are scraped from public bank websites and may lag the bank's quoted rate by several minutes. Always verify with the bank before transacting. This actor is not affiliated with, endorsed by, or sponsored by any of the banks listed.

- [ ] **Step 6: Confirm payout method**

In Account settings, verify PayPal Business (Perlog SRL) is configured as the payout method, OR document the fallback in `docs/operations.md` if the application is still pending.

- [ ] **Step 7: No commit needed.** Tick the boxes in `CONTEXT.md` Faza 3 once each is done.

---

### Task 3.5: Verify the 6-hour schedule has run cleanly four times in a row

This is part of the §9 final gate. Wait at least 24 hours after enabling the schedule.

- [ ] **Step 1: Open Apify Console → Schedules → moldova-bank-rates: every 6h → "Last runs".**

Expected: 4 consecutive `SUCCEEDED` runs.

- [ ] **Step 2: If any run failed**, open the run log, identify the failing bank, fix the parser (TDD-style: add the failing fixture, write a regression test, fix), and restart the cycle.

- [ ] **Step 3: Record stable schedule confirmation in `docs/operations.md`** and commit.

---

## Phase 4 — Final pre-publish gate (CONTEXT §9)

### Task 4.1: Run the §9 checklist

Walk every box in CONTEXT.md §9 against the current state of the actor. Tick each in `CONTEXT.md`. Any unticked item — stop. Do not flip the actor Public.

- [ ] Every box in §5 Faza 0–3 ticked.
- [ ] Latest platform run validates against §4 schema for every record (sample 5 records by hand, or write a small offline validator script that loads the latest dataset export through `Rate.model_validate`).
- [ ] Cost per run documented in the listing (Task 3.1 README "Pricing" section).
- [ ] README has all five sections + at least one runnable API example.
- [ ] Pricing model decided and set (Task 3.4).
- [ ] GitHub auto-deploy verified end-to-end (Task 3.3).
- [ ] 6-hour schedule produced ≥ 4 successful runs in a row (Task 3.5).
- [ ] Smoke test from external account succeeded (Task 3.3 Step 6).
- [ ] Disclaimer text matches §3 Faza 3 exactly (Task 3.4).
- [ ] Day-30 calendar event blocked (create now in your calendar).
- [ ] Day-60 calendar event blocked.

### Task 4.2: Flip the actor from Private to Public

⚠ **Confirm with the user before flipping. This is the irreversible step (you can flip back, but the listing URL is then publicly indexed).**

- [ ] **Step 1: In the actor's Publication tab, set Visibility = Public.**

- [ ] **Step 2: Within 1–6 hours, search "Moldova" and "exchange rate" in the Apify Store search box.** The listing should appear.

- [ ] **Step 3: Tag the release in git**

```bash
git tag -a v0.1.0 -m "Public release: Moldova Bank Exchange Rates v0.1.0"
git push --tags
```

- [ ] **Step 4: Append release line to `CHANGELOG.md`** (move "Unreleased" → today's date) and commit.

```bash
git add CHANGELOG.md
git commit -m "release: v0.1.0"
```

---

## Phase 5 — Post-launch (operational, not code)

These items are tracked in CONTEXT.md §5 "Post-launch" sections. They are **not** implementation tasks for an agent — they are scheduled human work. Listed here so the plan covers the full Definition of Done.

- **Week 1 (3 h budget):** one Reddit post, one Perlog blog post, one public-APIs aggregator submission, ≥ 3 outreach DMs, first external user.
- **Day 30 (calendar-blocked):** record metrics, decide between (a) one more push, (b) accept invisibility, or (c) plan to kill at day 60. Write decision in `docs/operations.md`.
- **Day 60 (calendar-blocked):** kill / maintain / double-down decision per CONTEXT.md §5 thresholds.

---

## Self-Review

Spec coverage check (CONTEXT.md → plan):

- §1 Business context — informs README copy in Task 3.1; nothing else to implement.
- §2 Locked technical decisions — selectolax, httpx async, Pydantic v2, no browser, single-actor, Apify Proxy datacenter, two records per pair (cash/card) all encoded across Tasks 0.3, 0.5, 0.7, 1.x, 2.x.
- §3 Scope — banks, pairs, rate types, defaults all in input schema (Task 2.3) and `InputConfig` (Task 0.6). `available` field present (Task 0.5).
- §4 Output contract — `Rate` model has every listed field with correct types and invariants (Task 0.5).
- §5 Faza 0 — Tasks 0.1–0.11 cover every checkbox.
- §5 Faza 1 — Tasks 1.1–1.5.
- §5 Faza 2 — Tasks 2.1–2.6.
- §5 Faza 3 — Tasks 3.1–3.5 + Task 4.2.
- §5 post-launch sections — Phase 5 (operational, not code).
- §6 Operational readiness (versioning, payout, pricing) — README + actor.json + docs/operations.md.
- §7 Marketing — Phase 5.
- §8 Risk register — mitigations encoded: per-bank isolation (Task 1.5), fixtures + tests (Tasks 0.7, 0.8, 1.x, 2.x), 6h schedule (Task 3.3), disclaimer (Task 3.1).
- §9 Final pre-publish gate — Task 4.1.

Placeholder scan: no `TBD` / `TODO` / "implement later" remain. Where the plan asks the engineer to inspect a fixture before writing assertions (Tasks 0.9, 1.2, 1.4, 2.2), that is unavoidable — the published HTML drives the parser, so the fixture is the source of truth for expected values.

Type consistency: `Rate` model fields, `InputConfig` defaults, `BankFetcher` protocol, `gather_all_rates` signature all consistent across Tasks 0.5, 0.6, 0.9, 1.5, 2.2.

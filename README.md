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

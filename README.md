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
4. When the run finishes (~5 s), open the **Dataset** tab.
5. Export as JSON / CSV, or call the Dataset API URL shown in the run summary.

## Input

The input is a small JSON object. All fields are optional and have defaults that produce ~25–30 records per run.

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
    "buy": 20.10,
    "sell": 20.30,
    "mid": 20.20,
    "spread_pct": 0.99,
    "currency_unit": 1,
    "timestamp": "2026-05-06T20:17:46Z",
    "bank_updated_at": null,
    "source_url": "https://www.maib.md/en/curs-valutar",
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

## Running via API

```bash
curl -X POST "https://api.apify.com/v2/acts/blameless_rumor~moldova-bank-rates/run-sync-get-dataset-items?token=YOUR_APIFY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"banks":["bnm","maib"],"pairs":["EUR/MDL"],"rate_types":["card"]}'
```

Returns the dataset items inline. For asynchronous runs use `/runs` and poll, or hook a webhook on completion.

## Pricing — How much does it cost to scrape Moldovan bank rates?

Pay-per-result, **$0.50 per 1000 records** ($0.0005 / record). A typical run with default input produces 25–30 records, so each run costs roughly **$0.013–$0.015**. Running every 6 hours for a month: about **$1.80**. The Apify free tier covers many runs.

## Tips

- Narrow `banks` and `pairs` to cut record count and cost.
- Schedule every 6 hours rather than every hour — bank rates do not move that fast.
- Use `use_apify_proxy: true` (the default) to avoid rate-limiting from any single IP.
- The actor is idempotent — re-running with the same input returns the latest snapshot, not historical data. For a time series, schedule + persist downstream.

## FAQ, disclaimers and support

> Exchange rates are scraped from public bank websites and may lag the bank's quoted rate by several minutes. Always verify with the bank before transacting. This actor is not affiliated with, endorsed by, or sponsored by any of the banks listed.

- **Selector broke?** Open an Issue on the actor's GitHub repo. Selector fixes typically ship within 24 hours.
- **Need another bank or pair?** Open an Issue describing the use case.
- **Custom integration?** Contact the maintainer via the Apify Store profile.

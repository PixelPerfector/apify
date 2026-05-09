# Operations log

## Ownership and payouts

- Actor owned by **Perlog SRL** (Apify account `blameless_rumor`).
- Payout method: **PayPal Business** linked to Perlog SRL — preferred.
  - Fallback while PayPal application is pending: PayPal personal (income would be personal, IT Park 7% does not apply).
- Switch to **wire transfer** (EUR/USD account) at $100/month run-rate.

## Apify identifiers

- Actor ID: `Spmkpmmwi0bg18Fwh`
- Slug: `blameless_rumor/moldova-bank-rates`
- Console: https://console.apify.com/actors/Spmkpmmwi0bg18Fwh

## First successful platform run (Task 2.6)

- Date: 2026-05-06 23:17 UTC+3
- Build: 0.1.1
- Run ID: `Si0PwPUaTC4KqipIf`
- Run URL: https://console.apify.com/actors/Spmkpmmwi0bg18Fwh/runs/Si0PwPUaTC4KqipIf
- Dataset: https://console.apify.com/storage/datasets/S74X0eSaqYfoDNYPV
- Records produced: **27** (BNM 5 / MAIB 7 / MICB 7 / Victoriabank 8)
- Bank failures: 0
- Duration: ~5 s (parallel fetch)

## Schedule (Task 3.3)

- Schedule ID: `vupWSQY2Ungbf5nod`
- Name: `moldova-bank-rates-every-6h`
- Cron: `0 */6 * * *` (UTC) — fires at 00:00, 06:00, 12:00, 18:00
- isEnabled: true | isExclusive: true
- Email notifications: enabled (default — covers schedule-level failure alerts)
- Created: 2026-05-06 (next fire: 2026-05-07T00:00:00Z)
- API: `apify api /v2/schedules/vupWSQY2Ungbf5nod`

## Pricing (Task 3.4 — pending Console)

Set via Apify Console **Publication** tab when submitting for store review:
- Model: pay-per-result
- $0.50 per 1000 results ($0.0005 / unit, unit = "result")

The REST API rejects setting `pricingInfos` directly on a Private actor (Apify routes paid pricing through the Publication review flow).

## Categories & SEO (set via API 2026-05-09)

- `categories: ["BUSINESS"]` — Apify's enum does **not** include `FINANCE`; `BUSINESS` is the closest match. CONTEXT.md §5 Faza 3 requested both, recorded the deviation here.
- `seoTitle: "Moldova Bank Exchange Rates"` (longer titles >~60 chars rejected by the API)
- `seoDescription: "Live commercial cash and card exchange rates from MAIB, MICB, Victoriabank, BNM."`
- Tags: not exposed via REST API for actors — must be set in the Console (Publication tab).

## Schedule run history (Task 3.5 verified)

12 consecutive scheduled runs SUCCEEDED before this entry was written:

```
2026-05-09 18:00 UTC  SUCCEEDED  10s  27 records
2026-05-09 12:00 UTC  SUCCEEDED  15s
2026-05-09 06:00 UTC  SUCCEEDED  36s
2026-05-09 00:00 UTC  SUCCEEDED  16s
2026-05-08 18:00 UTC  SUCCEEDED  12s
2026-05-08 12:00 UTC  SUCCEEDED  16s
2026-05-08 06:00 UTC  SUCCEEDED  57s
2026-05-08 00:00 UTC  SUCCEEDED  25s
2026-05-07 18:00 UTC  SUCCEEDED  31s
2026-05-07 12:00 UTC  SUCCEEDED  16s
2026-05-07 06:00 UTC  SUCCEEDED  23s
2026-05-07 00:00 UTC  SUCCEEDED  14s
```

§9 also requires every record to validate against the §4 schema. Spot-checked the 2026-05-09 18:00 UTC run dataset (`joqv30JqaxHqzmJoE`, 27 records) — **27/27 validate** under `Rate.model_validate`.

## Listing & publish work still owed by the user (Console only)

Items below cannot be set via the Apify REST API and need a click-through in the Console:

1. Source tab → connect GitHub repo → enable build-on-push for branch `main` (Task 3.3 GitHub auto-deploy)
2. Settings → Notifications → enable per-actor failure email alerts (the schedule already emails on failure; this covers ad-hoc-run failures)
3. Publication tab → Pricing → pay-per-result $0.50/1000 results (goes through Apify review)
4. Publication tab → Tags → add `Moldova`, `exchange rate`, `bank rates`, `currency`, `MDL`
5. Publication tab → Listing description → paste the disclaimer (file: `docs/disclaimer.md`)
6. Publication tab → Listing assets → 1280×640 hero image + at least one dataset screenshot
7. Account settings → Payouts → confirm PayPal Business (Perlog SRL) is configured
8. Smoke-test the actor from a second account (or have a friend log in and run it)
9. Calendar: add `docs/calendar/day-30-review.ics` and `docs/calendar/day-60-decision.ics` to your calendar (default dates are 30 / 60 days after 2026-05-06; move them if the publish date differs)

After the above, ask the controller agent to walk the §9 final gate and flip the actor Public.

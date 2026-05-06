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

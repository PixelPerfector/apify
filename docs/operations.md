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

## Pricing (Task 3.4 — set 2026-05-09)

**Configured live in the Console wizard. Strategic deviation from CONTEXT.md §6.**

Plan called for $0.50 per 1000 results ($0.0005/record). User overrode at the wizard step with explicit instruction "I want this actor to be as cheap as possible". New pricing:

| Event | Per event | Per 1 000 |
|---|---|---|
| `apify-default-dataset-item` (Result, primary) | $0.00001 | **$0.01** |
| `apify-actor-start` (Actor start, infrequent — first 5 s waived) | $0.00005 | $0.05 |

Both are Apify's prefilled minimums. Pricing model: **Pay per event** (PPE — replaces the deprecated Pay-per-Result). Platform usage included free in the per-event price (buyers see one number).

Per typical 27-record run: 1 × $0.00005 + 27 × $0.00001 = **$0.00032**. A 6 h-schedule subscriber ≈ **$0.04/month**. CONTEXT.md §1 sizing was based on $0.0005/record → revise downward 50×: realistic per-buyer ARR is now ~$0.50/year, not $1.20/month.

Trade-off: maximizes adoption / Store discoverability over revenue. Fits the "no validated first customer" position. Re-priceable later (Apify allows pricing edits with a 14-day notice on Public actors).

The REST API rejects setting `pricingInfos` directly; pricing must go through the Console wizard, which gates on:
1. Billing details + Payment method on Subscription tab
2. **Identity verification** (KYC) — done automatically by Apify after Billing setup; took ~5 min for this account, notification "Your identity verification has been approved" lifted the gate.

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

## Console configuration completed in browser session 2026-05-09

Actions taken during the assisted browser session:

- **Publication → Display information** saved with category `Other` (Apify Store enum has no Business/Finance category — closest match). Actor name, short description, custom SEO title and description all populated; "Hide source files from Actor detail" enabled.
- **Source tab** switched from `Web IDE` (multi-file from `apify push`) to `Git repository` pointing at `https://github.com/PixelPerfector/apify.git`, branch `main`, root folder. Manual rebuild verified: build 0.1.4 SUCCEEDED 2026-05-09 22:42 UTC, cloned commit `b30564a`. Future updates: `git push` then trigger build manually OR finish the GitHub-webhook setup for auto-rebuild on push.
- **Monitoring → Alerts** new alert "Run failed (Failed/Aborted/Timed out)" — Status metric, triggers on Failed/Timed out/Aborted. Email-only notification to `perlogv@gmail.com`. Enabled.

## Listing & publish work still owed by the user (Console only)

Items below cannot be set via the Apify REST API and need a click-through in the Console (or a github.com action prohibited per safety rules):

1. **GitHub repo visibility** ✅ Made public 2026-05-09 (Apify can now clone). Future enhancement: set up GitHub webhook for auto-rebuild on every push (Source tab → "GitHub integration" link).
2. Settings → Account → Profile → fill in a real bio + README (current text is the Apify placeholder template) and toggle **"Make profile publicly visible"** ON. Required by Apify before a paid actor can be published to the Store.
3. Publication → Monetization → Pricing → pay-per-result $0.50/1000 results. Blocked on **"Billing details and payment method not set"** — visit `Settings → Billing` first to add company billing info + PayPal Business for Perlog SRL, then return to the actor's Monetization section.
4. Publication → Display information → Icon (hero/banner) — upload a 1280×640 image. The Apify UI does NOT have a separate banner field; the icon is the only image input.
5. Account settings → Payouts → confirm PayPal Business (Perlog SRL) is configured (item 3 covers most of this).
6. Smoke-test the actor from a second account (or have a friend log in and run it).
7. Calendar: add `docs/calendar/day-30-review.ics` and `docs/calendar/day-60-decision.ics` (default dates are 30 / 60 days after 2026-05-06; move them if the publish date differs).

After the above, ask the controller agent to walk the §9 final gate and flip the actor Public.

# Moldovan Bank Exchange Rates Actor — Definition of Done

This document is the contract for the project. Everything in §5 must be checked off before flipping the actor to Public on Apify Store. §9 is the final gate.

---

## 1. Business context

**Product.** An Apify actor that, given a list of Moldovan banks and currency pairs, returns current exchange rates in a normalized JSON dataset. Differentiator: **commercial/counter rates from specific banks** (not the generic central-bank reference rate), on a market (Moldova) where no aggregator API exists.

**Buyers (three plausible personas).**

1. Remittance / regional fintech firms showing users "where to exchange best" — need live multi-bank data.
2. Travel agencies and booking platforms displaying MDL-converted prices — need current rates (Pandatur adjacency).
3. Personal-finance comparison sites and bloggers in Moldova/Romania.

**Honest market sizing.** Total addressable buyers globally: probably 50–200 willing to pay. Unit economics at the launch price of $0.50/1000 results ($0.0005/record) × ~20 records/run × 4 runs/day × 30 days ≈ **$1.20/month per active buyer**. Reaching €300/month minimum needs ~250 active buyers or a few enterprise contracts at custom pricing — *not realistic in year one* at floor pricing. Re-pricing decision happens at day-60 (§5) if demand signal exists. First 6 months realistically €0–20/month without active marketing.

**Why ship anyway.** Low maintenance cost (4 HTML selectors), demonstrable portfolio piece, end-to-end Apify learning on a low-stakes case, replicable template for "Romanian / Ukrainian / Bulgarian Bank Rates" — each a new actor with ~80% reused code.

**No validated first customer.** Building for the listing, not a specific buyer. Week-1 outreach (§7) is the validation loop. If 30-day gate (§8) shows zero buyers, decide consciously.

---

## 2. Locked technical decisions

| Decision | Choice | Rejected | Why |
|---|---|---|---|
| Single vs multi-actor | Single, multi-bank | Per-bank | Buyer UX, single listing to market |
| Language | Python | Node/TS | Existing stack; Apify SDK Python is mature for data-heavy actors |
| HTTP client | `httpx` async | `requests` sync | 4 banks in parallel ≈ <3s vs 10s+ |
| Parsing | `selectolax` (lexbor) | BeautifulSoup | 10–30× faster, simple CSS selectors |
| Browser engine | None | Playwright/Selenium | Rate pages are server-rendered |
| Validation | Pydantic v2 | Raw dicts | Clear errors on HTML drift, auto-documented schema |
| Scraping framework | Apify SDK direct | Crawlee | 4 known GETs — Crawlee is overkill |
| Proxy | Apify Proxy datacenter | None / residential | Free with platform, sufficient for public rate pages |
| BNM (central bank) | Included in same actor | Separate actor | Reference for spread, simpler buyer experience |
| Cash vs card rates | Two separate records, `rate_type` field | Single combined record | Richer data, zero extra cost |
| Repo visibility | Public | Private | SEO + trust > selector secrecy |
| Actor slug | `moldova-bank-rates` | `md-fx-rates`, `moldova-exchange-rates` | Matches buyer search intent ("Moldova", "bank", "rates"); locked at Faza 2, hard to rename post-publish |
| Actor display name | "Moldova Bank Exchange Rates" | — | Same SEO logic |

---

## 3. Scope

**In v1.**
- Banks: BNM (XML), MAIB, MICB, Victoriabank
- Currency pairs: at minimum EUR/MDL, USD/MDL, RON/MDL, GBP/MDL, CHF/MDL, RUB/MDL, UAH/MDL — actual list per bank availability
- Rate types: `cash` and `card` where banks publish both; otherwise whichever exists, marked with `rate_type`
- Output: one record per (bank × pair × rate_type)

**Default input for unattended (6-hour schedule) runs.**
- Banks: all four (BNM, MAIB, MICB, Victoriabank)
- Pairs: EUR/MDL, USD/MDL, RON/MDL, GBP/MDL, CHF/MDL
- Rate types: both `cash` and `card` where the bank publishes both, otherwise whichever exists
- Expected output: ~30–40 records per scheduled run

**Out of v1 (deferred or never).**
- Historical rates / time series
- Alerts on rate change
- Cross-rate calculation (EUR/USD via MDL)
- Forward / forecast rates
- Banks beyond the four listed

---

## 4. Output contract

Per record (bank × pair × rate_type):

| Field | Type | Example | Notes |
|---|---|---|---|
| `pair` | string | "EUR/MDL" | ISO 4217, slash-separated |
| `base` | string | "EUR" | Base currency |
| `quote` | string | "MDL" | Quote currency |
| `bank` | string | "maib" | Internal slug, lowercase |
| `bank_display_name` | string | "Moldova Agroindbank" | For buyer UI |
| `rate_type` | string | "cash" / "card" | Card = card / account transfer |
| `buy` | float \| null | 19.45 | Bank buys base from customer |
| `sell` | float \| null | 19.85 | Bank sells base to customer |
| `mid` | float \| null | 19.65 | (buy+sell)/2; null if either missing |
| `spread_pct` | float \| null | 2.05 | ((sell−buy)/mid)×100 |
| `currency_unit` | int | 1 | Some banks quote per 100 (e.g. 100 JPY) |
| `timestamp` | string ISO | "2026-05-06T14:30:00Z" | Fetch time, UTC |
| `bank_updated_at` | string \| null | "2026-05-06T09:00:00Z" | If bank publishes its own update time |
| `source_url` | string | "https://maib.md/..." | Exact URL scraped |
| `available` | bool | true | False if bank does not quote that pair/rate_type |

**Invariants enforced by Pydantic.**
- `pair == base + "/" + quote`
- If both `buy` and `sell` present, `sell ≥ buy` (else `available=false` and log warning)
- `timestamp` always present, UTC ISO 8601
- Currency codes match ISO 4217

---

## 5. Definition of Done — per phase

### Pre-Faza 0 — Long-lead administrative item (start now, runs in parallel)

- [ ] PayPal Business application for Perlog SRL submitted. Lead time post-2025 reforms is still 1–3 weeks; do not block Faza 0 coding on it but do not approach Faza 3 publishing without it resolved.

### Faza 0 — Setup + BNM scraper (2–3h, hard stop at 4h)

- [ ] Repo on GitHub, public, first commit pushed
- [ ] Apify CLI installed, authenticated with personal token
- [ ] Apify payout method configured: PayPal Business linked to Perlog SRL (preferred) or wire transfer to Perlog SRL bank account; PayPal personal only as fallback. Note in README which entity owns the actor.
- [ ] `apify run` executes locally without errors (even with empty output initially)
- [ ] BNM XML endpoint fetched successfully (HTTP 200)
- [ ] At least 5 pairs from BNM XML parsed correctly
- [ ] Manual sanity check: open bnm.md in browser, compare 3 rates with output — match
- [ ] Output records validate against the §4 schema (Pydantic enforced)
- [ ] Console logging shows per-source fetch time, e.g. "Fetched BNM: 5 pairs in 0.4s"
- [ ] README has at minimum a name and 2-sentence description
- [ ] 30-min ToS skim done for all 4 banks; no explicit prohibition found, or prohibition flagged and decision recorded
- [ ] **Hard stop:** if BNM is not functional at 4h, halt and debug — no progression

### Faza 1 — Two commercial banks + infra (3–4h)

- [ ] Two of {MAIB, MICB, Victoriabank} have functional local scrapers
- [ ] Pydantic Rate model rejects invalid input (a test confirms)
- [ ] Number normalizer handles: "19,45" → 19.45, "1 945,32" → 1945.32, "19.4500" → 19.45
- [ ] Pair normalizer handles: "EUR/MDL", "eur-mdl", "EURMDL" → ("EUR", "MDL")
- [ ] Cash and card rates emitted as separate records where banks publish both
- [ ] HTML fixtures saved under `tests/fixtures/` per bank (regenerate offline tests without network)
- [ ] At least 3 unit tests on normalizers (offline, no network)
- [ ] Visual sanity check: 3 rates per bank match the live site
- [ ] Per-bank error isolation: one bank failing does not crash the actor
- [ ] Per-bank fetch time visible in logs

### Faza 2 — Fourth scraper + Apify deploy (2–3h)

- [ ] All four banks functional locally
- [ ] `.actor/actor.json` valid with locked slug `moldova-bank-rates` and display name "Moldova Bank Exchange Rates" (`apify push` produces no error)
- [ ] `input_schema.json` renders correctly in Apify Console (manual check)
- [ ] `dataset_schema.json` and `output_schema.json` aligned with §4
- [ ] `docker build .` clean (no critical warnings)
- [ ] First Apify platform build completes successfully (built, not just pushed)
- [ ] One platform run produces ≥15 records (4 banks × ~4 pairs)
- [ ] Dataset exports as JSON and CSV from Apify Console (clicked, verified)
- [ ] Total run time: <30 seconds
- [ ] Per-run compute units / cost visible in Run details
- [ ] Run page shareable: copy URL, open in incognito, see result

### Faza 3 — Publishing (2h)

- [ ] Apify Store README has 5 sections: Description, Use cases (3 personas from §1), Input parameters, Output schema with example, FAQ
- [ ] README contains at least one use case with API call example
- [ ] Pricing set in Apify Console: pay-per-result, **$0.50 per 1000 results** ($0.0005/record)
- [ ] Categories and tags set: Business, Finance + relevant keyword tags ("Moldova", "exchange rate", "bank rates", "currency", "MDL")
- [ ] Listing assets uploaded: one banner/hero image (1280×640 or per Apify spec) and at least one screenshot of sample JSON output. Without these the listing looks abandoned.
- [ ] Disclaimer present in listing description, exact text: *"Exchange rates are scraped from public bank websites and may lag the bank's quoted rate by several minutes. Always verify with the bank before transacting. This actor is not affiliated with, endorsed by, or sponsored by any of the banks listed."*
- [ ] PayPal Business for Perlog SRL is approved and configured as Apify payout method (or fallback documented if not yet approved)
- [ ] GitHub auto-deploy configured and verified: a trivial commit triggers a platform build
- [ ] Schedule configured for self-run every 6 hours (catches HTML drift early)
- [ ] Apify monitoring/alerting active on run failure
- [ ] Smoke test as external buyer: log in with a different account (or ask a friend), run actor, verify identical output
- [ ] Actor flipped from Private to Public
- [ ] Listing appears in Apify Store search for "Moldova" or "exchange rate"

### Post-launch — Week 1 marketing push (3h budget, concentrated)

- [ ] One Reddit post in r/Moldova or r/Romania (respect community promo rules)
- [ ] One blog post on Perlog site: "Free API for Moldovan bank exchange rates"
- [ ] Submission to one public-APIs aggregator list (e.g. github.com/public-apis)
- [ ] Outreach DM to at least 3 named prospects in the three persona segments
- [ ] First external user (even a personally invited one) has completed a run

### Post-launch — Day 30 status review (mandatory, calendar-blocked)

Recorded metrics: paying runs, total non-owner runs, unique non-owner users, inbound contacts (Apify issues, emails, GitHub interactions, DMs).

**"Alive" signals — at least one of:**
- [ ] ≥1 paying run from a non-owner account
- [ ] ≥10 unique non-owner runs
- [ ] ≥1 inbound contact

If none of the three are met: the listing is invisible. Decision required between (a) one more concentrated marketing push (~3h), (b) accept invisibility and move to silent maintenance, or (c) kill at day 60. Decision written down here.

- [ ] At least one README iteration based on observed first real use (or, if no real use, based on what's missing in the listing)

### Post-launch — Day 60 kill-or-double-down

Compare month-2 metrics against:

- [ ] **Double down** (scope a second country actor — RO/UA/BG): ≥3 paying buyers **or** ≥€10/month run-rate
- [ ] **Maintain** (keep alive, no further investment beyond §6 baseline): ≥1 paying buyer **and** ≥30 unique non-owner runs in month 2
- [ ] **Kill or silent-maintenance** (unlist from Store or leave listed but stop responding to support; repo stays public): below both thresholds

Day-60 is *not* the €300/month target — that needs 6+ months of organic discovery. Day-60 only tests whether any demand signal exists.

---

## 6. Operational readiness

**Maintenance commitment.** ~2h/month indefinite, distributed:
- Selector breakage: 30–60 min when it happens (1–2× per year per bank)
- Dependency updates: 30 min/quarter
- Buyer support (issues, questions): variable
- Adding banks/pairs on validated request: 1–3h per accepted request

If this commitment is not realistic, kill at the 30-day gate (§5) — do not let it become a zombie project.

**Versioning.**
- Bug fix → patch (0.1.1)
- New bank, output backward-compatible → minor (0.2.0)
- Output schema change → major (1.0.0)
- Pre-1.0.0 = public beta, breaking changes allowed more freely

**Legal posture.** Scraping public bank rate pages is generally legal in EU jurisdictions (public factual data, no copyright). Mitigations:
- ToS skim done in Faza 0 — only block on explicit prohibition
- Rate-limit conservative (1 request per 5–10 seconds per bank) by design
- `robots.txt` respected explicitly (Apify SDK does not by default)

**Payouts.** Apify pays creators via **PayPal** (min $20) or **wire transfer** (min $100) — *not* Stripe (Stripe is Apify's collection side). Default route:
- **Start: PayPal Business linked to Perlog SRL.** PayPal MD business accounts became practical after the April 2025 government reforms enabling Stripe/PayPal/Revolut for MD businesses. Low threshold means early small payouts actually disburse. IT Park 7% applies because revenue lands in the SRL.
- **Switch at $100/month run-rate: wire transfer** to Perlog SRL EUR/USD account. Lower fees, cleaner accounting.
- **Fallback only: PayPal personal.** Income would be personal, IT Park 7% does not apply. Avoid unless SRL PayPal Business cannot be opened.

**Pricing.** Pay-per-result, **$0.50 per 1000 results** ($0.0005/record) at launch. Rationale: matches the Apify Store floor for established scrapers (Instagram, Twitter at $0.25–$0.50/1k), signals "real data" without distress pricing. Per typical run (~20 records) ≈ $0.01. Per active buyer/month ≈ $2.40 (revise §1 expectations downward accordingly). Re-price upward at day-60 if double-down threshold (§5) is hit.

---

## 7. Marketing plan (passive-leaning)

3h concentrated budget in week 1 (see §5), then **observation mode**. The Apify Store listing is the primary asset — buyers search "Moldova", "exchange rate", "bank rates", "currency". Listing SEO is the long-term lever.

Available channels beyond the Store, ranked by expected return:
1. Cross-list on RapidAPI (same code via Apify API gateway)
2. github.com/public-apis submission
3. r/Moldova, r/Romania post (one-time, respectful of promo policies)
4. Perlog blog article
5. Local fintech Facebook groups (last; lowest signal)

---

## 8. Risk register

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Selectors break in first 3 months | High (60–80%) | Medium | Logging + alerting, fixture tests, 6h schedule catches it |
| A bank blocks Apify Proxy | Medium | High | Test without proxy first; residential proxy as backup |
| Zero buyers in 60 days | High (≥50%) | Medium | Acceptable sunk cost if Faza 0–3 stays ≤12h; 30/60-day gates |
| Apify changes pricing/policy | Low | High | Code is portable — RapidAPI as escape hatch |
| Interest dies after 2 weeks (per pattern) | High | Total | 30-day gate is the commitment device |
| Normalizer bug produces wrong rates (financial!) | Medium | High | Sanity check vs live site in CI; visible disclaimer in README |
| ToS violation triggers cease-and-desist | Low | High | Skim done, conservative rate-limit, respond fast if contacted |

---

## 9. Final pre-publish gate

The actor goes Public only when **all** of the following are true. No exceptions, no "fix-it-after".

- [ ] Every box in §5 Faza 0–3 is checked
- [ ] Output validates against §4 schema for every record produced in the latest platform run
- [ ] Cost per run is known and documented in the listing
- [ ] README has all 5 sections, including at least one runnable API example
- [ ] Pricing model decided and set
- [ ] GitHub auto-deploy verified end-to-end with a real test commit
- [ ] 6-hour schedule is live and has produced at least 4 successful runs in a row
- [ ] Smoke test from external account (different from owner) succeeded
- [ ] Disclaimer in listing matches the exact text specified in Faza 3
- [ ] Day-30 calendar event blocked for status review
- [ ] Day-60 calendar event blocked for kill-or-double-down decision

If any box is unchecked, the actor stays Private. The cost of shipping an embarrassing or broken financial-data actor is much higher than the cost of one extra day of polish.

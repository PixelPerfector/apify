# Legal & ToS skim notes

30-min ToS / robots.txt skim per CONTEXT.md §5 Faza 0. Update before publishing.

## bnm.md

- Page: https://www.bnm.md/en/official_exchange_rates
- XML endpoint used: https://www.bnm.md/en/official_exchange_rates?get_xml=1&date=DD.MM.YYYY
- Fixture captured: 2026-05-06 (HTTP 200, 6943 bytes, schema: `ValCurs[Valute[CharCode, Nominal, Value]]`)
- Skim date: <FILL IN BEFORE PUBLISH>
- robots.txt: <FILL IN — paste relevant rules>
- ToS notes: <FILL IN — explicit prohibitions, attribution requirements>
- Decision: <PROCEED / BLOCK / NEEDS LEGAL REVIEW>

## micb.md

- Page: https://micb.md/en/ (homepage; `<section class="exchange-section">` is server-rendered)
- Fixture captured: 2026-05-06 (HTTP 200, 184872 bytes; WordPress site)
- Notes: rates inlined in homepage; both cash and card panels in DOM with `data-exchangetab="cash|card"`. Card section has no BNM column.
- Skim date: <FILL IN BEFORE PUBLISH>
- robots.txt: <FILL IN — paste relevant rules>
- ToS notes: <FILL IN — explicit prohibitions, attribution requirements>
- Decision: <PROCEED / BLOCK / NEEDS LEGAL REVIEW>

## maib.md

- Page: https://www.maib.md/en/curs-valutar (server-rendered; correct URL — `/en/exchange-rates` is a 404)
- Fixture captured: 2026-05-06 (HTTP 200, 169318 bytes, 7 `<table class="exchange__item">` blocks for branch-cash, customs-cash, card)
- Notes: site is a Laravel SPA but the rate page is server-rendered; behind Incapsula WAF (some headers blocked). Real-browser UA + `Accept-Language: en-US` succeeded from datacenter IP.
- Skim date: <FILL IN BEFORE PUBLISH>
- robots.txt: <FILL IN — paste relevant rules>
- ToS notes: <FILL IN — explicit prohibitions, attribution requirements>
- Decision: <PROCEED / BLOCK / NEEDS LEGAL REVIEW>

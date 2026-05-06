Iată tot contextul, cu DoD foarte specifice și întrebările pe care le am încă deschise (marcate cu ❓ și grupate la final).

---

## 1. Contextul de business

**Produsul în două propoziții.** Un actor Apify care, dat fiind o listă de bănci moldovenești și perechi valutare, returnează ratele de schimb curente într-un format JSON normalizat. Diferențiator: rate **de ghișeu/comerciale** ale băncilor specifice (nu rate oficiale generice de la banca centrală), pe o piață (Moldova) unde nu există API agregator existent.

**Cui îi vinzi.** Trei personas plauzibile:

1. **Firme de remitențe / fintech regionale** care arată user-ului "unde schimbi cel mai bine" — au nevoie de date live multi-bank.
2. **Agenții de turism și platforme de booking** care afișează prețuri în MDL convertite — au nevoie de rate curente (asta e adjacency-ul tău Pandatur).
3. **Comparatoare de rate / blogeri de finanțe personale** din Moldova/România.

**Realitatea pieței.** Volum total de buyeri posibili: probabil 50-200 globally interesați să plătească pentru asta. La $0.002/rate × ~20 rate/run × 4 runs/zi × 30 zile = ~$5/lună per buyer activ. Pentru €300/lună (target tău minim) ai nevoie de ~60 buyeri activi sau câțiva enterprise. Realist, primele 6 luni ești în zona €0-50/lună dacă nu marketizezi activ.

**De ce e totuși worth shipping.** Cost de mentenanță scăzut (4 selectori HTML), e un proiect demonstrabil în portofoliu, învață platforma Apify end-to-end pe un caz cu mize mici, și template-ul îl poți replica pentru "Romanian Bank Rates", "Ukrainian Bank Rates", "Bulgarian Bank Rates" — fiecare un actor nou cu 80% cod refolosit.

❓ **Q1**: ai vreun first customer în minte (chiar ca smoke test gratuit) care ar folosi datele astea? Validation pre-lansare schimbă scope-ul — dacă există o agenție de turism care zice "îmi trebuie", construiești pentru ei specific.

---

## 2. Contextul tehnic — decizii și WHY

| Decizie               | Aleasă                         | Alternativa respinsă     | Motivul                                                                         |
| --------------------- | ------------------------------ | ------------------------ | ------------------------------------------------------------------------------- |
| Single vs multi-actor | Single, multi-bank             | Per-bancă                | UX buyer + un singur listing de marketat                                        |
| Limbaj                | Python                         | Node/TypeScript          | Stack-ul tău existent, Apify SDK e mai matur în Python pentru actors data-heavy |
| HTTP client           | `httpx` async                  | `requests` sync          | 4 bănci în paralel = sub 3s vs 10s+                                             |
| Parsing               | `selectolax` (lexbor)          | BeautifulSoup            | 10-30x mai rapid, CSS selectors simpli                                          |
| Browser engine        | Niciunul                       | Playwright/Selenium      | Rate pages sunt server-rendered — costul Playwright nu se justifică             |
| Validation            | Pydantic v2                    | Dict-uri raw             | Erori clare la HTML schimbat, output schema documentat automat                  |
| Scraping framework    | Apify SDK direct, fără Crawlee | Crawlee                  | 4 GET-uri pe pagini cunoscute = Crawlee e overkill                              |
| Proxy                 | Apify Proxy datacenter         | Fără proxy / residential | Inclus gratuit, suficient pentru rate publice                                   |

❓ **Q2**: BNM are date oficial publicate prin XML (un endpoint stabil). Le incluzi ca "bank=bnm" alături de cele 3 bănci comerciale (avantaj: referință oficială pentru spread calculation), sau separi în două actors? Recomand să le incluzi în același actor, simplifică buyer experience.

---

## 3. Modelul de output — exact ce returnezi

Per fiecare combinație (bancă × pereche), un record în dataset cu aceste câmpuri:

| Câmp                | Tip            | Exemplu                | Notă                                              |
| ------------------- | -------------- | ---------------------- | ------------------------------------------------- |
| `pair`              | string         | "EUR/MDL"              | Format standardizat ISO 4217                      |
| `base`              | string         | "EUR"                  | Valuta de bază                                    |
| `quote`             | string         | "MDL"                  | Valuta de cotație                                 |
| `bank`              | string         | "maib"                 | Slug intern, lowercase                            |
| `bank_display_name` | string         | "Moldova Agroindbank"  | Pentru UI buyer                                   |
| `buy`               | float \| null  | 19.45                  | Rata la care banca cumpără valuta de bază         |
| `sell`              | float \| null  | 19.85                  | Rata la care banca vinde valuta de bază           |
| `mid`               | float \| null  | 19.65                  | Calculat (buy+sell)/2, sau null dacă lipsește una |
| `spread_pct`        | float \| null  | 2.05                   | Calculat ((sell-buy)/mid)\*100                    |
| `currency_unit`     | int            | 1                      | Unele bănci cotează la 100 (ex. 100 JPY)          |
| `timestamp`         | string ISO     | "2026-05-06T14:30:00Z" | Când ai fetch-uit, UTC                            |
| `bank_updated_at`   | string \| null | "2026-05-06T09:00:00Z" | Dacă banca afișează când a actualizat ea          |
| `source_url`        | string         | "https://maib.md/..."  | URL-ul exact scrapat                              |
| `available`         | bool           | true                   | False dacă banca nu cotează acea pereche          |

❓ **Q3**: include `spread_pct` calculat în output, sau lași buyer-ul să-l calculeze? Argumentul pentru include: e principala valoare de business a datelor astea (cine are spread mai mic = unde schimbi mai bine).

❓ **Q4**: unele bănci au rate diferite pentru **cash** vs **card/cont** — diferă cu 0.5-2%. Le tratezi ca două record-uri separate (cu `rate_type: "cash" | "card"`), sau iei doar una (care?), sau pe ambele într-un câmp compus? Recomand: două record-uri, e date mai bogate la cost zero.

---

## 4. Definition of Done — fiecare fază

### Faza 0: Setup + primul scraper (BNM) — 2-3h

DoD:

- [ ] Repo GitHub creat, primul commit pushed
- [ ] Apify CLI instalat, autentificat cu token-ul tău
- [ ] `apify run` local execută fără erori (chiar și cu output gol inițial)
- [ ] BNM XML fetched cu success (HTTP 200)
- [ ] Cel puțin 5 perechi din BNM XML parsate corect
- [ ] Output validat: rulezi `apify run`, deschizi `storage/datasets/default/`, verifici 5 fișiere JSON cu structura din tabelul de mai sus
- [ ] Sanity check manual: deschizi bnm.md în browser, compari 3 rate cu output-ul tău — match
- [ ] Logging clar: vezi în consolă "Fetched BNM: 5 pairs in 0.4s"
- [ ] `git push` realizat, repo are README cu minim numele și 2 fraze descriere
- [ ] **Hard stop**: dacă la 4h nu ai BNM funcțional, oprește și debug — nu mergi mai departe

### Faza 1: Două bănci comerciale + infra — 3-4h

DoD:

- [ ] Două din {maib, micb, victoriabank} au scrapere funcționale local
- [ ] Pydantic Rate model rejectează input invalid (ai un test care confirmă)
- [ ] Normalizer pentru numere: "19,45" → 19.45, "1 945,32" → 1945.32, "19.4500" → 19.45
- [ ] Normalizer pentru perechi: "EUR/MDL" / "eur-mdl" / "EURMDL" → ("EUR", "MDL")
- [ ] Sanity check vizual pentru fiecare bancă: 3 rate match cu site-ul în browser
- [ ] Fixture HTML salvat în `tests/fixtures/` per bancă (ca să poți regenera teste fără rețea)
- [ ] Cel puțin 3 unit tests pentru normalizer (offline, fără rețea)
- [ ] Logging: timpul de fetch per bancă vizibil
- [ ] Erori la o bancă nu doboară celelalte (try/except per bancă, nu per actor)
- [ ] `git push` cu commit message clar

### Faza 2: Al patrulea scraper + deploy Apify — 2-3h

DoD:

- [ ] Toate 4 bănci funcționale local
- [ ] `.actor/actor.json` valid (Apify CLI nu dă eroare la `apify push`)
- [ ] `input_schema.json` deschis în Apify Console afișează UI corect (manual check)
- [ ] Dockerfile build local cu `docker build .` fără warnings critice
- [ ] Primul build pe Apify platform finalizat cu success (nu doar pushed — _built_)
- [ ] Un test run pe Apify produce dataset cu ≥15 records (4 bănci × ~4-5 perechi)
- [ ] Dataset exportabil ca JSON și CSV din Apify Console (clic verificat)
- [ ] Total runtime al unui run: <30 secunde
- [ ] Cost estimat per run vizibil în Run details (compute units)
- [ ] Run page is shareable — copiezi URL-ul, deschizi în incognito, vezi rezultatul

### Faza 3: Publishing — 2h

DoD:

- [ ] README pe Apify Store are 5 secțiuni: Description, Use cases (3 personas), Input parameters, Output schema with example, FAQ
- [ ] README include cel puțin 1 use case cu exemplu de cod (cum apelezi actor-ul prin API)
- [ ] Pricing setat: pay-per-result, preț confirmat de tine
- [ ] Actor mutat din Private în Public
- [ ] Actor apare în Apify Store la căutarea "Moldova" sau "exchange rate"
- [ ] GitHub auto-deploy configurat și verificat: faci un commit minor, vezi build automat pe Apify
- [ ] Smoke test ca buyer extern: te loghezi cu alt cont (sau cere unui prieten), rulezi actor-ul, verifici că output-ul e identic
- [ ] Categorii și tags setate pe Apify Store: Business, Finance + tags relevante

### Post-launch (săptămâna 2)

DoD:

- [ ] Schedule self-run la 6h interval (catch HTML breakage early)
- [ ] Apify monitoring/alerting activ pe failure
- [ ] Primul user extern (chiar dacă tu îl inviți) a făcut un run
- [ ] Iterație #1 pe README bazat pe ce ai observat la primul use real

❓ **Q5**: ai un timeline strict pentru postlaunch? Sugerez: dacă în 30 zile de la launch ai 0 revenue și 0 buyeri organici, decizi conștient: (a) marketing push activ, (b) low-maintenance + treci la următorul actor, (c) kill. Fără timeline ferm, riscul de procrastinare-cu-mentenanță e mare.

---

## 5. Contextul operațional

**GitHub repo — public sau privat?**

| Public                                     | Privat                                         |
| ------------------------------------------ | ---------------------------------------------- |
| SEO bonus pentru Apify listing (link-back) | Cod proprietar protejat                        |
| "Built in public" ca marketing             | Mai multă libertate la experimente             |
| Ușor de partajat în portofoliu             | Selectorii nu sunt vizibili pentru competitori |
| Trust signal pentru buyeri                 | —                                              |

❓ **Q6**: public sau privat? Recomand **public** la primul actor — selectorii oricum sunt triviali, beneficiul de SEO și trust depășește riscul.

**Mentenanță continuă.** Te aștepți la ~1-2h/lună pe actor, distribuit:

- Selectori care se strică: 30-60 min când se întâmplă (1-2x pe an per bancă)
- Actualizări dependențe: 30 min/trimestru
- Suport buyeri (issue-uri, întrebări): variabil
- Adăugări de bănci/perechi cerute: 1-3h per cerere validă

❓ **Q7**: ești OK cu commitment-ul ăsta de ~2h/lună indefinit? Dacă nu, modelul de business pivotează spre "publish & forget, accept attrition".

**Versionare.**

- Bug fix → patch (0.1.1)
- Bancă nouă, output backward-compatible → minor (0.2.0)
- Schimbare în output schema → major (1.0.0)
- Înainte de 1.0.0 ești în "beta" public, ai voie la breaking changes mai des

**Ownership legal.** Sub Perlog Software (IT Park Moldova, 7%) sau personal? Dacă vrei să tratezi venitul ca income corporate, factoring-ul Apify trebuie să meargă către contul Perlog. Apify plătește prin Stripe Connect/PayPal — verifică ce suportă pentru SRL Moldova.

❓ **Q8**: cum colectezi banii? Stripe pe SRL Perlog, Stripe personal, Wise, sau lași Apify să acumuleze și retragi rar? Asta afectează doar cum setezi contul Apify la început, dar e mai ușor de făcut bine de la start decât de migrat după.

**Legal/ToS.** Scraping-ul de rate publice afișate pe site-uri bancare e în general legal în UE (e date publice, factuale, neprotejate de copyright). Dar:

- Citești ToS la fiecare bancă — unele interzic explicit acces automat
- Respect `robots.txt` (Apify SDK nu o face by default — îl adaugi manual)
- Rate-limit conservator (1 request per 5-10 secunde per bancă) ca să nu pari malițios

❓ **Q9**: ai timp de 30 min să verifici ToS-urile pentru cele 4 bănci? Sau preferi să mergi cu "rate limit conservator + dacă cineva se plânge, adaptez"? Recomandare: skim ToS-urile, dar nu te bloca aici.

---

## 6. Marketing și discovery (după publishing)

Apify Store search e principal — buyeri caută "Moldova", "exchange rate", "bank rates", "currency". SEO-ul listing-ului e cel mai important asset de marketing pe care îl ai. Dincolo de Store:

- Cross-listing pe RapidAPI (poate fi același cod prin Apify API gateway)
- Submission pe Public APIs lists (github.com/public-apis)
- Post pe r/Moldova, r/Romania, grupuri Facebook fintech locale (atenție la promo policies)
- Articol blog pe propriul site Perlog: "Free API for Moldovan bank exchange rates"

❓ **Q10**: marketing activ vs pasiv? Pasiv = doar listing-ul Apify, vezi ce vine organic. Activ = ~5-10h în prima lună pe distribution. Dat fiind pattern-ul tău, recomand maxim 3h marketing concentrat în prima săptămână, apoi observation mode.

---

## 7. Riscuri și ce îți poți da-stuck

| Risc                                           | Probabilitate      | Impact | Mitigare                                           |
| ---------------------------------------------- | ------------------ | ------ | -------------------------------------------------- |
| Selectori HTML se strică în primele 3 luni     | Mare (60-80%)      | Mediu  | Logging + alerting, fixture tests                  |
| Bancă blochează Apify Proxy                    | Medie              | Mare   | Test fără proxy întâi, residential proxy ca backup |
| Zero buyeri în 60 zile                         | Mare (50%+)        | Mediu  | Cost sunk acceptabil dacă faza 0-3 a fost <12h     |
| Apify schimbă pricing/policies                 | Mică               | Mare   | Cod portabil — putem migra pe RapidAPI             |
| Tu pierzi interes după 2 săptămâni             | Mare (per pattern) | Total  | Commitment device + decizie conștientă la 30 zile  |
| Bug în normalizer dă rate greșite (financial!) | Medie              | Mare   | Sanity check vs site real în CI                    |
| ToS violation triggers cease-and-desist        | Mică               | Mare   | Skim ToS, conservative rate-limit                  |

---

## 8. Sumar întrebări deschise

| #   | Întrebare                                          | Decizie blocantă pentru                    |
| --- | -------------------------------------------------- | ------------------------------------------ |
| Q1  | First customer/use case validat?                   | Schimbă scope-ul de la generic la specific |
| Q2  | BNM inclus în același actor?                       | Faza 0 (recomand: da)                      |
| Q3  | `spread_pct` calculat în output?                   | Faza 0 (recomand: da)                      |
| Q4  | Cash vs card rates separat?                        | Faza 0 (recomand: două record-uri)         |
| Q5  | Timeline strict postlaunch?                        | Disciplină generală                        |
| Q6  | Repo public sau privat?                            | Faza 0 (recomand: public)                  |
| Q7  | OK cu ~2h/lună mentenanță indefinit?               | Decizie de a publica vs a face throwaway   |
| Q8  | Cum colectezi plățile (Stripe Perlog vs personal)? | Setup cont Apify, before publishing        |
| Q9  | Verifici ToS-urile băncilor?                       | Înainte de publishing public               |
| Q10 | Marketing activ sau pasiv?                         | După publishing                            |

Răspunde la cele care contează pentru tine acum (Q2, Q3, Q4 sunt cele care îți blochează scrierea codului — restul pot aștepta sau pot fi decise pe parcurs).

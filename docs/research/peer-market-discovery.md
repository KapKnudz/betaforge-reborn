# Finding peers and market evidence

Research reviewed on 6 November 2026. This is a source assessment and proposed discovery procedure, not an implemented data service or a validated peer set. Source access was checked through documentation, public pages and two Yahoo profiles; no new subscription, credential registration or Börsdata request was made.

## Recommendation

Start with the preserved Nordic Börsdata directory, then use business descriptions and global searches to find stronger economic matches. Swedish peers are useful; US peers are optional. Select by products, customers, revenue model and capital needs under the [comparison policy](../analysis-policy.md#evidence-and-comparisons).

There is an official database for Swedish companies by industry: SCB's Business Register with SNI codes. It describes legal entities, including unlisted businesses, rather than a ready-made list of comparable listed groups. For Betaforge's first version, use it as optional enrichment rather than importing all Swedish businesses. [SCB register and legal-entity definition](https://www.scb.se/vara-tjanster/bestall-data-och-statistik/foretagsregistret/avgiftsfria-uppgifter-i-foretagsregistret/).

Keep three questions separate: **which companies exist**, **which businesses are economically comparable**, and **which financial values can be compared**. A screener answers only part of this sequence.

## Sources worth using

| Source | Useful information | Access established and main limitation | First use |
|---|---|---|---|
| Preserved Börsdata directory | Nordic instruments, tickers/ISINs/Yahoo symbols, country/market and sector/branch lookup IDs. | Saved JSON is available offline. The wider directory is separate from the 30-company financial corpus. Instruments are not unique operating groups. | Primary local candidate source. |
| Nasdaq Nordic and First North | Official venue listings and instrument identity; ICB supplies an industry hierarchy. | Public screener exists, but rows did not populate in the research web tool. Documented reference-file delivery requires product entitlements; a free stable public API was not established. | Check listings and supplement discovery. |
| Spotlight and NGM | Official supplemental Swedish-venue company/instrument lists. | Public pages exist; a general anonymous universe/classification API was not verified. Nasdaq alone does not establish coverage of these venues. | Add when the listing scope needs them. |
| SCB Business Register | Swedish legal entities/workplaces, organization numbers, activity codes and size classes. | Free documented JSON API with registration and API key; authenticated queries were not tested. Legal-entity activity can differ from consolidated group activity. | Optional SNI/identity enrichment. |
| Bolagsverket's SCB bulk distribution | Organization identifiers and up to five SNI codes in a documented weekly file. | Free file route documented, but direct download was blocked by a human-check page here. No successful bulk import is claimed. | Evaluate only if bulk SNI enrichment becomes useful. |
| Yahoo Finance | Country/sector/industry discovery, company profiles, security symbols and dated valuation context. | Non-US profiles were verified in a browser. Some web requests returned 429; Swedish screener output and a stable supported automation API were not verified. | Global discovery and secondary quote context. |
| Issuer reports; SEC EDGAR for US filers | Products, segments, customers, financial definitions, reports and named competitors. | Original reports establish accounting meaning. SEC's documented APIs cover standard entity-wide XBRL facts, not every custom/segment metric. | Validate candidate fit and material financials. |

Sources: [Börsdata instruments](https://github.com/Borsdata-Sweden/API/wiki/Instruments); [Nasdaq screener](https://www.nasdaq.com/european-market-activity/shares), [reference-file product](https://www.nasdaq.com/products/data/nordic-baltic/nordic-reference-data-files), [ICB owner](https://www.lseg.com/en/ftse-russell/industry-classification-benchmark-icb); [Spotlight companies](https://spotlightstockmarket.com/en/market-overview/our-companies/), [NGM companies](https://www.ngm.se/noterade-bolag); [SCB](https://www.scb.se/vara-tjanster/bestall-data-och-statistik/foretagsregistret/avgiftsfria-uppgifter-i-foretagsregistret/), [Bolagsverket download documentation](https://bolagsverket.se/apierochoppnadata/hamtaforetagsinformation/nedladdningsbarafiler.2517.html); [Yahoo screener help](https://en-global.help.yahoo.com/kb/SLN28083.html), [equity screener](https://finance.yahoo.com/research-hub/screener/equity/); [SEC APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces).

The matrix is an integration recommendation based on the evidence below, not a claim that each source has a working connector. FinBas was also checked; its documented academic-use restriction makes it unsuitable as the default personal-investment source. [Provider terms](https://www.houseoffinance.se/data-center/shof-data-center--a-national-mission/terms-and-conditions/).

## What we already have

The frozen 3 November corpus includes a broader Nordic catalogue: 1,706 instrument records, 10 sectors, 94 branches, 73 markets and 19 country lookup entries. A direct read of one saved full capture confirmed these counts and nonempty Yahoo-symbol fields. This does not establish that every symbol resolves today or that every country entry has covered operating companies.

The [acquisition plan](../../scripts/fetch_borsdata_context.py) requests the unfiltered directory and dictionaries. The [storage layer](../../betaforge/storage.py) preserves instrument versions and raw lookup payloads. An instrument carries `insId`, `isin`, `ticker`, `yahoo`, `sectorId`, `branchId`, `marketId`, `countryId` and currencies. Branches link to sectors; markets link to countries and exchange names. These existing relations can seed discovery without live API access.

Do not describe this as 1,706 researched companies. The catalogue includes multiple instrument types, share classes and indices; full financial captures remain limited to the selected 30. There is no issuer-group key in the saved instrument schema. The separate global-directory endpoint was not part of this capture plan. [Börsdata instrument types/relations](https://github.com/Borsdata-Sweden/API/wiki/Instruments), [separate global directory](https://github.com/Borsdata-Sweden/API/wiki/Global-Instruments).

Private checks also tried same-branch discovery for two selected companies. Both returned many ordinary-share records, demonstrating a broad starting pool rather than a ready-made peer list. No candidate's economic comparability or valuation was validated by that experiment.

The private source/count receipt is retained at `data/research-audits/20261106-peer-discovery/catalogue-check.json`; it records the saved JSON paths and hashes. Counts and field presence are verified separately from current symbol validity or financial coverage.

## How the agent knows what to search for

### 1. Write a short business profile

Extract five items from the target's reports: products/services, customers/end markets, revenue model, principal costs/capital needs, and operating geography. Include disclosed segment mix where material. Use the [business-evidence guide](../skill-drafts/betaforge-company-analysis/references/business-evidence.md); a claim such as pricing power needs evidence rather than a label.

### 2. Generate a bounded candidate list

Use the saved branch and neighboring categories as search leads. Combine them with product/business-model terms in Swedish and English, named competitors in reports and official venue lists. A classification filter can miss a good peer; do not require identical codes across providers.

Start locally for convenience, then look across Europe, North America and other relevant markets for a stronger match. Country affects comparability through actual regulation, tax, customers and economics. Ease of US data access is useful but does not establish a better economic match.

### 3. Resolve identity and validate the business

Use the saved Yahoo symbol when present; verify the resulting name, exchange, share class and currency. Otherwise search issuer name plus exchange and confirm against an official listing or issuer page. Do not guess a ticker suffix. Keep listing venue, legal domicile and sales geography separate.

Read each promising candidate's business/segment description and latest available annual/interim. Record **why it matches**, **the main difference**, and whether it is an operating peer, a partial/segment comparison or context only. Resolve duplicate share classes/cross-listings at issuer level; a matching ISIN identifies a security, not the whole group. Retain roughly three to five useful peers, or fewer with a reason. These are working categories, not a scoring model.

### 4. Retrieve only the comparisons that matter

Normally select sales/growth, EBIT/margin, material capital/cash needs and a dated EV/EBIT or P/E check when comparable. Preserve report definitions, periods, currency, scope and adjustments under the [handoff guide](../skill-drafts/betaforge-market-peer-research/references/evidence-handoff.md). Distinguish reported actuals, issuer guidance and third-party estimates. A provider's EV/EBITDA cannot be relabeled EV/EBIT; a parent security price needs compatible earnings/claims.

Use peer market multiples as evidence of relative pricing. The lead analyst must explain differences and why a selected exit multiple fits the target at the forecast horizon. Neither a peer mean nor the current target-company multiple automatically establishes fair value.

## Concrete search examples

These illustrate discovery, not selected peer groups or a new valuation.

| Starting business evidence | Search terms to try | Validation question |
|---|---|---|
| AQ describes several electrical, mechanical and system manufacturing activities. | `contract manufacturing industrial electrical mechanical systems annual report`; `high mix low volume electronics manufacturing listed company` | Does a candidate match the relevant product/customer mix and capital needs, or only one part of AQ? A single electronics category may miss the broader business. |
| Lime's annual report describes CRM software plus its own implementation/support activities. | `CRM software recurring revenue own implementation annual report`; `listed vertical CRM software Europe` | Is the candidate a software owner, reseller or consultancy? How different are service mix, customer size, sales channel and capitalized development? |

Evidence: [AQ business areas](https://www.aqgroup.com/en/business-areas), [AQ sheet-metal business](https://www.aqgroup.com/en/business-areas/sheet-metal-processing/about); [Lime 2024 annual report, printed p.12](https://investors.lime-technologies.com/wp-content/uploads/2025/03/Annual-Report-Lime-2024.pdf). The queries and match tests are our proposed application of those descriptions; no search ranking or final peer fit is established by them.

Two live Yahoo profile checks demonstrate non-US usefulness: [NOTE.ST](https://finance.yahoo.com/quote/NOTE.ST/profile/) exposed a Stockholm/SEK listing, an electronics classification and an EMS business description; [CSU.TO](https://finance.yahoo.com/quote/CSU.TO/profile/) exposed a Toronto/CAD listing and vertical-market software description. The latter is Canadian, illustrating why global does not mean US-only. Neither is adopted as a peer by this observation. Yahoo's screener offered Sweden, but the research session reset to US; no successful Swedish result export is claimed. A readable profile does not establish complete Swedish coverage or reliable automated retrieval.

One tested query, `site:sec.gov/Archives/edgar "electronics manufacturing services" "2025" "Plexus"`, returned [Plexus's 2025 Form 10-K](https://www.sec.gov/Archives/edgar/data/785786/000078578625000064/plxs-20250927.htm). Its competition discussion distinguishes complex, lower-volume work from high-volume manufacturing. Separately, [Kimball Electronics' 2026 Form 10-K, Business/Competitors](https://www.sec.gov/Archives/edgar/data/1606757/000160675726000032/ke-20260630.htm) names Benchmark, Flex, Jabil, Plexus and Sanmina. This demonstrates a way to expand a seed list through original reports; those names still need economic matching before selection.

## Add market context through the same drivers

Select one or two indicators that could change a material forecast: customer output/orders, inventories, price trends, replacement demand or capacity. SCB publishes monthly production statistics and documents its [PxWebApi v2](https://www.scb.se/en/api); Eurostat documents [API access](https://ec.europa.eu/eurostat/web/user-guides/data-browser/api-data-access) for its datasets. These provide market context, not individual-company lists.

Match the indicator's product/geography to company exposure. Save series ID, units, price basis, seasonal/calendar adjustment, observation period, release date and revision vintage. Do not join classification codes without their versions: the SCB register uses SNI 2025 while the retrieved [production-index catalogue](https://www.scb.se/NV0006) still identifies a SNI 2007 series. A broad Swedish production index does not represent a global supplier's customers automatically.

The handoff should explain **market observation → exposed activity → operating/cash consequence → scenario question**, including contrary evidence. An industry growth forecast cannot directly become the company's revenue forecast or a precise scenario probability.

## Minimal implementation proposal and remaining checks

1. Use the saved directory and small private per-company candidate records. Keep taxonomy provider/version, source date, identity, business fit, differences and inclusion/exclusion reasons; store original evidence through the existing preservation approach. A new master database is unnecessary for the first exercise.
2. Trial one manufacturing and one software discovery brief. Measure whether candidates can be found, identified and compared from accessible reports. Record where classifications fail and whether external sources add useful candidates.
3. Only then add the smallest required frozen-brief delivery to the existing preparation layer. The analyst selects scenarios; code performs named arithmetic; the independent reviewer challenges both evidence and assumptions. Preserve historical runs.

For a historical cutoff, admit only the source version demonstrably available then. Current directories, web profiles and revised statistics help today's discovery but do not prove a historical universe. Keep later evidence as a separate update. The existing [draft role](../skill-drafts/betaforge-market-peer-research/SKILL.md) remains outside active discovery; this research does not activate it.

**Bounded conclusion:** accessible sources and preserved metadata support a small peer-discovery trial. A complete Swedish/global issuer master, authenticated SCB/bulk import, stable Yahoo automation, comparable peer financials and successful runner delivery remain unverified. The next useful proof is the two short briefs, not a larger provider platform.

# Börsdata retrieval, retention and report mapping

Research date: 2026-11-01. Status: accepted by the user as the starting implementation specification; see [ADR 0002](../adr/0002-local-evidence-storage.md). This research record describes the design, not by itself a completed implementation or validation. It applies first to Gränges and ordinary nonfinancial operating companies. Banks, insurers and investment companies need additional metric definitions and valuation methods.

## Recommendation

Acquire complete statement history and source responses deterministically. Keep immutable JSON/PDF files and use a local SQLite database for identities, dated financial observations, mappings and analysis records. Give the analyst a compact financial view plus tools over the saved evidence. Storage coverage and model context are separate decisions. The initial [evidence-storage decision](../adr/0001-persist-company-evidence.md) left the database open; [ADR 0002](../adr/0002-local-evidence-storage.md) subsequently accepted SQLite. The [implemented walkthrough](../granges-codex-walkthrough.md) records validation and remaining limits.

Retain all source fields even when their meaning is unresolved. A raw provider value becomes a usable valuation input only after its period, unit, currency and financial basis are identified. Preserve Börsdata and issuer observations separately; record which one a calculation used and why. An unresolved field should trigger a focused follow-up or a disclosed assumption, not prevent all useful analysis. This follows the [agreed scope](../retrieval-design.md#agreed-scope).

Companion evidence:

- [Exact endpoint inventory and documentation conflicts](borsdata-endpoints.md).
- [All report fields and Gränges reconciliation](granges-borsdata-mapping.md).
- [Preserved public OpenAPI schema](../../data/bf-borsdata-research/swagger.json), [source hash](../../data/bf-borsdata-research/swagger-source.json).
- [Saved statement snapshot](../../data/borsdata/granges/20261101T161712Z/manifest.json), [live metadata](../../data/borsdata/metadata/20261101T165621Z/manifest.json), [live KPI summaries](../../data/borsdata/granges-research/20261101T165729Z/manifest.json). These account responses are local ignored evidence.

## What to retrieve and how much to retain

History lengths below are bootstrap targets bounded by provider availability, not promises that every issuer has that history. Keep accumulating observations after bootstrap; do not delete a stored year merely because it disappears from the API's rolling window. Full paths, parameter contracts and sources are in the endpoint inventory.

| Dataset | Initial retrieval | Retention and refresh proposal | Why it matters |
|---|---|---|---|
| Company/instrument metadata | `/v1/instruments`, descriptions, markets/countries/sectors/branches; full relevant dictionaries | All fields; retain changed versions. Check weekly and on unknown identifiers or corporate changes. | Stable Börsdata ID, ISIN, share class, listing, reporting/price currencies and peer classification. |
| Financial statements | `/v1/instruments/{id}/reports?maxYearCount=20&maxR12QCount=40&original=1`, or batches of up to 50 through `/v1/instruments/reports` | All fields in up to 20 annual, 40 quarterly and 40 R12 rows. Recheck on new reports, update signals, splits and a weekly full reconciliation; manual refresh may force a check. Preserve revisions. | Financial foundation and cycle context. |
| Report/KPI definitions | `/v1/instruments/reports/metadata`, `/v1/instruments/kpis/metadata`, `/v1/translationmetadata` | Complete changed versions; bind each interpretation to the version used. | Units, labels, numeric/string types and stable IDs. These are not complete financial formulas. |
| Prices and splits | `/v1/instruments/{id}/stockprices?maxCount=20`; `/v1/instruments/StockSplits?from=…` | All returned daily OHLCV up to 20 years, all relevant split events. Append new market dates; refresh affected historical series after splits and reconcile periodically. | Current market comparison, liquidity and historical price context. |
| Latest closing prices | `/v1/instruments/stockprices/last` or a bounded date-range history request | One latest observation per trading date/version in the price table; preserve changed versions and acquisition records. Daily at most. | A dated current price; report-period average/high/low is not the current quote. |
| Financial KPI summaries | `/v1/instruments/{id}/kpis/{reporttype}/summary` for year/R12/quarter, requesting the relevant history limit and measuring actual coverage | Keep every returned KPI and period. Refresh with financial history. Treat summary price basis as unspecified until verified. | Low-call-cost access to margins, returns, EBITDA and provider-derived cross-checks. |
| Explicit valuation histories | `/v1/instruments/{id}/kpis/{kpiId}/{reporttype}/{pricetype}/history` | Up to 20 year/40 R12 observations, using supported mean/low/high variants for the selected ratios below. Preserve each combination separately. | Comparable historical valuation ranges with explicit numerator/denominator basis. |
| Current valuation/quality KPIs | Documented screener route `/v1/instruments/{id}/kpis/{kpiId}/{calcGroup}/{calc}` | Complete returned values for selected metrics, once per refresh; retain changes. Resolve valid calculation pairs from the catalogue rather than inventing them. | Market cap, EV, leverage and quality context where verified. |
| Insider transactions | `/v1/holdings/insider?instList=…` | All returned history, documented as ten years, including corrections and trade/verification dates. Refresh at most daily. | Management activity context. |
| Short selling | `/v1/holdings/shorts` | One observed company snapshot per refresh, with changed versions retained. Our history begins when collection starts. | The endpoint is a current company summary, not a complete historical position ledger. |
| Buybacks | `/v1/holdings/buyback?instList=…` | Every returned row and correction. Record actual earliest/latest dates; no unsupported history-length promise. Refresh at most daily. | Capital allocation and share-count context. |
| Report/dividend calendars | `/v1/instruments/report/calendar?instList=…` and `/v1/instruments/dividend/calendar?instList=…` | All returned past/future records and changes. Preserve proposed, changed and cancelled events distinctly where the source provides them. | Freshness and dividend timing; a calendar entry is not evidence of payment. |
| Company reports | Existing issuer/MFN acquisition | Five latest available annuals plus five years of interims in the archive; mandatory reading of five annuals and every interim since latest annual year-end. Keep original and revised versions; acquire older reports when needed. | Definitions, adjustments, business evidence and figures missing from the API. |

The API limits above come from [OpenAPI](https://apidoc.borsdata.se/swagger/v1/swagger.json), [Reports](https://github.com/Borsdata-Sweden/API/wiki/Reports), [Stockprice](https://github.com/Borsdata-Sweden/API/wiki/Stockprice), [KPI History](https://github.com/Borsdata-Sweden/API/wiki/KPI-History) and [Holdings](https://github.com/Borsdata-Sweden/API/wiki/Holdings). Refresh and retention policies are our proposal. The five-year report archive is agreed scope; the existing walkthrough has only its eight required PDFs, not the complete five-year interim archive.

### Which financials the analyst should see

Preserve every statement field; initially display the following financial groups. These groups describe intended analysis inputs, not an assertion that Börsdata provides every required detail.

| Group | First financial view | Supplement or qualification |
|---|---|---|
| Earnings and growth | Net sales, total revenue separately, provider gross-income measure, reported EBIT, profit before tax, profit attributable to shareholders, EPS | Gränges' provider gross income matches net sales less materials, not a report-labelled gross-profit subtotal. Add company-adjusted EBIT/EBITDA and bridges from reports. Never replace reported values silently. Volume, price/mix, segments and acquisitions usually require reports. |
| Cash generation and investment | Statutory CFO, investing cash flow, financing cash flow, period net cash flow, provider FCF | Obtain capex, acquisitions/disposals, working-capital changes, taxes, interest and D&A separately where material. Total investing cash flow is not automatically capex; provider FCF is not automatically cash flow to the firm. |
| Financial position | Cash, net debt, equity, assets, current/noncurrent liabilities, tangible/intangible assets | Obtain gross borrowings, leases, pensions, debt maturities, covenants, goodwill and minority interests from reports where needed. Current assets minus current liabilities is not automatically operating working capital. |
| Per-share and capital allocation | EPS, dividends, provider share count, verified latest outstanding shares | Keep basic/diluted weighted-average shares, issued shares and treasury shares distinct. EPS denominators and a current equity-value denominator serve different purposes. |
| Market and valuation | Latest dated close, market cap/EV where verified, historical multiple ranges | Price currency must match valuation currency; a share-class quote cannot be multiplied by an unexplained group share count. |
| Operating quality | Margins, ROE/ROIC/ROC where definitions are verified, net debt/EBITDA, payout, cash conversion | Preserve provider calculations as such. Negative denominators, sector relevance and average versus closing balance definitions matter. |

Recommended explicit historical ratio IDs: dividend yield **1**, P/E **2**, P/S **3**, P/B **4**, EV/EBIT **10**, EV/EBITDA **11**, EV/S **15**, and P/FCF **76**. For price-sensitive multiples, retain annual and R12 mean/low/high where the documented combination exists; do not attempt every possible KPI permutation. Year means and ranges are context, not market prices at publication time. [KPI History table](https://github.com/Borsdata-Sweden/API/wiki/KPI-History#kpi-table).

For operating analysis, preserve all returned summary groups and make a named selection visible: gross/operating/profit/EBITDA margins **28/29/30/32**, ROE **33**, ROIC **37** where available, net debt/EBITDA **42** where available, EBITDA **54**, CFO **62**, FCF **63**, capex **64**, market cap **50** and EV **49** where the documented route supports them. These IDs are confirmed in [live KPI metadata](../../data/borsdata/metadata/20261101T165621Z/kpis.json); metadata membership does not prove history availability or calculation equivalence. Some require explicit history or screener requests because the summary does not include them.

Current scope preserves all agreed data families. Technical indicators, rankings and other screener permutations remain available for question-driven retrieval; they are not required to establish the first valuation foundation. Any new fetched payload is retained in full.

### What the live probes establish

- Statement acquisition returned **14 annual rows (2012–2025), 40 quarter rows and 40 R12 rows (through Q3 2026)**. The saved JSON bodies total **103,010 bytes**, excluding their manifest. HTTP success demonstrates access, not financial reconciliation. [Statement manifest](../../data/borsdata/granges/20261101T161712Z/manifest.json).
- Three metadata endpoints returned HTTP 200. Report metadata gives EPS/dividend format `CURR`, shares `MILL`, and statement amounts `MCURR`. Preserve the provider names and use reconciled units rather than following the wiki's inconsistent “Million” labels. [Report metadata](../../data/borsdata/metadata/20261101T165621Z/reports.json).
- `year/summary?maxCount=20` returned **42 KPI groups, 15 rows each**. The first row is **2026 period 3** and its EPS matches the latest R12 series: this is not 15 completed annual reports. `r12/summary?maxCount=40` returned **27 groups, 40 rows each** and omits valuation ratios such as P/E and EV/EBIT. Therefore the summary cannot replace explicit valuation histories. Quarter summary and other account endpoints were not probed in this research. [Summary snapshots](../../data/borsdata/granges-research/20261101T165729Z/manifest.json).

## Storage proposal

### Files plus SQLite

Keep original PDFs and JSON response bodies as immutable files addressed by content hash, with their original bytes preserved. Store extracted report pages separately with source hash, extractor version and physical PDF page number. SQLite holds searchable observations and source links. It is suitable as a starting design for one local user and a bounded watchlist; this is an engineering judgment, not a measured load-test result. No vector database is needed for numeric storage.

Use a small set of logical records; exact SQL migrations are a later implementation task:

| Record | Minimum information |
|---|---|
| Issuer and instrument | Internal issuer ID; Börsdata instrument ID, ticker, ISIN, class/type, currencies, exchange and dated issuer relationship. Several instruments may belong to one issuer. |
| Acquisition | Provider, endpoint, nonsecret parameters, request/response time, status, per-instrument errors, body hash/path, metadata/schema version. Never persist `authKey` or the full authenticated URL. |
| Source observation | Instrument/issuer scope, source field or KPI ID, exact decimal value or original string/null, units/scale, effective currency, original/converted mode, period dates or as-of date, report/price basis, source pointer and observation time. |
| Market observation/event | Instrument, quote/trade/ex/event date, provider event ID if supplied, payload, status, verification/publication date if supplied, source revision. Preserve full OHLCV and event fields. |
| Metric definition and mapping | Provider key and metadata version; canonical meaning; unit, scale, currency rule, stock/flow/per-share/ratio kind, adjustment basis, applicability scope and evidence. Mappings have versions and explicit unresolved states. |
| Report evidence | Document hash/version, issuer, publication date, financial period, original URL, page/section/table/row/column, extracted text/image reference and figure. |
| Analysis and calculation | Run ID, frozen source/observation/mapping IDs, input values, formulas, assumptions, outputs, chosen substitutions and unresolved issues. Website views read this saved result. |

Keep original numeric tokens as decimal text or an equivalent exact representation; use Python Decimal for financial calculations. Provider floating-point noise in KPI JSON should not create false precision: preserve raw values, define display rounding separately and use explicit tolerances for comparisons. Never convert null or an absent field to zero. Retain both original source units and a clearly specified normalized value.

For an observation, period start/end, provider report/publication date and our first-observed/retrieved time are different facts. Do not manufacture publication times from fiscal dates. If the API only provides year/period, retain that and attach an explicit, evidenced period mapping before using it as a dated financial input.

### Identity, revisions and retention

The conceptual identity of a report observation is provider + instrument + statement family + actual period/as-of date + source field + currency mode. KPI identity also includes KPI ID, report type, price type or screener calculation pair. Unknown dimensions remain unknown; they must not collapse into a default. A revision adds source hash and observed time to that identity. Preserve endpoint provenance even when two endpoints return the same logical observation.

For each refresh:

1. Save the acquisition result, validate response shape/instrument/period/currency, and check per-instrument errors.
2. Deduplicate identical source bytes by hash. If provider serialization changes but financial content does not, retain acquisition evidence without duplicating normalized values.
3. Append new or changed observations; link their predecessor. Retain unchanged observations and record that they were checked.
4. Expose a convenient latest view, while prior analyses continue referencing their original revisions.

Retain all unique acquired source versions and mapped financial revisions for the life of the project by default. Deduplicate unchanged payloads; do not create a new full copy every day. Never prune inputs referenced by a saved analysis. Old price/corporate-action corrections must create versions too. Backups cover both database and source files; an atomic manifest ties them together. A refresh interrupted before validation cannot replace the current usable snapshot.

This preserves **what our system observed from now on**. It cannot reconstruct what Börsdata knew five years ago when today's API supplies revised history. Historical valuation context remains distinct from point-in-time backtesting, as defined in the [glossary](../../GLOSSARY.md).

### Expected size and request volume

The measured Gränges statement response is about 0.10 MB; scaling the same shape to 100 instruments is roughly 10 MB per full changed set before database/index overhead. This is an illustrative estimate, not a forecast of all companies or all datasets. Twenty years × about 252 trading days × 100 instruments is about 504,000 daily price rows. PDF storage is likely to dominate initial bytes: the existing eight-report sample is roughly 56 MB. [Measured corpus](../granges-walkthrough-results.md#acquisition-and-pdf-findings), [statement manifest](../../data/borsdata/granges/20261101T161712Z/manifest.json).

At 100 instruments, a 50-instrument batch route needs two calls. Eight selected ratios × two report bases × three price bases × two batches would be at most 96 history calls if all those combinations are supported; unsupported/redundant variants are omitted. Summary routes are per instrument. Bootstrap this once, then use new dates and change signals, with periodic full reconciliation. Rate-limit centrally, honor `Retry-After`, and use bounded transport retries. The provider documents 100 calls per ten seconds and asks clients to stay below 10,000 daily calls. This scale does not justify an aggressive scraper or repeated model-triggered refetches. [API rate limits](https://github.com/Borsdata-Sweden/API#rate-limits).

## Mapping provider fields to report figures

The [field-by-field mapping](granges-borsdata-mapping.md) is part of the specification. Do not implement a global rename such as `operating_Income → adjusted EBIT` or `free_Cash_Flow → FCFF`.

Every mapping needs:

- Provider field/KPI ID, canonical concept and the original source label.
- Unit and scale, currency basis, sign convention, and financial kind: period flow, closing balance, per-share value, ratio or event.
- Consolidation scope, reported/adjusted basis, share denominator where relevant, and applicable issuer/period range.
- Evidence: document version, physical PDF page and table/row/column, metadata version, comparison values and reconciliation result.
- Definition status: `documented` or `unresolved`, independent of numeric agreement. Reconciliation status: `unreviewed`, `matched`, `derived_match`, `disagrees`, or `not_comparable`, as used in the mapping note. These statuses concern a specific scope, not every company/year; a matching number alone does not establish a definition.

Keep a generic provider dictionary and issuer/period-specific reconciliation evidence. A numeric match in one quarter does not establish a universal rule. Preserve source-specific values and select valuation inputs explicitly, recording the reason for freshness overrides or report-derived substitutions.

### Gränges findings that affect implementation

1. **Correction to the earlier chat:** Q3 2026 reported EBIT is **546 MSEK**, adjusted EBIT **596 MSEK**. Börsdata `operating_Income=546` matches reported EBIT. The prior explanation reversed these; the frozen Q7 reference rubric already has the correct order. [Q7 reference](../../data/granges-walkthrough/reference-rubric.md#q7--adjusted-versus-reported-earnings), [mapping evidence](granges-borsdata-mapping.md).
2. **Cash-flow definitions differ.** Preserve statutory CFO, company-defined operating cash flow and provider FCF separately. Where provider FCF equals CFO plus total investing cash flow, that arithmetic still does not make it FCFF or maintenance-capex cash flow. [Mapping, cash-flow fields](granges-borsdata-mapping.md).
3. **EPS/share count require follow-up.** Q3 API EPS is 3.64 while the report shows 3.63. Provider shares are 106.3241 million; the current report's weighted-basic shares differ. Do not silently choose one denominator for market cap or intrinsic value per share. [Mapping, share reconciliation](granges-borsdata-mapping.md).
4. **Price summaries require follow-up.** Annual 2025 API high/low differ from the annual report's disclosed range. The values may have differing period/adjustment bases; their cause is not established. Obtain daily prices and split metadata before using these summaries for historical valuation. [Mapping, price fields](granges-borsdata-mapping.md).

Aggregate only appropriate quantities. Sum non-overlapping comparable period flows; use ending balances for stocks; recompute ratios from compatible inputs. Do not sum four R12 rows, four balance sheets, or quarter share counts. Do not convert a cumulative interim cash-flow column into a standalone quarter without a documented subtraction and consistent reporting scope.

## Implementation sequence and acceptance checks

1. Save metadata and implement source-preserving normalization for the existing statement snapshot. Validate instrument 426, fiscal dates, units, original-currency mode, null handling and unknown fields. Add meaningful fixtures for broken fiscal years, mixed annual/latest-R12 rows, batch errors and revisions.
2. Acquire prices/splits, explicit historical valuation ratios and relevant event context. Verify real envelopes and per-company coverage. Record missing datasets without blocking unrelated financial analysis.
3. Reconcile the material Gränges inputs against the PDFs. Use reported/adjusted bridges, cash-flow identities, balance-sheet totals, share-count basis and currency checks; allow explained rounding residuals instead of altering source numbers.
4. Freeze a versioned company evidence packet. Initial agent context: all available annual core financial history, the latest eight quarters, latest R12, latest dated price, historical valuation summary, document index and mapping issues. Tools can read every stored field and period; this is a context policy proposal, not a storage limit.
5. Wire report reads, page images, financial queries and explicit calculations into Codex. Require each material result to cite source observation IDs and report locations. Test one end-to-end analysis plus bounded cancellation/progress preservation, then run the authorized Gränges walkthrough with the retrieved numbers and reports.

This research does not rerun or alter the prior pi comparison. Nor does it establish that all endpoints, issuer types, provider corrections, price bases or report mappings are validated. Those limits are localized to the affected inputs; the next walkthrough can proceed with verified figures and explicit substitutions.

## Independent read-only review

Reviewed on 2026-11-01 against the saved schema, metadata, manifests and source references. The reviewer made no edits, new API/model runs, tests, waivers or merges. Overall recommendation: use the bounded design as the implementation starting point; no remaining material defect was found after clarifying the gross-income label and separating definition/reconciliation statuses.

| Finding | Verdict and reasoning | Missing evidence |
|---|---|---|
| Endpoints and retention | Supported by the saved schema and metadata; complete retained responses and changed versions suit repeated research. [Endpoint inventory](borsdata-endpoints.md#exact-endpoint-inventory). | Live prices, explicit ratio histories, holdings and event envelopes. |
| Storage and dates | Sound proposal: preserves source revisions and separates period, publication and observed dates. [Storage proposal](#storage-proposal). | Implemented schema, recovery/restore checks and measured load. |
| Mapping | Appropriately bounded to sample periods; preserves cash-flow, share-basis and stock/flow distinctions. [Mapping findings](granges-borsdata-mapping.md#findings-that-affect-valuation). | EPS/shares, price differences, earlier adjusted periods and original-page checks for each material valuation input. |
| Consistency | Resolved: provider gross income is not labelled report gross profit; definition and reconciliation are separate statuses. [Financial view](#which-financials-the-analyst-should-see), [mapping record](#mapping-provider-fields-to-report-figures). | No further evidence needed for these wording corrections. |

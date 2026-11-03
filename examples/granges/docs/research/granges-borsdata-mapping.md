# Gränges: Börsdata fields and report reconciliation

Research date: 2026-11-01. This is a mapping proposal and a bounded check of two reporting periods, not a universal Börsdata accounting dictionary. Preserve the original API fields even when a report-derived value is selected for analysis.

## Evidence and status vocabulary

- **A**: [2025 annual report](../../../../data/granges-walkthrough/sources/granges-annual-2025.pdf), especially consolidated statements pp132–135, EPS Note 18 p149, APM reconciliation p160, share information pp179–180 and definitions p181. Page numbers below are physical PDF pages, matching the printed labels for these pages.
- **Q**: [Q3 2026 interim report](../../../../data/granges-walkthrough/sources/granges-q3-2026.pdf), especially consolidated statements pp14–16, share-capital Note 6 p20, quarterly table p21, APM reconciliation pp27–28 and definitions p30.
- **BY/BQ/BR**: [annual](../../../../data/borsdata/granges/20261101T161712Z/year.json), [quarterly](../../../../data/borsdata/granges/20261101T161712Z/quarter.json) and [rolling twelve-month](../../../../data/borsdata/granges/20261101T161712Z/r12.json) responses. Values below use the first row: FY2025, Q3 2026 and R12 ending September 2026 respectively. Their instrument ID is 426; [snapshot manifest](../../../../data/borsdata/granges/20261101T161712Z/manifest.json) records retrieval parameters and hashes. These are local ignored artifacts.
- **W**: [official Reports documentation](https://github.com/Borsdata-Sweden/API/wiki/Reports), sections Report Periods, Report Currency, Report Data Model. It establishes the provider labels and period/currency conventions, but does not fully specify accounting adjustments.
- **M**: [live report metadata](../../../../data/borsdata/metadata/20261101T165621Z/reports.json), retrieved separately by the parent researcher during this investigation. It labels amounts `MCURR`, shares `MILL`, and EPS/dividends/prices `CURR`; these align with the report-based units below. Preserve the provider's literal `reportPropery` key and normalize the metadata alias `net_sales` to the response field `net_Sales` explicitly, rather than silently dropping it.
- **Matched** means the sample API value agrees with the cited report line, not that all periods or companies are validated. **Derived match** means an explicit sum agrees, without proving the provider's general formula. **Unresolved** means evidence is insufficient or the values differ.

Relevant original page images were inspected for Q pp14 and 21 and A pp149 and 179. Other mappings use saved page-addressable extraction; affected values should be visually checked before becoming valuation inputs. The extraction is known to split some digits, so the retained original PDF remains the source of record. [Extraction QA](../../data/qa/extraction-qa.json).

## Findings that affect valuation

1. **Correction to the prior chat: Q3 2026 operating profit is 546; adjusted operating profit is 596.** Börsdata `operating_Income=546` matches reported profit. Q pp14, 21 and 27 establish the labels; Note 5 p20 identifies 49 of fire-related comparability costs. `546 + 49 = 595`, leaving a 1 residual against the published adjusted total 596. Preserve each published figure and residual; do not silently repair either. FY2025 reported and adjusted profit are both 1,614, so that year's equality alone cannot distinguish the bases. [BQ; BY; Q pp14,20,21,27; A pp132,160.]
2. **EPS and shares need reconciliation.** BY EPS 9.55 matches basic annual EPS; diluted is 9.54. BQ EPS 3.64 differs from both reported Q3 basic and diluted EPS 3.63. BQ shares 106.3241 million do not match Q3 weighted basic 106.5625 million, weighted diluted 106.7503 million, or closing issued shares 106.594428 million. The same API share value happens to match the Q3 2025 weighted basic count shown in Q p21; that coincidence is not proof of stale data or the provider's share policy. BY shares 106.3241 million also differ from A's weighted basic 106.330276 million and closing issued 106.462154 million. Do not use a single `shares` field for all purposes. [BY; BQ; A pp149,179; Q pp14,20,21.]
3. **Cash flow labels are not interchangeable.** BY CFO 1,342 and BQ CFO 473 match statutory cash flow from operating activities. Gränges' APM named operating cash flow is instead 841 and 396. Provider free cash flow 570 and 290 equals CFO plus total investing cash flow in these two samples: `1342 - 772 = 570`, `473 - 183 = 290`. These observations do not establish a general provider formula, and none of these fields should automatically become forecast FCFF. Acquisition spending, tax, interest classification and maintenance/growth capex require separate treatment. [BY; BQ; A pp135,160; Q pp16,28.]
4. **Net debt matches an issuer-specific APM excluding leases in the FY2025/Q3 2026 samples.** BY 4,067 and BQ 4,987 match Gränges' financial net debt, whose reconciliation removes lease liabilities. The annual components shown at A p160 give `4894 - 551 - 275 = 4068`, versus displayed total 4,067; Q p27 gives `6082 - 847 - 247 = 4988`, versus displayed total 4,987. Keep the published totals and residuals. Retain lease liabilities separately for an explicit enterprise-to-equity bridge. Do not infer the sign from the prose definition alone: the displayed reconciliation uses debt less cash. Later walkthrough evidence shows the provider's 2021–2024 values instead reconcile to financial debt plus leases and pensions, within a 1 MSEK residual; see [the period-specific follow-up](granges-mapping-resolution.md#findings-added-by-the-completed-walkthrough). [BY; BQ; A pp160,181; Q pp27,30.]
5. **Market summaries have an unresolved discrepancy.** BY high/low are 166.1/102.0. A p179 states 145.70/105.30 for 2025; both lines were visually checked. Price conventions, observation dates, adjustments, or a source error must be investigated using daily price data before selecting a series. Neither set is automatically preferred by this check. [BY; A p179.]

## Complete saved report-field map

The rows cover all 37 fields observed in each sampled report object. Amounts below are **SEK million**, unless the Unit column says otherwise. “Flow” means a value over the explicit start/end dates; “stock” means a closing balance at the end date. R12 flows may be additive; stocks must not be summed. Provider units remain separate from normalized calculation units.

### Income, shares and dividends

| API field | Proposed meaning and report counterpart | Unit / temporal kind | FY2025 / Q3 2026 | Status and evidence |
|---|---|---|---|---|
| `revenues` | Provider total revenues; here equals report Net sales | million / flow | 28,362 / 9,485 | Matched, A p132 and Q p14. Do not treat as pure sales revenues: A separately reports 28,333 sales revenues plus 29 other operating revenues. |
| `net_Sales` | Report Net sales | million / flow | 28,362 / 9,485 | Matched, A p132 and Q p14. Here equals `revenues`; general equivalence unverified. |
| `gross_Income` | Provider gross income; candidate here is Net sales less Cost of materials | million / flow | 8,354 / 2,438 | Derived match: 28,362−20,008 and 9,485−7,047. Report does not label these subtotals gross profit. Payroll and other operating costs remain below them. A p132; Q p14. |
| `operating_Income` | Reported operating profit, distinct from adjusted operating profit | million / flow | 1,614 / 546 | Matched, A p132; Q pp14,21. Adjusted values 1,614 / 596 require separate facts. |
| `profit_Before_Tax` | Profit before taxes | million / flow | 1,317 / 476 | Matched, A p132; Q p14. Includes associates and net finance items. |
| `profit_To_Equity_Holders` | Profit attributable to owners of parent | million / flow | 1,015 / 387 | Matched, A p132; Q p14. Group profit including non-controlling interests is instead 1,058 / 388. |
| `earnings_Per_Share` | Provider EPS; retain basis as unresolved until period-specific reconciliation | SEK/share / period ratio | 9.55 / 3.64 | Annual matches basic 9.55, not diluted 9.54 (A p149). Q differs from reported basic/diluted 3.63 (Q pp14,21). |
| `number_Of_Shares` | Provider share count; cannot yet label closing, basic weighted or diluted weighted | million shares / basis unresolved | 106.3241 / 106.3241 | Unresolved; neither period matches relevant current report share counts. A pp149,179; Q pp20,21. |
| `dividend` | Provider dividend per share associated with report row; payout timing/status separate | SEK/share / fiscal distribution, not quarterly flow | 3.40 / 3.40 | FY2025 matches proposed dividend for that fiscal year, A pp179–180,183. Repeated Q3 value does not mean 3.40 paid in that quarter; Q p16 shows no Q3 dividend cash flow. Do not sum quarter rows. |

### Balance sheet

| API field | Proposed meaning and report counterpart | Unit / temporal kind | FY2025 / Q3 2026 | Status and evidence |
|---|---|---|---|---|
| `intangible_Assets` | Intangible assets | million / stock | 1,330 / 1,350 | Matched, A p133; Q p15. |
| `tangible_Assets` | Property, plant and equipment plus right-of-use assets | million / stock | 8,686 / 8,990 | Derived match: 8,423+263 and 8,749+241. Includes leased assets in these samples. A p133; Q p15. |
| `financial_Assets` | Provider residual non-current financial/other category | million / stock | 475 / 612 | Derived match: deferred tax assets + associates/joint ventures + other non-current receivables = 64+187+224 and 109+202+301. Do not label this all “investments” or add it entirely to equity value. A p133; Q p15. |
| `non_Current_Assets` | Total non-current assets | million / stock | 10,493 / 10,952 | Matched, A p133; Q p15. |
| `cash_And_Equivalents` | Cash and cash equivalents | million / stock | 547 / 847 | Matched, A pp133,149; Q p15. Restricted/unavailable cash still requires notes. |
| `current_Assets` | Total current assets | million / stock | 10,142 / 13,647 | Matched, A p133; Q p15. Includes cash; not operating working capital. |
| `total_Assets` | Total consolidated assets | million / stock | 20,634 / 24,599 | Matched, A p133; Q p15. |
| `total_Equity` | Consolidated equity including non-controlling interests | million / stock | 10,255 / 11,863 | Matched, A p133; Q p15. Parent-owner equity is 9,710 / 11,212; cannot substitute total equity for it in a per-share book-value calculation without disclosure. |
| `non_Current_Liabilities` | Total non-current liabilities | million / stock | 2,774 / 3,391 | Matched, A p133; Q p15. Includes non-debt items. |
| `current_Liabilities` | Total current liabilities | million / stock | 7,605 / 9,345 | Matched, A p133; Q p15. Includes operating and financing liabilities. |
| `total_Liabilities_And_Equity` | Total liabilities plus equity | million / stock | 20,634 / 24,599 | Matched, A p133; Q p15. Balance-sheet total, not debt. |
| `net_Debt` | Gränges financial net debt, excluding lease liabilities in samples | million / stock | 4,067 / 4,987 | Matched published APM total; component residual 1 in each sample. A p160; Q p27. General company mapping unverified. |

### Cash flows and market summaries

| API field | Proposed meaning and report counterpart | Unit / temporal kind | FY2025 / Q3 2026 | Status and evidence |
|---|---|---|---|---|
| `cash_Flow_From_Operating_Activities` | Statutory cash flow from operating activities | million / flow | 1,342 / 473 | Matched, A p135; Q p16. Not Gränges' similarly named operating cash flow APM. |
| `cash_Flow_From_Investing_Activities` | Total investing cash flow | million / flow | −772 / −183 | Matched, A p135; Q p16. Cannot universally substitute for capex: A p135 separately reports investments−773 and acquisitions in comparator year. |
| `cash_Flow_From_Financing_Activities` | Total financing cash flow | million / flow | −750 / −371 | Matched, A p135; Q p16. Interest paid/received are financing in these reports. |
| `cash_Flow_For_The_Year` | Cash flow for the row's period, before FX translation effects | million / flow | −181 / −82 | Matched, A p135; Q p16. Field name does not imply annual duration in quarter/R12 response. Not simply closing minus opening cash. |
| `free_Cash_Flow` | Provider FCF; in these samples CFO+total CFI | million / flow | 570 / 290 | Derived match. Different from issuer operating cash flow 841/396 and not automatically FCFF. A pp135,160; Q pp16,28. |
| `stock_Price_Average` | Provider period price summary, definition to verify | quote currency/share / market summary | 153.2 / 174.1 | Unresolved; no equivalent report average price identified. Never substitute for latest closing price. |
| `stock_Price_High` | Provider period high, price-adjustment convention to verify | quote currency/share / market summary | 166.1 / 189.5 | FY discrepancy with report 145.70, A p179. Q high not verified. |
| `stock_Price_Low` | Provider period low, price-adjustment convention to verify | quote currency/share / market summary | 102.0 / 160.8 | FY discrepancy with report 105.30, A p179. Q low not verified. |

### Identity, period and currency metadata

| API field | Proposed treatment | Sample and evidence |
|---|---|---|
| `year` | Provider fiscal-year label; retain independently from calendar dates | 2025 /2026. BY/BQ; W Report Periods/Broken fiscal year. |
| `period` | Provider period code, never sufficient without endpoint family and start/end dates | 5=annual,3=fiscal Q3 here. BR also uses 3 for an R12 row, so `(year,period)` alone is not a unique statement key. BY/BQ/BR; W Report Periods. |
| `report_Start_Date` | Economic period start, retain raw timestamp and parsed date | 2025-01-01 /2026-07-01. BR begins 2025-10-01. BY/BQ/BR. |
| `report_End_Date` | Economic period end; closing date for stock facts | 2025-12-31 /2026-09-30. BY/BQ/BR; A/Q statement headers. |
| `broken_Fiscal_Year` | Provider fiscal-calendar flag; use explicit dates even when false | false in both samples. BY/BQ; W Broken fiscal year. |
| `currency` | Original report currency; not sufficient to infer numeric currency without request parameters | SEK in samples. W explicitly says this field remains original currency even when values are converted. Preserve `original=1` from snapshot metadata. |
| `currency_Ratio` | Provider conversion factor; preserve without assuming valuation-date FX | 1.0 in samples. W Report Currency. Conversion direction and date should be verified before cross-currency valuation. |
| `report_Date` | Provider report date, separate from PDF publication and retrieval timestamps | BY 2026-01-29 versus annual PDF publication 2026-03-17 in [source manifest](../../data/source-manifest.json). BQ 2026-10-22 matches Q report. Do not relabel BY date annual-PDF publication. |

The wiki has visibly ambiguous table entries: EPS/dividend receive a “Million” conversion label, and the Swedish translations of average/high/low prices do not align with the English names. Live metadata M resolves these display-format issues: EPS/dividends/prices use `CURR`, while average/high/low Swedish labels align correctly. Use the metadata version plus report evidence above instead of treating the wiki table as an executable parser specification. Metadata does not settle the accounting/share basis or the price discrepancies. [W, Report Data Model; M.]

## R12 and source-difference checks

BR operating profit 1,943 matches Q's R12 reported operating profit (Q pp2,27), not adjusted 2,008. BR revenues 34,626 differ by 1 from the issuer R12 total 34,625 (Q p2); the four API quarters sum to 34,626. BR profit-to-equity 1,347 is a different scope from the issuer R12 group profit 1,365. BR shares remain 106.3241 and EPS 12.67; issuer R12 diluted EPS is 12.63 (Q p2). Preserve both views and investigate before per-share valuation. [BR; BQ first four rows; Q pp2,27.]

BR balance-sheet fields repeat the September 2026 closing balances; treating them as sums of four quarters would be wrong. Quarterly dividend 3.4 is repeated across the four latest rows; summing would also be wrong. These counterexamples require a temporal-kind field per metric instead of one generic “sum to R12” operation. [BQ/BR first rows; Q p15 and p27 closing-balance footnote.]

## Proposed mapping record and selection policy

Each mapping should retain the provider field, a precise internal metric name, fiscal period/start/end, duration/stock/ratio classification, currency and scale, consolidated/parent-company scope, reported/adjusted basis, share basis, source document/hash/page/table/row, mapping version and status. A mapping's applicability must be limited to the verified company/period or an explicitly tested wider rule. Keep provider raw values, report-derived values and selected calculation inputs as separate records linked by a reconciliation record.

Recommended statuses: `unreviewed`, `matched`, `derived_match`, `disagrees`, `not_comparable`. A discrepancy should carry both values, the explicit arithmetic residual, the proposed explanation if any, and the evidence needed to settle it. Do not use one boolean “valid” for all these cases.

For this walkthrough, reported operating profit, net sales, parent-owner profit, balance totals and statutory cash flows can be used with the sample mappings above. Store adjusted operating profit/EBITDA, depreciation, taxes paid, capex, working capital components, lease liabilities, minority interests and all three share bases from reports as separate supplemental facts. Select report EPS and share bases only for the matching calculation purpose; do not erase Börsdata's conflicting values. Preserve unresolved market summaries for follow-up rather than using them as today's price.

## Verdict and remaining evidence

**Bounded verdict:** the acquired responses provide a useful financial backbone, but they are insufficient as an unqualified valuation-input table. The strongest blockers are EPS/share-basis discrepancies, price-summary discrepancies and the temptation to collapse similarly named cash-flow/debt measures. The cited samples also demonstrate that provider categories can aggregate several report rows.

**Larger claim not established:** this is not a validation of all 94 saved rows, all companies, restatement behavior, all units, current market data or a full valuation. Check mappings across at least one earlier year with comparability adjustments, fetch and reconcile current shares/price data, verify R12 mechanics and inspect original pages for every material input used in the actual valuation. A numeric match supports a scoped mapping; it does not prove a universal accounting definition.

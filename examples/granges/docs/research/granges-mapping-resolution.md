# Gränges mapping resolution for the Codex walkthrough

As of 2026-11-01. This note resolves which figures the walkthrough should use and records the assumptions still needed. It does not assert that every unexplained provider difference has a known cause. Source values remain separate in storage.

## Evidence and selected inputs

The accompanying [82 report facts](../../data/reconciled-facts.json) identify metric, exact decimal value, scale, currency, period, accounting basis, source PDF hash, physical page, source row and selection reason. Amounts below are MSEK unless stated otherwise. The original images were checked for Q3 2026 pages 2, 14–16, 20–21, 27–28 and annual 2025 pages 135, 149, 160 and 179; original PDF hashes match the [source manifest](../../data/source-manifest.json).

| Decision | Selected value or treatment | Evidence and remaining limit |
|---|---|---|
| Q3 reported versus adjusted profit | Reported EBIT **546**; adjusted EBIT **596**; adjustment line **49** | [Q3 PDF pp 14, 20, 27](../../../../data/granges-walkthrough/sources/granges-q3-2026.pdf#page=27). Börsdata matches reported EBIT. `546+49=595`, a 1 residual against displayed 596. Retain the displayed totals. |
| R12 earnings base | Reported EBIT **1,943**; adjusted EBIT **2,008**; adjusted EBITDA **2,854** | Q3 p27. R12 adjustment line 64 also leaves a 1 residual (`1943+64=2007`). Use 2,008 as the company's displayed APM, not a repaired total. |
| EPS | Q3 basic/diluted **3.63 SEK**; R12 diluted **12.63 SEK**; FY 2025 basic 9.55 and diluted 9.54 | Q3 pp 2, 14, 21; [annual Note 18 p149](../../../../data/granges-walkthrough/sources/granges-annual-2025.pdf#page=149). Select the report EPS for its specified basis; do not automatically use API Q3 3.64 or R12 12.67 as diluted EPS. |
| Current per-share denominator | Latest disclosed issued shares **106,594,428**, one share class | Q3 Note 6 p20; confirmed by the current [issuer share-capital page](https://www.granges.com/investors/shares/share-capital-and-history/). This is issued shares, not a verified current fully diluted or treasury-adjusted denominator. |
| Historical EPS denominators | Q3 basic weighted **106,562,500**; diluted weighted **106,750,300** | Q3 p21 reports these in thousands; stored facts convert explicitly to individual shares. Use for matching historical EPS and dilution sensitivity, not automatically today's share count. |
| Net debt and leases | Financial net debt excluding leases **4,987**; leases **247**; total interest-bearing liabilities **6,082**; cash/interest-bearing receivables **847** | Q3 p27. `6082−847−247=4988`, 1 above displayed 4,987. Keep the reported APM and explain any bridge residual. |
| Minority interests | **651** non-controlling-interest book equity; parent-owner book equity **11,212** | Q3 p15. 651 is not a market/fair value estimate. A consolidated operating valuation needs an explicit treatment of minority ownership. |
| Cash generation | Statutory Q3 CFO **473**; company APM operating cash flow **396** | Q3 pp 16, 28. They have different definitions; neither is automatically FCFF. |
| R12 investment/cash pressure | Cash capex **639**; working-capital cash movement **−2,193**; company operating cash flow **−35** | Q3 p 28. Store capex as positive outflow magnitude, preserving the source line −639. Do not turn negative cash flow into a normalized positive forecast without a stated assumption. |

## EPS and share differences: resolved selection, bounded explanation

The API repeatedly reports 106.3241 million shares. That is not the latest disclosed issued count and differs from both current weighted denominators. Using the rounded reported parent-owner Q3 profit 387, `387/106.3241=3.6398`, which rounds to API EPS 3.64; `387/106.5625=3.6317`, which rounds to report basic EPS 3.63. This is consistent with a denominator-basis explanation, but rounded numerators and one-period arithmetic do not prove the provider's calculation policy or establish that its count is stale. [Saved quarterly response](../../../../data/borsdata/granges/20261101T161712Z/quarter.json); Q3 pp 14, 21.

For the walkthrough, select the report EPS and keep basic/diluted metrics separate. Use 106.594428 million issued shares for a current equity-value-per-share illustration only with an explicit assumption that shares and treasury holdings have not changed since the latest relevant disclosure. The difference from API 106.3241 million is about 0.254%, so it should be visible but need not stop a useful scenario analysis.

The official share-capital page, checked 2026-11-01, still gives 106,594,428 shares effective 12 August 2026. The [issuer press-release catalogue](https://www.granges.com/newsroom/press-releases/) shows the latest share-change release on 31 August 2026 and no newer share-change entry through the listed 22 October report. Absence of an entry is supporting context, not proof no change occurred. The [March 2026 AGM notice](https://www.mfn.se/a/granges/notice-of-the-annual-general-meeting-for-granges-ab-5) stated no treasury shares then; it cannot establish zero treasury shares in November. Do not store a current treasury count of zero as a fact.

## Earnings and cash-flow normalization

**Keep impairment treatment consistent.** The R12 adjusted-EBITDA bridge uses D&A/impairment 846; the cash-flow bridge uses 854. The 8 difference is consistent with the separately adjusted fire impairment in Note 5. `2008+846=2854`; adding 854 to adjusted EBIT would add the same impairment again. The provider's R12 EBITDA 2,789 equals `1943+846`; its difference from issuer adjusted EBITDA is principally the earnings adjustment basis, with the published rounding residual retained. [Q3 pp 20, 27–28](../../../../data/granges-walkthrough/sources/granges-q3-2026.pdf#page=27); [saved annual/R12 KPI summaries](../../../../data/borsdata/granges-research/20261101T165729Z/manifest.json).

**Keep working capital and capex separate.** Q3 company operating cash flow is calculated from operating profit, noncash addbacks, working capital and cash capex; statutory CFO also includes cash taxes and does not include investing capex. Net interest payments appear in financing cash flow in these reports. In the two checked periods, provider FCF equals statutory CFO plus total investing cash flow: FY 2025 `1342−772=570`; Q3 `473−183=290`. These identities do not establish a universal provider formula or an unlevered valuation cash flow. [Annual p135](../../../../data/granges-walkthrough/sources/granges-annual-2025.pdf#page=135); Q3 pp 16, 28.

**Retain rounding and reporting-duration differences.** R12 statutory CFO is 293 when summing the four quarter values `202−221−161+473` in Q3 p21, matching the API. Rolling the displayed annual and cumulative interim totals gives `1342+91−1139=294`. Keep the 1 difference, rather than overwrite either source. Report R12 sales 34,625 similarly differ by 1 from the API quarter sum 34,626. These are small residuals; neither proves a material reporting error. Q3 pp 2, 16, 21 and [API R12 response](../../../../data/borsdata/granges/20261101T161712Z/r12.json).

**Use historical cash flow as a diagnostic for an EBIT-based valuation.** A two-to-three-year EBIT scenario can proceed without pretending the weak R12 cash flow is sustainable or irrelevant. It should explain aluminium-related working capital, capex after the expansion programme and fire-related disruptions. The normalized future cash conversion, capex and working-capital assumptions remain assumptions, not replacements for saved historical facts. [Q3 p6 and pp 27–28](../../../../data/granges-walkthrough/sources/granges-q3-2026.pdf#page=6).

## Enterprise value to parent equity

Consolidated EBIT/EBITDA includes subsidiary operations attributable in part to minority owners. Therefore document the convention before multiplying earnings by a multiple:

1. State whether the chosen EV multiple includes lease debt and minority interests. Do not assume a provider ratio has the same convention as the forecast bridge.
2. Start from operating enterprise value on that convention. Subtract financial net debt 4,987 once. Cash has already been netted; do not add 847 cash again.
3. If the enterprise-value convention includes leases, also subtract 247 lease liabilities. If it excludes them, show the lease treatment and use a consistent earnings/peer-multiple basis. Do not silently alternate conventions.
4. Deduct the value attributable to minority owners when valuing consolidated operations. 651 is a disclosed book-value proxy available for a scenario, not an observed fair value. Label any use as an assumption and show sensitivity if material.
5. Add separately valued non-operating assets only if they were excluded from operating enterprise value. The report's 202 associate/JV investment balance is book value; API financial_Assets 612 additionally includes deferred tax and other receivables, so it cannot all be added as surplus investments.
6. Divide parent equity by the explicit selected share count, with a separate dilution sensitivity. Do not replace it with a period-weighted EPS denominator without explanation.

The debt, lease and minority facts are source-backed. The treatment of leases, minority fair value, non-operating assets, future debt and future dilution belongs to the valuation assumptions. This permits a complete, auditable scenario range while avoiding false certainty about the EV definition. [Q3 pp 15, 27](../../../../data/granges-walkthrough/sources/granges-q3-2026.pdf#page=15).

## Dated prices and provider EV conventions

The daily series resolves the annual report's price range. Across the 249 trading rows in 2025, the highest closing price is **145.70 SEK** and the lowest is **105.30 SEK**, exactly matching annual p179. The intraday range is 149.20–102.00 SEK. Thus the provider's annual low of 102.0 matches the intraday low, not the report's closing-price low. The annual API `report_Date` is 2026-01-29: that day's close is **153.2** and high is **166.1**, exactly matching annual API `stock_Price_Average` and `stock_Price_High`. The arithmetic mean of the 2025 daily closes is approximately **129.6598**, not 153.2. [Annual p179](../../../../data/granges-walkthrough/sources/granges-annual-2025.pdf#page=179); [annual API response](../../../../data/borsdata/granges/20261101T161712Z/year.json); [daily price series](../../../../data/borsdata/context/426/20261101T173056Z/prices.json), rows keyed by `d`.

Across all **92** annual, quarterly and R12 observations with a matching daily price in these saved responses, `stock_Price_Average` equals the daily close on `report_Date`. These include overlapping dates, so they are not 92 independent dates. High and low do not follow a universally reconciled period-start-to-report-date window in this sample. Preserve the observations and describe the demonstrated correspondence; do not infer an undocumented universal endpoint rule. The fetched [split response](../../../../data/borsdata/context/426/20261101T173056Z/splits.json) contains no Gränges event, which does not prove that every corporate-action adjustment is absent. The safe request windows and hashes are in the [context manifest](../../../../data/borsdata/context/426/20261101T173056Z/manifest.json).

For this walkthrough, the latest saved daily close is **172.20 SEK on 2026-10-30**. Use this dated normalized price fact for present valuation. Q3's report-date close of 174.1 on 2026-10-22 describes another date. Historical calendar price analysis should use daily rows and explicit closing versus intraday conventions.

The provider's saved EV and market-cap KPI observations reveal a useful bounded convention:

| Saved observation | Identity in MSEK | Interpretation |
|---|---|---|
| Latest 2026 period 3 | 23,342.486328125 − 18,355.486328125 = **4,987** | EV minus market cap matches lease-excluding financial net debt exactly. Separate leases and NCI are not added in this observed identity. |
| Annual 2025 period 5 | 20,355.8515625 − 16,288.8525390625 = **4,066.9990234375** | Matches reported financial net debt 4,067 within provider numeric precision. |
| Annual 2025 market cap | 16,288.8525390625 / 153.2 ≈ **106.324103 million shares** | Consistent with API shares and the report-date close, not the calendar-year average price. |
| Latest market cap | 18,355.486328125 / 172.2 ≈ **106.593997 million shares** | Approximately the current issued count; differs from the API report-share and KPI-share observations. This is not evidence that all provider share-dependent fields use one stale count. |

Sources: [EV KPI 49](../../../../data/borsdata/context/426/20261101T173056Z/kpi-49-year-mean.json), [market cap KPI 50](../../../../data/borsdata/context/426/20261101T173056Z/kpi-50-year-mean.json), [share KPI 61](../../../../data/borsdata/context/426/20261101T173056Z/kpi-61-year-mean.json), and Q3 p27. These are observed arithmetic relationships, not a complete provider methodology.

The 2025 EV divided by reported EBIT 1,614 is approximately **12.61205**, matching the saved EV/EBIT KPI **12.61200** within precision. The latest saved EV divided by R12 reported EBIT 1,943 is **12.01363**, whereas the saved latest EV/EBIT KPI is **11.99000**; that small residual remains unresolved. Recompute the walkthrough's current ratio from the selected dated inputs and retain the provider ratio as a separate observation. The API `priceValue: mean` label does not by itself establish an arithmetic calendar-year price average, and the latest partial-year row may change with quotes. [EV/EBIT KPI 10](../../../../data/borsdata/context/426/20261101T173056Z/kpi-10-year-mean.json).

Historical provider EV/EBIT is therefore useful context with its observed lease/NCI exclusions. It cannot be treated as a fully consolidated EV multiple including both liabilities without a convention adjustment. If a scenario deducts a minority fair-value proxy or leases from equity, explain how the chosen multiple accounts for that difference. Do not silently apply an additional deduction to a provider-comparable equity bridge and call the conventions identical.

## Bounded verdict

The material accounting mappings are usable with explicit selection rules: reported versus adjusted EBIT, cash-flow definitions, lease-excluding net debt, parent versus consolidated ownership and EPS/share bases are now separated. The current share denominator can be used as a disclosed issued-share proxy, rather than treated as a verified fully diluted outstanding count. The annual closing-price range is reconciled, and the provider report-date price correspondence is demonstrated for the saved sample. Broader provider computation policies remain unverified.

Missing evidence remains localized: current treasury holdings, minority fair value, future dilution and the remaining provider ratio/window differences. The first three require explicit scenario assumptions where they affect valuation; the provider differences remain recorded without blocking a calculation from selected inputs. The selected-fact file provides evidence, not forecasts or investment conclusions. No model valuation run was performed in this reconciliation task.

## Findings added by the completed walkthrough

The subsequent [Codex walkthrough](../granges-codex-walkthrough.md) found two additional period-specific qualifications. Its frozen packet retains the original version of this note, and its additional inputs and calculations remain in the run record.

**Historical provider net debt changes basis in this sample.** For 2021–2023, the provider values equal the issuer's lease-excluding financial debt plus leases and pensions. For 2024 the same bridge produces 4,871 MSEK against provider 4,870, retaining a 1 MSEK residual. For 2025 and September 2026 the provider instead matches lease-excluding financial net debt. Do not extrapolate the verified 2025/Q3 mapping backward without these qualifiers, or interpret the raw change as pure deleveraging. This is an observed reconciliation, not a proven universal provider policy. [Final answer section 2 and its source-page references](../../../../data/granges-codex/runs/20261101-full/answer.md); saved calculations `calc:991963a2c1273cf478c9`, `calc:583b26ceee9eea1081a9`, `calc:1826c934d6e307a3667b`, `calc:ee90c372dadf7a9474ef`.

**Pensions are an additional disclosed debt-like item.** Q3 physical p27 reports pensions of 229 MSEK, added back after non-interest-bearing liabilities in capital employed. This supports their separation from financial net debt. The walkthrough deducts the full amount as a proxy, without separately valuing a current tax benefit; settlement value and Q3 tax effects remain unverified. The present-value sensitivity is approximately 1.6 SEK/share. The independent reviewer found no apparent debt double-count. [Output review, Pension addition](granges-codex-output-review.md); [final answer sections 9–10](../../../../data/granges-codex/runs/20261101-full/answer.md).

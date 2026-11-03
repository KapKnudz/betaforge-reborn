# Damodaran benchmarks: assessment for a simpler Betaforge analysis

Reviewed 3 November 2026. This is source research and a proposal, not an ingestion implementation or a new Gränges valuation. The user's Armitage-inspired principles are treated as design requirements; this review does not claim to authenticate John Armitage's personal methodology.

## Verdict

**Useful for industry context; insufficient as a current company-level peer database.** Prefer the company's own history, then a short, reasoned global peer list, then these industry aggregates. Damodaran says individual company datasets stopped being published in 2018 and recommends current filings or a current data source for company comparisons. His company lookup can help inspect industry membership, but does not establish economic comparability. [Data breakdown, Company Lookup](https://pages.stern.nyu.edu/adamodar/New_Home_Page/databreakdown.html#company), [data history, Usage Rules](https://pages.stern.nyu.edu/adamodar/New_Home_Page/datahistory.html#rules).

The economic peer choice should remain explicit: product, customer exposure, metal-price pass-through, asset intensity and reinvestment economics matter for Gränges. A broad Metals & Mining row is not automatically a peer group for an aluminium rolling business. This is a proposed selection rule, not a peer list verified by this review.

## Dates, scope and inspection limits

The live catalogue reports a full update on **9 January 2026**, with most data updated annually. Its accounting figures generally use the latest available twelve months at that update; they are not uniformly FY2025 or current November 2026 results. Absolute amounts are generally **millions of US dollars**. The listed country-risk updates are exceptions to the annual cycle and do not refresh every industry table. [Current catalogue, update notice and Risk Premiums](https://pages.stern.nyu.edu/adamodar/New_Home_Page/datacurrent.html).

The HTML pages explicitly say **US**. Global and regional workbooks are separate selections; Global covers all firms, while regional buckets have the author's own geographic definitions. [Data breakdown, Regional Breakdown](https://pages.stern.nyu.edu/adamodar/New_Home_Page/databreakdown.html#region).

This review inspected the live HTML tables and definitions. Public HEAD requests confirmed HTTP 200 for the five global XLS links recommended below, with Last-Modified headers on 8 January 2026. The workbook bodies/formulas were **not parsed**: their row-level coverage, unit representation and exact aggregation must still be checked before ingestion. Website retrieval date, dataset analysis date, financial period and file modification date must remain separate.

## Minimal dataset selection

Start with four diagnostic families. Add the fifth only for an actual multiple-comparison question. Store the selected industry rows and their definitions, with the original source/version, rather than feeding every available table to the analyst.

| Priority and family | Useful fields and purpose | Official sources | Limit before comparison |
|---|---|---|---|
| **1. Operating margins** | EBIT margin and its history/peer context; stock-based compensation as a share of sales. | [US table](https://pages.stern.nyu.edu/adamodar/New_Home_Page/datafile/margin.html), [Global workbook](https://pages.stern.nyu.edu/~adamodar/pc/datasets/marginGlobal.xls) | Columns distinguish pre-stock-compensation, unadjusted, lease-adjusted and lease/R&D-adjusted margins. Select a matching basis; do not use the pre-SBC column as ordinary profitability. |
| **2. Working capital** | Receivables/sales, inventory/sales, payables/sales and non-cash working capital/sales. Explains cash absorption. | [US table](https://pages.stern.nyu.edu/adamodar/New_Home_Page/datafile/wcdata.html), [Global workbook](https://pages.stern.nyu.edu/~adamodar/pc/datasets/wcdataGlobal.xls) | These compare balance-sheet stocks with sales flows. Match periods and balance conventions; negative working capital can be a business-model feature. |
| **3. Return on capital** | ROC and invested-capital context. Tests whether growth appears capital efficient. | [US EVA/ROC table](https://pages.stern.nyu.edu/adamodar/New_Home_Page/datafile/EVA.html), [Global workbook](https://pages.stern.nyu.edu/~adamodar/pc/datasets/EVAGlobal.xls) | Do not equate issuer ROCE with Damodaran ROIC. A downloaded industry WACC is also not the already-agreed Investor B investment hurdle. |
| **4. Reinvestment and capital intensity** | Capex/depreciation, net capex/sales and sales/invested capital. Checks whether earnings growth requires substantial capital. | [US table](https://pages.stern.nyu.edu/adamodar/New_Home_Page/datafile/capex.html), [Global workbook](https://pages.stern.nyu.edu/~adamodar/pc/datasets/capexGlobal.xls) | The table separately reports acquisitions and net R&D. Neither low recent capex nor capex close to depreciation proves sustainable maintenance requirements. |
| **5. EV/EBIT, optional** | Broad valuation context for the existing EV/EBIT model. | [US table](https://pages.stern.nyu.edu/adamodar/New_Home_Page/datafile/vebitda.html), [Global workbook](https://pages.stern.nyu.edu/~adamodar/pc/datasets/vebitdaGlobal.xls) | Includes EV/EBIT as well as EBITDA multiples. The sample split is **positive EBITDA firms versus all firms**, not positive EBIT versus all firms. Avoid mechanically setting a target multiple from a sector row. |

The capital-efficiency and capex observations above are interpretation rules proposed for Betaforge. They do not assert that any industry row proves Gränges' future returns.

## Definitions that can otherwise mislead

Damodaran's variable page defines ROC/ROIC using after-tax EBIT divided by book debt plus book equity less cash. It defines non-cash working capital more broadly than receivables plus inventory less payables. Many ratios use sector sums rather than a simple company average, so they must not be called peer medians. The page's introductory P/E wording appears inverted, while the actual P/E table explicitly labels market-capitalization/net-income columns; verify the selected table or workbook rather than copying prose blindly. [Variable definitions](https://pages.stern.nyu.edu/adamodar/New_Home_Page/datafile/variable.htm), [P/E table](https://pages.stern.nyu.edu/adamodar/New_Home_Page/datafile/pedata.html).

His methodology also capitalizes leases and R&D for some measures, changing operating income and invested capital. This can make a nominally identical metric incompatible with unadjusted issuer data. [Data breakdown, Data Variables](https://pages.stern.nyu.edu/adamodar/New_Home_Page/databreakdown.html#variables).

Recommended comparison record: metric, company/industry, region, analysis date, financial period if known, numerator/denominator, accounting adjustments, aggregation method, sample count and source. This is a small definition record, not another forecasting model.

## Items not to add automatically

- **P/E:** the US table is useful but differentiates current/trailing/forward and aggregate/positive-income samples. The guessed `pedataGlobal.xls` and `pbvdataGlobal.xls` URLs returned HTTP 404 in this review. Do not invent a global link merely by changing a filename; use verified peers and existing company data instead. [Actual P/E table](https://pages.stern.nyu.edu/adamodar/New_Home_Page/datafile/pedata.html).
- **FCF yield:** the catalogue's dividends/FCFE table contains different pre- and post-debt cash-flow measures; it is not a direct equivalent of Börsdata's FCF label. Define the company cash flow first. Equity cash flow belongs with equity value; unlevered firm cash flow belongs with enterprise value. [Dividends and FCFE table](https://pages.stern.nyu.edu/adamodar/New_Home_Page/datafile/divfcfe.html).
- **SBC as a separate benchmark download:** the margin table already includes SBC/sales. The employee table also provides it but would duplicate that first use case. Treat SBC and share dilution as economic costs in the company analysis. [Employee table and coverage note](https://pages.stern.nyu.edu/adamodar/New_Home_Page/datafile/Employee.html).
- **Country tables:** use them when an economic exposure requires them. Do not make domicile the automatic peer selector. Regional selection is an additional comparison choice, not a substitute for business-model matching. [Regional definitions](https://pages.stern.nyu.edu/adamodar/New_Home_Page/databreakdown.html#region).
- **Complex regressions, betas and option models:** no demonstrated gap in the present task requires them. Their availability is not a reason to expand the valuation.

## Global peers and optional SEC gap filling

Select a few economically comparable companies with a written inclusion/exclusion reason, then collect the same small set of current and historical metrics from their reports or an existing provider. Country differences should enter the explanation where taxes, regulation, accounting, market structure or operating exposure makes them relevant. These are proposed review criteria; no specific peer group has been approved here.

SEC EDGAR is a possible later source for peers with SEC filings. Its public JSON submissions and company-facts interfaces require no API key and include US-GAAP/IFRS standard-taxonomy facts, with limitations around custom concepts, entity scope, units and period alignment. Use it only to fill an identified peer-data gap, not as a new first-stage ingestion project. [SEC EDGAR API documentation, XBRL Data APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces).

## Overall recommendation and missing evidence

**Proceed with a small, optional industry-context layer; preserve the current valuation.** Company history and a short, explicitly matched global peer set should carry more weight than broad aggregate rows. Margins, working capital, capital efficiency and reinvestment are the useful starting context; EV/EBIT is an optional sanity check.

Before implementation, verify the global workbook headers/formulas and selected industry membership, approve company metric definitions and identify actual peer candidates. This review does not establish a Gränges fair-value change, statistical probability calibration, a complete benchmark loader or an authenticated Armitage doctrine. No application, pipeline, philosophy or frozen valuation was changed.

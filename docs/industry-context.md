# Optional industry context

`scripts/fetch_industry_context.py` downloads four official Damodaran **Global** XLS files: [margins](https://pages.stern.nyu.edu/~adamodar/pc/datasets/marginGlobal.xls), [working capital](https://pages.stern.nyu.edu/~adamodar/pc/datasets/wcdataGlobal.xls), [ROC/EVA](https://pages.stern.nyu.edu/~adamodar/pc/datasets/EVAGlobal.xls) and [capital expenditure/reinvestment](https://pages.stern.nyu.edu/~adamodar/pc/datasets/capexGlobal.xls). The optional [EV/EBIT workbook](https://pages.stern.nyu.edu/~adamodar/pc/datasets/vebitdaGlobal.xls) is fetched only with `--include-ev-ebit`. URLs are fixed in the script. There is no screening or inferred valuation multiple.

Use the project virtual environment with its pinned Requests and xlrd dependencies:

```sh
.venv/bin/python scripts/fetch_industry_context.py --industry 'Metals & Mining'
```

Repeat `--industry` to select another exact source label. Matching ignores case and repeated whitespace; a missing or duplicate match fails. The script locates the actual industry header, requires a workbook date, and retains the sheet and Excel row/column locations. It does not silently choose a similar industry.

## Stored snapshot and packet input

Each run creates a new directory under ignored `data/benchmarks/damodaran/<UTC timestamp>/`:

- `raw/*.xls`: exact downloaded source bytes, never rewritten by the script.
- `manifest.json`: source URLs, byte counts, SHA-256 hashes, response Last-Modified values and retrieval times. A failed acquisition or parse leaves `status: "incomplete"` and no usable `context.json`.
- `context.json`: only the selected industry rows plus source metadata and caveats. Its manifest path and raw paths are relative to the snapshot. It records the manifest hash and each raw workbook hash.

The optional packet-builder input is the path to `context.json`. The packet builder should copy that file, its referenced manifest and raw sources, verify their hashes and record the context file's own hash. No network fetch is needed when assembling or reading a saved packet.

`context.json` has `schema_version: 1`, `provider`, `geographic_scope`, `retrieved_at_utc`, `manifest`, `manifest_sha256`, `industry_selections`, `definitions_url`, `caveats` and `datasets`. Each dataset records `id`, `source_url`, `raw_file`, `raw_sha256`, `source_analysis_date`, its original `source_date_label`, `sheet`, one-based `header_row`, `definition_sheet`, dataset `caveats`, the original nonempty metadata cells in `preamble`, and `selected_rows`. A selected row has `industry`, one-based `excel_row` and `cells`; each cell has one-based `column`, original `name`, original cached `value`, `cell_type`, `excel_number_format` and `unit`. An array preserves repeated source headers without overwriting them.

Percent-formatted numbers retain their fraction: `0.125` with `0.00%` means a displayed 12.50%, not 0.125%. A quoted or escaped percent symbol does not establish a percentage. Count columns are labeled as counts. Capital expenditure headers explicitly state US dollar millions; EVA monetary units follow that workbook's `Variables & FAQ` sheet and the catalogue's dollar convention. Known capex/depreciation, sales/invested capital and EV/EBIT columns are labeled multiples; the original format is still retained. For example, source capex/depreciation `2.0676` has a percent display format, meaning approximately 206.76% or 2.0676 times. Unknown fields/units remain explicit rather than being silently mapped to a company financial metric.

xlrd reads cached XLS values and exposes number formats; it does **not** expose formula expressions or recalculate them. The loader never evaluates formula-like text. The original XLS preserves formulas, but cache freshness and cell-level formula status are not verified. Excel errors and missing values retain their source types; they are not replaced with zero.

## Interpretation limits

Use the company's own 5–10-year history first, then economically matched businesses, then this broad industry context. The Global Metals & Mining row is **not** a verified Gränges peer median and cannot set an exit multiple. Damodaran describes many sector ratios as ratios of aggregate numerators and denominators; those are different from company medians. His [variable definitions](https://pages.stern.nyu.edu/adamodar/New_Home_Page/datafile/variable.htm) and [data-variable adjustments](https://pages.stern.nyu.edu/adamodar/New_Home_Page/databreakdown.html#variables) also make lease/R&D, tax and invested-capital matching necessary.

The workbook analysis/update date, HTTP modification time, retrieval time and constituent financial periods are separate. The [catalogue](https://pages.stern.nyu.edu/adamodar/New_Home_Page/datacurrent.html) describes most data as annual updates, with absolute values generally in millions of US dollars. The context does not claim every firm has the same reporting period or that retrieval makes an old aggregate current. Source SBC and adjusted/unadjusted margin columns remain separate; pre-SBC margins are not a replacement for ordinary profitability.

## Inspected Global workbooks, 3 November 2026

The real snapshot `data/benchmarks/damodaran/20261103T120604422959Z/` selected the exact `Metals & Mining` row in each workbook. Each reports 1,874 firms; that does not establish the same usable sample for every metric. All raw hashes and the context's manifest reference were verified after acquisition.

| Workbook | Internal `Date updated:` | Header / selected Excel row | HTTP Last-Modified |
|---|---|---|---|
| `marginGlobal.xls` | 5 January 2026 | 9 / 61 | 8 January 2026 |
| `wcdataGlobal.xls` | 5 January 2026 | 8 / 60 | 8 January 2026 |
| `EVAGlobal.xls` | **5 January 2025** | 19 / 71 | 8 January 2026 |
| `capexGlobal.xls` | 5 January 2026 | 8 / 60 | 8 January 2026 |

**The EVA/ROC date discrepancy is unresolved.** Its internal label may be stale, or the underlying figures may be older; these files alone do not establish which. The loader preserves the label and flags the different modification year in dataset caveats. It does not silently replace 2025 with the catalogue's 2026 update year. Do not describe this ROC figure as a verified January 2026 or current peer benchmark.

All four contain a `Variables & FAQ` sheet. This source distinguishes aggregate ratios, effective-tax ROC, capitalized R&D and cash-only acquisitions. Its capital expenditure/acquisition measures do not establish maintenance capex or include all share-funded acquisitions. The preserved source rows include other original columns, including WACC/beta and EBITDA variants; retention provides source fidelity and does not adopt those columns as valuation inputs. The optional EV/EBIT file was not fetched for this first snapshot.

## Gränges candidate comparisons

[data/peers/granges.json](../data/peers/granges.json) records a short human-reviewed candidate list with official sources beside each observation. It contains no peer financial values or derived multiples.

- **Constellium SE (NYSE: CSTM):** rolled products and recycling with packaging and automotive overlap; aerospace and structural extrusions require product/segment matching. [Business units](https://www.constellium.com/our-business-units), [current issuer identification](https://www.constellium.com/news/constellium-reports-strong-third-quarter-2026-results-raises-full-year-2026-guidance).
- **UACJ Corporation (Tokyo: 5741):** rolling includes automotive heat exchanger and fin materials, with broader foil, extrusion and other businesses. Match metal-price lag, profit adjustments and ROIC basis before comparing margins/returns. [Business](https://www.uacj.co.jp/english/company/business/), [listing](https://www.uacj.co.jp/english/ir/stockinfo/stock.html), [profit/ROIC definitions](https://www.uacj.co.jp/english/sustainability/message.html).
- **Kaiser Aluminum (Nasdaq: KALU):** fabrication and rolling serve packaging, automotive, aerospace and engineering; conversion revenue excludes hedged metal cost and cannot be compared directly with reported sales. [Business](https://investors.kaiseraluminum.com/), [listing](https://investors.kaiseraluminum.com/resources/faq), [Metal Pricing Policies](https://investors.kaiseraluminum.com/sec-filings/all-sec-filings/content/0001193125-26-059575/kalu-20251231.htm).
- **Novelis:** rolling/recycling operating reference only. It is a wholly owned Hindalco subsidiary; a parent equity multiple does not provide a standalone Novelis multiple. [Business](https://novelis.com/about-us/), [ownership](https://www.hindalco.com/businesses/novelis).

The reasons for review are product/customer overlap, conversion pricing and metal pass-through, rolling/recycling capital intensity and reinvestment. These are candidate comparisons, not demonstrated equivalence. Harmonized peer financial history, cash flow, maintenance investment and market multiples remain future evidence work; no EDGAR integration or full peer acquisition was added.

## Verification

Deterministic tests cover header/date/scope selection, missing or ambiguous industries, repeated headers, percentage and money/multiple units, unknown/formula-like/error/missing values, exact source bytes and hashes, failed parse behavior, the explicit optional fifth file, date mismatches, non-200 stop behavior and snapshot overwrite prevention. They do not depend on live network responses.

```sh
.venv/bin/python -m unittest discover -s tests -p 'test_industry_context.py'
```

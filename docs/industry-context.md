# Optional industry context

`scripts/fetch_industry_context.py` downloads four official Damodaran **Global** XLS files: [margins](https://pages.stern.nyu.edu/~adamodar/pc/datasets/marginGlobal.xls), [working capital](https://pages.stern.nyu.edu/~adamodar/pc/datasets/wcdataGlobal.xls), [ROC/EVA](https://pages.stern.nyu.edu/~adamodar/pc/datasets/EVAGlobal.xls) and [capital expenditure/reinvestment](https://pages.stern.nyu.edu/~adamodar/pc/datasets/capexGlobal.xls). The optional [EV/EBIT workbook](https://pages.stern.nyu.edu/~adamodar/pc/datasets/vebitdaGlobal.xls) is fetched only with `--include-ev-ebit`. URLs are fixed in the script. There is no screening or inferred valuation multiple.

Set `INDUSTRY_LABEL` to the exact source industry label. Use the project virtual environment with its pinned Requests and xlrd dependencies:

```sh
.venv/bin/python scripts/fetch_industry_context.py --industry "$INDUSTRY_LABEL"
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

Use the company's own 5–10-year history first, then economically matched businesses, then this broad industry context. A broad industry aggregate is not a verified peer median for the selected company and cannot set an exit multiple automatically. Damodaran describes many sector ratios as ratios of aggregate numerators and denominators; those are different from company medians. His [variable definitions](https://pages.stern.nyu.edu/adamodar/New_Home_Page/datafile/variable.htm) and [data-variable adjustments](https://pages.stern.nyu.edu/adamodar/New_Home_Page/databreakdown.html#variables) also make lease/R&D, tax and invested-capital matching necessary.

The workbook analysis/update date, HTTP modification time, retrieval time and constituent financial periods are separate. The [catalogue](https://pages.stern.nyu.edu/adamodar/New_Home_Page/datacurrent.html) describes most data as annual updates, with absolute values generally in millions of US dollars. The context does not claim every firm has the same reporting period or that retrieval makes an old aggregate current. Source SBC and adjusted/unadjusted margin columns remain separate; pre-SBC margins are not a replacement for ordinary profitability.

The [worked example](../examples/granges/docs/industry-context.md) records one selected industry, source-date discrepancy and candidate peer list. Those observations do not define a universal peer set or target multiple.

## Verification

Deterministic tests cover header/date/scope selection, missing or ambiguous industries, repeated headers, percentage and money/multiple units, unknown/formula-like/error/missing values, exact source bytes and hashes, failed parse behavior, the explicit optional fifth file, date mismatches, non-200 stop behavior and snapshot overwrite prevention. They do not depend on live network responses.

```sh
.venv/bin/python -m unittest discover -s tests -p 'test_industry_context.py'
```

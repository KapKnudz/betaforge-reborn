# Review saved analyses locally

The workbench has three views: **Project** for priorities and completed work, **Architecture** for the technical map and analysis process, and **Company** for saved research. Task bars count completed tasks; they do not measure investment confidence or time remaining. The [process guide](analysis-process.md) separates code checks, analyst judgment and coordinator actions.

```sh
.venv/bin/python scripts/serve_progress.py
```

Open **http://127.0.0.1:8765**. The project plan refreshes while the page is open. Browse captured companies with an explicit corpus manifest; read their research by adding saved-view exports.

## Add a saved company run

For a new structured run, use its frozen packet and saved `analysis.json`, inputs, calculations and tool state. Supply the company name and the valuation method actually used; the exporter does not infer them from generated prose.

```sh
.venv/bin/python scripts/export_saved_analysis.py \
  --run data/COMPANY/runs/RUN --packet data/COMPANY/PACKET \
  --company 'Company name' --ticker TICKER --id company-run \
  --method 'Forward EV/EBIT scenarios' \
  --output data/saved-views/company-run.json
```

The exporter verifies the original evidence and report quotations, copied scenario outputs, complete reading and exact saved artifacts. The narrative must equal the text generated from the canonical report. An optional `analysis-review.json` must match the current report and packet hashes; draft feedback stays with its original artifacts. Follow the [bounded analysis workflow](analysis-workflow.md).

Structured review provenance hashes the validated JSON content using the tool's canonical encoding, so indentation and a trailing newline do not change its identity. The private archive preserves the original file bytes. Legacy financial-review hashes retain their original file-byte convention.

Earlier structured exports may retain an unselected historical comparator as `null`, even when context is preserved. New exports copy the matching saved SIXRX value; every displayed comparator must match that source.

For an older unstructured run, also provide its deterministic financial review:

```sh
.venv/bin/python scripts/export_saved_analysis.py \
  --review data/financial-reviews/COMPANY/review.json \
  --run data/COMPANY/runs/RUN \
  --packet data/COMPANY/PACKET \
  --company 'Company name' --ticker TICKER --id company-run \
  --method 'Forward EV/EBIT scenarios' \
  --output data/saved-views/company-run.json

.venv/bin/python scripts/serve_progress.py \
  --analysis data/saved-views/company-run.json
```

Repeat `--analysis` to show more saved runs. Use a new output filename for a revised export. The exporter verifies artifact identity and preserves saved decimal values, missing outputs and probability qualifications. It does not calculate a new valuation or call Börsdata or a model.

For multiple companies, configure their saved memos in the same command:

```sh
.venv/bin/python scripts/serve_progress.py \
  --corpus data/corpora/CORPUS/manifest.json \
  --analysis data/saved-views/company-a.json \
  --analysis data/saved-views/company-b.json \
  --market-db data/evidence/evidence.sqlite3
```

The Company selector combines the configured corpus and saved memos by Börsdata instrument ID. Captured companies without research show **No memo**; selecting one displays its snapshot date and **No saved analysis yet**. Memo version selects a saved report when available. Capturing data does not produce an analysis automatically.

`--corpus` is optional and reads only the existing version-1 `verified_api_capture` manifest at startup. It exposes company ID, name, optional ticker and capture timestamp, without opening the frozen database or serving raw data. Omit `--analysis` to browse a catalogue before any memos exist. Restart when changing the corpus or registering another `--analysis` path; the Refresh button reloads the configured memo files and retains the startup catalogue. Unavailable or malformed corpus manifests fail startup rather than silently hiding companies.

A newly selected company defaults to its newest analysis cutoff, then completion date. Your memo choice is retained when switching back or refreshing while it remains available. Identical visible version labels are distinguished by cutoff and, when necessary, analysis ID; company-name changes do not create a new company identity.

Identity checks bind the packet, frozen database, original inputs and calculation records. Scenario references must exist in that supplied run/review. Summary and narrative hashes record the exact text copied into the export; older run metadata does not authenticate those sidecars. Their financial claims remain subject to the saved review and later mapping checks.

## Attach a reader memo

Keep the canonical report intact when shortening its prose. Supply a private JSON memo and write a separate saved-view file:

```sh
.venv/bin/python scripts/attach_reader_memo.py \
  --view data/saved-views/company-run.json \
  --memo data/saved-views/company-reader-memo.json \
  --output data/saved-views/company-run-with-memo.json
```

The optional `reader_memo` object has exactly `schema_version: 1`, `analysis_sha256` matching the view's provenance, a timezone-bearing ISO `edited_at`, `summary`, `sections` and `scenarios`. Its six section IDs are `thesis`, `drivers`, `quality`, `management`, `valuation` and `risks`. Each section contains `id`, `title` and one to six `paragraphs`; each paragraph contains `kind` (`fact`, `interpretation` or `assumption`), `text` and nonempty `references`. Each canonical scenario appears once with `id`, `rationale`, `assumption_rationale`, `probability_rationale` and nonempty `references`. References must resolve to existing saved records or available report pages. No numeric fields, new sources or valuation overrides are accepted.

The memo is limited to 64 KiB: summary 1,000 characters, titles 150, paragraphs 1,500 and each scenario rationale 1,200; each reference list has at most 100 entries. Legacy views and stale analysis hashes are rejected. Attachment preserves the view ID, canonical analysis, original prose, prices, calculations, probabilities, provenance and saved review. It makes no provider or model calls and never overwrites an existing output. Configure the new file with `--analysis` to display it.

Validation checks structure, analysis identity and reference availability. It does not verify the memo's truth, completeness or numeric consistency. Independent editorial review must compare the rewrite with the canonical report and cited evidence. The existing independent analysis review covers the canonical report; it does not approve the reader memo.

Reader editions retain the original analysis ID. Configure the chosen edition once; the server rejects two files with the same ID. A genuinely new analysis uses its own ID and can appear as another memo version.

## Read the company tab

- **Company and memo:** separate selectors choose a captured business and its saved report when available. An available memo is selected initially; your company choice survives refresh even before a memo exists. The company header keeps the analysis cutoff separate from completion/review dates. The original conclusion remains available in a disclosure; the return overview copies existing results rather than rewriting the report.
- **Analysis and scenarios:** the full structured report separates facts, interpretations and assumptions. Clearly dated present values and future targets link to case-specific rationale, assumptions and saved calculations. Present values use horizontal dots; future share targets use columns. Each chart has its own scale and no annual price path is invented. Present value includes discounted dividends; the future share target excludes separately paid dividends. Legacy targets remain in their saved basis when no structured endpoint exists. Conditional weights retain their qualifications.
- **Management comparisons:** direct targets, guidance and related operating drivers retain issuer definitions, publication dates, target periods and physical-page quotations. An absent margin target stays absent; issuer ROCE and utilization are not relabelled operating ROIC or EBIT margin.
- **Calculations:** named formulas, inputs, units, scale, source IDs, physical-page evidence, outputs and missing inputs. The original run trace, including scalar operations and named formulas, is available separately.
- **Sources and review:** archived report identities and hashes, saved analysis, caveats and a separately bound independent-review verdict. The analysis cutoff differs from execution completion. The compatibility field `reviewed_at` holds completion time for structured runs and financial-review time for legacy runs; the interface labels those dates accordingly. A review without a saved date receives no invented review timestamp.
- **Material values:** definitions, exact selected sources, provider comparisons, residuals and selection reasons. Current R12 diagnostics take precedence when their financial periods match; annual-only fallbacks carry an explanation. [Period and mapping rules](material-inputs.md)

The reader opens with the conclusion, dated market/report prices and distinct valuation charts. Four expandable chapters keep business reasoning, valuation assumptions, financials/management and evidence accessible. Saved period tables can supply selectable charts; supplied labels distinguish actuals from forecasts. Dated current figures belong beside scenarios only when their meaning is explained. The latest compatible stored quote is a reference line on both valuation charts, without changing the report's inputs or return.

The historical index comparison is context, not a future return forecast. Missing cash-conversion inputs remain missing. Showing a result does not verify its accounting definitions or prove its investment thesis.

## Separate market-price context

Add `--market-db data/evidence/evidence.sqlite3` to the server command to show the latest available daily close for companies whose reports are explicitly configured. The header distinguishes that quote and its trading date from the selected report price. A new quote does not recalculate the report's return or valuation; an unavailable quote leaves the report usable. Price evidence contains the source and capture/check dates.

Refresh prices separately through the existing credential-safe acquisition and ingestion pipeline:

```sh
.venv/bin/python scripts/fetch_borsdata_context.py --instrument INSTRUMENT_ID --prices-only
.venv/bin/python scripts/ingest_evidence.py data/borsdata/context/INSTRUMENT_ID/CAPTURE --db data/evidence/evidence.sqlite3
```

Use the actual capture directory printed by acquisition. This fetches the price endpoint without refreshing the research datasets. The viewer only reads the configured store; it makes no provider calls and does not promise an intraday quote. Its price date remains visible.

## Privacy and boundaries

Exports belong under ignored `data/` and in the private research archive. Keep exact evidence and saved analyses out of the public repository. The server binds to loopback, exposes only explicitly configured exports, their allowlisted companies' optional market quotes and public document routes, and accepts no write or analysis-launch requests. Do not expose it through a tunnel or a public host.

The first viewer supports the existing completed-run and financial-review artifact formats. Broader decision records, material mapping validation and another-company walkthrough remain tracked in [the plan](../work/plan.json).

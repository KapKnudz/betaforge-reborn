# Review saved analyses locally

The workbench has three tabs: **Project** for priorities and completed work, **Architecture** for the data flow, and **Company** for saved research. Task bars count completed tasks; they do not measure investment confidence or time remaining.

```sh
.venv/bin/python scripts/serve_progress.py
```

Open **http://127.0.0.1:8765**. The project plan refreshes while the page is open. A company view requires an explicit private export.

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

Identity checks bind the packet, frozen database, original inputs and calculation records. Scenario references must exist in that supplied run/review. Summary and narrative hashes record the exact text copied into the export; older run metadata does not authenticate those sidecars. Their financial claims remain subject to the saved review and later mapping checks.

## Read the company tab

- **Analysis and scenarios:** the full structured report separates facts, interpretations and assumptions. Clearly dated present values and future targets link to case-specific rationale, assumptions and saved calculations. Separate endpoint charts share a scale and do not invent an annual price path. Legacy targets remain in their saved basis when no structured endpoint exists. Conditional weights retain their qualifications.
- **Management comparisons:** direct targets, guidance and related operating drivers retain issuer definitions, publication dates, target periods and physical-page quotations. An absent margin target stays absent; issuer ROCE and utilization are not relabelled operating ROIC or EBIT margin.
- **Calculations:** named formulas, inputs, units, scale, source IDs, physical-page evidence, outputs and missing inputs. The original run trace, including scalar operations and named formulas, is available separately.
- **Sources and review:** archived report identities and hashes, saved analysis, caveats and a separately bound independent-review verdict. The analysis cutoff differs from execution completion. The compatibility field `reviewed_at` holds completion time for structured runs and financial-review time for legacy runs; the interface labels those dates accordingly. A review without a saved date receives no invented review timestamp.
- **Material values:** definitions, exact selected sources, provider comparisons, residuals and selection reasons. Current R12 diagnostics take precedence when their financial periods match; annual-only fallbacks carry an explanation. [Period and mapping rules](material-inputs.md)

The historical index comparison is context, not a future return forecast. Missing cash-conversion inputs remain missing. Showing a result does not verify its accounting definitions or prove its investment thesis.

## Privacy and boundaries

Exports belong under ignored `data/` and in the private research archive. Keep exact evidence and saved analyses out of the public repository. The server binds to loopback, exposes only explicitly configured exports and public document routes, and accepts no write or analysis-launch requests. Do not expose it through a tunnel or a public host.

The first viewer supports the existing completed-run and financial-review artifact formats. Broader decision records, material mapping validation and another-company walkthrough remain tracked in [the plan](../work/plan.json).

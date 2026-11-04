# Review saved analyses locally

The workbench has three tabs: **Project** for priorities and completed work, **Architecture** for the data flow, and **Company** for saved research. Task bars count completed tasks; they do not measure investment confidence or time remaining.

```sh
.venv/bin/python scripts/serve_progress.py
```

Open **http://127.0.0.1:8765**. The project plan refreshes while the page is open. A company view requires an explicit private export.

## Add a saved company run

Use a completed run, its original frozen packet and the deterministic financial review. Supply the company name and the valuation method actually used; the exporter does not infer them from generated prose.

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

- **Conclusion and scenarios:** the dated saved conclusion and present values. Future targets and discount assumptions remain in each case’s basis. Conditional case weights are proposals, with their saved qualifications.
- **Calculations:** named formulas, inputs, units, scale, source IDs, physical-page evidence, outputs and missing inputs. The original arithmetic trace is available separately.
- **Sources and interpretation:** archived report identities and hashes, saved analysis, caveats and the distinction between an analysis date and a later review date.

The historical index comparison is context, not a future return forecast. Missing cash-conversion inputs remain missing. Showing a result does not verify its accounting definitions or prove its investment thesis.

## Privacy and boundaries

Exports belong under ignored `data/` and in the private research archive. Keep exact evidence and saved analyses out of the public repository. The server binds to loopback, exposes only explicitly configured exports and public document routes, and accepts no write or analysis-launch requests. Do not expose it through a tunnel or a public host.

The first viewer supports the existing completed-run and financial-review artifact formats. Broader decision records, material mapping validation and another-company walkthrough remain tracked in [the plan](../work/plan.json).

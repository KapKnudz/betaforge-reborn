# Codex evidence tools

Implemented 2026-11-01. The local Python controller drives the desktop-bundled Codex app-server and dispatches client-owned tools over a frozen evidence packet. It uses exact `gpt-6.1-sol`, high reasoning and the existing Codex login. No Börsdata key is passed to the model process. The original pi experiment remains separate.

## Entry point

```sh
.venv/bin/python scripts/run_codex_granges.py \
  --packet /absolute/path/packet.json \
  --prompt /absolute/path/prompt.txt \
  --output /absolute/path/new-run-directory
```

The output must be new unless `--resume` is explicitly supplied. Default deadline is 7,200 seconds; `--timeout` may reduce it. `--smoke` performs a short financial-query, report-read, original-image and calculation check, waiving complete report reading only for that check. `--codex` may select another explicitly tested executable; the default is `/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex`.

Packet fields:

```json
{
  "snapshot_dir": "snapshot",
  "reports_dir": "reports",
  "instrument_id": 426,
  "required_reports": ["granges-annual-2021"],
  "context": "Dated interpretation and reconciliation notes",
  "initial_context": {},
  "datasets": ["reports", "prices", "kpis"]
}
```

Paths resolve relative to the packet file. `required_reports` defaults to every report in `prepared/index.json`; `datasets` defaults to the frozen store's actual dataset names. Production Gränges packets require all eight existing reports, not the one-report illustrative list above. The index supplies PDF/prepared hashes and physical page counts. Initialization verifies the frozen database/blob hashes and every PDF/prepared file, then validates issuer-report observation links against document hash/page bounds.

## Tool contract

- `read_report`: complete consecutive physical pages up to 45,000 characters; follows `next_page` and persists delivery coverage. Delivery is not proof of human-like comprehension.
- `search_reports`: literal, bounded snippets; never increases full-page coverage.
- `view_report_page`: original PNG via `pdftoppm`, returned as a native image content item. It rechecks the PDF hash and records image provenance.
- `get_financials`, `get_dataset`, `get_source`, `get_catalogue`: bounded queries against the frozen SQLite store and source metadata. Financial queries include observation IDs, original values, scales, periods, currencies and reconciliation status. Dataset names are allowlisted by the packet.
- `record_input`: stores a report-derived number or an explicit assumption before arithmetic. Report inputs require a real report/page and a quote matching saved text; they remain marked analyst-extracted, not independently reconciled. A matching quote alone does not prove the numeric extraction. Prefer curated stored observations when available.
- `get_calculation_definitions`: supplies the fixed formula registry and verified frozen policy/catalogue. Historical packets without an adopted contract are labeled legacy.
- `calculate_financial`: preferred for the [named formulas](calculations.md). A single `valuation_case` record contains debt, EV, claims, common equity, target, dividends and PV. Inputs are named saved IDs; output references such as `calc:ID#future_target` reuse a result directly. Formula/version, normalized source inputs, assumptions, basis, missing inputs and warnings remain visible. Money is currently SEK. The wrapper rejects known incompatible units/currencies, mismatched paired periods, ordinary earnings multiples based on quarters/YTD, and stale opening capital dates. Undated assumptions and economic scope still need analyst judgment.
- `calculate`: consumes saved observation/input/calculation IDs. It **multiplies each original value by its stored scale exactly once**, then calculates in base units using Decimal. A value of 546 with scale 1,000,000 becomes SEK 546,000,000. Shares with scale 1 remain actual shares. Outputs have scale 1; derived results are not rescaled again. Add/subtract/growth require compatible units and currency; multiplication/division propagate dimensions. The requested output label must match the inferred base unit. Percent is distinct from a fraction; rates such as 10% should be entered as 0.10 dimensionless, or converted explicitly. Unknown KPI units are readable but unavailable to arithmetic until mapped.
- `finish_research_round`: after mandatory reading, records an investigation summary and retrieved evidence IDs. Ten rounds, two rounds with no newly cited retrieved evidence, or explicit finalization closes research. Further evidence reads are then denied. At most 200 finalization calls (saved-input calculations, input registration, catalogue/provenance and final round status) are permitted; the outer deadline remains active. Novelty is an auditable evidence-ID proxy, not a semantic guarantee that a round was useful.

No arbitrary expression evaluator or shell tool is exposed through the client-owned tools. Codex is configured with no environment access and disabled shell, browser, app, delegation and hook features; unexpected native tool activity fails the run. These settings are per invocation/thread and do not modify global configuration. The protocol and exact build still need verification when the installed Codex binary changes.

## Cancellation, recovery and records

Create a file named `CANCEL` inside the run directory to request cancellation, or send SIGTERM/SIGINT to the Python controller. The controller requests `turn/interrupt`, closes stdin, then uses bounded terminate/kill fallbacks. Polling occurs between tool dispatches; a PDF render has a 60-second maximum and is shortened to the remaining run deadline. Shutdown may add a short grace period after the deadline.

Remove the `CANCEL` marker before deliberate continuation, then rerun the same command with `--resume`. Resume validates packet/database/report identity and the frozen prompt hash, restores input/calculation/coverage state and resumes the saved Codex thread. It does not silently restart the analysis with new evidence. A deliberately resumed invocation has a fresh deadline.

New packets also freeze and verify the adopted policy/catalogue and optional industry/market contexts with source-file hashes. Resume now requires identical complete implementation hashes for tools, formulas, storage and runner. An old or changed implementation needs a separate run; the controller cannot silently mix financial definitions in one run.

Prior invocation metadata and answers are retained under `prior-invocations/` on deliberate resume.

Artifacts:

- `run.json`: model, thread/turn IDs, status, elapsed time, coverage, usage events and limits.
- `events.jsonl`: timestamped JSON-RPC traffic, with image data replaced by hash/length metadata.
- `tool-audit.jsonl`: tool calls, results and failures; `tool-state.json` retains resumable coverage, inputs and calculations.
- `answer.md`, `messages.jsonl`, `calculations.json`, `inputs.json`, and original rendered page images.

The website can display these saved records without rerunning the model. This controller does not itself implement a website.

## Protocol evidence and validation

The [official app-server documentation](https://learn.chatgpt.com/docs/app-server#dynamic-tool-calls-experimental) identifies dynamic tools as experimental and describes their server-to-client request flow. The installed `0.165.0-alpha.1.2` binary's generated JSON schemas were inspected: function schemas are supplied on `thread/start`, calls arrive as `item/tool/call`, and results contain `inputText`/`inputImage` items. Durable dynamic tools are restored on `thread/resume`.

Behavioral tests cover exact decimal/scale arithmetic, incompatible currencies, fabricated input references, quote/source/page validation, corrupted frozen files, persisted coverage, research closure, sanitized child environment, JSON-RPC responses and a silent-server timeout. A real smoke verified saved financial queries, complete-page text, native PDF image interpretation and calculations; A live turn was deliberately cancelled and resumed on the same durable thread; the resumed smoke correctly calculated an actual revenue observation with its million-currency scale. These smoke traces are separate from the full walkthrough. Smoke coverage is intentionally incomplete and must never be presented as the full walkthrough.

The [full Gränges walkthrough](granges-codex-walkthrough.md) subsequently completed in 23.2 minutes, delivering 921/921 required pages and saving 326 calculations across four research rounds. All 326 calculations and 919 operands passed separate arithmetic/source-value checks. The read-only output review found no material defect in the selected final valuation, while retaining the forecast and accounting-proxy limits. Seven tool rejections were recovered; no unexpected native tools were recorded. This is one-company execution evidence, not a general reliability claim.

## Current integration verification, 3 November 2026

The new packet at `data/granges-codex/packet-quality-20261103` contains the versioned policy, 14 named formulas, eight reports/921 required pages, 40 extra report facts, four Damodaran workbooks and the exact SIXRX source bundle. It reuses the saved Börsdata responses; assembly made no new provider request. Provider ROIC 37 has an explicitly sourced percent unit in new ingestion, while the original frozen observation remains unchanged.

Live GPT-6.1 Sol/high smoke on `codex-cli 0.166.0-alpha.5.1` completed in 43.232 seconds: 13 successful tool calls, zero errors, no unexpected native tools. It read the frozen policy/formula definitions, queried observations, interpreted Q3 p21 as reported EBIT 546/adjusted 596 MSEK, and calculated matched R12 reported EBIT margin 5.61139% with a named output. Only 16 text pages were delivered because full reading is waived for smoke; the run is `smoke_completed`, not a new valuation. Exact logs are in `data/granges-codex/runs/20261103-quality-smoke` in the private evidence bundle.

Poppler 26.05.0 from the verified desktop runtime rendered the original images through `BETAFORGE_PDFTOPPM`. Set that variable to an executable path when `pdftoppm` is not on PATH. See [Mac setup and preservation](research-handoff.md) and the [bounded implementation review](research/simple-framework-implementation-review.md).

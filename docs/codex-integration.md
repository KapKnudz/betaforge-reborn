# Codex evidence tools

The local Python controller drives the desktop-bundled Codex app-server and dispatches client-owned tools over a supplied frozen company packet. New runs use exact `gpt-6.1-sol`, `xhigh` reasoning and the workstation's existing Codex login, following the [project model policy](model-routing.md). The analyst process receives no Börsdata key.

## Entry point and packet

```sh
.venv/bin/python scripts/run_codex_analysis.py \
  --packet /absolute/path/packet.json \
  --prompt /absolute/path/prompt.md \
  --output /absolute/path/new-run-directory
```

The output must be new unless `--resume` is explicit. Default deadline is 7,200 seconds; `--timeout` may reduce it. `--smoke` performs a bounded financial-query, first-report/page-image and calculation check using the supplied packet. It waives full reading only for that integration check; it does not expect a named company's report, page or earnings values. `--codex` selects an explicit executable or PATH command. Otherwise the runner discovers `codex` on PATH, then checks the existing Mac application bundle. An unavailable executable fails before creating run output. Discovery does not establish client compatibility or authentication.

A minimal packet has this shape; the numeric ID below is illustrative, never a runtime default:

```json
{
  "snapshot_dir": "snapshot",
  "reports_dir": "reports",
  "instrument_id": 777,
  "required_reports": ["annual-2025"],
  "context": "Dated company interpretation and reconciliation notes",
  "datasets": ["reports", "prices", "kpis"]
}
```

A valid selected instrument ID is required. Paths resolve relative to the packet. `required_reports` defaults to all reports in `prepared/index.json`; `datasets` defaults to the frozen store's names. The caller supplies the required annual/interim corpus. The index supplies original/prepared hashes and physical page counts. Initialization verifies the database/blob and PDF/prepared hashes, then validates that selected issuer's report facts against document hashes/page bounds.

The packet builder additionally freezes the adopted policy/calculation catalogue and optional industry/market context with source-file hashes. It requires explicit company ID, report corpus, prompt and analysis date. Company reconciliations and extra sourced facts are optional explicit inputs, not issuer defaults. [Preparation command](../scripts/prepare_codex_packet.py), [retrieval contract](retrieval-design.md).

## Tool contract

- `read_report`: complete consecutive physical pages up to 45,000 characters; follows `next_page` and persists delivery coverage. Delivery is not proof of human-like comprehension.
- `search_reports`: literal, bounded snippets; never increases full-page coverage.
- `view_report_page`: original PNG via `pdftoppm`, returned as a native image content item. It rechecks the PDF hash and records image provenance.
- `get_financials`, `get_dataset`, `get_source`, `get_catalogue`: bounded queries against the frozen SQLite store and source metadata. Financial queries include observation IDs, original values, scales, periods, currencies and reconciliation status. Dataset names are allowlisted by the packet.
- `record_input`: stores a report-derived number or an explicit assumption before arithmetic. Report inputs require a real report/page and a quote matching saved text; they remain marked analyst-extracted, not independently reconciled. A matching quote alone does not prove the numeric extraction. Prefer curated stored observations when available.
- `get_calculation_definitions`: supplies the fixed formula registry and verified frozen policy/catalogue. Historical packets without an adopted contract are labeled legacy.
- `calculate_financial`: preferred for the [named formulas](calculations.md). A single `valuation_case` record contains debt, EV, claims, common equity, target, dividends and PV. Inputs are named saved IDs; output references such as `calc:ID#future_target` reuse a result directly. Formula/version, normalized source inputs, assumptions, basis, missing inputs and warnings remain visible. Money is currently SEK. The wrapper rejects known incompatible units/currencies, mismatched paired periods, ordinary earnings multiples based on quarters/YTD, and stale opening capital dates. Undated assumptions and economic scope still need analyst judgment.
- `calculate`: consumes saved observation/input/calculation IDs. It **multiplies each original value by its stored scale exactly once**, then calculates in base units using Decimal. A value of 100 with scale 1,000,000 becomes SEK 100,000,000. Shares with scale 1 remain actual shares. Outputs have scale 1; derived results are not rescaled again. Add/subtract/growth require compatible units and currency; multiplication/division propagate dimensions. The requested output label must match the inferred base unit. Percent is distinct from a fraction; rates such as 10% should be entered as 0.10 dimensionless, or converted explicitly. Unknown KPI units are readable but unavailable to arithmetic until mapped.
- `finish_research_round`: after mandatory reading, records an investigation summary and retrieved evidence IDs. Ten rounds, two rounds with no newly cited retrieved evidence, or explicit finalization closes research. Further evidence reads are then denied. At most 200 finalization calls (saved-input calculations, input registration, catalogue/provenance and final round status) are permitted; the outer deadline remains active. Novelty is an auditable evidence-ID proxy, not a semantic guarantee that a round was useful.

No arbitrary expression evaluator or shell tool is exposed through the client-owned tools. Codex is configured with no environment access and disabled shell, browser, app, delegation and hook features; unexpected native tool activity fails the run. These settings are per invocation/thread and do not modify global configuration. The protocol and exact build still need verification when the installed Codex binary changes.

## Cancellation, recovery and records

Create a file named `CANCEL` inside the run directory to request cancellation, or send SIGTERM/SIGINT to the Python controller. The controller requests `turn/interrupt`, closes stdin, then uses bounded terminate/kill fallbacks. Polling occurs between tool dispatches; a PDF render has a 60-second maximum and is shortened to the remaining run deadline. Shutdown may add a short grace period after the deadline.

Remove the `CANCEL` marker before deliberate continuation, then rerun the same command with `--resume`. Resume validates packet/database/report identity and the frozen prompt hash, restores input/calculation/coverage state and resumes the saved Codex thread. It does not silently restart the analysis with new evidence. Unstructured invocations receive a fresh deadline; structured continuations share the cumulative 7,200-second limit described below.

New packets also freeze and verify the adopted policy/catalogue and optional industry/market contexts with source-file hashes. Resume now requires identical complete implementation hashes for tools, formulas, storage and runner. An old or changed implementation needs a separate run; the controller cannot silently mix financial definitions in one run.

Prior invocation metadata and answers are retained under `prior-invocations/` on deliberate resume.

Artifacts:

- `run.json`: model, thread/turn IDs, status, elapsed time, coverage, usage events and limits.
- `events.jsonl`: timestamped JSON-RPC traffic, with image data replaced by hash/length metadata.
- `tool-audit.jsonl`: tool calls, results and failures; `tool-state.json` retains resumable coverage, inputs and calculations.
- `answer.md`, `messages.jsonl`, `calculations.json`, `inputs.json`, and original rendered page images.

The website can display these saved records without rerunning the model. This controller does not itself implement a website.

## Structured reports and independent challenge

Use `--structured` for new philosophy-based reports. `submit_analysis` validates six named sections, labelled facts/interpretations/assumptions, saved references, sourced management statements and dated bear/base/bull cases. Present values and targets are copied from saved `valuation_case` outputs. An explicit target-date precision prevents an annual or monthly horizon from becoming an invented day. `get_saved_record` resolves existing inputs, observations and calculation records for inspection.

The controller writes `analysis.json` and a readable `answer.md`, recording the exact report, input and calculation artifact hashes. Structured completion requires delivered mandatory pages and an accepted submission. This is a structural and identity check, not an assessment of the investment thesis. Existing unstructured runs and smoke checks retain their original contracts.

The session coordinator obtains an independent read-only Sol/xhigh challenge following [the analysis workflow](analysis-workflow.md). The controller does not dispatch financial subagents itself. Review feedback is tied to the packet and exact draft hash. `--resume --structured --review-feedback PATH` permits one explicit revision, preserves draft artifacts, and reopens at most two targeted research rounds. Structured analyst execution has a cumulative 7,200-second limit across continuations. The original prompt and implementation identity remain fixed; feedback has its own saved hash. A revised report remains pending content review until independently checked.

## Protocol and verification scope

The [official app-server documentation](https://learn.chatgpt.com/docs/app-server#dynamic-tool-calls-experimental) describes experimental dynamic tools and their server-to-client flow. The implementation supplies schemas on `thread/start`, handles `item/tool/call`, and returns `inputText`/`inputImage` items. Durable tools are restored on `thread/resume`. An installed Codex build change needs another integration check.

Tests cover decimal/scale arithmetic, currency and period mismatches, fabricated references, source/quote/page validation, hash corruption, coverage and research closure, sanitized child environment, JSON-RPC responses, timeout and implementation identity on resume. Alternate synthetic instrument/report inputs exercise company selection; this does not establish source coverage for another real issuer.

On 3 November 2026, the company-neutral CLI completed a live integration smoke against a supplied frozen example packet: `gpt-6.1-sol`/high, `codex-cli 0.166.0-alpha.5.1`, 50.764 seconds, 17 successful tool calls, zero tool errors or unexpected native tools, and four calculations. The first report/page came from the packet; no fixed interim-report assertion was used. Only 16 of 921 text pages were delivered because this was an integration smoke, not a valuation. The private saved run is `data/runs/generic-core-smoke-20261103`.

Earlier full valuation, cancellation/resume and deterministic replay evidence is retained in the [worked example](../examples/granges/README.md). It establishes bounded execution/arithmetic behavior, not predictive accuracy, arbitrary-company coverage or cross-workstation live-thread migration. See [setup and private handoff](research-handoff.md).

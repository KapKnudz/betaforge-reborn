# Betaforge Reborn

Personal company research with deterministic Börsdata acquisition, preserved report evidence, a local SQLite store and Codex analysis tools. The current implementation supports a bounded Gränges walkthrough. The personal website, automatic refresh scheduler and general OCR pipeline remain to be built.

## Specification and evidence

- [Adopted analysis policy](docs/analysis-policy.md) and [all financial formulas](docs/calculations.md)
- [Exact evidence and Mac handoff](docs/research-handoff.md)
- [Selected industry context and economic peers](docs/industry-context.md)
- [Accepted local storage decision](docs/adr/0002-local-evidence-storage.md)
- [Evidence persistence decision](docs/adr/0001-persist-company-evidence.md)
- [Retrieval design and remaining choices](docs/retrieval-design.md)
- [Börsdata retrieval, retention and storage specification](docs/research/borsdata-retrieval-storage.md)
- [Börsdata endpoint inventory](docs/research/borsdata-endpoints.md)
- [Gränges field mapping](docs/research/granges-borsdata-mapping.md) and [resolved input selections](docs/research/granges-mapping-resolution.md)
- [Codex tool integration and run controls](docs/codex-integration.md)
- [Completed Codex financial walkthrough and review](docs/granges-codex-walkthrough.md)
- [Original pi comparison results](docs/granges-walkthrough-results.md)
- [Planning foundation](docs/planning/decisions.md)

On 2026-11-01, all 86 requests in the Gränges acquisition plan returned HTTP 200. The saved evidence includes 14 annual, 40 quarterly and 40 R12 statement rows, 3,036 daily price rows, KPI summaries and selected histories, metadata, holdings and calendars. This verifies the selected routes for one company and account; it does not establish coverage for every issuer. See the [acquisition manifest](data/borsdata/context/426/20261101T173056Z/manifest.json).

The store retains exact decimal values, periods, units, scales, currency modes and source references, with immutable raw JSON and observation revisions. The [82 selected report facts](data/granges-walkthrough/reconciled-facts.json) preserve material report/API differences. The latest saved close is 172.20 SEK on 2026-10-30. See the [mapping resolution](docs/research/granges-mapping-resolution.md) for EPS/share bases, reported versus adjusted earnings, cash flow, debt/leases and dated price conventions.

## Acquire and prepare evidence

Put `BORSDATA_API_KEY=your-key` in ignored `.env.local`. Quotes around the value are optional. `.env.example` contains only the variable name. Do not put a real key in a command, commit or chat. Acquisition uses Python `requests` against `apiservice.borsdata.se`; the key is not passed to the Codex model process.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/fetch_borsdata_context.py --instrument 426
```

Each acquisition writes a new dated directory under ignored `data/borsdata/context/426/`. The fetcher disables redirects, records safe diagnostics and hashes, and bounds retries. The initial `urllib` client received Cloudflare HTTP 403 / Error 1010; the configured key succeeded using `requests`.

The eight Gränges PDFs and prepared text already exist locally. To reproduce their preparation, install `pypdf` and `pdftoppm`, then run:

```sh
.venv/bin/python scripts/fetch_granges.py
.venv/bin/python scripts/prepare_granges.py
```

To ingest the verified acquisition and freeze a self-contained analysis packet:

```sh
.venv/bin/python scripts/prepare_codex_packet.py \
  data/borsdata/context/426/20261101T173056Z \
  --analysis-date 2026-11-01 \
  --db data/evidence/new-quality-build/evidence.sqlite3 \
  --extra-facts data/granges-walkthrough/quality-facts-20261103.json \
  --benchmark-context data/benchmarks/damodaran/20261103T120604422959Z/context.json \
  --market-benchmark-context data/benchmarks/sixrx/20261103T121617260724Z/context.json \
  --output data/granges-codex/new-quality-packet
```

The original packet is preserved at `data/granges-codex/packet-20261101`. Preparation refuses an existing destination; choose a new directory for a deliberate rebuild and substitute the acquisition path when refreshing. New packets freeze the adopted policy and formula catalogue, validate issuer-specific report links, copy original PDFs/prepared text, and freeze the SQLite database and source blobs. The analysis date is explicit; a new preparation date does not make old source data fresh. The general [ingestion CLI](scripts/ingest_evidence.py) is also available for storage without packet preparation.

The [named formula registry](betaforge/financials.py) groups each EV/EBIT scenario into one auditable bridge and reuses named outputs. Quality checks have explicit definitions, units, periods and missing-input warnings. They complement the case without automatically revising the original valuation. SIX Return Index (SIXRX) is the agreed market hurdle, compared with IRR of expected cash flows; the historical 10% discount assumption remains separate.

Build a saved financial-quality review from the original frozen evidence without a model or provider call:

```sh
.venv/bin/python scripts/build_financial_review.py \
  --output data/financial-reviews/new-quality-review \
  --scenario-weights 0.25 0.55 0.20 \
  --market-benchmark-context data/benchmarks/sixrx/20261103T121617260724Z/context.json
```

The weights in that command explicitly replay the existing conditional analyst proposal; they are editable examples, not defaults. The final saved review is [here](data/financial-reviews/granges-20261103-quality-v2/review.md), available after restoring the private evidence bundle. It preserves all three original scenario targets/present values, adds the quality checks and compares the expected-cash-flow IRR with the [verified SIXRX measurement](docs/research/sixrx-benchmark.md).

## Run the Codex walkthrough

The full financial walkthrough completed in 23.2 minutes: all 921 required pages delivered, 326 saved calculations and four research rounds. All 35 implementation tests passed; independent arithmetic checks reproduced all 326 calculations and 919 source operands. The read-only output review found no material defect in the selected final valuation, with forecasts and accounting proxies explicitly qualified. See the [results and review](docs/granges-codex-walkthrough.md). Separate live smoke checks also verified cancellation and resume on the same Codex thread.

For a new analysis using the adopted policy and grouped financial tools:

```sh
.venv/bin/python scripts/run_codex_granges.py \
  --packet data/granges-codex/packet-quality-20261103/packet.json \
  --prompt data/granges-codex/packet-quality-20261103/prompt.md \
  --output data/granges-codex/runs/new-analysis
```

The Python controller uses the desktop-bundled Codex app-server with GPT-6.1 Sol/high and existing Codex login. Its tools query frozen evidence, read and search reports, view original pages, save assumptions and calculate from saved numeric IDs using Decimal. The required set is all five annual reports for 2021–2025 and Q1, half-year and Q3 2026. Runs persist coverage, calculations, source references, activity and answers. The default outer deadline is two hours; follow-up research is bounded. See [Codex integration](docs/codex-integration.md) for cancellation, resume and tool contracts. Output directories must be new unless deliberately resuming.

On 3 November, all 78 tests passed and a live integration smoke on Codex `0.166.0-alpha.5.1` completed with the frozen policy, verified benchmarks, original PDF image, saved financial data and a named EBIT-margin calculation. It used 13 successful tool calls, with no tool errors or unexpected native tools. This verifies the integration; it is not a new full valuation. See [implementation verification](docs/research/simple-framework-implementation-validation.md).

To rebuild the local review page from the completed saved run, without calling the model:

```sh
.venv/bin/python scripts/render_codex_walkthrough.py
```

The page is written to `.lavish/granges-codex-walkthrough.html`. It contains the reviewed scenario summary, full report, searchable calculations, source inventory and coverage. The portable export is available at `.lavish/granges-codex-walkthrough-export.html`.

## Preserve the original report comparison

The earlier upfront-versus-tool-read comparison used pi 1.4.0 with `openai-codex/gpt-6.1-sol`. Both arms delivered all 921 prepared pages and scored 40/40 on the frozen rubric. This is a bounded report-retrieval result; the original corpus did not contain Börsdata financial responses. It has not been relabeled as the Codex financial walkthrough.

Reproduction requires Python with `pypdf`, Node.js, `pdftoppm` and an authenticated pi installation:

```sh
python3 scripts/run_granges.py self-test
node scripts/test_granges_tools.mjs
python3 scripts/run_granges.py both
```

The original runner refuses to overwrite existing `runs/upfront` or `runs/tools` results. Preserve those directories before a deliberate rerun. Both arms used identical questions, source corpus and custom tools, with a two-hour deadline per arm. See the [protocol](data/granges-walkthrough/protocol.md), [reference rubric](data/granges-walkthrough/reference-rubric.md) and [extraction QA](data/granges-walkthrough/qa/extraction-qa.json).

The original PDFs came directly from Gränges' investor-relations archive. The [separate MFN discovery check](data/granges-walkthrough/mfn-discovery.json) found all eight release records, but MFN attachment downloads returned HTTP 403. Attachment byte identity remains unverified. Raw PDFs, prepared text, database snapshots and model traces are excluded from ordinary Git history and preserved in [private release assets](https://github.com/KapKnudz/betaforge-reborn/releases/tag/research-baseline-2026-11-03). Secrets remain local and are excluded from both Git and research bundles. See the [verified restore instructions](docs/research-handoff.md).

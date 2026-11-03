# Gränges worked example

This case preserves the original evidence-retrieval comparison, integrated Codex valuation and simpler financial-quality review for Börsdata instrument **426**. Shared storage, HTTP, formulas, packet preparation and Codex execution live in the core. This folder supplies Gränges-specific prompts, mappings, facts, report acquisition and replay code.

## Files and evidence

- `data/`: compact sourced facts, report manifest, analyst prompts, questions, extraction QA and frozen comparison rubric.
- `scripts/`: case-specific acquisition/preparation, original pi comparison, deterministic financial review and saved-result rendering.
- `docs/`: report findings, reconciliations, financial/benchmark reviews and historical execution records.
- [peers.json](peers.json): candidate businesses and reasons for comparison; no inferred peer multiple.

Exact original/prepared PDFs, raw API captures, database snapshots, watchlist and full model traces remain in [private research release assets](https://github.com/KapKnudz/betaforge-research-private/releases/tag/research-quality-2026-11-03). Follow [setup/download/restore](../../docs/research-handoff.md). The bundle's legacy `data/granges-walkthrough/` and `data/granges-codex/` paths are deliberately unchanged. Do not move or rewrite a frozen packet to match the new source layout.

The original integrated analysis date is **1 November 2026**, with latest saved close 172.20 SEK on 30 October. Restoring it does not refresh those facts. The [field mapping](docs/research/granges-borsdata-mapping.md) and [resolved selections](docs/research/granges-mapping-resolution.md) preserve reported/adjusted earnings, cash definitions, leases, minority ownership and share-basis differences.

## Prepare a new packet from saved evidence

Run commands from the repository root after installing the pinned dependencies. This explicit invocation reuses the original self-contained report corpus and old API capture, then writes a new packet/store:

```sh
.venv/bin/python scripts/prepare_codex_packet.py \
  data/borsdata/context/426/20261101T173056Z \
  --instrument 426 \
  --analysis-date 2026-11-01 \
  --db data/companies/426/rebuild/evidence.sqlite3 \
  --reports data/granges-codex/packet-20261101/reports \
  --prompt examples/granges/data/analysis-questions-v1.md \
  --facts examples/granges/data/reconciled-facts.json \
  --extra-facts examples/granges/data/quality-facts-20261103.json \
  --mapping-resolution examples/granges/docs/research/granges-mapping-resolution.md \
  --benchmark-context data/benchmarks/damodaran/20261103T120604422959Z/context.json \
  --market-benchmark-context data/benchmarks/sixrx/20261103T121617260724Z/context.json \
  --output data/packets/granges-new
```

Choose new output/store paths when repeating it. The historical baseline bundle lacks the later benchmark snapshots; restore the quality release for this command. No provider request is made by assembly. For fresh numbers, acquire a new explicit capture and select the analysis date/corpus deliberately:

```sh
.venv/bin/python scripts/fetch_borsdata_context.py --instrument 426
```

The example report scripts are available for a missing corpus:

```sh
.venv/bin/python examples/granges/scripts/fetch_granges.py
.venv/bin/python examples/granges/scripts/prepare_granges.py
```

Reuse restored prepared evidence when present. Preparation refuses to overwrite an existing `prepared/` directory. Acquisition checks the configured source manifest and original file hashes; the old frozen packets remain the preferred exact replay source. The original PDFs came from issuer IR. MFN release discovery succeeded but attachment downloads were blocked; see the [comparison findings](docs/granges-walkthrough-results.md).

## Run the analyst or a tool smoke

```sh
.venv/bin/python scripts/run_codex_analysis.py \
  --packet data/packets/granges-new/packet.json \
  --prompt data/packets/granges-new/prompt.md \
  --output data/runs/granges-new
```

Add `--smoke` and choose another output directory for integration checks. The shared smoke uses the supplied packet rather than a hard-coded Gränges report/page. On 3 November 2026 it passed in 50.764 seconds with 17 successful tool calls, no errors/unexpected native tools and four calculations. Its partial 16/921 text-page coverage is not a completed new valuation. [Integration details](../../docs/codex-integration.md#protocol-and-verification-scope).

## Replay the saved financial review

This deterministic review does not call a model, provider or canonical-store ingestion:

```sh
.venv/bin/python examples/granges/scripts/build_financial_review.py \
  --packet data/granges-codex/packet-20261101 \
  --facts examples/granges/data/quality-facts-20261103.json \
  --original-run data/granges-codex/runs/20261101-full \
  --scenario-weights 0.25 0.55 0.20 \
  --market-benchmark-context data/benchmarks/sixrx/20261103T121617260724Z/context.json \
  --output data/financial-reviews/granges-new-quality
```

The explicit weights replay an editable conditional analyst proposal, not adopted defaults. The review preserves all three original target/PV cases, adds qualified incremental margins and an explicit operating-tax ROIC proxy, and leaves undisclosed lease principal/owner FCF gaps visible. The [probability proposal](docs/research/scenario-probabilities-proposal.md), [SIXRX method](docs/research/sixrx-benchmark.md) and [historical validation record](docs/research/simple-framework-implementation-validation.md) explain the assumptions and limits.

Render the original completed model result from saved records without rerunning analysis:

```sh
.venv/bin/python examples/granges/scripts/render_codex_walkthrough.py \
  --packet data/granges-codex/packet-20261101/packet.json \
  --run data/granges-codex/runs/20261101-full \
  --output .lavish/granges-codex-walkthrough.html
```

The [full walkthrough](docs/granges-codex-walkthrough.md) retains 921/921-page delivery and the original 326-calculation audit. The simpler review uses grouped formulas without replacing that history. The original report-only pi experiment remains separately reproducible with `examples/granges/scripts/run_granges.py self-test` and `examples/granges/scripts/test_granges_tools.mjs`; pi/Node are needed only for that historical comparison.

## Preserve this case privately

Select the paths to preserve explicitly. This example includes restored legacy evidence, the final quality review and compact case inputs; the live store is frozen separately:

```sh
.venv/bin/python scripts/archive_research.py \
  --include examples/granges/data \
  --include data/granges-walkthrough \
  --include data/granges-codex/packet-20261101 \
  --include data/granges-codex/packet-quality-20261103 \
  --include data/granges-codex/runs/20261101-full \
  --include data/borsdata/context/426/20261101T173056Z \
  --include data/financial-reviews/granges-20261103-quality-v2 \
  --include data/benchmarks \
  --db data/evidence/evidence.sqlite3 \
  --output data/backups/granges-selected-research.tar.gz
```

Stop writers first, include any additional saved run deliberately, and upload only to the private research repository. Missing selected paths fail rather than being silently omitted. Historical archive hashes are in the [original handoff record](docs/granges-research-handoff.md).

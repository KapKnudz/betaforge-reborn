# Betaforge Reborn

Personal company research with deterministic Börsdata acquisition, source-linked financial observations, preserved reports and explainable Codex valuations. The shared workflow takes an explicit company and its evidence. Company-specific prompts, mappings and replay scripts live in [examples](examples/granges/README.md).

The current backend uses SQLite and immutable source files. The financial formulas currently use SEK and ordinary nonfinancial operating-company concepts. A local website, automatic refresh scheduler and general report discovery/OCR remain future work.

## Project layout

- `betaforge/`: shared financial formulas, evidence storage, HTTP client and Codex tools/controller.
- `scripts/`: company-neutral acquisition, packet preparation, analysis and private archival commands.
- `docs/`: investment policy, formula definitions, provider contracts and setup.
- `examples/granges/`: the preserved worked example, its sourced facts, company-specific scripts and validation history.
- `data/`: ignored local evidence, packets and saved runs; exact research is stored in [private release assets](https://github.com/KapKnudz/betaforge-research-private/releases).

## Setup

Python 3.14.7 is the tested version. Install Poppler for original PDF page images, then create the project environment:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests -v
```

Put `BORSDATA_API_KEY=your-key` in ignored `.env.local`; quotes are optional. Acquisition uses the shared Python client against `apiservice.borsdata.se`. The key is never passed to the analyst process. Authenticate Codex separately on each workstation. See [Mac setup and private research handoff](docs/research-handoff.md).

## Company workflow

Select the positive Börsdata instrument ID explicitly; commands have no issuer default:

```sh
.venv/bin/python scripts/fetch_borsdata_context.py --instrument "$COMPANY_ID"
```

Each acquisition writes a new dated directory under `data/borsdata/context/<instrument-id>/`. It preserves original response bytes, hashes and safe diagnostics. Available report/KPI history, source dates, currencies and revisions stay distinct.

Prepare the selected company's original PDFs and physical-page text/index first. Then supply its captured API directory, report corpus and analyst prompt. The variables below denote paths and values chosen by the caller:

```sh
.venv/bin/python scripts/prepare_codex_packet.py "$CAPTURE_DIR" \
  --instrument "$COMPANY_ID" \
  --analysis-date "$ANALYSIS_DATE" \
  --reports "$REPORT_CORPUS" \
  --prompt "$ANALYST_PROMPT" \
  --output "$PACKET_DIR"
```

Add `--facts`/`--extra-facts` for sourced issuer figures and `--mapping-resolution` for company-specific reconciliations. Optional industry and market contexts are frozen with their raw-source hashes. The builder validates selected company identity and source links, copies the reports, and freezes the store, policy and calculation catalogue. It refuses an existing output. An analysis date does not make old source evidence fresh.

```sh
.venv/bin/python scripts/run_codex_analysis.py \
  --packet "$PACKET_DIR/packet.json" \
  --prompt "$PACKET_DIR/prompt.md" \
  --output "$RUN_DIR"
```

The controller uses GPT-6.1 Sol/high with existing Codex login. It exposes bounded reads and calculations over the supplied packet. It records sources, assumptions, formulas, reading coverage and results. Required reports come from that packet. `--smoke` exercises the supplied company's tools with limited reading; it is not a valuation. See [tool contracts, cancellation and resume](docs/codex-integration.md).

The [Gränges example](examples/granges/README.md) supplies complete concrete commands, preserves the original report comparison and demonstrates the financial-quality review. Its private evidence paths and company assumptions are example inputs. A second real-company end-to-end walkthrough remains to be verified.

## Financial and evidence contracts

- [Adopted investment policy](docs/analysis-policy.md) and [all financial formulas](docs/calculations.md).
- [Retrieval design](docs/retrieval-design.md), [accepted storage decision](docs/adr/0002-local-evidence-storage.md) and [glossary](GLOSSARY.md).
- [Börsdata endpoint inventory](docs/research/borsdata-endpoints.md) and [retrieval/retention specification](docs/research/borsdata-retrieval-storage.md).
- [Optional industry context](docs/industry-context.md) and [private archival/restore workflow](docs/research-handoff.md).

The primary model is forward operating EV/EBIT with an explicit common-equity bridge. Named calculations retain source IDs, normalized units, assumptions and missing-input warnings. P/E and ownership-matched cash yield are sanity checks. Scenario probabilities are company-specific judgments; expected-cash-flow IRR is compared with the selected historical SIXRX benchmark, separately from the discount-rate assumption. No full reverse DCF is implemented.

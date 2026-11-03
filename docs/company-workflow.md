# Run a company analysis

Complete [Mac setup](research-handoff.md#mac-prerequisites) first. The shared workflow requires an explicit company and its evidence. Company-specific prompts, mappings and replay scripts belong under `examples/`.

## 1. Capture financial data

Put `BORSDATA_API_KEY=your-key` in ignored `.env.local`; quotes are optional. Acquisition uses the shared Python client against `apiservice.borsdata.se`. The analyst process receives no Börsdata key. Authenticate Codex separately on each workstation.

Select a positive Börsdata instrument ID; commands have no issuer default:

```sh
.venv/bin/python scripts/fetch_borsdata_context.py --instrument "$COMPANY_ID"
```

Each acquisition writes a new dated directory under `data/borsdata/context/<instrument-id>/`. It preserves original response bytes, hashes and safe diagnostics. History, source dates, currencies and revisions remain distinct. See the [endpoint inventory](research/borsdata-endpoints.md) and [retrieval/retention specification](research/borsdata-retrieval-storage.md).

## 2. Prepare frozen evidence

Prepare the selected company's original PDFs and physical-page text/index first. General report discovery/OCR remains future work; the [Gränges example](../examples/granges/README.md) supplies a concrete preparation workflow.

Supply the captured API directory, report corpus and analyst prompt. The variables below are paths and values selected by the caller:

```sh
.venv/bin/python scripts/prepare_codex_packet.py "$CAPTURE_DIR" \
  --instrument "$COMPANY_ID" \
  --analysis-date "$ANALYSIS_DATE" \
  --reports "$REPORT_CORPUS" \
  --prompt "$ANALYST_PROMPT" \
  --output "$PACKET_DIR"
```

Add `--facts`/`--extra-facts` for sourced issuer figures and `--mapping-resolution` for company-specific reconciliations. Optional industry and market contexts are frozen with their raw-source hashes. The builder validates company identity and source links, copies reports, and freezes the store, policy and calculation catalogue. It refuses an existing output. An analysis date does not make old evidence fresh.

The backend uses SQLite and immutable source files. Its financial formulas currently use SEK and ordinary operating-company concepts. See the [retrieval design](retrieval-design.md), [storage decision](adr/0002-local-evidence-storage.md), [optional industry context](industry-context.md) and [glossary](../GLOSSARY.md).

## 3. Run the analyst

```sh
.venv/bin/python scripts/run_codex_analysis.py \
  --packet "$PACKET_DIR/packet.json" \
  --prompt "$PACKET_DIR/prompt.md" \
  --output "$RUN_DIR"
```

The controller uses GPT-6.1 Sol/high with the workstation's Codex login. It provides bounded reads and calculations over the supplied packet and records sources, assumptions, formulas, reading coverage and results. Required reports come from that packet. `--smoke` checks integration with limited reading; it is not a valuation. See [tool contracts, cancellation and resume](codex-integration.md).

The primary model is forward operating EV/EBIT with an explicit common-equity bridge. P/E and ownership-matched cash yield are checks. Scenario probabilities are company-specific judgments; expected-cash-flow IRR is compared with the selected historical SIXRX benchmark, separately from the discount-rate assumption. A full reverse DCF is not implemented. The [analysis policy](analysis-policy.md) and [formula catalogue](calculations.md) define these choices.

## 4. Preserve the result

Follow the [private archival and restore workflow](research-handoff.md). Preserve the database, source files and saved run together. Credentials stay local.

The [Gränges example](../examples/granges/README.md) preserves report comparisons, sourced facts and financial-quality validation. Its company assumptions and private evidence paths are example inputs. Another real-company end-to-end walkthrough and an automatic refresh scheduler remain to be verified or implemented.

# Gränges: stored evidence and Codex valuation walkthrough

Analysis date: 2026-11-01. **Completed and reviewed.** This is the integrated financial walkthrough, separate from the [original pi report-retrieval comparison](granges-walkthrough-results.md). The independent reviewer found no material defect in the selected final valuation; the forecasts remain conditional research assumptions. [Output review](research/granges-codex-output-review.md).

## Result

| Measure | Result |
|---|---:|
| Model | GPT-6.1 Sol, high reasoning, through Codex |
| Model-run time | 23.2 minutes |
| Required text pages delivered | 921 / 921 |
| Original-page image calls | 26 |
| Saved calculations | 326 |
| Follow-up research rounds | 4; research closed explicitly |
| Unexpected native tool activity | 0 |

The illustrative valuation concludes roughly fair value under its base assumptions:

| SEK per share | Bear | Base | Bull |
|---|---:|---:|---:|
| Present value at a 10% required return, including interim dividends | 52.35 | 168.14 | 249.09 |
| November 2029 target | 58.43 | 212.54 | 320.28 |

The observed price was 172.20 SEK. These are conditional scenarios, not probability-weighted forecasts. The base case assumes 700 ktonnes volume, 3,600 SEK EBIT per tonne, an 11-times full EV/EBIT multiple and 350 MSEK annual retained cash after dividends and all other cash outflows. NCI uses a book-value proxy. [Full report, sections 9–11](../../../data/granges-codex/runs/20261101-full/answer.md).

The local [review page](../../../.lavish/granges-codex-walkthrough-export.html) exposes the saved report, calculation inputs, source inventory and coverage. It follows the existing Betaforge review design and does not initiate analysis.

## Method and philosophy clarification — 3 November 2026

The primary model forecasts operating earnings, applies EV/EBIT, converts enterprise value into parent equity, then discounts the future equity target and dividends. The backward calculation solves for EBIT consistent with the observed price; no full reverse DCF was run. The [calculation guide](research/granges-calculation-guide.md) explains every saved operation, including 82 presentation conversions, and distinguishes final citations, their intermediate dependencies and other working records.

Selected principles from the investment philosophy were translated into the walkthrough prompt. The full philosophy document was not supplied to the runtime as a versioned instruction. The [philosophy application review](research/granges-philosophy-application.md) identifies what was implemented and what remains missing.

The 10% equity required return was an illustrative analyst assumption. The agreed Investor B trailing ten-year total-return hurdle was not measured or tested. The original scenarios have no assigned probabilities, so their base present value is not a probability-weighted expected value. The user subsequently confirmed that the analyst proposes editable probabilities. The [follow-up probability proposal](research/scenario-probabilities-proposal.md) gives provisional 25/55/20 weights for the three modeled going-concern cases, with an indicative weighted present value of 155.38 SEK/share and explicit distribution limits. These clarifications and draft weights do not change the frozen report or establish that its forecasts have been independently validated.

## What is implemented

The accepted [SQLite and immutable-file specification](../../../docs/adr/0002-local-evidence-storage.md) now has a working local implementation. Acquisition uses Python Requests, preserves raw responses and safe request metadata, and bounds retries. Storage retains exact decimals, units, scales, periods, currencies, source references and changed observations. Analysis packets freeze the database, source JSON, original PDFs and prepared page text.

The Python controller drives the authenticated desktop Codex app-server using GPT-6.1 Sol at high reasoning. Its tools query saved financials and contextual datasets, read complete report pages, search, inspect original PDF images, record sourced inputs or assumptions, and calculate from saved numeric IDs. The agent has no general shell, filesystem or web tool in this run. See [the integration contract](../../../docs/codex-integration.md).

The controller records reading coverage, activity, input selections and calculations; it enforces research closure and a two-hour model execution deadline. A separate live smoke established original-image access, scale-aware arithmetic, cancellation and continuation on the same Codex thread. Existing answers and invocation metadata are preserved on deliberate resume.

## Frozen evidence

The [acquisition manifest](../../../data/borsdata/context/426/20261101T173056Z/manifest.json) records 86 HTTP 200 responses. The data includes 14 annual, 40 quarterly and 40 R12 statement rows, 3,036 daily price rows, selected KPI histories and summaries, definitions, classifications, insider/short/buyback data and calendars. This verifies the selected routes for Gränges and this account, not universal issuer coverage.

The [packet](../../../data/granges-codex/packet-20261101/packet.json) contains:

- 87 source versions: 86 provider responses plus the selected report-fact source.
- 22,593 stored observation versions, of which 22,566 are current within this snapshot.
- 10,531 contextual dataset rows, including global definitions and lookups.
- 82 independently selected report facts, with PDF hashes and physical page references.
- Five annual reports for 2021–2025 and Q1, H1 and Q3 2026: 921 physical PDF pages.

These observation counts include daily-price fields and overlapping provider series; they are not counts of independent reports or economically independent facts. The latest saved closing price is 172.20 SEK on 2026-10-30.

The original PDFs came from Gränges' issuer archive. MFN discovery found all eight release records, but its attachment downloads returned HTTP 403; attachment byte identity remains unverified. The eight-report required set is complete. The broader five-year interim archive has not yet been collected.

## Material input choices

The [mapping resolution](research/granges-mapping-resolution.md) and [selected report facts](../data/reconciled-facts.json) retain provider and issuer observations separately.

| Issue | Treatment in the walkthrough |
|---|---|
| Q3 earnings | Reported EBIT 546 MSEK; adjusted EBIT 596 MSEK. Preserve the displayed one-million rounding residual. |
| Shares and EPS | Use issuer basic/diluted EPS on its stated basis. Current valuation uses 106,594,428 disclosed issued shares as an explicit proxy; current treasury holdings and future dilution remain assumptions. |
| Cash flow | Provider FCF, statutory CFO and company operating cash flow remain distinct. Provider FCF is not automatically valuation FCFF. |
| Debt and ownership | Financial net debt 4,987 MSEK excludes leases. Separately identify 247 MSEK leases and 651 MSEK minority book equity; minority fair value is a scenario assumption. |
| Dated prices | Use the dated daily close. In the saved sample, the report field named average corresponds to the report-date close, not the calendar-year arithmetic mean. |
| Historical multiples | Retain the provider's observed convention and residual differences. A current revised history is not a point-in-time backtest. |

The deeper walkthrough also identified pensions of 229 MSEK on Q3 physical page 27. The capital-employed reconciliation adds these back after subtracting non-interest-bearing liabilities; this supports treating them as separate from financial net debt. The final scenarios use a separately disclosed debt-like proxy. This additional input is preserved in the run's input records rather than silently changing the frozen 82-fact source.

## Validation and limits

All 35 automated tests passed. They cover acquisition failures and redaction, bounded retry/defer behavior, revisions, missing values, company and currency identity, snapshot integrity, report source links, exact arithmetic, unit guards, research closure, prompt identity and runner lifecycle behavior. The independent implementation review found no remaining material blocker for the bounded Gränges run.

All 326 model calculations were separately recomputed with Decimal and their 919 operands checked against frozen observations, saved inputs and earlier results. Every result and source value/scale matched. That validates arithmetic and selected source values; it cannot establish that a forecast, valuation multiple or accounting convention is economically correct. [Arithmetic check](../../../data/granges-codex/runs/20261101-full/calculation-verification.json), [independent output review](research/granges-codex-output-review.md).

Seven tool calls were rejected and recovered: invalid pagination, an unretrieved evidence ID, unsuitable output units and unresolved provider currency. They did not prevent completion. The audit preserves these attempts. It also preserves intermediate calculations: 77 calculation IDs are cited in the final report, while 249 are intermediate or uncited. An early gross-income label was corrected in the selected final answer; the history was not erased.

The run used 228 financial-query calls and 93 dataset-query calls. That demonstrates a practical improvement opportunity: add period/date filters and compact dataset summaries before scaling the watchlist. This successful run does not establish that the present query interface is optimally efficient.

The app-server reported 10,720,226 accumulated input tokens, including 10,417,664 cached input tokens, and 47,643 output tokens. These accumulate across model requests; they are not unique source-text size, an invoice or a fair performance comparison with the earlier report-only pi experiment. No explicit compaction event was recorded.

This implementation does not yet establish a general multiissuer production workflow. A personal website, scheduled refresh, general OCR and complete historical interim acquisition remain future work. The saved HTML review reads existing results and never starts a new analysis.

## Local records and reproduction

- [Run metadata](../../../data/granges-codex/runs/20261101-full/run.json)
- [Full model report](../../../data/granges-codex/runs/20261101-full/answer.md)
- [Saved calculations](../../../data/granges-codex/runs/20261101-full/calculations.json)
- [Saved inputs](../../../data/granges-codex/runs/20261101-full/inputs.json)
- [Packet and corpus identity](../../../data/granges-codex/packet-20261101/packet.json)

The [README](../../../README.md) gives acquisition, preparation and execution commands. Preserve the existing packet and run; choose a new output directory for a deliberate new analysis. Local data and model traces are ignored by Git.

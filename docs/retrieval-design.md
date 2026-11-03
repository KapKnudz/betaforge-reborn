# Company evidence retrieval

The accepted design separates deterministic acquisition and storage from the evidence the analyst receives. [ADR 0001](adr/0001-persist-company-evidence.md) records persistence; [ADR 0002](adr/0002-local-evidence-storage.md) adopts immutable files plus SQLite. The [worked-example history](../examples/granges/docs/retrieval-design-history.md) preserves the original comparison and subsequent source findings.

## Agreed scope

The system is for one person's repeated research on a maintained company list, initially small and eventually about 30–100 companies. A personal local website should initiate analyses and show retrieved evidence, calculations and saved results. That website and an automatic refresh scheduler remain future work.

Select companies by explicit Börsdata instrument IDs. The API scope includes structured financial history, classifications, historical valuation context and documented holdings/events; API coverage does not imply every website feature. Financial reports come from issuer/MFN sources. Broader non-report disclosure collection has not been agreed.

Bootstrap all available structured history and five years of annual/interim reports, bounded by actual source availability. Read at least the five most recent available annual reports plus every interim since the latest annual reporting year-end. Older reports remain available for focused questions. Refresh manually or at most daily; no schedule is enabled by this design.

Analyze information available at the selected analysis date. A later acquisition date, revised provider history and document publication date are separate facts. Historical multiples provide context; current revised data does not establish a point-in-time backtest.

## Deterministic foundation

Save original JSON/PDF bytes, hashes, acquisition status and safe provenance. Normalize numeric observations into SQLite with exact values, units/scales, currency, periods, source pointers, definitions and revisions. Preserve ambiguous fields and conflicting source values. The [retrieval/retention specification](research/borsdata-retrieval-storage.md) defines the selected families.

Each analysis receives a frozen packet: selected instrument identity, source-linked financial observations, verified report corpus, analyst prompt, mapping notes, adopted policy/calculation catalogue and optional source context. The packet builder requires company-specific inputs explicitly. The tools reject a missing or invalid company identity; they do not choose an issuer for the caller.

Initial context is a compact financial history, latest saved price and interpretation notes. Tools can read all saved fields and report pages. Storing an entire document does not require sending every document immediately to the model. The pilot found upfront and tool-based reading viable for one bounded corpus; it does not establish universal retrieval superiority.

## Report preparation and reading

Preserve original PDF versions and prepare native text with physical page boundaries. Keep source and preparation hashes, page counts and source metadata. A supplied corpus has `sources/<report-id>.pdf`, `prepared/<report-id>.json`, `prepared/index.json` and `source-manifest.json`. Prepared page records retain page numbers and text.

Read complete reports in page ranges; search and summaries assist navigation but do not substitute for mandatory reading. Inspect original page images for charts, tables, ambiguous extraction, headings, units and footnotes. Native extraction can fail on numeric spacing and reading order. General OCR/discovery is not implemented; the [reference example](../examples/granges/README.md) includes one report-preparation workflow and its extraction QA.

When fresh report figures replace or supplement API observations, save them separately with source page, unit, period and basis. Calculations identify the selected observation rather than silently overwriting the provider's number.

## Analysis and execution

Python owns acquisition, preparation, storage, evidence validation, arithmetic records and execution limits. Codex reasons over the frozen packet using client-owned tools. The frontend can display saved records without starting another analysis. See [Codex integration](codex-integration.md) and the [analysis policy](analysis-policy.md).

After mandatory reading, allow at most ten follow-up research rounds and stop after two consecutive rounds without newly cited retrieved evidence. A two-hour outer deadline and bounded finalization calls prevent endless operation. Evidence-ID novelty is a practical progress proxy, not proof that reasoning improved. Save partial results and missing evidence at a limit; required-reading failure remains incomplete.

Calculations consume saved numeric inputs, normalize scale once, use Decimal, and keep formulas/assumptions visible. Company-specific mappings, operating drivers and probability judgments stay in the supplied case; the shared engine implements the defined formulas and controls. Missing evidence should localize uncertainty instead of blocking unrelated useful analysis.

## Validation and remaining work

The [Gränges example](../examples/granges/README.md) records original report-reading and integrated financial executions. It establishes one-company feasibility, not general source coverage or forecast accuracy. Synthetic alternate-issuer tests exercise shared interfaces; another real-company end-to-end workflow remains to be verified.

Remaining work is targeted: broader issuer/source checks, report discovery/OCR, evaluation of initial-context choices, and a local website over saved activity/results. Add issuer/period filtering and ordinary text search before considering semantic retrieval for demonstrated questions.

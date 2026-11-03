# Retrieval design discussion

Status: the user accepted deterministic acquisition and preserved evidence in [ADR 0001](adr/0001-persist-company-evidence.md), then accepted the SQLite/file specification and Codex walkthrough in [ADR 0002](adr/0002-local-evidence-storage.md). Storage and the Codex evidence tools are implemented. Both the original pi report comparison and the [integrated Codex financial walkthrough](granges-codex-walkthrough.md) are complete. The permanent initial-context policy remains open beyond this tested starting configuration.

## Agreed scope

- The system is for personal research.
- Repeatedly investigate a maintained set of companies.
- Start with a small company list; the expected eventual size is approximately 30–100 companies at most.
- The user supplied `/Users/kasperknudas/Downloads/Knudz_Watchlist.csv` as the candidate pool and authorized selecting any company from it. Inspection found 152 entries with distinct Börsdata IDs, including separate share classes; this does not mean all entries must be monitored or represent distinct issuers.
- The user wants a personal local website for initiating company analysis and following retrieved evidence and calculations.
- Begin with an established, nonfinancial operating company.
- The requested Börsdata scope is financial numbers, "short holdings," and the other documented company data. The working interpretation of "short holdings" is the documented short-selling dataset; full website coverage is not implied by API coverage.
- The requested MFN scope is financial reports, including annual reports and earnings/interim reports. A broader collection of non-report disclosures has not been agreed.
- Initially acquire all available structured financial history and five years of annual and interim reports. Older reports may be acquired when an analysis requires them.
- Refresh manually for a user-selected company list, or automatically no more than daily. A daily schedule has not been requested or created; whether to enable it initially remains open.
- Assess the company using information available now.
- Historical valuation context may help explain the company's current valuation alongside its financial history and reports.
- An initial valuation may identify gaps and lead to further evidence gathering and revision. Incomplete evidence should not routinely prevent useful analysis.
- The analyst may read any saved evidence and acquire older reports within the agreed sources without asking the user before each read.
- Response speed is not a priority. An analysis taking approximately an hour is acceptable; this is neither a required runtime nor an agreed hard limit.
- The analyst must read at least the five most recent annual reports when available. The acquisition process may need to go beyond the initial five-year archive window to meet this requirement. Summaries alone do not fulfill required report reading. Native-text extraction, page-delivery coverage and original-page inspection are implemented; delivery coverage alone does not establish comprehension or extraction fidelity.
- The analyst must also read every interim report since the latest annual reporting year-end. Older interim reports remain available for targeted historical questions. This is the accepted starting reading policy.
- The user has ChatGPT Pro, intends to use GPT-6.1 Sol primarily, and does not want a spending cap or aggressive token minimization. They use pi but are also willing to start with Codex if it simplifies integration. Python is the preferred candidate for the local backend; the frontend does not require a particular agent harness.
- The user accepts finalizing when main valuation assumptions have evidence or explicit uncertainty, material contradictions have been investigated, and further reading no longer changes the valuation case.
- After required reading, allow at most 10 follow-up research rounds. Stop earlier after two consecutive rounds without meaningful new evidence. Enforce a two-hour overall timeout outside the model. These initial limits are accepted and may be adjusted after the walkthrough.
- At a limit, save the current analysis, reading coverage and unresolved questions for deliberate continuation. Mark the run incomplete if required reading remains unfinished.
- When Börsdata lacks fresh information, the analyst may use report-derived figures as sourced calculation inputs, checking period, units and metric definitions. Preserve the original Börsdata values and make substitutions visible.

## Accepted foundation and remaining choices

Acquire the agreed company information deterministically and persist it for reuse, with page-linked report preparation, original-page checks and explicit calculation tools. The user accepted this recommendation after the walkthrough.

The accepted [retrieval and storage specification](research/borsdata-retrieval-storage.md) defines dataset coverage and retention. Immutable JSON/PDF files preserve sources; SQLite stores source-linked observations, metadata, dated identity and revisions. Numeric observations retain decimal values, units, scales, currency mode, periods and basis. Each analysis uses a frozen packet so later ingestion cannot change its evidence. The permanent initial-context policy is still open.

The implemented Gränges packet at `data/granges-codex/packet-20261101` contains a frozen store, all eight original PDFs and prepared reports, 82 selected report facts, the mapping resolution, compact financial history and the walkthrough prompt. See [packet preparation](../scripts/prepare_codex_packet.py), [storage](../betaforge/storage.py) and [Codex integration](codex-integration.md).

## Retrieval comparison and current packet

Acquire and preserve reusable company evidence independently of what the agent reads. The original comparison tested initial report loading against selective tool reads over identical saved reports. Both workflows were viable in that bounded test; the permanent context policy remains a choice to evaluate as the financial workflow develops.

Persistence is now implemented through SQLite and immutable files. Acquiring evidence does not require placing all saved material into every model context. The new Codex walkthrough starts with compact financial history and mapping decisions, then reads required reports through tools; it is not a rerun of the original two-arm pi comparison.

Both workflows require the five most recent available annual reports and every interim since the latest annual reporting year-end. The original pi experiment held report evidence coverage constant and did not include Börsdata numbers. The current Codex packet supplies compact financial history and mapping decisions initially, then uses report tools for mandatory reading and follow-up evidence. Prioritize evidence quality and successful completion; record tokens and latency as diagnostics rather than spending or speed targets.

## PDF preparation baseline

- Preserve each original PDF and its source/version metadata.
- Extract native text once, retaining physical page boundaries and section headings where reliably detected. Preserve printed page labels separately when available.
- Use OCR for pages that lack usable native text. Flag unresolved extraction failures instead of silently treating those pages as read.
- Expose page images for charts, uncertain reading order and financial tables that need visual inspection. Preserve table headers, units, periods and footnotes when extracting figures for calculation.
- Let the analyst read complete reports in sequential page ranges, search within them, and reopen cited pages. A report index or generated summary assists navigation but does not substitute for required report reading.
- Reuse prepared content while the source PDF and extraction method remain unchanged. Test extraction quality on actual reports before choosing a parsing library.

The walkthrough preserves originals and uses page-addressable native text plus a page-image tool. Eight sample pages were visually checked; numeric spacing and reading-order defects were found. This is not validation of every page or an implemented general OCR pipeline. See [extraction QA](../data/granges-walkthrough/qa/extraction-qa.json). Primary documentation explains [PDF reading-order and table ambiguity](https://pypdf.readthedocs.io/en/stable/user/extract-text.html#why-text-extraction-is-hard), [conditional OCR](https://pypdf.readthedocs.io/en/stable/user/extract-text.html#ocr-vs-text-extraction), and [page coordinates and rendering](https://github.com/jsvine/pdfplumber#the-pdfplumberpage-class).

## Execution boundary

The implemented local Python controller drives the desktop-bundled Codex app-server. Python owns source acquisition, PDF preparation, storage, source validation, calculation records, coverage and execution limits. Codex reasons over the frozen packet using client-owned tools. The personal website is still planned. See [Codex integration](codex-integration.md) for the exact protocol, tool contracts and cancellation/resume behavior.

The tools provide bounded financial/context queries, source lookup, full-page report reads, literal search, original PDF images, saved assumptions and Decimal calculations. Calculations apply stored scales once and enforce compatible units/currencies. Known historical valuation ratios have dimensionless multiple units; unresolved KPI units/currencies remain visible and cannot silently become calculation inputs. Initialization verifies database/blob and PDF/prepared hashes and checks every report-derived observation against its source PDF hash and page bounds.

The controller records a research round only after mandatory reading. It closes research after ten rounds, two rounds without newly cited retrieved evidence, or explicit finalization. Novel evidence IDs are a practical progress proxy, not proof of useful reasoning. A two-hour outer deadline and bounded finalization calls prevent indefinite operation. Cancellation uses an interrupt request followed by bounded process shutdown; resume checks the frozen evidence and prompt identities and restores saved tool state.

The installed desktop-bundled executable `/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex` (0.165.0-alpha.1.2) runs exact GPT-6.1 Sol/high with existing Codex authentication. Real smoke checks verified financial queries, report text, original images and scaled arithmetic. A live turn was deliberately cancelled and resumed on the same durable thread. These establish the tested lifecycle and tool path, not full-walkthrough completion. Dynamic tools remain an experimental app-server interface and need rechecking when the binary changes. [Implementation and validation record](codex-integration.md#protocol-evidence-and-validation).

The older PATH Codex executable (0.153.2) rejected this model route. The original comparison therefore used pi 1.4.0 and GPT-6.1 Sol/high; those results remain preserved under their original harness. Pi is still an alternative, but the current implementation uses Codex.

The planned local website should expose retrieved documents, selected inputs, explicit formulas and outputs, run status and saved results. It can display the controller's saved records without rerunning analysis. No website or automatic daily scheduler is implemented. Existing harness authentication is used without reading or displaying credential values; the Börsdata key is used only by acquisition.

## Verified acquisition and mapping

The original source-preservation and retrieval proposal is now the accepted starting specification. Its referenced `data/bf-retrieval-landscape/report.md` was absent when inspected; the three linked primary sources were reviewed independently. The original PDFs came from Gränges' issuer IR archive. A separate MFN discovery check found all eight releases, but MFN attachment downloads returned HTTP 403, leaving attachment byte identity unverified.

The key is configured in ignored `.env.local`; quotes around it are optional. The first Python `urllib` request received HTTP 403 / Error 1010. Python `requests` succeeded with the configured key against `apiservice.borsdata.se`. The precise Cloudflare matching rule is unknown. The [context fetcher](../scripts/fetch_borsdata_context.py) disables redirects, excludes credentials from logs, bounds retries and writes source hashes plus safe diagnostics.

The completed [2026-11-01 acquisition](../data/borsdata/context/426/20261101T173056Z/manifest.json) saved **86 HTTP 200 responses**. They include 14 annual, 40 quarterly and 40 R12 report rows, 3,036 daily prices, annual/quarter/R12 KPI summaries, selected valuation and operating KPI histories, report/KPI definitions, classifications, insider/short/buyback data and calendars. An empty company result is retained as evidence of the response. This verifies the requested routes for Gränges and the configured account; multiissuer ingestion, small-company coverage and every documented endpoint combination remain outside this check. Batch KPI history normalization is not implemented.

The [mapping resolution](research/granges-mapping-resolution.md) and [82 selected report facts](../data/granges-walkthrough/reconciled-facts.json) separate reported/adjusted EBIT, statutory/company cash flow, lease-excluding debt, minority ownership, and EPS/share bases. Reported Q3 EBIT is 546 MSEK; adjusted EBIT is 596 MSEK. The annual report's 2025 closing-price range matches the daily price series. The latest saved close is 172.20 SEK on 2026-10-30. Provider report-price fields show a report-date correspondence in the saved sample and must not be assumed to be calendar-year averages. Remaining rounding, ratio/window and share-basis differences are retained without blocking calculations from explicitly selected inputs.

Current treasury holdings, future dilution, minority fair value and valuation convention choices still require explicit assumptions where material. The observed provider EV convention excludes leases and minority interests in the checked identities; a valuation bridge must make its own convention visible. These bounded findings do not establish universal provider formulas. Current revised history is not a point-in-time backtest.

The documented [shorts dataset](https://github.com/Borsdata-Sweden/API/wiki/Holdings) supplies instrument-level positions, not a proven complete transaction history. Documented API coverage also does not establish parity with all website data. The store preserves source-specific observations and versions rather than silently filling such gaps.

Acquisition and packet preparation commands are in the [README](../README.md#acquire-and-prepare-evidence). The canonical local packet is `data/granges-codex/packet-20261101`; rebuilding requires a new destination. Preparation verifies PDF and prepared-file hashes, validates every report fact's hash/page link and freezes the database with its required raw blobs.

## Original report comparison and new financial walkthrough

Original pi report comparison: completed. Gränges, Börsdata ID 426 and ticker GRNG, was the first technical candidate. Eight originals (921 PDF pages) are saved with hashes and publication/source metadata. Candidate questions and the independent reference rubric were frozen before model runs. Both used GPT-6.1 Sol through pi; both supplied all prepared text pages and scored 40/40. This is a bounded tie, not a general quality-equivalence claim. See [results](granges-walkthrough-results.md), [protocol](../data/granges-walkthrough/protocol.md) and [source manifest](../data/granges-walkthrough/source-manifest.json).

The [issuer report archive](https://www.granges.com/investors/reports-and-presentations/) links annual reports for 2021–2025 and Q1, half-year and Q3 reports for 2026. The 2025 annual was published on 17 March 2026; Q3 2026 on 22 October 2026. The 2023 and 2024 annual links were verified, but browser size limits prevented content inspection. MFN carries the [2025 annual release](https://mfn.se/a/granges/annual-and-sustainability-report-2025.iframe) and [Q3 2026 release](https://mfn.se/a/granges/granges-q3-interim-report-2026-record-earnings-and-improved-cash-flow). MFN classifies Gränges as Large Cap, so this example does not validate coverage for smaller issuers.

Accepted interim reading policy: retain the five-year interim archive, require reading each interim since the latest annual reporting year-end, and use older interims for targeted historical questions. For this candidate, the mandatory starting set is eight reports: annual reports for 2021–2025 plus Q1, half-year and Q3 2026. The later Q3 report covers a May 2026 fire and production disruption absent from the 2025 annual; this demonstrates the current-evidence value of interim reports. [IAS 34](https://www.ifrs.org/issued-standards/list-of-standards/ias-34-interim-financial-reporting/) describes interims as updates on the latest annual financial statements.

The original report comparison used these acceptance checks:

1. Acquire and preserve the agreed inputs for one company. Record missing source data explicitly. Its report-only corpus did not require a database.
2. Prepare the required annual reports and the agreed interim set with page references and visual fallback. Account for every required page and inspect representative financial tables, including headers, units and footnotes.
3. Prepare a common set of analysis questions and independently locate their supporting evidence before comparing model outputs. Include a cross-year question, a table/footnote question and a missing or conflicting input when the selected company's material supports these cases.
4. Compare supplying more report content upfront with sequential report reads over the identical saved evidence. Keep the model, questions and minimum five-annual-report coverage constant. If the upfront variant cannot fit, record that limit rather than silently truncating it.
5. Compare supported answers, important omissions, cited figures' periods/units/sources, unresolved extraction failures and completed reading coverage. Record usage and time as secondary diagnostics. One company establishes feasibility and exposes failures; it does not establish universal superiority of a retrieval policy.

The full Codex financial walkthrough completed using frozen Börsdata observations and report facts alongside the eight required reports. It delivered all 921 pages, saved 326 calculations and closed research after four rounds. Independent arithmetic checks and a read-only review support the bounded result; future cash conversion, multiples and ownership-value proxies remain assumptions. See the [results](granges-codex-walkthrough.md). Successful cancellation/resume smoke checks remain separate lifecycle evidence. Automatic refresh and a general multiissuer valuation methodology remain open.

## Remaining decisions and validation

- Complete and assess the Codex financial walkthrough: required reading, cited periods/units, material contradictions, explicit assumptions and reproducible calculations.
- Test more issuers, including smaller companies, before claiming broader source coverage or ingestion reliability.
- Choose the permanent initial-context policy from observed analysis quality. The original pi tie does not establish universal equivalence between upfront and tool-read context.
- Improve PDF extraction and define escalation for pages needing OCR; no general OCR pipeline exists yet.
- Build the personal website around saved evidence, inputs, calculations and results.
- Decide whether refreshed evidence should trigger analysis and whether to enable automatic refresh within the daily limit.
- Evaluate whether the evidence-ID progress proxy adequately bounds productive follow-up research.

The implemented storage and harness are a starting foundation. Unresolved source definitions remain attached to the affected input; unrelated analysis can continue with sourced selections and explicit scenario assumptions.

# Frozen Börsdata development corpus

Initially reviewed 3 November 2026 against public Börsdata documentation and this repository. That feasibility review made no provider requests, account changes or new valuations; the subsequent capture is recorded separately.

**Project update, 3 November 2026:** the user confirmed that data-use permission is resolved and instructed capture to proceed. The permissions research below records the earlier uncertainty; it is no longer a project blocker. The API capture plan now includes the documented dividend-yield history and five current screener snapshots, for 97 requests per issuer. Original PDFs and financial reconciliation remain separate coverage requirements.

## Verdict

**A frozen set of 10–30 companies can support most remaining development.** Acquisition is separate from packet preparation and read-only analysis. Field reconciliation, calculations, saved results and interface behavior can be developed against dated evidence without fresh API calls. The initial review did not establish post-subscription use rights; the user has since confirmed that permission is settled for this project. [Acquisition plan](../../scripts/fetch_borsdata_context.py), [packet preparation](../../scripts/prepare_codex_packet.py), [read-only evidence tools](../../betaforge/tools.py).

## Captured API snapshot

On 3 November 2026, the corpus expanded from ten to **thirty distinct operating-company issuers**: **2,910/2,910 planned responses**, 2,620 source blobs and 724,710 current observations. Actual coverage is 7–20 annual periods per issuer and 101,708 price rows in total. The original ten captures remain unchanged; their [initial release](https://github.com/KapKnudz/betaforge-research-private/releases/tag/development-corpus-2026-11-03) is retained separately.

The [expanded private release](https://github.com/KapKnudz/betaforge-research-private/releases/tag/development-corpus-30-2026-11-03) preserves the raw captures, frozen SQLite store, exact selection/watchlist and verification receipts. Request-plan, issuer/KPI-basis and hash checks, database integrity/foreign keys, a clean restore against the reviewed file inventory, and exact checksums of all seven downloaded original assets pass. All 138,506 stored KPI metadata links were checked; 64,905 percentage/MCURR unit checks had zero mismatches. The [offline verifier](../../scripts/verify_development_corpus.py) ingests captures chronologically. Bounded transport retries recovered temporary connection failures; incomplete attempts were reacquired before freezing.

This is an API-only corpus. Original PDFs and report-level accounting reconciliation remain separate work. Current screener responses retain their raw context; format and metadata checks do not establish financial meaning or reconstruct every normalized value from its source. Unknown formats and historical currency/continuity cases remain explicitly unreviewed. Frozen evidence supports offline mapping, calculation and interface work; changed-provider and fresh-data checks still need live access before current use.

## What can be frozen

| Family | Documented coverage and limits |
|---|---|
| Financial statements | Up to 20 annual and 40 quarterly/R12 observations. R12 is based on the last four quarters; annual responses may include a latest R12 row. Original/converted currency modes differ. These maxima do not guarantee that every issuer has that much history. [Reports](https://github.com/Borsdata-Sweden/API/wiki/Reports). |
| Prices | Up to 20 years of end-of-day prices, with no intraday feed. [Stockprice](https://github.com/Borsdata-Sweden/API/wiki/Stockprice), [history limits](https://github.com/Borsdata-Sweden/API/wiki/20-year-history). |
| Historical KPIs | Only a subset of screener metrics has history. Report type and price basis are separate dimensions; keep the supported combinations and metadata. [KPI History](https://github.com/Borsdata-Sweden/API/wiki/KPI-History). |
| Ownership/events | Insider data is described as ten years; short-selling is one row per instrument, rather than a complete historical ledger. Holdings are Nordic-only. Calendars return old/new report and dividend dates. [Holdings](https://github.com/Borsdata-Sweden/API/wiki/Holdings), [Calendar](https://github.com/Borsdata-Sweden/API/wiki/Calendar). |
| Original reports | The numeric statement API does not replace original PDFs and page-linked narrative evidence. The current packet builder takes a separate prepared report corpus. Preserve the five available annuals and relevant interims required by the project, including originals and preparation hashes. [Packet interface](../../scripts/prepare_codex_packet.py), [retrieval contract](../retrieval-design.md). |

Define “complete” as **all available fields and agreed dataset families, with a recorded coverage manifest**, not every possible screener permutation. Empty, unavailable and failed datasets need separate states. The updated unbatched plan has 97 requests per instrument: approximately 970–2,910 for 10–30 instruments before retries. It repeats some global lookups; no batching redesign is needed to begin. The provider documents 100 calls per ten seconds and requests fewer than 10,000 daily calls. Some routes accept up to 50 instruments, but batch normalization must be supported before using those responses. [Current plan](../../scripts/fetch_borsdata_context.py#L29), [rate guidance](https://github.com/Borsdata-Sweden/API#rate-limits), [array routes](https://github.com/Borsdata-Sweden/API/wiki/API-Array-calls), [normalization](../../betaforge/storage.py).

## Initial permissions review

The API information page permits downloading data for personal calculations and publishing one's own analysis results. It also requires an API-use agreement and prohibits redistribution/sharing of API data and external systems, homepages or widgets displaying it. Its wording does not explicitly distinguish a private localhost dashboard, a private cloud backup or an AI processor. Do not infer either automatic approval or a blanket ban on all personal tooling from that ambiguity. [API page, “Are there any restrictions?”](https://borsdata.se/en/info/api/api_page).

The membership terms describe private download/processing/analysis rights and end subscription access at the billing-period boundary. They do **not explicitly settle post-cancellation retention/reuse** in the public text reviewed. The displayed terms date is 7 February 2025. The user's signed API agreement may contain additional conditions. An engineering policy to retain data for the life of the project is not a licence grant. [Membership terms, sections 3.5, 5 and 6](https://borsdata.se/en/terms), [Swedish terms](https://borsdata.se/terms).

The initial review recommended clarifying retention after paid access ends, personal offline use, local display, private backup and AI processing. The user subsequently confirmed that permission is resolved and instructed the project to proceed. The paragraphs above retain the original public-source research, rather than an outstanding approval request. [API restrictions](https://borsdata.se/en/info/api/api_page).

The official API repository says new REST access moved to PRO+ on 1 February 2025. Some other product-page examples still mention PRO; the user's actual account/agreement must govern access rather than an assumed plan name. [Official API repository](https://github.com/Borsdata-Sweden/API#important-changes-from-1-feb-2025).

## Recommended development sequence

1. Select 10–30 distinct issuers from the maintained list, checking share-class duplicates. Include capital-intensive, capital-light, acquisitive/SBC-heavy and high-working-capital businesses, plus currency/fiscal-period and missing-data cases. This is a proposed test design, not verified coverage.
2. Capture one dated, immutable development corpus while access is available, with raw responses, definitions, report PDFs/text, actual earliest/latest periods, missingness, errors and hashes. Deeply reconcile three to five materially different companies first; retain the others as broader regression cases. Reuse the existing store/freeze/archive flow. [Storage and mapping contract](borsdata-retrieval-storage.md), [private archival workflow](../research-handoff.md).
3. Develop mappings, deterministic calculations and the saved-result interface against frozen inputs, with synthetic fixtures for additional edge cases. Display “frozen as of” dates separately from the valuation date; opening a saved page must not imply a refresh. [Analysis policy](../analysis-policy.md), [saved-result integration](../codex-integration.md).
4. Keep a small refreshed comparison set for testing changed reports, revisions and price/event updates before live use. Frozen data cannot test future provider changes or support a fresh current-price valuation indefinitely. A current historical series also does not establish what information was available at each past date. [Revision semantics](borsdata-retrieval-storage.md#identity-revisions-and-retention), [provider timing](https://github.com/Borsdata-Sweden/API/wiki/Stockprice).

**Recommendation:** use a frozen corpus for development. The user has confirmed that the applicable use permission is settled. Verify the captured API data and preserve explicit report/mapping gaps; current live-data checks can resume before live use. The original feasibility review did not itself collect data or change the subscription.

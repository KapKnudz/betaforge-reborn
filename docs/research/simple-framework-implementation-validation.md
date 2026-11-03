# Simple financial framework: execution record

3 November 2026. This records implementation checks, separately from the [independent read-only review](simple-framework-implementation-review.md). The original Gränges packet and full model run were preserved.

## What changed

The [adopted policy](../analysis-policy.md) combines the supplied case philosophy with the user's earnings-quality principles. The [catalogue](../calculations.md) defines every valuation/diagnostic formula, units, assumptions and limits. New packets freeze both documents and selected source context. The primary valuation remains forward EV/EBIT, with one operating-driver formula and one complete bridge per case. A full reverse DCF remains unimplemented; market-implied EBIT is a separately labeled conditional check.

## Saved deterministic review

Final artifact: `data/financial-reviews/granges-20261103-quality-v2/review.{json,md}`. Source evidence is in the private research bundle; the [40 additional facts and three notes](../../data/granges-walkthrough/quality-facts-20261103.json) are compact, versioned extractions with PDF hashes/pages/quotes.

| Check | Result and scope |
|---|---|
| Preserve scenarios | All six original bear/base/bull target and present-value comparisons match exactly. The new calculation path uses one grouped bridge per case. This is arithmetic continuity, not new evidence for the forecasts. |
| Financial quality | Reported margin history, qualified group incremental margins, actual trade balances relative to sales, invested capital, explicit operating ROIC, cash bridge, diluted P/E and SBC/supplier-finance notes. ROIC is 8.5751% under a 20% analyst operating-tax proxy, with 19%/25% sensitivities. |
| Cash gaps | FY2025 CFO less cash capex and gross outside-CFO interest is SEK 289m before lease principal/dividends. Exact principal remains missing, so the final post-lease conversion ratio is unavailable. No ownership-mismatched FCF yield is inferred. |
| Probabilities | Explicitly supplied 25/55/20 replays the existing subjective conditional proposal. Weighted PV is SEK 155.3838, future target SEK 195.5618 and expected-cash-flow IRR 6.2264%. These are not universal weights or calibrated full-distribution expectations. |
| Market comparison | Verified historical SIXRX gross CAGR is 11.6078% from rounded public levels; difference versus candidate IRR is −5.3814 percentage points. The three-year candidate and ten-year historical index have different interpretation and reinvestment assumptions. The comparison does not change the original 10% discount assumption. [Source method](sixrx-benchmark.md). |

## New packet and live Codex integration

`data/granges-codex/packet-quality-20261103` freezes the adopted policy/catalogue, eight reports/921 required pages, saved Börsdata responses and the 40 extra report facts. It also freezes six industry-context files and eight market-context files, including the exact SIXRX calculation script. A separate build database preserves the original canonical store and packet. Original PDF/prepared hashes, database/blob identities, both policy hashes and all selected context-file hashes passed initialization.

Live smoke: `data/granges-codex/runs/20261103-quality-smoke`.

- Exact model `gpt-6.1-sol`, high reasoning; `codex-cli 0.166.0-alpha.5.1`.
- Status `smoke_completed`; 43.232 seconds; 13 successful tool calls; zero tool errors and unexpected native tools.
- Verified policy/formula delivery, saved financial queries, original image interpretation, source-scale arithmetic and a grouped R12 reported EBIT-margin result of 5.6113903% with a named output reference.
- PDF image: Q3 2026 physical p21, reported EBIT 546 MSEK and adjusted EBIT 596 MSEK. Poppler 26.05.0 was supplied through the explicit executable override.
- Only 16 text pages were delivered. Full reading was waived for the integration smoke; this is not a completed new valuation. The original completed run retains its 921/921-page record.

## Automated checks

All **78 tests passed** under the project virtual environment (`.venv/bin/python -m unittest discover -s tests -q`). Coverage includes formula edge cases, exact original-case parity, source/quote/hash validation, ownership-scope options, units/scales, financial periods, implementation identity on resume, archive mutation/omission failures and benchmark parsing. Diff whitespace checks passed. These checks establish the tested behavior; they do not audit every source number or predict investment outcomes.

## Preservation and limits

Code/documents live on `feat/granges-walkthrough`. The [baseline private release](https://github.com/KapKnudz/betaforge-reborn/releases/tag/research-baseline-2026-11-03) targets commit `5678dd1` and preserves 432 exact files. GitHub's asset digest and a fresh download matched the local SHA256. A clean clone restored both evidence databases and their 87 blobs each, and rendered the saved completed result without fetching data or calling a model. See [handoff verification](../research-handoff.md#verified-private-checkpoint).

The baseline bundle predates the new quality packet, review and benchmarks. The archive selection now explicitly includes those new directories when present; a separate versioned implementation bundle preserves them. No physical second Mac or live Codex conversation transfer was tested. Harmonized peer financials and an end-to-end full valuation under the new policy remain outside this execution check.

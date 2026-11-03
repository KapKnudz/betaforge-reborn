# Simpler investment analysis: review and minimum plan

Reviewed 3 November 2026. **Review complete; changes below are proposed.** No valuation, model instructions, application code or accepted philosophy was changed. No tests, company-data acquisition, model runs, commits or pushes were started. Public benchmark-source research and read-only repository inspection support this assessment.

This note records the completed pre-implementation review. The user subsequently authorized its priorities. Current rules are in the adopted [analysis policy](../analysis-policy.md) and [calculation catalogue](../calculations.md); preservation is recorded in [the handoff guide](../research-handoff.md). SIXRX superseded the earlier Investor B benchmark. The original Gränges result remains frozen.

The user confirmed **Macs first** and **exact source evidence plus saved analyses** for workstation handoff. Git should preserve source and documents; separate private frozen bundles should preserve research bytes. The bundle destination and live-conversation migration remain open.

## Recommendation

Keep the existing operating EV/EBIT valuation and evidence pipeline. Make the economic reasoning smaller and more visible, add the few missing earnings-quality checks, and preserve the work in version control before expanding it. The current architecture does not justify a new valuation engine, another financial-data pipeline or an extensive ratio catalogue. [Financial coverage review, Overall verdict and Architecture](simple-financial-analysis-coverage.md#overall-verdict).

The current central model already has a small set of economic assumptions: volume, EBIT per tonne, a multiple, retained cash and an equity bridge. However, its execution is unnecessarily granular: 326 calculation records include 82 display conversions, repeated bridges and superseded work. Simplification should remove that repetition as well as shorten the report. [Calculation guide, Why the count is large and Groups](granges-calculation-guide.md#why-the-count-is-large).

## What the current Gränges case establishes

| Finding | Bounded verdict and reasoning | Missing evidence or limit |
|---|---|---|
| The primary valuation can remain | **Keep.** It forecasts volume and operating profit per tonne, applies EV/EBIT, deducts explicit claims and values the equity/dividends over three years. Its assumptions can be stated on one page. [Saved answer section 9](../../data/granges-codex/runs/20261101-full/answer.md#9-three-year-operating-valuation). | Future profit per tonne, the multiple and retained cash remain judgments. The simple structure does not prove those forecasts. |
| The arithmetic count indicates unnecessary work | **Simplify actual execution.** Presentation conversions and repeated initial/final bridges inflate the audit; dimensional/source checks remain useful. [Calculation guide, Which calculations support the final answer?](granges-calculation-guide.md#which-calculations-support-the-final-answer); [calculator](../../betaforge/tools.py#L301). | Hiding the log alone would not address the user's concern. Do not delete source provenance or economically real debt/minority claims to reduce the count. |
| Cash quality is the most useful financial improvement | **Prioritize.** The report identifies weak cash generation, but forecasts retained cash as a scalar assumption after distributions and all other cash needs. A compact cash bridge can directly challenge that assumption. [Saved answer sections 6 and 9, Cash conversion and distributions](../../data/granges-codex/runs/20261101-full/answer.md#cash-conversion-and-distributions). | Sustainable capex, operating working-capital requirements and future cash conversion are not established. |
| The philosophy is fully enforced | **Not established.** Selected principles entered the prompt, but neither the full supplied draft nor a versioned set of adopted rules was a runtime input. The agreed Investor B return hurdle was not measured; 10% was an illustrative rate. [Philosophy application review, Material gaps](granges-philosophy-application.md#material-gaps-in-the-agreed-policy). | A few additional ratios do not fix policy provenance or the missing benchmark comparison. |
| More valuation cross-checks add independent conviction | **Limited.** The EBITDA cross-check shares EBIT, debt and ownership assumptions, while adding depreciation and another multiple. [Saved answer section 9, EBITDA cross-check](../../data/granges-codex/runs/20261101-full/answer.md#ebitda-cross-check). | It does not resolve maintenance-capex or cash-conversion uncertainty. Make it optional rather than a default second valuation. |

The frozen present-value cases of approximately 52/168/249 SEK/share, and the separately proposed probability weights, should remain unchanged during this review. A diagnostic finding should change a future valuation only through a stated revision to an input or assumption. [Original answer, Executive assessment](../../data/granges-codex/runs/20261101-full/answer.md#executive-assessment); [probability proposal](scenario-probabilities-proposal.md#provisional-analyst-weights-for-gränges).

## Financial metrics: reuse first, add only a useful insight

| Requested insight | Existing coverage | Minimum proposal |
|---|---|---|
| Incremental EBIT margin | Comparable sales and EBIT are stored; no named recurring output. | Add `change in EBIT / change in revenue` only for comparable periods and a meaningful denominator. Show the two changes and the earnings basis. Flag scope changes, FX, exceptional items and pass-through revenue. For Gränges, retain volume and EBIT/tonne as the primary explanation. |
| EBIT margin | Sales, reported EBIT and provider operating-margin KPI 29 are acquired. | Expose the company's five-to-ten-year trend. Keep reported/adjusted bases explicit; no new endpoint is needed. |
| ROIC | Provider KPI 37 is acquired, but its unit/definition is unresolved; issuer ROCE is already discussed. | Verify provider ROIC or derive one simple, consistently defined after-tax return on average invested capital. Do not rename ROCE as ROIC. Align taxes, cash, leases, goodwill and capital averaging before peer comparison. |
| FCF conversion | Detailed cash reconciliations exist; there is no standardized earnings-conversion output. Gränges' own cash-conversion APM uses operating cash flow/adjusted EBITDA. | Start with a cash bridge, then one explicitly named conversion ratio with aligned period and ownership scope. Working-capital movement is already inside statutory CFO: expose that component or reverse it before normalization, never subtract it again. For the debt forecast, carry the bridge through cash capex, financing-classified interest, minority distributions and common dividends to retained cash. Do not relabel issuer cash conversion or provider CFO-plus-total-investing-flow as sustainable owner cash flow. |
| Receivables, inventory and payables | Aggregate current assets/liabilities exist; operating components are not structured. | Extract a small set of balances from existing report notes when working capital is material. Use comparable sales periods and balance conventions. Never substitute total current liabilities for trade payables. Ratios to sales are indicators, not automatically inventory/payable days. |
| EV/EBIT and P/E | Already used with selected current inputs and historical provider series. | Reuse; improve clarity rather than create another implementation. Preserve enterprise-value, EPS, share and date conventions. |
| FCF yield | Provider FCF and P/FCF are acquired; a consistent yield is not defined. | Settle the cash-flow definition first. Match cash to equity with equity value, or unlevered firm cash with EV. An inverse provider P/FCF is not automatically a sustainable equity-cash yield. |
| SBC and dilution | Issued/basic/diluted shares and a generic dilution sensitivity exist. Material remuneration programs are not translated into a specific cost/share note. | Identify expense, outstanding awards, settlement method and plausible issuance from reports. Retain the economic compensation cost, explain cash-flow addbacks and future dilution, and avoid charging the same item twice. |

Evidence and row-specific limitations are in the [financial coverage review, Requested metrics](simple-financial-analysis-coverage.md#requested-metrics), including acquisition requests, metadata, storage, report facts and original report-page references.

ROIC should not be compared mechanically with the 10% equity-return assumption or the Investor B hurdle. A claim that growth creates economic value needs a comparable return-on-capital and cost-of-capital basis. Until that is available, use history and economically matched peers as quality context without asserting a precise value-creation spread. [Benchmark review, Definitions](damodaran-benchmark-assessment.md#definitions-that-can-otherwise-mislead); [planning foundation, Return hurdle](../planning/decisions.md#return-hurdle).

## Proposed philosophy addendum

Treat the user's Armitage-inspired brief as a project-design addition to the existing case-oriented philosophy, not as a verified quotation or replacement for its source synthesis. The proposed rules are:

1. Identify **three to five earnings drivers** and the evidence for each. A ratio is useful only when it helps explain a driver, business quality, cash generation or the price paid.
2. Judge operating leverage, pricing power and competitive advantage from business mechanics and observed outcomes. Revenue growth or a large accounting margin spread alone is insufficient.
3. Test growth against reinvestment, working capital, capital efficiency and cash generation. Treat stock compensation and share claims as costs of ownership.
4. Compare the company's own history first, then a small global set of economically comparable businesses, then industry context. Keep the Nordic investment universe separate from the global comparison universe.
5. Use a simple operating valuation and a few pertinent checks. EV/EBIT is the current primary method; EBITDA remains relevant for specified lender/issuer measures but is not a compulsory valuation anchor.
6. Separate **observed fact, interpretation and forecast assumption**. State what a modest disappointment would do to the thesis and name the evidence that would invalidate it.

These proposed rules complement the existing emphasis on profitable businesses, management execution, a defined horizon and a margin of safety. They do not add a quality score, fixed target margin or mechanical buy rule. [Current philosophy sections 3–8 and 11](../planning/investment-philosophy-draft.md); [philosophy application review](granges-philosophy-application.md).

## Qualitative analysis: make the existing work sharper

The report already examines investment execution, metal-price pass-through, cash weakness and invalidation evidence. Its missing structure is a short, repeatable explanation that connects those observations to the assumptions. [Saved answer sections 3–4 and 6,9–11](../../data/granges-codex/runs/20261101-full/answer.md).

For Gränges, candidate drivers are volume/utilization; fabrication pricing and product mix; scrap/material economics; cash tied up in metal and operating working capital; and reinvestment/returns. The analyst should select the three to five that matter, explain their interaction and avoid counting the same utilization benefit twice. Capacity is not sales, and metal-price pass-through is not proof of pricing power. [Saved answer sections 3,4,9](../../data/granges-codex/runs/20261101-full/answer.md#9-three-year-operating-valuation).

The concise output should include:

- A one-sentence thesis and horizon.
- Three to five drivers, each with an observed fact, interpretation and forecast assumption.
- A small historical financial-quality table and one cash bridge.
- One scenario valuation bridge, with the selected probability estimates and their uncertainty.
- One or two modest, thesis-relevant disappointment checks.
- Two or three observable conditions that would weaken or invalidate the thesis, and the next evidence to review.

This is an output proposal, not an instruction to calculate every requested ratio for every company. Detailed provenance remains accessible separately. The management section should retain a few important claims and outcomes rather than introduce a new scoring system. [Existing output and identified gaps](granges-philosophy-application.md#trace-from-philosophy-to-instructions-and-observed-behavior).

## Damodaran and global benchmarks

The supplied database is useful for industry context, not a replacement for current company-level peer research. Its catalogue reports a full update on 9 January 2026; much accounting data reflects the latest trailing period available then. HTML tables are US-only, with separate global/regional workbooks. Absolute values are generally US-dollar millions. [Official catalogue](https://pages.stern.nyu.edu/adamodar/New_Home_Page/datacurrent.html).

Start with four relevant families: **operating margins/SBC, working capital, returns on capital, and reinvestment/capital intensity**. Add EV/EBIT context only for a concrete multiple question. Inspect selected global workbook columns and definitions before using them. This review verified links and HTML/definitions; it did not parse global workbook bodies. [Benchmark assessment, Minimal dataset selection](damodaran-benchmark-assessment.md#minimal-dataset-selection).

Choose a few global peers by products, customers, pricing/pass-through, asset intensity and reinvestment needs. Country becomes relevant through actual tax, regulation, accounting, market structure or operating exposure. Do not use a broad industry row as an automatic peer valuation or assume a sector aggregate is a median. A first version needs a short reasoned peer list, not a global screening engine. Use SEC EDGAR only when an identified peer-data gap justifies it. [Benchmark assessment, Definitions and Global peers](damodaran-benchmark-assessment.md#global-peers-and-optional-sec-gap-filling).

## Prioritized minimum implementation plan

| Priority | Proposed work | Reuse and completion criterion |
|---|---|---|
| **P0 — Preserve the work** | Review and checkpoint source, tests, README, glossary, accepted decisions, philosophy inputs and research notes in the existing private GitHub repository. Also inventory and privately copy/archive the existing frozen packet, completed Codex run and earlier pi comparison results selected for preservation. Record an archive digest covering exact inputs and outputs; choose a small portable document index and complete dependency/setup instructions. | Existing repository and evidence; explicit file inventory, no blanket workspace add. A fresh Mac clone can find the authoritative documents. Private archives preserve research beyond one Mac; packet input hashes alone do not identify every answer or trace. The archive destination remains to be chosen. [Portability review, First checkpoint and Minimal workflow](version-control-portability-review.md#recommended-first-checkpoint). |
| **P1 — Simplify the analysis contract** | Turn the approved financial principles into a short versioned policy the analyst actually receives. Specify three to five drivers, few diagnostics, fact/interpretation/assumption separation and one primary formula per case. Remove display conversions from economic calculations, reuse shared values and make the EBITDA valuation optional. | Existing packet, calculator and renderer. A reader can reconstruct a case from one assumption table and one bridge, with fewer repeated operations as well as a shorter output. [Architecture coverage](simple-financial-analysis-coverage.md#architecture-and-reuse). |
| **P1 — Add the useful quality checks** | Expose existing EBIT-margin history; add qualified incremental margin, a cash bridge and a short SBC/share-cost note. Extract only material missing working-capital facts from saved reports. Verify ROIC definitions and cash-flow scope before presenting comparable ROIC, conversion or yield. | Existing Börsdata captures, report-fact storage and numeric safeguards. Each displayed metric has an explicit formula, period, basis and source; unavailable or incomparable figures stay visible as gaps. [Requested metrics](simple-financial-analysis-coverage.md#requested-metrics). |
| **P2 — Add narrow benchmark context** | Select a few economic peers and the needed Damodaran families/industry rows. Preserve source dates, definitions, sample/aggregation and adjustments. | Existing evidence/dataset approach; no new collector platform. A reviewer can explain why each peer/industry row is relevant. [Benchmark recommendation](damodaran-benchmark-assessment.md#overall-recommendation-and-missing-evidence). |
| **P2 — Complete the investment decision inputs** | Measure the already-agreed Investor B hurdle with explicit total-return conventions; make return attribution and the probability proposal visible. Distinguish discounting, opportunity-cost comparison and conditional going-concern scenario weights. | Existing planning and probability notes. No new hurdle identity, distribution calibration or automatic investment verdict is assumed. [Return hurdle](../planning/decisions.md#return-hurdle); [probability limits](scenario-probabilities-proposal.md#return-risk-and-the-agreed-benchmark). |
| **P2 — Verify exact Mac handoff** | Restore a frozen packet and saved result on a second Mac, verify identities, then render the result without reacquisition or a model rerun. Carry the canonical store with its blobs when transferring current watchlist state. | Existing freeze/packet design. Same-thread live Codex resume remains a separate unproved capability. [Portability review, Minimal workflow](version-control-portability-review.md#minimal-workstation-workflow). |

Priorities describe implementation order after review approval; they are not changes made by this document. Do not add a new DCF, simulation system, universal score, bulk industry ingestion or additional provider integration as part of this minimum plan.

## GitHub and exact workstation handoff

As inspected on 3 November, Git tracks only the two original planning documents, and remote `main` remains at the initial commit. Code, tests, later documentation and ignore rules are still local. The repository is private. [Portability review, Git inventory](version-control-portability-review.md#git-inventory).

Recommended separation:

- **Git:** source, tests, setup/dependency declarations, README, glossary, approved policy/decisions, research notes, compact manifests and selected final report/assumption documents worth comparing over time.
- **Private research bundles:** exact raw/prepared PDFs, provider responses, database plus blobs, frozen packet and saved run. The current packet/run are approximately 100 MB/79 MB. These need a private versioned archive, not ordinary Git history.
- **Each Mac:** its own environment variables, Börsdata credential and Codex authentication. The current executable override can be reused; dependency setup still needs Python/PDF prerequisites and a verified Codex build.

Use repository-relative navigational links; preserve original paths inside historical provenance records. Export quiescent/frozen evidence through the existing snapshot approach rather than treating a live SQLite file as a document to edit concurrently on both Macs. The archive location still needs selection. Viewing exact completed research is the first handoff target; active conversation migration is not yet verified. [Portability review, Findings and Minimal workstation workflow](version-control-portability-review.md#findings).

## Validation proposed for the later changes

Use a small set of meaningful acceptance checks: formulas and source selections match identified report lines; ROIC/ROCE and cash-flow definitions remain distinct; zero/small revenue changes and loss periods are interpreted correctly; SBC is neither free nor charged twice; repeated formatting does not create extra economic calculations; and the preserved Gränges valuation changes only through an explicit approved input/method revision. Then verify a second-Mac restore against existing hashes. No new test or valuation run was necessary for this read-only first deliverable. [Existing safeguards and missing coverage](simple-financial-analysis-coverage.md); [handoff limits](version-control-portability-review.md).

The broader reliability of multi-company metrics, selected peers, forecasts and cross-workstation live resume remains unproved. The present review supports the small plan above; it does not establish a revised Gränges fair value or a statistically calibrated investment process.

## Independent read-only challenge

An independent reviewer supported retaining the existing EV/EBIT/evidence approach and simplifying actual repeated work, rather than only hiding the audit. The reviewer requested three clarifications now incorporated: P0 includes exact research preservation beyond Git; working-capital cash movement must not be deducted twice and the cash bridge must reach retained cash if it supports the debt forecast; and the supplied philosophy draft must remain distinct from the adopted rules. Evidence is in [the calculation guide](granges-calculation-guide.md#groups-and-their-uses), [financial coverage](simple-financial-analysis-coverage.md#requested-metrics), [planning philosophy](../planning/decisions.md#philosophy) and [portability review](version-control-portability-review.md#minimal-workstation-workflow).

The bounded verdict is that this is a suitable minimum enhancement plan, with no remaining material financial-definition or source error identified in the reviewed plan. Global workbook contents, actual peers, financial metric definitions and second-Mac restoration still need the stated checks before implementation claims are made. The reviewer made no edits, tests, provider requests, model/valuation runs, waivers or merges.

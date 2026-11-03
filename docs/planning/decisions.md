# Betaforge: adopted planning decisions

Updated 3 November 2026. This records current decisions. The [analysis policy](../analysis-policy.md) and [calculation catalogue](../calculations.md) define the rules frozen into new analysis packets; dated research notes retain their evidence and proposal status.

## Destination and scope

Build a private investment-research tool, eventually with a local website. After the Gränges walkthrough and financial-framework review, the user authorized implementation in priority order on 3 November 2026. Preserve the original evidence and valuation while simplifying future analysis. See the [minimum enhancement plan](../../examples/granges/docs/research/simple-investment-framework-review.md).

The website should provide a shared view of progress and analysis, including company lookup by name or ID, visible company data and calculations, and an evidence-backed investment judgment with bear, base and bull ranges over two to three years. Forward EV/EBIT scenarios are the adopted valuation; a true reverse DCF is an optional future addition. The exact first page and its contents remain to be specified.

The product is initially for one person's own use. Python acquisition/preparation, immutable source files, SQLite evidence, frozen packets and Codex tools are implemented. Acquisition is separate from what the analyst reads; a saved result does not rerun the analyst. A complete website, automated refresh and general multiissuer production workflow remain future work. See [ADR 0001](../adr/0001-persist-company-evidence.md), [ADR 0002](../adr/0002-local-evidence-storage.md), [retrieval design](../retrieval-design.md) and [Codex integration](../codex-integration.md).

## Research focus

- Swedish listed companies first.
- Normally profitable businesses.
- Roughly SEK 300 million–10 billion market capitalization, as a research focus rather than an automatic exclusion rule.
- The motivation is lower analyst coverage and a possible informational edge, not an assumption that excess returns are guaranteed.

## Philosophy

The [unchanged investment-philosophy draft](investment-philosophy-draft.md) remains a supplied synthesis of Petter Hedborg's investment approach. The user's Armitage-inspired principles add earnings-quality, cash, capital-efficiency and compensation discipline. Neither is represented as an authenticated quotation or complete doctrine of either investor.

The adopted project interpretation is the short [analysis policy](../analysis-policy.md): a falsifiable two-to-three-year case, three to five earnings drivers, business quality, management execution, cash-backed earnings, defensible valuation and disconfirming evidence. Separate facts, interpretations and assumptions. Suggested scores and thresholds in the supplied draft are not adopted, and extensive ownership analysis is not a compulsory checklist.

New packets freeze the policy and calculation catalogue with relative paths and SHA256 hashes. Historical packets retain their original instructions and results.

Business quality and investment attractiveness at today's price are separate judgments. An excellent business is not currently investable when its price demands performance the outlook does not support.

## Valuation roles

The primary model is a simple forward operating EV/EBIT scenario approach:

- revenue growth;
- EBIT-margin development;
- a defensible EV/EBIT multiple;
- net debt/cash and share-count effects in the equity and per-share valuation.

For some businesses, a company-specific equation such as sales volume multiplied by EBIT per tonne is more useful than nominal revenue multiplied by margin. Show the full enterprise-to-common-equity bridge, forecast shares, future target, present value and dividends explicitly.

P/E and a properly scoped FCF yield are sanity checks. EV/EBITDA valuation is optional; it can remain relevant to an issuer/lender leverage convention. A related multiple using the same forecasts is not independent confirmation.

Market-implied EBIT is a complementary backward check under stated assumptions. A full reverse DCF remains a separate, unimplemented cash-flow model and must not be implied by that check. No simulation system, universal quality score or automatic industry-multiple valuation is required. Detailed formulas and non-use conditions are in the [catalogue](../calculations.md).

## Return hurdle

The candidate statistic is **IRR of probability-weighted cash flows**. Weight each modeled dividend/terminal payment at its date, then solve for the annual rate equating those cash flows with the starting share price. It must exceed the measured benchmark hurdle before a hurdle-pass claim. Do not average scenario IRRs or annualize only expected terminal wealth.

The user selected **SIX Return Index (SIXRX)** as the primary reference: trailing ten-year annualized total return with reinvested dividends, measured as of the analysis date. This broad-market opportunity-cost reference is not a forecast of the index's future return or automatically the company's discount rate. The earlier Investor AB B reference is superseded as a historical prior decision. Do not silently substitute another index if SIXRX data is unavailable. No fixed universal hurdle rate is adopted; measure the historical index return for the selected analysis date. The [dated example measurement](../../examples/granges/docs/research/sixrx-benchmark.md) does not set the rate for future analyses, and an example discount rate is not automatically the market hurdle.

The exact data source and calculation conventions still need verification, including consistent currency, dates, and treatment of distributions and corporate actions.

## Scenario probability ownership

Agreed on 3 November 2026: the analyst proposes company-specific scenario probabilities, explains the evidence and uncertainty, and lets the user override them. A fixed bear/base/bull split is not an adopted default. Outcome definitions and numerical weights remain analysis choices to make explicit; the return statistic is the expected-cash-flow IRR adopted above. This decision does not assign probabilities to the original Gränges report. See the [probability proposal](../../examples/granges/docs/research/scenario-probabilities-proposal.md).

## Adopted cash and capital definitions

The user selected **group cash conversion before dividends**: statutory group CFO less cash capex, cash interest outside CFO and lease principal outside CFO, divided by consolidated group net income. CFO already contains cash taxes and working-capital movement. Missing gross outside-CFO interest or lease principal stays missing; known earlier bridge amounts remain visible. SBC addbacks are separately disclosed. This group diagnostic is not parent-common FCF or the issuer's own cash-conversion APM.

The user selected **operating ROIC** using an explicit operating-tax assumption and average opening/closing invested capital. The selected book-capital proxy is group equity plus gross debt including leases and additional net pension liabilities, less cash and identified non-operating assets. Goodwill/NCI already in group equity and leases already in gross debt are not added again. Provider ROIC and issuer ROCE keep their own labels. See the [implemented formula definitions](../calculations.md).

## Preservation and Mac handoff

The user selected Macs first and exact evidence plus saved analyses for workstation handoff. The user subsequently selected public application code in `KapKnudz/betaforge-reborn` and separate private research storage in `KapKnudz/betaforge-research-private`. Preserve source, tests, setup, policy and public reference documents in the code repository. Preserve exact reports, databases, watchlists and saved analyses in private versioned release assets outside ordinary Git history. Archive digests cover saved outputs as well as input evidence.

Each Mac has its own local credentials and Codex authentication. Completed-result restoration and active conversation migration are separate capabilities; cross-Mac live resume remains unverified. See [research handoff](../research-handoff.md).

## Available or proposed sources

- Börsdata API.
- Company reports potentially retrieved from mfn.se.

Selected Börsdata routes and Gränges account coverage were exercised in the saved walkthrough. Original PDFs came from issuer IR; MFN discovery succeeded while attachment downloads were blocked. This is not universal issuer coverage. Use company history first, then economically comparable global peers, then industry context; add a provider only for an identified gap. Credentials stay local.

## Historical first investigation

> I think a first area of focus has to be the flow of data. How the retrieval of data from the sources to the agents should be done in best practice for agentic way. It could be via tool-calling letting the agent retrieve data when needed, or retrieve all of the data deterministic and store it efficiently for agent to access.

That initial investigation compared upfront and tool-based exposure against preserved evidence. The report-only pi experiment and the later integrated Codex walkthrough support the current foundation; they do not establish universal retrieval superiority or predictive valuation accuracy. See [report comparison](../../examples/granges/docs/granges-walkthrough-results.md) and [integrated walkthrough](../../examples/granges/docs/granges-codex-walkthrough.md).

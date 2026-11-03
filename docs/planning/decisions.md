# Betaforge reborn: agreed planning foundation

## Destination and scope

Produce a lean, implementation-ready specification for the first useful version of a private investment-research website. Planning is authorized. The user subsequently authorized a bounded Gränges retrieval experiment, including local preparation and comparison scripts; application implementation and deployment remain outside that experiment. See [retrieval design discussion](../retrieval-design.md) for the agreed data scope and experiment decisions.

The website should provide a tangible shared view of progress and analysis, including company lookup by name or ID, visible company data, reverse DCF results, and eventually an evidence-backed investment judgment with bear, neutral/base, and bull ranges over two to three years. The exact first page and its contents remain to be specified.

The product is initially for one person's own use. Avoid overengineering; combine deterministic processing with agent reasoning and tools where useful. No technology stack, agent topology, storage system, or retrieval architecture has been selected.

## Research focus

- Swedish listed companies first.
- Normally profitable businesses.
- Roughly SEK 300 million–10 billion market capitalization, as a research focus rather than an automatic exclusion rule.
- The motivation is lower analyst coverage and a possible informational edge, not an assumption that excess returns are guaranteed.

## Philosophy

The starting input is the [unchanged investment-philosophy draft](investment-philosophy-draft.md), a supplied synthesis of Petter Hedborg's investment approach.

It is a draft, not an independently verified transcript analysis. Its source-backed philosophy must remain distinct from proposed agent implementation choices. Its suggested scores, weights, thresholds, continuous watchlists, and extensive ownership analysis are not automatically first-version requirements.

Business quality and investment attractiveness at today's price are separate judgments. An excellent business is not currently investable when its price demands performance the outlook does not support.

## Valuation roles

The preferred primary model is the draft's simple scenario approach:

- revenue growth;
- EBIT-margin development;
- a defensible EV/EBIT multiple;
- net debt/cash and share-count effects in the equity and per-share valuation.

This preference is conditional on confirming that the model is straightforward to implement appropriately. Reverse DCF is complementary: it should examine what operating performance the current price requires under explicitly stated assumptions.

Scenario construction and the detailed investability decision rules remain to be specified.

## Return hurdle

The expected annualized return of a candidate must exceed the benchmark hurdle.

The agreed reference is Investor AB's B share's trailing ten-year annualized total return, including reinvested dividends, measured as of the analysis date. This historical reference is a hurdle, not a forecast of Investor B's future return. No numerical return threshold has been asserted.

The exact data source and calculation conventions still need verification, including consistent currency, dates, and treatment of distributions and corporate actions.

## Scenario probability ownership

Agreed on 3 November 2026: the analyst proposes company-specific scenario probabilities, explains the evidence and uncertainty, and lets the user override them. A fixed bear/base/bull split is not an adopted default. Outcome definitions, numerical weights and the return statistic remain analysis choices to make explicit; this decision does not assign probabilities to the original Gränges report. See the [probability proposal](../research/scenario-probabilities-proposal.md).

## Available or proposed sources

- Börsdata API.
- Company reports potentially retrieved from mfn.se.

Exact coverage, account entitlements, permitted access methods, and source limitations have not yet been established. Credentials must not be committed.

## First investigation

> I think a first area of focus has to be the flow of data. How the retrieval of data from the sources to the agents should be done in best practice for agentic way. It could be via tool-calling letting the agent retrieve data when needed, or retrieve all of the data deterministic and store it efficiently for agent to access.

The requested deliverable is a source-backed comparison and recommendation, not implementation. The alternatives include agent-requested retrieval, deterministic retrieval with stored access, and any justified combination. No alternative has been selected.

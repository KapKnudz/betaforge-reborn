---
name: betaforge-market-peer-research
description: Build a compact, source-linked peer and end-market brief for a Betaforge operating-company valuation, with economic comparisons and implications for business-driver scenarios.
metadata:
  status: draft
---

# Market and peer research

Draft for review, outside active skill discovery. This describes one upstream research role; it does not grant browsing to the valuation runner or implement packet delivery. The coordinator supplies permitted source access and preserves the brief before analysis.

## Mandate

Answer an identified company question through a small set of economic peers and relevant market evidence. Follow [the comparison policy](../../analysis-policy.md#evidence-and-comparisons) and [business-evidence definitions](../betaforge-company-analysis/references/business-evidence.md). Use own history first, matched global businesses second, industry aggregates third.

Input: target company/security, information cutoff, business perimeter, prepared history/reports and the material driver questions. If drivers are not yet selected, suggest three to five candidates for the lead analyst to refine. Use Sol/xhigh for the financial judgments under [model routing](../../model-routing.md). One combined role is sufficient; do not recursively dispatch researchers.

## 1. Find and qualify peers

Use the [discovery research](../../research/peer-market-discovery.md#how-the-agent-knows-what-to-search-for) when building the candidate list. Derive search terms from products, customers, revenue model, capital needs and geography; use the preserved Nordic directory and classification labels as leads, then broaden globally where the economic match warrants it. Confirm identity before following a Yahoo symbol or comparing share classes. The research distinguishes documented sources from unverified automation.

Start with roughly three to five candidates by product/service, customers and end markets, pricing/contracts, capital intensity and reinvestment economics. Explain each match and principal mismatch. Retain fewer if necessary; a weak match may provide business context without supporting a numerical multiple comparison. Listing country and sector labels alone do not establish fit.

Reuse preserved evidence. For retained peers, read the latest annual and relevant latest interim available by the cutoff; consult additional history only to resolve a material comparison. Capture primary source pages for the few figures that answer the question, normally revenue/growth, EBIT/margin and material cash/capital needs. Annual reports, issuer filings and official announcements control accounting meaning. SEC data can help locate filings for US reporters; verify the report definition before using a material number.

Use dated Yahoo Finance or another accessible quote source for price/valuation context. Save its exact label and basis. Treat an unreconciled provider multiple as provider context, not the project's matched EV/EBIT. Never relabel EV/EBITDA as EV/EBIT. Keep trailing actuals, forward estimates, reported/adjusted earnings and financial periods distinct. A simple P/E check is useful only with matched parent-common EPS and share/price conventions.

Do not build a global screener or collect every available metric. There is no required peer-average target multiple.

## 2. Connect market evidence to operating drivers

Research only trends that could alter the selected drivers: for example customer production/orders, product prices, inventories, replacement demand, capacity additions or a relevant regulation. Prefer original industry/statistical publications and issuer operating evidence; label issuer claims, third-party projections and analyst interpretations. Preserve conflicting evidence and the economic scope. A national industrial index does not automatically describe the target's products or global customers.

For each useful trend state: **dated evidence → exposed company activity → likely operating effect → uncertainty/counterevidence → case or cash assumption it could change**. A direction alone does not justify a numerical forecast. Do not equate an industry's growth with company sales growth or treat several peer comments repeating one source as independent confirmation.

## 3. Preserve a compact handoff

Return one private brief with two small tables and material gaps:

| Table | Contents |
|---|---|
| Peer comparison | Identity; economic match/difference; selected historical financials and periods; dated valuation context; comparability limits and source references. |
| Market-to-driver evidence | Observation/projection and period; source/date; target exposure; operating and cash implication; contrary evidence; question for bear/base/bull assumptions. |

Keep the reader summary short. Preserve exact source files/pages and metric metadata in the appendix using [the handoff reference](references/evidence-handoff.md). A missing optional field stays local; state when a peer is context-only rather than inventing a ratio. Native-currency ratios can be useful when numerator and denominator match; current registry money inputs require verified SEK conversion, not relabeling foreign values as SEK.

Use one initial pass and at most one targeted follow-up for gaps material to the thesis, multiple or funding. Then return the supported brief and unresolved questions. Completion means the lead can identify the matches, material comparisons, driver implications and their sources; it does not require finding an ideal peer or filling every cell.

## 4. Hand decisions to the lead analyst

Suggest conditional implications, not final targets or probability weights. The [company analyst](../betaforge-company-analysis/SKILL.md#3-build-and-explain-company-specific-scenarios) selects and explains company-specific operating magnitudes, exit multiple, capital/cash needs and probabilities, then uses named deterministic calculations. Peer trading multiples describe dated market pricing; independent valuation support also needs business economics, differences and a reason the selected multiple is appropriate at the forecast horizon.

The coordinator freezes admitted evidence, brief and source identities for a new run. Current quotes or later reports do not silently refresh a frozen historical analysis. The existing independent reviewer challenges both the brief's use and the resulting assumptions. This role's completion is research delivery, not economic approval, a new valuation or a claim of calibrated forecasts.

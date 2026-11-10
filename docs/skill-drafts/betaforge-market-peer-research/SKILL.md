---
name: betaforge-market-peer-research
description: Build a compact, source-linked peer and end-market brief for a Betaforge operating-company valuation, with economic comparisons and implications for business-driver scenarios.
metadata:
  status: draft
---

# Market and peer research

Draft for review, outside active skill discovery. This describes one upstream research role; it does not grant browsing to the valuation runner or implement packet delivery. The coordinator supplies permitted source access and preserves the brief before analysis.

## Mandate

Show where the target performs better, similarly or worse than its selected peers and explain the main reason. Follow [the comparison policy](../../analysis-policy.md#evidence-and-comparisons) and [business-evidence definitions](../betaforge-company-analysis/references/business-evidence.md). Use own history first, matched global businesses second, industry aggregates third.

Use the target company/security, information cutoff, business perimeter, preserved issuer reports and up to three unanswered questions from the [business brief](../betaforge-company-analysis/references/business-evidence.md#write-the-business-brief-before-forecasting). If drivers are not yet selected, suggest three to five candidates for the lead analyst to refine. Use Sol/xhigh for the financial judgments under [model routing](../../model-routing.md). One combined role is sufficient; do not recursively dispatch researchers.

For a targeted question, go straight to [step 2](#2-connect-market-evidence-to-operating-drivers). Use step 1 when the question calls for a peer comparison.

## 1. Find and qualify peers

Start with the target's products, customers and how it earns money. When useful and available, seed the pool from the target's exact branch in the preserved Nordic directory. Propose roughly 5–10 plausible names from known businesses and saved descriptions. Treat both as leads: a generic description can hide a different business model. Check a short issuer overview for promising names. Leave unread names unassessed.

If a material gap remains, try one or two searches combining a specific product or process, buyer and revenue model, plus listing or geography terms where useful. Record the queries. Check promising results against the directory or an official listing, including leads in other branches or markets. Use the [discovery examples](../../research/peer-market-discovery.md#concrete-search-examples) when choosing terms. Verify issuer, venue and share class before using a quote; avoid counting duplicate listings as separate businesses.

Label each reviewed candidate **group comparison**, **segment comparison**, **context only**, or **unclear**. Give one reason for the fit and the main difference. Aim for three useful peers and compare at most five in total, including segment peers. Use fewer when fit or evidence is weak. Compare the business model, customers and capital needs before looking at margins or multiples. A segment peer supports conclusions about the matched segment.

For retained names, reuse verified figures or open the annual or interim reports needed for the latest common period. Start with reported sales growth, reported EBIT margin, gross cash investment as a share of sales, and group cash conversion where supported. Use the same asset categories for gross cash investment, including capitalized development where relevant. Use the [calculation definitions](../../calculations.md) for the cash bridge and its scope. Check whether an acquisition, disposal or spin-off changes what the figures cover. Compare matching periods, business scope and accounting definitions. Show a short reason when a figure is unavailable or unsuitable for comparison. Add at most one business-specific measure when it answers the research question. SEC data can help locate US filings. The original report establishes accounting meaning.

Use dated Yahoo Finance or another accessible quote source for price and provisional trading context when needed. If a rough size or earnings check helps narrow the shortlist, look up the verified saved symbol and record the provisional operating rows as labelled. Save each figure's date and basis or mark it unknown. Check any operating figure used in the analysis against its issuer report. If using P/E, match the share price and parent diluted EPS; if using EV/EBIT, match the dated equity value, enterprise claims and operating earnings. Keep provider multiples under their displayed names and do not treat a peer mean as an automatic exit multiple.

When a disposal or spin-off breaks the earnings comparison, inspect earlier interims and transaction/carve-out disclosures for a continuing-business reconciliation before declaring the denominator unavailable. Keep reported results, perimeter adjustments and optional normalization of one-off items in separate columns; preserve the issuer's definitions, assurance status and rounding residuals. An issuer pro forma figure is evidence to inspect, not automatically sustainable earnings. Derive R12 only when the full year, current year-to-date and comparative year-to-date cover the same business and accounting basis. A usable nine-month reconciliation does not fill a missing comparative period, and a strong quarter must not be annualized to bypass that gap.

For a historical quote acquired later, record the observation date separately from retrieval and verify the listing, currency, share/entitlement basis and any intervening corporate actions. Corroboration across displayed quotes can strengthen the observation without proving independent data lineage, the provider's adjustment history or a contemporaneous archive. Keep any unresolved basis limitation beside the pricing comparison.

## 2. Connect market evidence to operating drivers

Research only trends that could alter the selected drivers: for example customer production/orders, product prices, inventories, replacement demand, capacity additions or a relevant regulation. Prefer original industry/statistical publications and issuer operating evidence; label issuer claims, third-party projections and analyst interpretations. Preserve conflicting evidence and the economic scope. A national industrial index does not automatically describe the target's products or global customers.

For each unanswered question, start with the preserved issuer evidence. If it leaves a material gap, make up to two targeted searches across the initial pass and any follow-up. Prefer primary issuer, customer or competitor disclosures or original market statistics available by the same cutoff. Stop once the question is answered or no promising lead remains. Preserve the answer or gap and what it could change in the analysis.

For each useful trend state: **dated evidence → exposed company activity → likely operating effect → uncertainty/counterevidence → case or cash assumption it could change**. A direction alone does not justify a numerical forecast. Do not equate an industry's growth with company sales growth or treat several peer comments repeating one source as independent confirmation.

## 3. Preserve a compact handoff

Return one private brief. For a targeted check without a peer comparison, record the question, supported answer or gap, sources and proposed effect. For a peer comparison, start with the period and scope, then show the target and selected peers in one table.

| Company and scope | Sales growth | EBIT margin | Cash investment / sales | Group cash conversion | Main difference |
|---|---:|---:|---:|---:|---|
| Target and each selected peer | % | % | % | % | Business fit or limit that matters |

For a peer comparison, follow the table with one short verdict. Choose **ahead**, **similar**, **mixed**, **behind**, or **insufficient evidence**. Name the comparable measures that drive it and the main qualification. Judge lower investment in light of growth and cash generation. Base group verdicts on group comparisons and name the comparator when there is only one. State any segment conclusion at segment scope. Use **insufficient evidence** and name the gap when the measures cannot support a verdict for the requested scope. Explain the trade-offs without a score or tally.

Add a short market note or dated multiple only when it helps answer the research question. If you screened peers, record the directory date, discovery scope, reviewed names and reasons for retention or exclusion in the appendix. Preserve source pages, metric definitions and calculations using [the handoff reference](references/evidence-handoff.md). Native-currency ratios can be useful when numerator and denominator match. Current registry money inputs require verified SEK conversion.

Use one initial pass and at most one targeted follow-up for gaps material to the thesis, multiple or funding. Completion means the lead has the supported answers or comparisons, their sources, the driver implications and any unresolved questions.

## 4. Hand decisions to the lead analyst

For each material input the brief addresses, propose a change with the starting value, suggested value and evidence, a sensitivity with its range, or context only with the reason. When the starting assumption is unavailable, identify the input and explain what evidence the analyst can use to test it. The [company analyst](../betaforge-company-analysis/SKILL.md#3-build-and-explain-company-specific-scenarios) owns final assumptions and any probabilities.

Keep operating implications separate from pricing. A higher exit multiple requires separate pricing evidence, comparable earnings and claims, and a reason the multiple fits the company at the forecast horizon.

The coordinator freezes admitted evidence, brief and source identities for a new run. Current quotes or later reports do not silently refresh a frozen historical analysis. The existing independent reviewer challenges both the brief's use and the resulting assumptions. This role's completion is research delivery, not economic approval, a new valuation or a claim of calibrated forecasts.

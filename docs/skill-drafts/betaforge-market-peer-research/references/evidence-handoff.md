# Peer and market evidence handoff

Draft delivery guidance for the [combined research role](../SKILL.md). Reuse the project's source-preservation approach; this is a brief and evidence appendix, not a new database schema. Exact issuer research belongs in ignored/private storage under the [handoff rules](../../../research-handoff.md).

## What to preserve

Shared metadata can live once per source rather than in every visible table cell. Save original bytes and SHA256 identities, with page/table or structured-data locations for selected facts. A derived ratio cites its component facts and calculation, not just a provider title. Missing data is not zero.

| Evidence | Required meaning where applicable |
|---|---|
| Identity | Issuer/group, ticker/exchange/share class; economic match and material mismatch. Identify ADR/depositary ratios when relevant. Do not invent Börsdata IDs for foreign peers. |
| Source | Original URL; saved file and physical page/table or data location; hash; publication/filing date; capture time; availability qualification against the chosen cutoff. |
| Financial fact | Original label/value, currency/scale/unit; flow start/end or balance date; annual/quarter/YTD/R12; group/parent/segment; reported/adjusted and restatement vintage. Keep source values separate from analyst normalization. |
| Valuation observation | Quote date/time and price convention; security/currency; supplied or rebuilt multiple; actual trailing or forward-estimate denominator, period and vintage. For rebuilt EV, name debt, cash, leases, pensions, NCI, surplus assets and material subsequent changes. An unresolved claim limits comparability. |
| Market indicator | Product/geography coverage, units, observation period or projection horizon, publication date and revisions; target exposure, mechanism and counterevidence. |
| Judgment | Fact/interpretation/assumption; allowed comparison, unresolved definition and material next question. Any summary statistic states constituents, dates, exclusions and compatible bases. |

Use the project's [financial definitions](../../../calculations.md) and [material-input rules](../../../material-inputs.md). A peer's issuer ROCE, provider ROIC or EBITDA margin is not automatically comparable with Betaforge's operating ROIC or EBIT margin. Do not calculate a cash yield from group cash against parent-common market capitalization. Keep accounting and scope differences visible when a full normalization would add little insight.

## Respect the cutoff

Financial-period end, publication date, quote date and retrieval time answer different questions. A report published after a historical cutoff cannot establish what was known then, even when it covers an earlier year. Current web fundamentals may include restatements or later filings. Admit a newly captured source to a frozen-cutoff exercise only when its availability and relevant version by that cutoff are verified. Otherwise keep it as an unverified gap or a separately labelled later/retrospective check; it cannot justify the historical assumptions. Even verified earlier availability does not by itself establish a point-in-time backtest.

Keep new information separate as a later-dated research update. Do not overwrite an existing packet or silently mix today's peer multiples into a 3 November analysis. The research brief can still be useful with a qualified or missing historical valuation column.

## Source choices and limits

- **Issuer reports and filings:** primary financial definitions and reconciliations; record the actual publication and accounting periods. An issuer's competitor list is a discovery lead, not proof of economic comparability.
- **SEC EDGAR:** [official APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) can locate submissions and standard entity-wide XBRL facts. Custom/segment metrics and comparable EBIT still need filing inspection; current aggregated facts do not establish historical availability. No SEC client is introduced by this draft.
- **Yahoo Finance or an accessible equivalent:** dated price and displayed valuation context. Yahoo's [provider/delay guide](https://help.yahoo.com/kb/SLN2310.html) identifies exchange-specific data arrangements, but full metric methodology and stable automated access have not been established here. Direct help-page retrieval was rate-limited during source research. Use a different accessible source or disclose a gap rather than promising an API. Yahoo's [adjusted-close explanation](https://in.help.yahoo.com/kb/adjusted-close-sln28256.html) describes split/dividend adjustment; an adjusted total-return series is not silently the cash purchase price for a valuation with separate dividends.
- **Original market statistics:** use a relevant product/activity series and its methodology. For example, [Eurostat industrial production](https://ec.europa.eu/eurostat/statistics-explained/index.php?title=Industrial_production_(volume)_index_overview) measures price-adjusted output; match activity/geography before applying it to customer demand. A broad indicator supplies context, not a company growth forecast.
- **Damodaran:** use the existing [industry context](../../../industry-context.md), retaining its dates, units, accounting adjustments and aggregation caveats. A sector aggregate is neither the selected peers' median nor an automatic exit multiple.

## Runtime boundary

The existing [architecture](../../../architecture.md) separates acquisition from frozen analysis. Preserve this boundary: permitted external research first, then frozen evidence for the lead analyst. The [industry snapshot implementation](../../../../scripts/fetch_industry_context.py) provides a useful raw-source/hash pattern, but its workbook-specific copying does not prove that arbitrary peer briefs are delivered by the packet builder. Target-company report facts also cannot silently become facts for another issuer.

Before runtime adoption, explicitly implement and verify source/brief delivery, hash binding, issuer identity and historical-cutoff behavior through the existing preparation layer. Keep the lead's restricted tool set and historical packet bytes intact. Draft documents alone do not activate this agent or make its evidence available in a valuation run.

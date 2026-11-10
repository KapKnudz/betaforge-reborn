---
name: betaforge-company-analysis
description: Produce a source-linked Betaforge operating-company valuation using the adopted investment philosophy, saved evidence and named financial calculations.
metadata:
  status: draft
---

# Company analysis

Repository guidance stored outside active skill discovery. New packets freeze the selected analyst guides into the prompt and preserve the reviewer guide for the coordinator's handoff. Use those frozen copies, not later edits to this directory. Preserve historical analysis instructions and results.

## Foundation and scope

Apply the combined philosophy in [analysis-policy.md](../../analysis-policy.md): understand earnings drivers, business quality, cash and capital needs, management allocation and the price paid. This is the project's Hedborg/Armitage synthesis; investor-writing examples guide communication, not a different investment strategy. Keep financial definitions in the [calculation catalogue](../../calculations.md).

For an actual run, use the policy and definitions frozen in its packet. Use only the supplied evidence and permitted tools. The coordinator owns acquisition, packet preparation and independent reviewer dispatch. Ordinary operating companies are the initial scope; identify a different business or security scope before applying these equations.

Read the [calculation guide](references/calculations.md) before selecting valuation inputs. The [investor process notes](../../research/investment-process-sources.md) explain the source of selected analytical ideas and where Betaforge makes its own choices. Follow the [analysis workflow](../../analysis-workflow.md) and six-section report contract.

## 1. Establish the evidence

Identify the company/security, cutoff, dated purchase price, currency, ownership basis and horizon. Complete required report reading, including the five latest annuals where available and relevant current interims. Use compatible latest quarter/R12 flows and closing balances for current questions; use five-to-ten-year history where available for context.

Reconcile each material selected input with the report and provider definition: period, units, reported/adjusted basis, group/parent scope, acquisitions and source revisions. Save report substitutions and assumptions with exact references. A missing optional input stays a local qualification; continue the useful supported analysis.

Completion: material inputs have a stated meaning and saved source, or an explicit assumption/gap.

## 2. Explain the business and select initial calculations

Complete the [business brief](references/business-evidence.md#write-the-business-brief-before-forecasting) from the preserved issuer evidence before selecting forecasts. Use the same guide to identify three to five drivers of earnings and cash and test pricing power, competitive advantages, management delivery, capital allocation and prospective dilution. Compare own history first, economically matched global peers second, and qualified industry data third. Use a frozen [market and peer brief](../betaforge-market-peer-research/SKILL.md) when supplied. The coordinator owns external research, and you own its forecast implications.

Complete the guide's [management-delivery and insider-evidence checks](references/business-evidence.md#check-management-delivery-and-insider-evidence) and put their bounded conclusions in the management section. Use all relevant captured insider rows, not a first-page sample. If evidence or trade definitions are unavailable, state the coverage and unresolved interpretation rather than inferring no activity. Explain whether management delivery and alignment evidence support, weaken or leave unchanged confidence in the material assumptions; do not translate either into an automatic multiple or return adjustment.

Select calculations by the question they answer:

| Purpose | Existing calculations |
|---|---|
| Earnings quality | EBIT margin; qualified incremental EBIT margin with both deltas visible. |
| Capital and cash needs | Operating ROIC; working-capital balances relative to sales; group cash conversion and its cash bridge, where meaningful and supported. |
| Initial price checks | Matched EV/EBIT and diluted P/E; ownership-matched FCF yield only when its cash numerator is supportable. |
| Primary valuation | Revenue × EBIT margin, or volume × EBIT per tonne, then the complete EV-to-common-equity bridge. |
| Shareholder outcome | Per-case cash-flow IRR and discounted value. Use a secondary weighted cash-flow IRR only when the probabilities have a defensible basis. |

Use the guide's formulas and limits. These diagnostics inform assumptions; they do not mechanically score the company or set its value. Retain depreciation and compensation economics, including awards and dilution. Add calculations only when they resolve a material question.

## 3. Build and explain company-specific scenarios

Choose one operating equation for the same business. Use the business brief to support the magnitude and timing of forecast changes. Define bear/base/bull through business conditions and outcome ranges at a common horizon, rather than fixed percentage moves around today's price. Test material driver assumptions jointly against compatible history; explain a central case that combines exceptional scale and profitability.

Use the [material-assumption note](references/business-evidence.md#explain-material-assumptions) for material forecasts, exit multiples, cash retention and any probability judgment. Complete the evidence-to-decision explanation for retained inputs as well as changed ones before finalizing the cases.

For each material input the peer brief addresses, record a changed assumption with its before/after values and basis, a new sensitivity with its range, or context only with the reason it leaves the case unchanged. Use the [comparison policy](../../analysis-policy.md#evidence-and-comparisons) when assessing the strength of a peer comparison.

If the case needs a material EBIT margin increase, bridge the latest comparable annual or trailing 12-month result to the margin at the forecast horizon. Identify the gross profit or operating cost changes that explain the increase, the evidence for their size and timing, and any capital required. Keep longer-term margin potential separate. Consult the [Hedborg cases](../../research/hedborg-podcast-evidence.md#what-betaforge-can-use) when testing a recovery, margin improvement or rerating.

If a material input such as a contract price is private, explain the estimate using disclosed evidence where available. Use the existing cases or a sensitivity to show whether a defensible range changes the investment call. If the range itself lacks support, state the gap. See the [Armitage examples](../../research/armitage-podcast-evidence.md#named-cases) for backlog, pricing and downside checks.

Select the exit multiple on the same earnings/claims basis as the forecast. Identify its provenance and economic justification. A maintained-current-multiple case is a conditional pricing benchmark; explain separate support before presenting it as an independent fair-value estimate. The market-implied EBIT check answers a conditional question and does not corroborate its own inputs.

Explain which operating changes drive forecast EBIT and which part of the investment case depends on a change in the multiple. If rerating is material to the call, use the existing scenario calculation at a defensible lower multiple with the same operating and cash assumptions. State whether the return still clears the hurdle.

Support forecast cash with an earnings path or horizon average and material noncash, tax, interest, working-capital, investment and lease adjustments. Show cash uses, acquisitions, claim settlements, minorities and common dividends before retained cash. Complete the debt/claims/assets/share bridge once; identify financing or dilution needed to fund the case. State material post-statement events and any transaction scope the case excludes.

Follow the [probability policy](../../analysis-policy.md#probabilities-and-returns). If comparable outcome frequencies or a documented elicitation support company-specific weights, save the rationale and source references for all cases. State omitted outcomes and show a justified alternative allocation when it could change the conclusion. When evidence is too thin, omit weights for all cases and use `probability_limits` to explain the gap. An equal split also requires evidence.

Completion requires sourced or explicitly assumed drivers, an explained multiple, a funded or qualified cash/claims bridge and a clear basis for weighting or leaving the cases unweighted.

## 4. Calculate and present the shareholder result

Use saved input IDs and named deterministic formulas; normalize source scale once. Present scenario returns first. Use the existing IRR function separately with each case's dividends and target, then reference those results in existing valuation paragraphs/tables. Keep dates, target precision, dividend timing and price-only change distinct from annual cash-flow return.

Use the policy's starting 10% personal equity hurdle and 9% PV sensitivity, with explained overrides. Keep historical SIXRX total return separate. With supported weights, weight dated cash flows before solving a secondary IRR and explain its conditional scope. With unweighted cases, explain the conditions that would clear the hurdle. Test the principal operating disappointment and its associated capital/cash needs using existing formulas.

Use the [financial report guide](../betaforge-financial-report/SKILL.md) to write the owner memo from the saved analysis. Name observations that would weaken the thesis and the next evidence to inspect.

Completion: the structured report references saved calculations and source evidence, explains its material judgments and uncertainties, and is ready for independent challenge. Structural submission acceptance is distinct from economic review.

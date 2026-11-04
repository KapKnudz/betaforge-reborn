# Return consistency and a shorter company report

Reviewed 4 November 2026. The user adopted the return rule: 10% starting personal hurdle, 9% sensitivity and explained company-specific overrides; SIXRX remains historical context. The dividend/cash-flow and presentation changes below remain proposed. Saved valuations retain their original assumptions.

## Priority and scope

Review the main earnings assumptions before payment-timing refinements. Assess whether the central case requires several favorable operating outcomes together and whether the evidence supports their joint feasibility. Present the latest comparable annual/R12 results, historical range, forecast and business explanation using the existing evidence and sensitivity tools. A small haircut to an optimistic case may still assume unusually strong operations; the sensitivity must address the principal optimistic dependency. Above-history assumptions require explanation, not an automatic cap or reclassification.

Apply the [generic analysis rule](decisions.md#generic-analysis-before-company-tuning). A concern found in one issuer justifies shared changes only when it exposes a reusable analytical problem. Issuer-specific forecast corrections stay in the company's analysis. The acceptance criterion is clearer, economically consistent analysis across companies, not a preferred worked-example valuation.

## Financial changes

| Issue | Smallest proposed change |
|---|---|
| A central case can combine strong scale and strong profitability without sufficient joint support. | First compare the major drivers with compatible history and identify the evidence for the combination, including cash and reinvestment needs. Reuse existing sensitivity tools for a coherent disappointment. Keep material uncertainty in the main reader view; no new earnings model or historical-peak ceiling is required. |
| Required return, expected return and historical market return have different roles. | Adopted: start at a 10% personal required equity return, show 9% sensitivity and explain company-specific overrides. Use the selected personal hurdle as the investment threshold; keep SIXRX separately labelled as historical context. Reuse the existing required-return input. |
| Upcoming dividends are available through the existing dataset tools but absent from the initial financial context. | Put relevant known dividend events beside the saved price. Retain amount, currency, ex-date, expected payment date, status and source references. A future provider field named `amountPaid` does not establish payment. |
| Constant year-end dividends omit actual known payment timing. | Use one explicit shareholder cash-flow schedule for present value, expected-cash-flow IRR and display. Known distributions use sourced dates; forecast timing remains an explicit assumption. Resolve whether a declared event replaces part of a forecast payment before including it. State the price date, valuation date and model endpoint convention. |
| Dividends and after-dividend retention can be chosen independently. | Reconcile cash available before common dividends, common distributions and retained cash. A distribution change with unchanged cash generation must change retained cash and future net debt. Show and explain a payout requiring funding; do not automatically reject every negative-retention case. Label an implied bridge as an assumption, not independently verified cash generation. |
| A payout comparison requires comparable earnings and timing. | Compare against parent-common earnings and matching shares/financial year when supported. A constant multi-year DPS assumption cannot establish a terminal-year payout ratio from EBIT alone. Do not create an unsupported EPS estimate or force dividends to a policy percentage. |

Reuse the existing operating and equity bridges, evidence store and calendar acquisition. Dated present values and IRR require a small extension to the [named cash-flow calculation contract](../calculations.md), which currently supports constant annual year-end dividends. No second earnings model or new retrieval system is needed. The confirmed return rule is recorded in the [financial policy](../analysis-policy.md).

## Human report

Keep the existing six sections and saved references. Add one small display distinction between main content and supporting detail; fact, interpretation and assumption remain separate semantic labels.

| Main reading view | Expandable supporting detail |
|---|---|
| Conclusion, price date, horizon and material uncertainty | Execution notes, extraction history and review bookkeeping |
| Three to five drivers: actuals, analyst case, relevant management guidance and material departures from history | Full quotes, source identities and accounting reconciliations |
| Dated scenario values, proposed probabilities and key assumptions | Complete calculation trace, input values and formula definitions |
| Main risks, thesis-breaking evidence and next checks | Full independent challenge and remaining technical qualifications |

Material uncertainty stays beside the affected conclusion. A required assumption does not become hidden merely because it is an assumption. Main prose leads with the business conclusion, uses short sentences and compact tables, and avoids first-person process narration.

The current paragraph contract has `kind`, `text` and `references`; the renderer displays every paragraph equally. An optional supporting-detail flag is a smaller change than a separate report engine. Earlier saved reports retain their existing interpretation.

## Inputs and implementation order

Existing selected inputs and material mapping decisions preserve units, periods, scope and provenance where established; unresolved definitions remain explicit. The report already has drivers, management comparisons, scenarios and references. Keep that structure.

1. Return rule confirmed. Review the principal operating assumptions jointly and rank remaining issues by economic materiality. Record which findings concern generic analysis and which concern issuer-specific assumptions.
2. Review the proposed reading layout and dividend/cash-flow scope against that priority. Use existing evidence and sensitivity functionality for the operating review.
3. Connect known dividend events to the initial context and a shared payment schedule. Reconcile distributions with retained cash and debt; cover eligibility, replacement/double-counting and weak-cash cases with focused tests.
4. Add the small display distinction and writing contract. Check an actual saved page in desktop and narrow layouts.
5. Produce a separately saved analysis under the confirmed convention, using the existing bounded analyst/challenge/revision workflow. Keep the original run available.

Before publishing, obtain independent read-only review and the normal current-head PR checks. A lower discount rate alone does not improve the modeled investment return.

## Evidence for this proposal

- [Initial financial context](../../scripts/prepare_codex_packet.py), `initial_context`: financial history, latest price and available metrics; no selected dividend events.
- [Evidence tools](../../betaforge/tools.py), `catalogue` and `get_dataset`: calendar records are already accessible.
- [Calculation registry](../../betaforge/financials.py), `valuation_case` and `expected_cashflow_irr`: constant annual dividends and an independent required-return input.
- [Report contract](../../betaforge/analysis_report.py), `validate_report`: paragraph kind, text and references.
- [Company renderer](../../web/progress/app.js), `renderAnalysis`: all saved paragraphs are displayed together.
- [Current workflow](../analysis-workflow.md): frozen evidence, independent challenge and at most one revision.

The company-specific audit and numerical illustration stay in ignored private research storage.

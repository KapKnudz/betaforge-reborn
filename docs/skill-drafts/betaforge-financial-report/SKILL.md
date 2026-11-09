---
name: betaforge-financial-report
description: Write or revise a concise Betaforge investment memo from company analysis, source evidence and saved calculations.
metadata:
  status: draft
---

# Financial report writing

The lead analyst uses this guide when writing the report for independent challenge. Use the evidence, policy and calculations of the selected run. Follow the [six-section memo structure](../betaforge-company-analysis/references/memo-structure.md) and keep its saved references and paragraph kinds.

## 1. Lead with the investment decision

Open with the business, the main assumption that drives returns, what the scenarios imply at the dated price and what could change the view. Put the price date, forecast horizon and hurdle beside the relevant figures. Explain the operating mechanism in plain financial language. Give the historical anchor, chosen forecast and reason for the difference where it affects the decision.

State **Attractive**, **Wait** or **Pass** at the report price. Explain why the case merits consideration, what would justify waiting for a better entry or more evidence, or why the case is worth passing over at that price. Compare scenario returns with the hurdle and explain why the evidence and downside support the selected call. A downside case below the hurdle is not by itself a reason to Wait. State the conditions behind any entry price, especially when it depends on a particular exit multiple or improvement in cash generation.

## 2. Give the reader a way to verify it

Condense the [business brief](../betaforge-company-analysis/references/business-evidence.md#write-the-business-brief-before-forecasting) into the developments that explain the decision. Condense the [material-assumption notes](../betaforge-company-analysis/references/business-evidence.md#explain-material-assumptions) beside the assumptions that drive the call: explain the selected amount and timing, what remains judgment and, where tested, whether an alternative changes the decision. Use the six sections to move from thesis to drivers, quality, management, valuation and risks. Distinguish actual results, management guidance and analyst assumptions. Place the material evidence beside each claim. Show how earnings turn into cash and common equity value where that bridge affects the conclusion. Put detailed reconciliations and source pages in supporting evidence.

Show bear, base and bull returns. Explain the business conditions behind each case and what would weaken the thesis. Where peer evidence mattered, identify what changed or what sensitivity it prompted. Label comparisons used only as context. Use the [valuation guide](../betaforge-company-analysis/references/calculations.md) for calculations and return definitions.

If the evidence supports weights, put the qualified weighted result and its rationale in supporting valuation detail. Give the coordinator its saved calculation ID. If the cases are unweighted, record the reason and explain what would clear the hurdle. See the [export guide](../../saved-analysis-view.md#add-a-saved-company-run).

## 3. Choose visuals that answer a question

1. **Overview.** Plot the saved bear, base and bull annual cash-flow IRRs on one horizontal scale with zero and the selected hurdle. Give the purchase price and date, the horizon and dividend treatment. Show dated present values and future share targets in the valuation details, with their own labels and units. If saved returns cannot be verified, use the dated values and targets.
2. **Investment case.** Show decisive drivers against comparable company history. For reported net sales and EBIT margin, start the paragraph with “Reported group history uses net sales.” Use `Period`, `Net sales (SEK m)` and `EBIT margin (%)` headers, substituting the saved currency code. Use at least two fiscal-year labels and, when available, one `R12 Month YYYY` label. Reference each saved `ebit_margin` result as `calculation-id#margin_percent`, with matched dated revenue and EBIT inputs or a dated revenue extraction and its report page. In Valuation, start the forecast bridge heading cell with its target year, use the saved scenario names as columns, and include rows named `Net sales, SEK m` and `Reported EBIT margin`. Use percent signs in the forecast margin row. The scenario valuations must link their forecast EBIT to the corresponding `revenue_ebit` calculations. Other operating equations, units or accounting bases can use separate saved tables with clear labels and qualifications. Chart intermediate periods only where the saved model has forecasts.
3. **Valuation assumptions.** Choose one supporting visual that explains the decision. In a sensitivity table, vary the decisive inputs explicitly and hold the other inputs fixed. Use a cash waterfall when reconciled cash movements explain the decision. Label each scope and subtotal, and end at the last verified subtotal if a line is missing. Group cash after capex is a different measure from cash available to common shareholders. Use a sourced table for peer comparisons and state any material basis differences.

Keep displayed table cells and prose in plain text. Put saved IDs in the paragraph's structured references, where the viewer links them. Start an expandable supporting paragraph with a `###` heading followed by a blank line. The reader can then open the details alongside the memo.

Apply the [design brief](../../../DESIGN.md) to presentation. The [investor examples](../../research/investor-writing-examples.md) show ways to explain an operating thesis and present cash, capital and valuation. Check every displayed figure against the saved calculation or source before submission. The [independent review guide](../betaforge-valuation-review/SKILL.md) covers the next stage.

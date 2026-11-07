---
name: betaforge-financial-report
description: Write or revise a concise Betaforge investment memo from company analysis, source evidence and saved calculations.
metadata:
  status: draft
---

# Financial report writing

The lead analyst uses this guide when writing the report for independent challenge. Use the evidence, policy and calculations of the selected run. Follow the [six-section memo structure](../betaforge-company-analysis/references/memo-structure.md) and keep its saved references and paragraph kinds.

## 1. Lead with the investment decision

Use the report's `summary` to open with the business, the main assumption that drives returns, what the scenarios imply at the dated price and what could change the view. Put the price date, forecast horizon and hurdle beside the relevant figures. Explain the operating mechanism in plain financial language. Give the historical anchor, chosen forecast and reason for the difference where it affects the decision.

State **Attractive**, **Wait** or **Pass** at the report price. Explain why the case merits consideration, what would justify waiting for a better entry or more evidence, or why the case is worth passing over at that price. Compare returns with the hurdle and exercise judgment about the downside. If weights are weak, the scenario evidence can still support a call. State the conditions behind any entry price, especially when it depends on a particular exit multiple or improvement in cash generation.

## 2. Give the reader a way to verify it

Use the six sections to move from thesis to drivers, quality, management, valuation and risks. Distinguish actual results, management guidance and analyst assumptions. Place the material evidence beside each claim. Show how earnings turn into cash and common equity value where that bridge affects the conclusion. Put detailed reconciliations and source pages in supporting evidence. Keep any peer comparison that materially supports or challenges the call, including the main comparability limit.

Show bear, base and bull returns before any weighted summary. Explain the business conditions behind each case and what would weaken the thesis. Use the [valuation guide](../betaforge-company-analysis/references/calculations.md) for calculations and return definitions.

If the memo adopts a weighted return, give the coordinator its saved calculation ID. The [export guide](../../saved-analysis-view.md#add-a-saved-company-run) explains how to select it when the run retains several IRR calculations.

## 3. Choose visuals that answer a question

- Use the existing scenario view to show dated present values and future share targets. Label the measure, units and price date. Use intermediate points only where the saved model has corresponding forecasts.
- Use a short historical chart when comparable saved periods show a trend that matters to the thesis. The viewer charts Markdown tables whose first heading is exactly `Period`, with at least two labelled rows and numbers alone in each charted column. Put units in headers, such as `EBIT margin (%)`. Split incompatible series or use a plain table with `Reporting period` as the first heading and explain the basis change.
- Use compact tables for actuals versus scenario assumptions and for the earnings-to-equity bridge. Keep the basis and source beside the figures.

Keep displayed table cells and prose in plain text. Put saved IDs in the paragraph's structured references, where the viewer links them. Start an expandable supporting paragraph with a `###` heading followed by a blank line. The reader can then open the details alongside the memo.

Apply the [design brief](../../../DESIGN.md) to presentation. The [investor examples](../../research/investor-writing-examples.md) show ways to explain an operating thesis and present cash, capital and valuation. Check every displayed figure against the saved calculation or source before submission. The [independent review guide](../betaforge-valuation-review/SKILL.md) covers the next stage.

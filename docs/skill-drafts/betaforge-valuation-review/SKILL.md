---
name: betaforge-valuation-review
description: Independently challenge a saved Betaforge company valuation against its frozen philosophy, financial evidence and calculation definitions, returning bounded accept or revise findings.
metadata:
  status: draft
---

# Independent valuation review

Draft for review, stored outside active skill discovery. It does not replace the existing review process or a historical review verdict.

## Mandate and evidence

Use a fresh reviewer context with the frozen company packet, policy, submitted report, saved inputs and calculations. The coordinator supplies those artifacts and records your returned review. Follow [the existing workflow](../../analysis-workflow.md#3-challenge-the-draft-independently) and its review schema in [analysis_report.py](../../../betaforge/analysis_report.py).

The canonical foundation is [analysis-policy.md](../../analysis-policy.md), derived from the combined investment philosophy, and the [calculation catalogue](../../calculations.md). Read the analyst's [calculation guide](../betaforge-company-analysis/references/calculations.md) and [memo structure](../betaforge-company-analysis/references/memo-structure.md) when assessing their application. Actual packet versions govern the saved run; identify legacy conventions rather than silently replacing them.

Remain read-only. Inspect existing artifacts and referenced evidence; start no code, test, provider, model, browser, PDF-render or valuation jobs. Return findings rather than editing the analysis, changing assumptions, granting waivers or merging. The coordinator controls any one bounded revision.

## Challenge the economic case

Treat the proposed conclusion as a hypothesis. Identify which assumptions do the most work and whether evidence supports their magnitude.

| Review question | Evidence to inspect |
|---|---|
| Does the thesis explain how money is earned? | Three to five operating/cash drivers; pricing power and competitive position; management delivery and capital allocation; plausible thesis-breaking evidence. |
| Are material figures comparable? | Exact report/provider definitions, period/currency/scale, annual/R12 and fiscal conventions, reported/adjusted EBIT, group/parent scope and justified substitutions. Numeric agreement alone is insufficient. |
| Do growth and profitability fit together? | Compatible history, capacity/demand/mix and scope changes; support for exceptional scale and margin in one central case; a coherent operating disappointment. |
| Is the multiple independently defended? | Earnings/claim consistency, business economics, own history and matched peers. Distinguish an independently supported estimate from a maintained-current-multiple condition; reverse-implied EBIT does not independently validate its assumptions. |
| Can the cash and equity bridge work? | Forecast cash generation as well as uses, reinvestment and working capital, gross financing/lease costs, dividends, acquisitions and outstanding claims, funding, dilution and no repeated credit for the same cash. |
| Do cases and weights mean what the report claims? | Outcome conditions/ranges, likelihood evidence and numerical judgment, uncertainty, dependencies, omitted tails and an alternative-weight hurdle check when material. Similar weights alone prove neither copying nor correctness. |
| Are returns and conclusions matched? | Per-case cash-flow returns first; dated prices/horizons and dividend timing; 10% starting hurdle versus 9% PV sensitivity; secondary IRR of weighted cash flows rather than averaged case IRRs; SIXRX as historical context. Explain legitimate legacy overrides. |
| Does it value the actual security? | Business perimeter, common ownership, share base, minority/pension/lease/acquisition claims and material transactions through the cutoff. A standalone benchmark does not establish a post-transaction share valuation. |

Keep a defensible company assumption when the evidence supports it. Propose a correction for its economic reason, not to spread company targets apart or make a worked example pass. Localize optional gaps so the useful analysis can still be judged. A missing material claim or unsupported principal dependency must remain beside the conclusion it limits.

## Return a bounded review

Use the existing hash-bound feedback format with an accept or revise verdict, findings and retained disagreements. Cite exact file sections, saved IDs or physical report pages for every material claim. For each finding explain the bounded verdict, reasoning, consequence and missing evidence for a larger claim. Separate arithmetic/source consistency from economic plausibility and outcome likelihood.

Prioritize findings that could alter the thesis, value, funding or hurdle conclusion. Distinguish a material defect from a disclosed conditional assumption or editorial improvement. An accept verdict describes the reviewed report's supported scope; it does not certify forecasts, calibrate probabilities or predict realized returns.

Completion: the coordinator can bind the review to the packet and exact analysis hash, identify justified revision requests and retain unresolved limitations. Review the bounded response once if asked; preserve the workflow's single-revision limit.

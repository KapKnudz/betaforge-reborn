---
name: betaforge-valuation-review
description: Independently challenge a saved Betaforge company valuation against its frozen philosophy, financial evidence and calculation definitions, returning bounded accept or revise findings.
metadata:
  status: draft
---

# Independent valuation review

Repository guidance stored outside active skill discovery. New packets preserve this guide for the coordinator's explicit reviewer handoff; the controller does not dispatch the reviewer. It does not replace a historical review verdict.

## Mandate and evidence

Use a fresh reviewer context with the frozen company packet, policy, submitted report, saved inputs and calculations. The coordinator supplies those artifacts and records your returned review. Follow [the existing workflow](../../analysis-workflow.md#3-challenge-the-draft-independently) and its review schema in [analysis_report.py](../../../betaforge/analysis_report.py).

Use the packet's frozen reviewer and analyst guides when present and record their identities in the review handoff. Do not silently apply live repository edits to a historical run. For legacy packets, identify which separately supplied guidance governs a retrospective supplement; lack of the new metadata does not invalidate the original report.

When supplied, inspect the full frozen [management history](../../management-history.md) and its identity. Challenge every captured transaction and the source-owner versus corroborated person/entity distinction, aliases, role/ownership dates, responsibility links, source scope and stated gaps. Check the report's readable row/source/pointer provenance against the raw captured payloads and source pages. A valid sidecar preserves evidence identity, not the correctness of its associations or an inherited supplement judgment. A fresh analyst must support its own forecasts. Check that the memo contains a compact, sourced management-history overview and material changes, with date precision and unresolved ownership/person links visible.

The canonical foundation is [analysis-policy.md](../../analysis-policy.md), derived from the combined investment philosophy, and the [calculation catalogue](../../calculations.md). Read the analyst's [calculation guide](../betaforge-company-analysis/references/calculations.md) and [memo structure](../betaforge-company-analysis/references/memo-structure.md) when assessing their application. Actual packet versions govern the saved run; identify legacy conventions rather than silently replacing them.

Remain read-only. Inspect existing artifacts and referenced evidence; start no code, test, provider, model, browser, PDF-render or valuation jobs. Return findings rather than editing the analysis, changing assumptions, granting waivers or merging. The coordinator controls any one bounded revision.

## Challenge the economic case

Treat the proposed conclusion as a hypothesis. For the two or three drivers that most affect value, trace the [business brief](../betaforge-company-analysis/references/business-evidence.md#write-the-business-brief-before-forecasting) where supplied. Check the rationale in the notes or saved report against the [material-assumption guidance](../betaforge-company-analysis/references/business-evidence.md#explain-material-assumptions): does evidence support the selected magnitude and timing, or only the direction? Trace remaining judgment through the cash/value calculation and the final call. Test whether the drivers can occur together with the assumed cash and capital needs. Use the [business-evidence tests](../betaforge-company-analysis/references/business-evidence.md#turn-a-judgment-into-an-evidence-test) when challenging quality claims. For each material input addressed by peers, verify the economic fit, financial definitions, source and cutoff dates, and the stated effect. Inspect the before and after values and basis, the new sensitivity, or the reason it stayed context only. Require separate pricing evidence and economic justification for any peer-driven multiple uplift.

| Review question | Evidence to inspect |
|---|---|
| Does the thesis explain how money is earned? | Three to five operating/cash drivers; pricing power and competitive position; management delivery and capital allocation; plausible thesis-breaking evidence. |
| Do the management checks support their conclusion? | Require explicit results or bounded evidence gaps for both [commitment/outcome and insider-evidence checks](../betaforge-company-analysis/references/business-evidence.md#check-management-delivery-and-insider-evidence). Inspect original commitments, revisions, responsible management where disclosed, deadlines and later comparable outcomes across available years. Check captured transaction coverage to exhaustion, date/correction/type/incentive qualifications and the consequence for confidence. Current target/latest actual or ownership levels alone do not complete these checks; missing terms do not establish dishonesty, no trades or an automatic valuation adjustment. |
| Are material figures comparable? | Exact report/provider definitions, period/currency/scale, annual/R12 and fiscal conventions, reported/adjusted EBIT, group/parent scope and justified substitutions. Numeric agreement alone is insufficient. |
| Do growth and profitability fit together? | Compatible history, capacity/demand/mix and scope changes; support for exceptional scale and margin in one central case; a coherent operating disappointment. |
| Is the multiple independently defended? | Earnings/claim consistency, business economics, own history and matched peers. Distinguish an independently supported estimate from a maintained-current-multiple condition; reverse-implied EBIT does not independently validate its assumptions. |
| Can the cash and equity bridge work? | Forecast cash generation as well as uses, reinvestment and working capital, gross financing/lease costs, dividends, acquisitions and outstanding claims, funding, dilution and no repeated credit for the same cash. |
| Do cases and any weights mean what the report claims? | Outcome conditions and ranges, dependencies and omitted tails. If weighted, check likelihood evidence, its applicability and an alternative-weight hurdle check when material. If unweighted, check the explanation and the conditions shown for clearing the hurdle. |
| Are returns and conclusions matched? | Per-case cash-flow returns first; dated prices/horizons and dividend timing; 10% starting hurdle versus 9% PV sensitivity; secondary IRR of weighted cash flows rather than averaged case IRRs; SIXRX as historical context. Explain legitimate legacy overrides. |
| Do the visuals support the decision? | Check displayed points against saved figures. Inspect the common IRR scale and hurdle, the separation of compatible actuals from dated forecast assumptions, and the inputs to the selected sensitivity or the verified scope and subtotals of the cash bridge. |
| Does it value the actual security? | Business perimeter, common ownership, share base, minority/pension/lease/acquisition claims and material transactions through the cutoff. A standalone benchmark does not establish a post-transaction share valuation. |

Keep a defensible company assumption when the evidence supports it. Propose a correction for its economic reason, not to spread company targets apart or make a worked example pass. Localize optional gaps so the useful analysis can still be judged. A missing material claim or unsupported principal dependency must remain beside the conclusion it limits.

## Return a bounded review

Use the existing hash-bound feedback format with an accept or revise verdict, findings and retained disagreements. Cite exact file sections, saved IDs or physical report pages for every material claim. For each finding explain the bounded verdict, reasoning, consequence and missing evidence for a larger claim. Separate arithmetic/source consistency from economic plausibility and outcome likelihood.

Prioritize findings that could alter the thesis, value, funding or hurdle conclusion. Distinguish a material defect from a disclosed conditional assumption or editorial improvement. A reconciled calculation does not validate its inputs; one disappointing sensitivity does not automatically require Wait. In a run comparison, check that discretionary input changes are not attributed to new evidence. An accept verdict describes the reviewed report's supported scope; it does not certify forecasts, calibrate probabilities or predict realized returns.

Completion: the coordinator can bind the review to the packet and exact analysis hash, identify justified revision requests and retain unresolved limitations. Review the bounded response once if asked; preserve the workflow's single-revision limit.

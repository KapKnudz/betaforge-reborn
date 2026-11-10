# Produce and review an analysis

Use this process during a working session when producing a new valuation or revising one after review. The coordinator maintains the [plan](../work/plan.json). The [policy](analysis-policy.md) owns financial choices; the [calculation catalogue](calculations.md) owns arithmetic.

[The visual process guide](analysis-process.md) explains the analyst's stated decisions and separates code-enforced checks, agent judgment and coordinator responsibilities.

```text
frozen evidence + policy
          ↓
one analyst → saved draft → independent challenge
                                  ↓
                         at most one revision
                                  ↓
                 saved report + review → local viewer
```

## 1. Freeze the question and evidence

Select the company, information cutoff, dated price, required reports and material mapping decisions. Freeze the policy and formulas with the packet. Use at least the latest five annual reports where available and the interims needed for current results. A later execution or mapping-review date does not refresh the market price or create a point-in-time backtest.

Before freezing, the coordinator researches the [material-event and security-scope check](skill-drafts/betaforge-company-analysis/references/business-evidence.md#check-material-events-and-security-scope), preserving selected disclosures and the checked coverage/gaps in admitted evidence. Apply the [canonical scope rule](analysis-policy.md#material-events-and-security-scope); required packet reading does not establish complete disclosure coverage.

New packets also freeze the selected repository analyst guides into `prompt.md`, with role/path/hash metadata in `analysis_guides`, and preserve the reviewer guide for the explicit handoff below. Inspect that metadata and the actual prompt rather than assuming skill discovery loads the documents. Existing packets and resumes retain their original prompt and guidance; do not attach current guides silently. The [packet contract](codex-integration.md) owns the delivery details.

For a requested five-year management/board and ownership history, prepare the [versioned evidence sidecar](management-history.md) from the frozen reports and captured datasets and supply `--management-history PATH`. Set the explicit requested window and preserve older context, every captured transaction version and unknown dates/identity matches. The new packet delivers the full index in its hashed prompt; it does not turn source associations or prior supplement judgments into issuer facts. A fresh analyst checks the sources and derives its own forecasts.

Completion: the packet has explicit identities, source hashes, coverage requirements and a question that can be answered from the preserved evidence. Missing optional context remains identified.

## 2. Run one lead analyst

Start a [business brief](skill-drafts/betaforge-company-analysis/references/business-evidence.md#write-the-business-brief-before-forecasting) from preserved issuer reports using the frozen guides. The coordinator handles any targeted external checks before freezing evidence for a new run. The lead analyst finishes the brief from admitted evidence before selecting forecasts. Structured submission does not require a separate brief.

The frozen analyst cannot browse for missing disclosures. Verify the event treatment from admitted sources and carry exclusions or incomplete coverage beside the conclusion and returns. New evidence requires a separate packet and run; preserve earlier packets, outputs and reviews.

Use Sol/xhigh with the existing evidence tools and `--structured`:

```sh
.venv/bin/python scripts/run_codex_analysis.py \
  --packet "$PACKET_DIR/packet.json" \
  --prompt "$PACKET_DIR/prompt.md" \
  --output "$RUN_DIR" --structured
```

The analyst reads the required reports, investigates material questions and submits six readable sections: thesis, earnings drivers, financial quality, management, valuation and risks. Facts, interpretations and assumptions carry distinct labels and saved references. Scenario values come from saved `valuation_case` outputs, with explicit dates and their precision. Management statements retain their wording, source, publication date, target period and definition.

Complete the [management commitment/outcome and insider-evidence checks](skill-drafts/betaforge-company-analysis/references/business-evidence.md#check-management-delivery-and-insider-evidence) in the management section and supporting notes. Preserve material commitments across the available years, revisions, original definitions/deadlines, responsible management when known and later compatible outcomes. Review all relevant captured insider rows through the cutoff, with dates, correction candidates, type definitions and incentive context; do not treat dataset ordering as chronology or net unmatched categories. Each check ends with its consequence for thesis confidence or an explicit bounded gap. A report can remain useful with missing optional evidence; it cannot imply that an omitted check was completed.

The report explains three to five drivers, useful quality diagnostics, one operating equation, the equity bridge, individual scenario returns, modest disappointments and evidence that would break the thesis. If the report uses weights, it explains their basis under the [probability policy](analysis-policy.md#probabilities-and-returns). A management ROCE target is compared with issuer ROCE. Related utilization or pricing guidance is labelled as a driver when shown beside EBIT margin.

Apply the policy's [writing rules](analysis-policy.md#output-and-calculation-discipline). The opening explains the investment case and its main uncertainty in plain financial language; each important forecast connects evidence, business mechanism and magnitude. The [investor examples](research/investor-writing-examples.md) are optional source reading for the coordinator, not additional issuer evidence or a replacement investment strategy. Review the forecast rationale, cash explanation and conclusion for clarity as part of the existing challenge.

Completion: required pages are delivered and `submit_analysis` accepts the report. This checks structure, source identity and saved calculation references. It does not certify economic judgment or enforce the presence of each requested scenario IRR. The independent review must check all three returns and their matched price, cash flows and horizon; the viewer falls back to saved valuation endpoints when compatible returns are missing. Probability validation checks reference presence and arithmetic, not whether the evidence supports the assigned likelihoods.

## 3. Challenge the draft independently

Dispatch a fresh Sol/xhigh reviewer with the same frozen evidence, policy, draft, saved inputs and calculations, and the manual business brief when used. The reviewer reads existing artifacts; it changes no files, starts no code, test, provider, model, browser or PDF-render runs, and grants no waivers. The coordinator saves its returned challenge as `draft-review.json` using `betaforge.tools.write_json`. If the draft is accepted, also save that exact review as `analysis-review.json` for display.

For packets with `analysis_guides`, verify and deliver the frozen reviewer guide and the frozen analyst guides as part of that handoff, recording their paths/hashes. This remains a coordinator action, not automatic reviewer dispatch. The reviewer must check both management evidence chains and the stated confidence consequence, including any absence/coverage claim. Source identity and complete pagination do not establish economic meaning or management motives.

For packets with `management_history`, also deliver the verified full sidecar and its company/cutoff/window/path/hash metadata. Challenge the distinction between reported source owners and corroborated people/entities, dated roles and ownership, responsibility links, scope omissions and every captured transaction row. Row/source/pointer and sidecar IDs can support readable provenance notes; they do not introduce new report or calculation reference types.

Challenge the thesis. Cover business mechanics, management comparisons, financial definitions, earnings versus cash, capital allocation and dilution, operating forecasts, the multiple and equity bridge, return timing, any probability coverage and disconfirming evidence. Check how each material use of peer evidence affected the analysis. Cite file sections and saved references. For each finding, give a bounded verdict, reasoning and missing evidence. Distinguish a supported local claim from a broader unverified claim. Name any unresolved disagreement.

Challenge the source of forecast cash as well as its uses. Connect assumed cash generation to the earnings path, noncash items, cash taxes, interest, working-capital movements and recurring investment. A compact reconciliation is enough; terminal earnings alone do not explain average cash over the horizon. Keep unsupported components explicit rather than inventing them.

Challenge the [event check](skill-drafts/betaforge-company-analysis/references/business-evidence.md#check-material-events-and-security-scope): source coverage, distinct dates/status, each event's disposition across earnings, funding, claims and shares, and whether the visible conclusion/return limitation matches the supported security scope.

Bind the review to the packet and exact `analysis.json` hash using the feedback schema in `betaforge/analysis_report.py`. The viewer accepts `analysis-review.json` only when it covers the current report. Keep draft feedback with the private artifacts; a review of an earlier draft does not approve a later revision.

Keep independent findings separate from any coordinator instructions added to revision feedback. Label their authorship and preserve the independent review alongside the combined feedback.

Completion: a saved `accept` or `revise` verdict explains the material findings and remaining limits. Execution completion and content review remain separate statuses.

## 4. Revise once, then preserve

For a justified `revise` verdict, the coordinator requests one explicit continuation:

```sh
.venv/bin/python scripts/run_codex_analysis.py \
  --packet "$PACKET_DIR/packet.json" \
  --prompt "$PACKET_DIR/prompt.md" \
  --output "$RUN_DIR" --structured --resume \
  --review-feedback "$RUN_DIR/draft-review.json"
```

The controller preserves the draft artifacts and frozen feedback. The analyst addresses justified findings or explains disagreement. Revision permits at most two targeted research rounds; there is one revision, with a cumulative 7,200-second analyst limit across the structured run. The initial investigation also retains its existing round and finalization limits. Changes to evidence, prompt or implementation require a separate run.

The reviewer may make one focused read-only check of the response. Save that returned review as `analysis-review.json`, bound to the final report. Without that check the revised report remains unreviewed; do not copy the draft verdict into the current-review file. If material issues remain, show them and stop; another automatic rewrite is outside this process.

Export the saved run for the [local viewer](saved-analysis-view.md), then archive the evidence, draft, feedback, final report and review through the [private handoff](research-handoff.md). Opening the website reads saved results. It does not launch this process.

## 5. Verify the effect of management evidence

When reviewing a change to management or insider evidence, start with the saved memos. Define the comparison questions before reading the results and record the exact identities of the baseline and updated reports, inputs, calculations, histories and reviews. Keep the financial outputs unchanged during this initial audit.

For each material finding, trace the source and its interpretation to a named forecast assumption, sensitivity, confidence qualification, monitoring condition or explicit reason for treating it as context only. Cite the actual memo passages and any saved input/calculation IDs. Separate financial treatment derived from disclosed instrument terms from interpretations of insider activity.

Read that chain alongside the investment conclusion. If the conclusion stays the same, identify the decisive constraint, such as price, return or funding, and the evidence that would reopen the decision. An unchanged forecast or conclusion can be justified; missing transmission needs an explanation or a bounded correction. Do not require a numerical adjustment or a different investment call merely to demonstrate impact.

Compare the baseline passages directly. Distinguish newly added or corrected reasoning, better support for an existing judgment, and reasoning that was already present. Record discretionary forecast changes separately. Complete captured-row delivery verifies coverage; this audit verifies how the memo uses the evidence. Neither establishes an isolated causal effect of the guidance or better forecast accuracy.

Preserve the detailed comparison privately with exact citations and artifact hashes, then obtain a fresh independent read-only challenge. The public plan records the bounded result and next action. Request another valuation only if a specific unresolved question requires it; preserve the original outputs and the single-revision limit above.

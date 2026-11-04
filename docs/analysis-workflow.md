# Produce and review an analysis

Use this process during a working session when producing a new valuation or revising one after review. The coordinator maintains the [plan](../work/plan.json). The [policy](analysis-policy.md) owns financial choices; the [calculation catalogue](calculations.md) owns arithmetic.

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

Completion: the packet has explicit identities, source hashes, coverage requirements and a question that can be answered from the preserved evidence. Missing optional context remains identified.

## 2. Run one lead analyst

Use Sol/xhigh with the existing evidence tools and `--structured`:

```sh
.venv/bin/python scripts/run_codex_analysis.py \
  --packet "$PACKET_DIR/packet.json" \
  --prompt "$PACKET_DIR/prompt.md" \
  --output "$RUN_DIR" --structured
```

The analyst reads the required reports, investigates material questions and submits six readable sections: thesis, earnings drivers, financial quality, management, valuation and risks. Facts, interpretations and assumptions carry distinct labels and saved references. Scenario values come from saved `valuation_case` outputs, with explicit dates and their precision. Management statements retain their wording, source, publication date, target period and definition.

The report explains three to five drivers, useful quality diagnostics, one operating equation, the equity bridge, company-specific probabilities, modest disappointments and evidence that would break the thesis. It uses the policy rather than inventing a scorecard. A management ROCE target is compared with issuer ROCE; related utilization or pricing guidance is labelled as a driver when shown beside EBIT margin.

Completion: required pages are delivered and `submit_analysis` accepts the report. This checks structure, source identity and saved calculation references. It does not certify economic judgment.

## 3. Challenge the draft independently

Dispatch a fresh Sol/xhigh reviewer with the same frozen evidence, policy, draft, saved inputs and calculations. The reviewer reads existing artifacts; it changes no files, starts no code, test, provider, model, browser or PDF-render runs, and grants no waivers. The coordinator saves its returned challenge as `draft-review.json` using `betaforge.tools.write_json`. If the draft is accepted, also save that exact review as `analysis-review.json` for display.

Challenge the thesis rather than confirm it. Cover business mechanics, management comparisons, financial definitions, earnings versus cash, capital allocation and dilution, operating forecasts, the multiple and equity bridge, probability coverage, return timing and disconfirming evidence. Cite file sections and saved references. For each finding, give a bounded verdict, reasoning and missing evidence; distinguish a supported local claim from a broader unverified claim. Name any unresolved disagreement.

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

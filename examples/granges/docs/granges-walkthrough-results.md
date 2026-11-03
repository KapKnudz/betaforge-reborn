# Gränges retrieval walkthrough

Both workflows completed and scored **40/40 on the eight source-based questions**. The independent review found no material numerical, period or citation error in the scored claims. This is a tie on this task, not proof of general equivalence. [Rubric](../data/reference-rubric.md), [review](../data/comparison-review.json).

## Results

| Metric | Reports upfront | Reports through tools |
|---|---:|---:|
| Independent score | 40/40 | 40/40 |
| Prepared text pages supplied | 921 in initial request | 921 in audited reads |
| Model-run time | 6.0 minutes | 6.9 minutes |
| Full-page tool reads | 0 | 85 |
| Literal searches | 0 | 4 |
| Original-page image checks | 9 | 21 |
| Calculation-tool results | 20 | 20 |
| Completed compactions | 0 | 1 |
| Accumulated uncached input tokens | 1,564,505 | 953,810 |
| Accumulated cached input tokens | 21,706,368 | 5,716,864 |
| Accumulated output tokens | 7,805 | 12,745 |

Both used GPT-6.1 Sol at high reasoning through pi 1.4.0, identical source/question hashes, original-page image access and the same arithmetic tool. Times exclude shared acquisition/preparation. Token counts accumulate across requests and include the tools workflow's compaction call; they are not unique corpus size or subscription charges. [Derived metrics](../../../data/granges-walkthrough/runs/comparison-summary.json), [protocol — observed execution facts](../data/protocol.md#observed-execution-facts).

The complete upfront request was accepted with **763,408 input tokens**, despite pi's catalogue describing a 500K context. This proves acceptance of that request on this route, not a guaranteed maximum context size. The installed Codex CLI rejected the same model, so both trials used the working pi route. [Protocol — model and harness](../data/protocol.md#model-and-harness).

## What the independent review established

Each question scored 5/5 in both answers: five-year financial series; revenue versus physical demand; strategy evolution; sustainability comparability; cash-flow definitions; the 2026 fire and changing outlook; adjusted-profit reconciliation; and conflicting acquisition chronology. Both audits contain 20 external calculations with source-linked operands. [Review — question findings](../data/comparison-review.json), [upfront final answer, Q1–Q8](../../../data/granges-walkthrough/runs/upfront/answer.md), [tools final answer, Q1–Q8](../../../data/granges-walkthrough/runs/tools/answer.md).

Both preserved published numeric discrepancies instead of changing source figures to force agreement. Both retained the conflicting acquisition/break-even chronology. The tools answer's Q5 wording should say “residual consistent with rounding”; the exact cause is not established. This did not change its rubric score. Candidate answers are preserved unchanged. [Rubric — Q5/Q7/Q8](../data/reference-rubric.md), [tools answer — Q5](../../../data/granges-walkthrough/runs/tools/answer.md).

The audits establish that every prepared text page was supplied. They do not establish comprehension of every page; the models' own claims that everything was “read” should be interpreted with that limit. [Protocol — arms](../data/protocol.md#arms).

## Acquisition and PDF findings

The eight originals were downloaded directly from Gränges' IR archive: annuals 2021–2025 and Q1/H1/Q3 2026, totaling 921 pages and about 56 MB. URLs, dates and hashes are preserved. A separate public MFN archive check found all eight releases and matching publication dates. Its PDF attachment downloads returned HTTP 403, so byte identity with the issuer originals remains unverified. [Source manifest](../data/source-manifest.json), [MFN check](../data/mfn-discovery.json).

Native extraction produced about 484,000 whitespace-delimited words. Visual QA of eight sample pages found split numeric characters and reordered note text; it did not validate the entire corpus. Both runs could view original pages when needed. Native extraction is therefore a useful reading representation, not a verified numeric database. [Prepared corpus index](../../../data/granges-walkthrough/prepared/index.json), [extraction QA](../data/qa/extraction-qa.json).

No Börsdata responses were included. Its key can be configured locally in ignored `.env.local`; adding data later must not silently change this frozen comparison.

## Recommendation and limits

Retain deterministic acquisition and reusable, page-linked reports as the common foundation. Both exposure methods are viable for this corpus. Keep whole-report upfront loading as a tested baseline and report tools for sequential reading and verification; this experiment supplies no answer-quality reason to mandate only one.

For a later product default, context capacity and reliability across representative smaller issuers matter more than this small timing difference. The tool workflow processed less accumulated context here, but it also compacted earlier evidence once. That is a trade-off to test, not proof of better reasoning. [Metrics](../../../data/granges-walkthrough/runs/comparison-summary.json), [protocol — arms and evaluation](../data/protocol.md).

Missing evidence for a broader architecture claim: repeated runs, held-out questions, smaller issuers, matched compaction policies, selective-reading tests, and actual Börsdata/MFN acquisition integration. This was an evidence-handling probe, not a full valuation or a production-system validation. [Independent review — limitations](../data/comparison-review.json).

## Reproducibility and checks

Scripts preserve source hashes, prepare page-addressable text, expose bounded report/image/calculation tools, and run the two trials with a two-hour outer deadline. Source/question hashes remained unchanged. Checks passed for PDF signature/hash validation, page bounds and coverage accounting, search bounds, arithmetic failures, real image rendering, and bounded child-process termination. Both model runs completed without model/tool errors. [Runner](../scripts/run_granges.py), [tool self-check](../scripts/test_granges_tools.mjs), [fetch validation](../scripts/fetch_granges.py), [metrics](../../../data/granges-walkthrough/runs/comparison-summary.json).

The workspace is connected to `KapKnudz/betaforge-reborn` on local branch `feat/granges-walkthrough`, based on the existing `main` history. No commit or push was made during this walkthrough. The local review page uses Lavish's Tailwind/DaisyUI fallback because the repository has no existing UI design system.

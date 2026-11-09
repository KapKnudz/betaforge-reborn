# How Betaforge produces an analysis

Betaforge preserves evidence, asks one analyst to explain the business, calculates from saved inputs and uses a separate reviewer to challenge the result. The Company viewer opens saved work. This document explains the current system; the [plan](../work/plan.json) owns delivery status.

## Technical architecture

```text
Börsdata + MFN / original company reports
                  ↓
raw captures + SQLite observations + source files
                  ↓
frozen company packet + policy + formula catalogue
                  ↓
bounded Codex analyst tools ↔ named Decimal formulas
                  ↓
saved analysis + inputs + calculations + audit artifacts
                  ↓
coordinator dispatches independent challenge → at most one revision
                  ↓
saved report + current review when obtained → explicit export
                  ↓
read-only Company viewer
```

Acquisition, storage, preparation, arithmetic, execution and presentation have separate owners. Public Git contains code, policies, documentation and safe delivery status. Raw evidence, frozen packets, exact research and reviews use ignored/private storage. Credentials stay local and separate from research archives. An explicitly configured private export can be served locally; that does not make the underlying evidence public. Opening the viewer performs no provider acquisition or model call. See [architecture: Ownership and Boundaries](architecture.md#ownership) and [saved analysis view: Add a saved company run](saved-analysis-view.md#add-a-saved-company-run).

The source map includes selected published reports. It does not establish a complete automated MFN collector: the [worked example's discovery record](../examples/granges/data/mfn-discovery.json) shows issuer PDFs and blocked supplemental MFN attachment downloads. General report discovery and wider report coverage remain separate work in [the plan](../work/plan.json).

The review step above is a coordinator responsibility. No autonomous review service runs inside the analyst controller. Export can accept a completed unreviewed report, so the diagram describes the intended working process rather than a mandatory review gate in code. See [workflow: Challenge the draft independently](analysis-workflow.md#3-challenge-the-draft-independently) and [`build_structured_saved_view`](../betaforge/saved_view.py), particularly its optional `analysis-review.json` branch.

## Who does what

| Responsibility | Meaning | Boundary |
| --- | --- | --- |
| **Code-enforced** | Check source/artifact identity, tool access, delivery coverage, named arithmetic and report structure. | Passing these checks does not establish financial truth. |
| **Agent judgment** | Interpret business mechanics, choose economic definitions and forecasts, assess the basis for any weights and challenge conclusions. | A plausible explanation is not a calibrated prediction. |
| **Coordinator · session policy** | Select the question and corpus, dispatch a fresh independent reviewer, save feedback and request an explicit revision. | These session actions are not automatically dispatched by the analyst runner. |

The lead analyst and independent reviewer are separate roles. The reviewer reads the same frozen evidence, policy, draft, saved inputs and calculations, and returns findings without changing files, starting new runs or granting waivers. The coordinator preserves the returned challenge. See [workflow: Run one lead analyst](analysis-workflow.md#2-run-one-lead-analyst) and [Challenge the draft independently](analysis-workflow.md#3-challenge-the-draft-independently).

## Draft skill guides

The local workbench lists these guides under **Architecture → Skills**. They describe intended use. The current runner delivers the packet policy and tools, while these guides are available for manual use as drafts.

| Guide | When to use it | Owner and output |
| --- | --- | --- |
| [Market and peer research](skill-drafts/betaforge-market-peer-research/SKILL.md) | Before freezing, when issuer evidence leaves a material question | Researcher returns a bounded answer or gap with sources and implications. The coordinator decides what enters the packet. |
| [Company analysis](skill-drafts/betaforge-company-analysis/SKILL.md) | While analysing the frozen evidence and building scenarios | Lead analyst writes the business brief before selecting forecast inputs for the named calculations. |
| [Financial report writing](skill-drafts/betaforge-financial-report/SKILL.md) | As the lead analyst prepares the draft | The same analyst writes the six-section memo from the saved evidence and results. |
| [Independent valuation review](skill-drafts/betaforge-valuation-review/SKILL.md) | After the draft | Separate reviewer challenges the material evidence, assumptions and conclusions. |

## What the analysis tries to understand

The analyst starts with three to five earnings and cash drivers and separates business quality from attractiveness at the dated price. Pricing power, competitive advantages, operating leverage and management’s capital allocation need business evidence. Use compatible company history first. For each material input addressed by peers, record a changed assumption, a new sensitivity or why the comparison stays as context. See [investment philosophy](analysis-policy.md#investment-philosophy), [evidence and comparisons](analysis-policy.md#evidence-and-comparisons) and [financial quality](analysis-policy.md#financial-quality).

The case follows earnings through working capital, reinvestment, financing, minority interests and dilution to common shareholders. It uses one understandable operating equation, normally revenue × EBIT margin or volume × earnings per unit. A complete claims-and-shares bridge connects that earnings forecast with per-share value. It tests modest disappointments, explains interactions and names observations that would weaken the thesis. See [policy: Valuation methods](analysis-policy.md#valuation-methods) and [Output and calculation discipline](analysis-policy.md#output-and-calculation-discipline).

The current primary method is forward operating EV/EBIT. A market-implied EBIT calculation shows the operating result required by selected assumptions. Scenario probabilities are optional. When evidence supports numerical weights, the analyst cites that evidence and explains the choice and its limits. The user can override the proposal. See [policy: Probabilities and returns](analysis-policy.md#probabilities-and-returns) and [calculation catalogue: Expected return, personal hurdle and historical comparison](calculations.md#expected-return-personal-hurdle-and-historical-comparison).

The inspectable reasoning is the saved rationale, selected evidence, assumptions, formulas and independent challenge. It is not a complete record of internal model deliberation. The observable report contract requires labelled paragraphs, references and scenario rationales; see [`validate_report`](../betaforge/analysis_report.py) and [`submit_analysis`](../betaforge/tools.py).

## 1. Set the question and freeze the evidence

**Inputs → outputs:** explicit company, information cutoff, dated market price, required report corpus and material mapping decisions → frozen database, source blobs, report index, policy, formula catalogue and packet identities.

**Coordinator · session policy:** select a corpus sufficient for the question, normally the latest five annual reports where available plus interims needed for current results. Identify missing context. A later execution or mapping-review date does not refresh the price or create a point-in-time backtest. See [workflow: Freeze the question and evidence](analysis-workflow.md#1-freeze-the-question-and-evidence).

**Code-enforced:** storage freeze makes an independent SQLite backup and copies source blobs after checking their hashes. Analyst initialization verifies database/blob hashes, report/preparation hashes, physical page structure, selected instrument and source-linked facts. New analysis packets freeze policy and catalogue files with hashes. See [`EvidenceStore.freeze`](../betaforge/storage.py), [`EvidenceTools.__init__`](../betaforge/tools.py), and [Codex integration: Entry point and packet](codex-integration.md#entry-point-and-packet).

**Limit:** these checks establish agreement with selected preserved inputs. They cannot show that all material evidence was selected, that it is fresh enough or that a financial field has the intended accounting meaning. The corpus selection remains explicit; see the caller-supplied `required_reports` contract in [`EvidenceTools.__init__`](../betaforge/tools.py).

## 2. Read, reconcile and save inputs

**Inputs → outputs:** frozen reports, observations and source metadata → delivered-page coverage, source references, explicit assumptions and report-derived input records.

**Agent judgment:** read the business, reconcile source differences, inspect original page images when extraction is ambiguous and select comparable periods, adjustment bases and ownership scope. Financial definitions must remain visible. See [policy: Financial quality](analysis-policy.md#financial-quality), [material input rules](material-inputs.md) and [Codex integration: Tool contract](codex-integration.md#tool-contract).

**Draft manual practice:** start a [business brief](skill-drafts/betaforge-company-analysis/references/business-evidence.md#write-the-business-brief-before-forecasting) with preserved issuer reports. Explain why customers buy and which recent developments could change earnings or cash. The coordinator handles bounded external research on material gaps before freezing evidence for a new run. The runner does not require a separate brief.

**Code-enforced:** `read_report` delivers complete consecutive physical pages within a bounded response and records delivery coverage. `search_reports` returns bounded snippets and does not increase full-page coverage. Financial/dataset queries are bounded and selected-company access is constrained. `record_input` saves a numeric assumption or a report input with report/page and a quote matching saved text; it creates a content-based input ID. See [`EvidenceTools.coverage`, `read_report`, `search_reports`, `get_financials`, `get_dataset`, `record_input` and `resolve_input`](../betaforge/tools.py).

**Limit:** delivery is not comprehension. A matching quotation does not independently verify the numeric extraction, economic definition or reconciliation. Report inputs are explicitly marked `analyst_extracted_not_independently_reconciled`. Search coverage is distinct from complete report delivery. See those same tool methods and [Codex integration: Tool contract](codex-integration.md#tool-contract).

## 3. Explain drivers and calculate scenarios

**Inputs → outputs:** saved observations and assumptions → named calculation records, bear/base/bull values and annual cash-flow returns, and sensitivities.

**Agent judgment:** connect each material forecast to its evidence anchor, business mechanism and selected magnitude. Test the joint growth/margin assumption against history, current evidence and capital needs. Explain multiple selection, retained cash, additional claims, non-operating assets and future diluted shares without counting benefits or claims twice. See [policy: Valuation methods](analysis-policy.md#valuation-methods) and [catalogue: Primary scenario bridge](calculations.md#primary-scenario-bridge-valuation_case).

**Draft manual practice:** use the completed business brief to show what changes an assumption, warrants a sensitivity or remains context. Carry material unanswered questions into the affected case.

**Code-enforced:** the analyst calls named financial formulas using saved IDs; the wrapper applies each original source scale once. Python Decimal arithmetic retains normalized inputs, formula/version, outputs, units, missing inputs and warnings. Known incompatible units, currencies and paired periods are rejected. Some capital/earnings checks reject known quarter/YTD or opening-date conflicts. See [`EvidenceTools.calculate_financial` and `_financial_periods`](../betaforge/tools.py), [`financials.evaluate`](../betaforge/financials.py), and [catalogue: Common conventions](calculations.md#common-conventions).

**Limit:** the registry currently assumes SEK, actual tonnes and actual shares. Undated assumptions and economically mismatched scope still require judgment. Group cash conversion is not automatically parent-common free cash flow; issuer ROCE, provider ROIC and selected operating ROIC retain different definitions. See [catalogue: Implemented named formulas](calculations.md#implemented-named-formulas).

Each case has an annual cash-flow IRR at the dated price. Compare the three returns with the personal hurdle and keep the historical SIXRX total return separate. With supported probabilities, an optional weighted IRR first weights the scenario payments and then solves their IRR. The formulas support constant year-end dividends and a common integer horizon of 1–10 years. A change in the present-value discount rate alone leaves cash-flow IRR unchanged. See [catalogue: Expected return, personal hurdle and historical comparison](calculations.md#expected-return-personal-hurdle-and-historical-comparison), and `scenario_weighted_values` / `expected_cashflow_irr` in [`financials.evaluate`](../betaforge/financials.py).

## 4. Submit a traceable report

**Inputs → outputs:** evidence, saved assumptions and calculations → `analysis.json`, readable `answer.md`, input/calculation artifacts and hashes binding those saved artifacts.

**Code-enforced:** require six sections, labelled paragraphs with resolvable references, and bear, base and bull cases with compatible dates. The tool copies scenario targets and present values from saved `valuation_case` outputs. New reports explain omitted probabilities or supply three saved weights summing to one, each with a rationale and factual source reference. Structured completion requires complete mandatory page delivery and an accepted submission. See [`validate_report`](../betaforge/analysis_report.py), [`EvidenceTools.submit_analysis`](../betaforge/tools.py) and [`_run_with_tools`](../betaforge/codex_runner.py).

**Agent judgment:** save the causal investment case and its uncertainty, including scenario and probability rationales, disappointment checks, disconfirmers and management’s important promises versus outcomes. See [policy: Output and calculation discipline](analysis-policy.md#output-and-calculation-discipline).

**Limit:** acceptance is structural and identity validation. It is not an economic verdict. `management_comparisons` may be empty; required rationale text is not checked for analytical quality. Three valid scenario weights do not establish a complete outcome distribution. See the list/text checks and `syntax_and_identity_valid` status in [`validate_report`](../betaforge/analysis_report.py).

## 5. Challenge independently and revise once

**Inputs → outputs:** exact draft plus frozen evidence/policy and saved inputs/calculations → independent findings, an `accept` or `revise` verdict, missing evidence and unresolved disagreement; one explicit analyst revision if justified.

**Coordinator · session policy:** dispatch a fresh independent read-only reviewer and save its return as `draft-review.json`. Challenge business mechanics, financial definitions, management comparisons, earnings versus cash, capital allocation, dilution, forecasts, multiple/claims bridge, probability coverage and return timing. Each finding distinguishes its supported local claim from any larger unverified claim. Preserve independent authorship separately from coordinator instructions. See [workflow: Challenge the draft independently](analysis-workflow.md#3-challenge-the-draft-independently).

**Code-enforced:** feedback validates against the packet and exact draft hash. The runner requires an explicit `revise` verdict, preserves prior artifacts, permits one revision and reopens at most two targeted research rounds. Structured analyst execution is limited to 7,200 cumulative seconds across continuations. See [`validate_feedback` and `validate_review`](../betaforge/analysis_report.py), [`_run_with_tools`](../betaforge/codex_runner.py) and [`EvidenceTools.reopen_revision_research`](../betaforge/tools.py).

**Limit:** hashes establish which draft was reviewed; they cannot prove reviewer independence or challenge quality. The coordinator must obtain a focused independent check of a revised report and save `analysis-review.json` bound to its new hash. A draft verdict cannot approve the revision. If material issues remain, preserve them and stop. The controller does not autonomously dispatch reviewers. See [workflow: Revise once, then preserve](analysis-workflow.md#4-revise-once-then-preserve).

## 6. Preserve, export and inspect

**Inputs → outputs:** completed structured run and saved artifacts, plus current review when present → explicit saved-view export and private research archive.

**Code-enforced:** export revalidates run/report/input/calculation identity, selected issuer, required reading coverage, report structure, scenario references and narrative agreement. If `analysis-review.json` exists, validate it against the exact report hash. The local server exposes only configured saved exports. See [`build_structured_saved_view`](../betaforge/saved_view.py) and [saved analysis view](saved-analysis-view.md).

**Coordinator · session policy:** preserve evidence, draft, feedback, final report and current review together. Keep the plan’s delivery state distinct from investment confidence. See [workflow: Revise once, then preserve](analysis-workflow.md#4-revise-once-then-preserve) and [private handoff](research-handoff.md).

**Limit:** export does not require a review file. A completed, structurally valid unreviewed report can reach the viewer. `reviewed_at` is populated from `run.finished_at`; it is a completion timestamp, not proof of economic review. The separately saved `analysis_review` carries the current review verdict. See the review-file branch and view construction in [`build_structured_saved_view`](../betaforge/saved_view.py).

## Execution boundaries and stopping rules

The analyst runner supplies only client-owned evidence tools. Its per-run settings disable native shell, browser, computer use, apps, connectors, delegation and hooks, and omit environment access; unexpected native tool activity fails the run. It requests exact `gpt-6.1-sol` with `xhigh` reasoning, disables provider model fallback and rejects a different returned model. These are configuration and protocol controls; a changed installed Codex build needs renewed integration verification. The coordinator operates outside this bounded analyst process. See `MODEL`, `CONFIG`, `AppServer` and `_run_with_tools` in [`codex_runner.py`](../betaforge/codex_runner.py), plus [Codex integration: Protocol and verification scope](codex-integration.md#protocol-and-verification-scope).

After mandatory reading, initial research closes at ten recorded rounds, two recorded rounds without a newly cited retrieved evidence ID, or explicit finalization. Evidence reads then stop; up to 200 finalization calls remain under the active deadline. Revision reopens at most two recorded targeted rounds. Novel evidence IDs are a bounded, auditable proxy, not proof of useful semantic progress. See [`EvidenceTools.finish_research_round`, `call` and `reopen_revision_research`](../betaforge/tools.py).

Cancellation and deliberate resume preserve audit and tool state, and check packet/prompt/implementation identity. A deliberately resumed unstructured invocation has a fresh invocation deadline; structured runs retain the cumulative 7,200-second cap. No deadline or research limit guarantees a correct thesis. See [`_run_with_tools`](../betaforge/codex_runner.py) and [Codex integration: Cancellation, recovery and records](codex-integration.md#cancellation-recovery-and-records).

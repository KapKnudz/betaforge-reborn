# Project architecture

Betaforge separates data collection, interpretation, arithmetic and presentation. The [investment policy](analysis-policy.md) owns valuation choices; [adopted decisions](planning/decisions.md) record agreements; [work/plan.json](../work/plan.json) tracks delivery.

The workbench's **Architecture** view shows the system map and analysis stages. [The process guide](analysis-process.md) explains each handoff, the analyst and reviewer roles, saved decisions, code checks and their limits.

```text
Börsdata + original reports
            ↓
Acquisition → raw files + SQLite → frozen company packet
                                         ↓
                           Codex evidence tools + named formulas
                                         ↓
                              saved analysis + audit records
                                         ↓
                              read-only saved-run viewer

work/plan.json → local research workbench ← explicit company catalogue + saved-view exports
```

## Ownership

| Layer | Location | Responsibility |
|---|---|---|
| Acquisition | `betaforge/borsdata.py`, fetch scripts | Download original responses with safe diagnostics; preserve sources. |
| Evidence | `betaforge/storage.py` | Normalize observations, keep definitions/provenance/revisions, freeze SQLite and source blobs. |
| Preparation | `scripts/prepare_codex_packet.py` | Select one issuer and freeze reports, evidence, policy and context for a run. |
| Curated history evidence | `betaforge/management_history.py` | Validate optional sourced party/role/ownership history and complete captured transaction links; no identity inference or financial arithmetic. |
| Report preparation | `scripts/prepare_reports.py` | Verify preserved PDF identities and produce physical-page text; keep the full archive separate from mandatory reading. |
| Arithmetic | `betaforge/financials.py` | Named, versioned deterministic formulas defined in [calculations](calculations.md). |
| Analyst access | `betaforge/tools.py` | Bounded reads, saved inputs, provenance and calculation calls. |
| Execution | `betaforge/codex_runner.py` | Run limits, cancellation/resume, model interaction and saved outputs. |
| Analysis report | `betaforge/analysis_report.py` | Structured reasoning, sourced management comparisons, dated scenario references and hash-bound review feedback. |
| Private preservation | `scripts/archive_research.py` | Versioned research bundles and verified restore. |
| Saved-run presentation | `betaforge/saved_view.py`, `scripts/export_saved_analysis.py` | Verify existing artifact identity and package saved results for local inspection; no new financial arithmetic. |
| Research workbench | `work/`, `scripts/serve_progress.py`, `web/progress/` | Session-maintained progress, visual architecture/process explanation and navigation over explicitly configured company metadata and saved results. |
| Design reference | `DESIGN.md`, `web/prototypes/company/`, `scripts/preview_company_design.py` | Preserve the approved design trial. The working Company view is maintained in `web/progress/`. |
| Company examples | `examples/<company>/` | Issuer prompts, reconciliations, replay scripts and public example documents. |

## Boundaries

- Acquisition is independent of analysis. Opening a saved result does not fetch data or rerun the analyst. [ADR 0001](adr/0001-persist-company-evidence.md)
- Raw provider values, report-derived facts and selected inputs retain their identities. SQLite and source files are backed up together; ingestion has one writer. [ADR 0002](adr/0002-local-evidence-storage.md)
- Financial arithmetic belongs in the named formula registry. The analyst explains assumptions and choices; the interface displays their saved records. The first formulas use SEK and operating-company concepts. [Policy](analysis-policy.md), [formula conventions](calculations.md#common-conventions)
- A new analysis follows the [bounded analyst and independent challenge process](analysis-workflow.md). Report structure and evidence identity are checked by code; economic judgment is reviewed separately. The session coordinator dispatches the reviewer through the existing harness, then requests at most one explicit analyst revision.
- Shared modules take explicit company inputs. Issuer assumptions belong in examples or private analysis inputs.
- Public Git holds code, policy, documentation and safe project status. Credentials, original evidence, watchlists and exact saved analyses belong in ignored/private storage. [Handoff](research-handoff.md)
- The progress plan is delivery state, not financial evidence or investment confidence. The local workbench serves an explicit set of public files and optionally configured private saved-view exports. It never starts analysis. The first viewer does not complete the broader mapping and decision-record work. [Local viewing](saved-analysis-view.md)

## Extension rule

Add the smallest capability to its owning layer. Change a boundary only for a demonstrated need and record the decision. A new service, database or agent framework needs a concrete requirement that the current modules cannot satisfy.

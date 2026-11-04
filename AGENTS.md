# Betaforge working instructions

## Start and resume

1. Read [work/plan.json](work/plan.json) and run `git status --short` before editing. Preserve unrelated work.
2. Match the user's request to a task. When asked to continue the plan, use `next_task`. Inspect the affected code and evidence before choosing a change.
3. Mark the task `in_progress` and update the session handoff. Read [architecture](docs/architecture.md) before changing module boundaries; read [policy](docs/analysis-policy.md) and [formulas](docs/calculations.md) before changing financial behavior.

## Keep the plan current

- Re-read the plan at scope changes, verified milestones and handoff. Record progress, blockers, changed priorities and the next concrete action then; a running chat is not durable project state.
- Follow [work/README.md](work/README.md) for the plan format. A task is `done` only when its acceptance criteria have evidence. Report partial results and missing checks explicitly.
- Have one coordinating agent edit the plan when workers run in parallel. Preserve other tasks and validate the JSON after updates.
- Update during working sessions. The dashboard reads this file; background execution requires a separate user request.

## Model routing

- Use `gpt-6.1-sol`/`xhigh` for the coordinating thinker, financial judgment and valuation runner. Astra is excluded. If the required Sol/`xhigh` is unavailable, stop and report it; never silently substitute a model.
- Delegate bounded implementation to the built-in `worker` on `gpt-6.1-sol`/`high`; escalate ambiguous design or financial meaning to the thinker.
- Use `explorer` on `gpt-6-luna`/`high` for narrow read-only file/source scans, `visual_evidence` on `gpt-6.1-terra`/`medium` for visual/UI/PDF layout evidence, and a fresh independent `reviewer` on `gpt-6.1-sol`/`high`. Return ambiguity and financial judgment to the thinker.
- When these roles are not exposed by the harness, pass those exact model/effort settings explicitly. Give cross-model workers fresh scoped briefs. Use a full-history fork only when its inherited model and effort match the assigned role.
- If Luna or Terra is unavailable, explicitly use Sol at the role's effort and report the substitution. For a difficult independent review, use a fresh generic Sol/`xhigh` agent: the configured `reviewer` pins `high` and overrides spawn settings.
- Read [the model policy](docs/model-routing.md) when selecting or changing roles, checking effective configuration, or handling unavailable models. Project defaults apply to new runs; they cannot change the model executing an existing turn.

## Boundaries and simplicity

- For frontend layouts, styling, charts or interactions, read [DESIGN.md](DESIGN.md) before editing and compare browser screenshots with its selected references. Keep prototype adoption separate from visual review.
- Implement the smallest complete change. Reuse existing modules and the standard library before adding dependencies, services or abstractions.
- For a new valuation or a review-driven revision, follow [the analysis workflow](docs/analysis-workflow.md): structured report, independent challenge and at most one revision. Keep execution completion distinct from economic review.
- Keep shared code company-neutral. Issuer prompts, mappings and replay scripts belong in `examples/<company>/`.
- Before changing shared financial logic, follow the [generic analysis rule](docs/planning/decisions.md#generic-analysis-before-company-tuning): name the reusable problem and benefit; keep company-specific forecast corrections in that company's analysis.
- Keep financial meaning, sources, assumptions and deterministic arithmetic inspectable. A matching number does not prove an accounting definition.
- Keep credentials and exact research in ignored local/private storage. The public plan contains delivery status and safe reference paths, never provider datasets or private investment notes.
- Delegate independent tasks when this improves quality or saves time. Give workers bounded ownership and coordinate shared files.

## Checks and pull requests

- Follow [CONTRIBUTING.md](CONTRIBUTING.md) for branches, PR scope, validation and handoff. The user reviews and merges.
- After opening or pushing a PR, run the project [greploop skill](.agents/skills/greploop/SKILL.md) during the active session: inspect feedback, fix justified issues, validate, push and obtain a fresh review without asking the user to repeat these steps. Use its retry/time limits and keep merge user-owned.
- Add tests for meaningful behavior or credible failures. Run appropriate checks; repeat them when subsequent changes or unresolved concerns justify it.
- Keep the README short: purpose, directory map, start commands and links. Put detailed procedures in their owning documents.
- Write short, concrete progress updates and a final account of changes, validation and remaining limits.

## Code Review Rules

- Use an independent read-only reviewer before declaring a PR ready. The reviewer changes no files, starts no new runs, grants no waivers and performs no merges.
- Challenge the proposed solution. For each finding, cite the file and section/line, state the bounded verdict and reasoning, and identify missing evidence for any larger claim. Give an overall recommendation.
- Flag company-specific assumptions in shared code, hidden financial definitions, duplicated plan state and public exposure of research or credentials.

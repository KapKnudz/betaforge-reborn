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

## Boundaries and simplicity

- Implement the smallest complete change. Reuse existing modules and the standard library before adding dependencies, services or abstractions.
- Keep shared code company-neutral. Issuer prompts, mappings and replay scripts belong in `examples/<company>/`.
- Keep financial meaning, sources, assumptions and deterministic arithmetic inspectable. A matching number does not prove an accounting definition.
- Keep credentials and exact research in ignored local/private storage. The public plan contains delivery status and safe reference paths, never provider datasets or private investment notes.
- Delegate independent tasks when this improves quality or saves time. Give workers bounded ownership and coordinate shared files.

## Checks and pull requests

- Follow [CONTRIBUTING.md](CONTRIBUTING.md) for branches, PR scope, validation and handoff. The user reviews and merges.
- Add tests for meaningful behavior or credible failures. Run appropriate checks; repeat them when subsequent changes or unresolved concerns justify it.
- Keep the README short: purpose, directory map, start commands and links. Put detailed procedures in their owning documents.
- Write short, concrete progress updates and a final account of changes, validation and remaining limits.

## Code Review Rules

- Use an independent read-only reviewer before declaring a PR ready. The reviewer changes no files, starts no new runs, grants no waivers and performs no merges.
- Challenge the proposed solution. For each finding, cite the file and section/line, state the bounded verdict and reasoning, and identify missing evidence for any larger claim. Give an overall recommendation.
- Flag company-specific assumptions in shared code, hidden financial definitions, duplicated plan state and public exposure of research or credentials.

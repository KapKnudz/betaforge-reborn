# Working on Betaforge

## One session

1. Read [the plan](work/plan.json), its handoff and the current Git changes.
2. Choose a bounded task and its acceptance criteria. Update the plan as work progresses.
3. Implement, check and obtain independent review. Record evidence and the next action before handoff.

The root [AGENTS.md](AGENTS.md) makes this the default project workflow. [Architecture](docs/architecture.md) defines ownership; [the investment policy](docs/analysis-policy.md) defines financial behavior.

## One pull request

- Use `feat/<short-purpose>` branches from `main`. Keep one reviewable outcome per PR; split unrelated cleanup and company research. Wait for required predecessor merges or make the dependency explicit.
- Shared code stays generic. Keep company-specific examples under `examples/<company>/`; exact evidence and saved runs use the existing private archive workflow.
- Title the PR by the resulting behavior. Explain the problem, change, checks actually run and material limitations. Use the [PR template](.github/pull_request_template.md).
- Link the relevant task ID and include its plan update. Move long research explanations to the appropriate document and link them.
- Preserve unrelated working-tree changes. Stage explicit files; inspect the staged diff for scope and private material before publishing.
- Prepare a draft PR when publication is part of the user's request or already authorized. Mark it ready after validation and independent review. The user reviews and merges; do not merge or push directly to `main`.

## Validation

Run targeted tests for behavior changed. Run the full offline suite before declaring a code PR ready:

```sh
.venv/bin/python -m unittest discover -s tests -v
git diff --check
```

For documentation-only changes, check links, commands and whitespace. For the dashboard, verify the page in a browser as well as its HTTP tests. Existing tests may skip private-evidence cases in a public clone; disclose skips. Live Börsdata/model calls are separate checks and are not implied by an offline test pass.

Have an independent read-only reviewer inspect the connected change, following the root review rules. Resolve findings or state the remaining limitation; record tests and review evidence in the PR and plan. If implementation changes after review, obtain a focused recheck of the affected findings.

## Handoff

Update `work/plan.json`: actual task status, evidence, blockers, session summary and next step. `done` means the task's acceptance criteria are met; it does not imply a PR was merged or the product is production-ready. Record pending review/merge explicitly when relevant.

Use [Mac setup and private research handoff](docs/research-handoff.md) to move workstations. Git carries code and project state; private archives carry exact research. Each workstation keeps its own credentials.

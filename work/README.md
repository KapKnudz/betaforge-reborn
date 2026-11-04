# Current work

[plan.json](plan.json) is the single current delivery plan. Agents maintain it during sessions; the local dashboard rereads it automatically. It does not execute tasks or infer progress from Git.

```sh
.venv/bin/python scripts/serve_progress.py
```

Open **http://127.0.0.1:8765**. Stop with `Ctrl+C`. The workbench shows project progress and architecture; [explicit private exports](../docs/saved-analysis-view.md) add saved company research.

## Update rules

1. At session start, read the plan and Git status. Find the requested task; when continuing the roadmap, use `next_task`.
2. Before implementation, mark the task `in_progress` and set the session handoff. At meaningful milestones or scope changes, re-read and update the file.
3. Mark `done` only after acceptance criteria are met. Add safe evidence paths and a short validation note. Use `blocked` with a concrete blocker when work cannot continue; missing optional evidence need not block unrelated work.
4. Before handoff, update `updated_at`, `session` and `next_task`. State partial work, pending review/merge and unchecked claims explicitly. Validate JSON after editing.

```sh
.venv/bin/python -m json.tool work/plan.json > /dev/null
```

## Fields

| Field | Meaning |
|---|---|
| `version` | Plan format, currently `1`. |
| `updated_at` | ISO 8601 time of the last plan edit, with timezone. |
| `goal`, `scope` | Current destination and agreed release scope. |
| `next_task` | Existing task ID to resume; `null` when the plan is complete. |
| `milestones` | Delivery stages with stable IDs and a short summary. |
| `tasks` | Stable ID, milestone ID, title, status, short `summary` and `purpose`, acceptance criteria, evidence paths, blocker and detailed note. Older plans may omit summary/purpose. |
| `session` | Active/last task ID, summary and next concrete step. |
| `references` | Links to the documents that own policy, architecture and procedures. |

Statuses are `pending`, `in_progress`, `blocked` and `done`. Keep milestone status consistent with its tasks; task counts describe completion of the listed work, not product maturity or valuation quality. Task scope can change, so counts are not a fixed estimate of remaining effort.

One coordinating agent edits the plan during parallel work. Keep tasks bounded and the handoff short; Git preserves previous versions. Store delivery information here, not company financial data, private theses, credentials or duplicated policy text. [Adopted decisions](../docs/planning/decisions.md) and [research notes](../docs/research/system-readiness-review.md) retain their separate roles.

# Betaforge Reborn

Personal company research: collect evidence, check financial definitions and produce explainable valuations.

## Project structure

| Path | Purpose |
|---|---|
| `betaforge/` | Shared data storage, calculations and Codex integration |
| `scripts/` | Commands to collect data, prepare evidence and run analyses |
| `web/progress/` | Local project and saved-research workbench |
| `web/prototypes/` | Preserved visual design trials |
| `work/` | Current goal, priorities, blockers and next steps |
| `docs/` | Architecture, investment policy, formulas and setup |
| `examples/granges/` | Company-specific worked example |
| `tests/` | Automated checks |
| `data/` | Private local evidence and saved analyses; excluded from Git |

## Start here

- **Continue work:** read [agent instructions](AGENTS.md) and the [current plan](work/plan.json).
- **Understand boundaries:** read the [architecture](docs/architecture.md).
- **Design the interface:** read the [design brief](DESIGN.md).
- **Make a change:** follow the [contribution and PR workflow](CONTRIBUTING.md).

## Run locally

Python 3.14.7 is tested. See [Mac setup](docs/research-handoff.md#mac-prerequisites) for prerequisites and credentials.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/serve_progress.py
```

Open **http://127.0.0.1:8765** for progress, visual architecture and the analysis process. To browse company memos, [add private saved-run exports](docs/saved-analysis-view.md).

## Research workflow

1. [Collect data, prepare a frozen packet and run an analysis](docs/company-workflow.md).
2. Apply the [investment policy](docs/analysis-policy.md) and [defined calculations](docs/calculations.md).
3. Preserve exact evidence and results using the [private backup and restore workflow](docs/research-handoff.md).

The primary valuation is forward EV/EBIT with an explicit equity bridge. The [Gränges example](examples/granges/README.md) demonstrates the workflow. Material mapping checks, broader company validation and fuller decision records remain on the plan.
